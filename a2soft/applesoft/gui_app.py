"""Editor window and application entry point.

A from-scratch Tkinter re-implementation of the workflow described in the
original macOS app's README: the editor window is the listing (line number +
breakpoint + source), a bottom Immediate field accepts a typed line (a
leading line number stores it, a bare number deletes it, anything else runs
now and prints to the run window).
"""

import os
import re
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from .as_common import AS_OK, AS_END, AS_INPUT, AS_GET, AS_DELAY, AS_PAUSED, AS_ERR_SYNTAX, AsError, as_error_text
from .as_program import AsProgram
from .as_screen import AsScreen
from .as_exec import AsMachine, as_check_line
from .as_tokenize import as_tokenize, as_detokenize
from .gui_run import RunWindow

_TEXT_LINE_RE = re.compile(r'^\s*(\d+)\s?(.*)$')

TICK_MS = 30
QUANTUM_SECONDS = 0.02


class EditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AppleSoft BASIC")
        self.root.geometry("760x620+60+60")

        self.prog = AsProgram()
        self.screen = AsScreen()
        self.machine = AsMachine(self.prog, self.screen)
        self.run_window = None
        self.file_path = None
        self._line_rows = []  # row index (0-based) -> AsLine, parallel to listing
        self._ticking = False

        self._build_menu()
        self._build_widgets()
        self.refresh_listing()
        self._set_status("")

    # -- UI construction -------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.cmd_new, accelerator="Ctrl+N")
        filemenu.add_command(label="Open...", command=self.cmd_open, accelerator="Ctrl+O")
        filemenu.add_command(label="Open Text...", command=self.cmd_open_text)
        filemenu.add_command(label="Save", command=self.cmd_save, accelerator="Ctrl+S")
        filemenu.add_command(label="Save As...", command=self.cmd_save_as)
        filemenu.add_command(label="Save As Text...", command=self.cmd_save_as_text)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        progmenu = tk.Menu(menubar, tearoff=0)
        progmenu.add_command(label="Run", command=self.cmd_run, accelerator="Ctrl+R")
        progmenu.add_command(label="Pause", command=self.cmd_pause)
        progmenu.add_command(label="Stop", command=self.cmd_stop, accelerator="Ctrl+.")
        progmenu.add_command(label="Step", command=self.cmd_step)
        menubar.add_cascade(label="Program", menu=progmenu)

        self.root.config(menu=menubar)
        self.root.bind("<Control-n>", lambda e: self.cmd_new())
        self.root.bind("<Control-o>", lambda e: self.cmd_open())
        self.root.bind("<Control-s>", lambda e: self.cmd_save())
        self.root.bind("<Control-r>", lambda e: self.cmd_run())

    def _build_widgets(self):
        toolbar = tk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        tk.Button(toolbar, text="Run", command=self.cmd_run).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Pause", command=self.cmd_pause).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Stop", command=self.cmd_stop).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Step", command=self.cmd_step).pack(side=tk.LEFT, padx=2, pady=2)

        self.listing = tk.Text(self.root, font=("Consolas", 12), wrap="none",
                                background="#fdfdf5", undo=False)
        self.listing.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=4, pady=(2, 0))
        self.listing.tag_configure("breakpoint", background="#ffd0d0")
        self.listing.tag_configure("keyword", foreground="#0000AA")
        self.listing.tag_configure("remark", foreground="#008000")
        self.listing.bind("<Double-Button-1>", self._on_listing_double_click)
        self.listing.bind("<Button-3>", self._on_listing_right_click)
        self.listing.bind("<Key>", lambda e: "break")  # read-only
        self.listing.bind("<<Paste>>", lambda e: "break")

        bottom = tk.Frame(self.root)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=4, pady=4)
        tk.Label(bottom, text="Immediate:").pack(side=tk.LEFT)
        self.entry = tk.Entry(bottom, font=("Consolas", 12))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.entry.bind("<Return>", self._on_entry_return)
        self.entry.focus_set()

        self.status_var = tk.StringVar()
        status = tk.Label(self.root, textvariable=self.status_var, anchor="w",
                           relief=tk.SUNKEN, font=("Consolas", 11))
        status.pack(side=tk.BOTTOM, fill=tk.X)
        status.bind("<Button-1>", self._on_status_click)

    # -- listing display --------------------------------------------------
    def refresh_listing(self):
        self.listing.configure(state=tk.NORMAL)
        self.listing.delete("1.0", tk.END)
        self._line_rows = []
        for ln in self.prog.lines:
            text = as_detokenize(ln.tokens)
            display = "%5d  %s" % (ln.number, text)
            row = len(self._line_rows) + 1
            self.listing.insert(tk.END, display + "\n")
            if ln.breakpoint:
                self.listing.tag_add("breakpoint", "%d.0" % row, "%d.end" % row)
            self._line_rows.append(ln)
        self.listing.configure(state=tk.DISABLED)

    def _row_at_event(self, event):
        index = self.listing.index("@%d,%d" % (event.x, event.y))
        row = int(index.split('.')[0]) - 1
        if 0 <= row < len(self._line_rows):
            return row
        return None

    def _on_listing_double_click(self, event):
        row = self._row_at_event(event)
        if row is None:
            return
        ln = self._line_rows[row]
        text = as_detokenize(ln.tokens)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, "%d %s" % (ln.number, text))
        self.entry.focus_set()
        self.entry.icursor(tk.END)

    def _on_listing_right_click(self, event):
        row = self._row_at_event(event)
        if row is None:
            return
        ln = self._line_rows[row]
        idx = self.prog.lines.index(ln)
        self.prog.set_break(idx, not ln.breakpoint)
        self.refresh_listing()

    def _on_status_click(self, event):
        text = self.status_var.get()
        marker = " IN "
        pos = text.rfind(marker)
        if pos < 0:
            return
        tail = text[pos + len(marker):]
        if tail.isdigit():
            self._scroll_to_line(int(tail))

    def _scroll_to_line(self, number):
        for i, ln in enumerate(self.prog.lines):
            if ln.number == number:
                self.listing.see("%d.0" % (i + 1))
                return

    # -- status -------------------------------------------------------
    def _set_status(self, text):
        self.status_var.set(text or "")

    # -- immediate field ------------------------------------------------
    def _on_entry_return(self, event):
        text = self.entry.get()
        self.entry.delete(0, tk.END)
        try:
            kind, err = self.machine.prompt(text)
        except AsError as e:
            kind, err = 0, e.code
        if err is not None:
            self._set_status("?SYNTAX ERROR")
            return
        self.refresh_listing()
        if kind == 2:
            self._ensure_run_window()
            self.run_window.show()
            self._start_ticking()
        self._set_status(self.machine.status)

    # -- run window / ticking -------------------------------------------
    def _ensure_run_window(self):
        if self.run_window is None:
            self.run_window = RunWindow(self.root, self.machine, on_close=self._on_run_window_closed)

    def _on_run_window_closed(self):
        self.machine.stop()

    def _start_ticking(self):
        if self._ticking:
            return
        self._ticking = True
        self._tick()

    def _tick(self):
        m = self.machine
        if m.running:
            try:
                rc = m.quantum(QUANTUM_SECONDS)
            except AsError as e:
                rc = e.code
            if rc not in (AS_OK, AS_INPUT, AS_GET, AS_DELAY, AS_PAUSED, AS_END):
                pass  # error already recorded in m.status
        if self.run_window is not None:
            self.run_window.redraw()
        self._set_status(m.status)
        if not m.running and not m.paused:
            self._ticking = False
            self.refresh_listing()
            return
        self.root.after(TICK_MS, self._tick)

    # -- commands -------------------------------------------------------
    def cmd_run(self):
        self.machine.run()
        self._ensure_run_window()
        self.run_window.show()
        self._start_ticking()
        self._set_status(self.machine.status)

    def cmd_pause(self):
        self.machine.pause()
        self._set_status(self.machine.status)

    def cmd_stop(self):
        self.machine.stop()
        self._set_status(self.machine.status)

    def cmd_step(self):
        self.machine.do_step()
        self._ensure_run_window()
        self.run_window.show()
        self._start_ticking()
        self._set_status(self.machine.status)

    def _reset_screen(self):
        """A fresh program should not inherit leftover text/graphics from
        whatever the previous program left on the Apple II screen."""
        self.screen = AsScreen()
        self.machine.screen = self.screen
        if self.run_window is not None:
            self.run_window.redraw()

    def cmd_new(self):
        if self.prog.dirty and not messagebox.askyesno("New", "Discard unsaved changes?"):
            return
        self.machine.stop()
        self.prog.clear()
        self.machine.edited()
        self._reset_screen()
        self.file_path = None
        self.refresh_listing()
        self._set_status("")

    def cmd_open(self):
        path = filedialog.askopenfilename(filetypes=[("AppleSoft programs", "*.abas"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
            self.machine.stop()
            self.prog.load(data)
            self.machine.edited()
            self._reset_screen()
        except (AsError, OSError) as e:
            messagebox.showerror("Open", "Could not load program:\n%s" % e)
            return
        self.file_path = path
        self.refresh_listing()
        self._set_status("")

    def cmd_open_text(self):
        """Load a plain-text BASIC listing (one `<number> <statement>` per
        line, as produced by LIST or any text editor) -- as opposed to the
        tokenized DOS 3.3 .abas format that cmd_open() reads."""
        path = filedialog.askopenfilename(
            filetypes=[("BASIC text", "*.bas *.txt *.lst"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            messagebox.showerror("Open Text", "Could not read file:\n%s" % e)
            return

        parsed = []
        problems = []
        for lineno, raw in enumerate(text.splitlines(), 1):
            line = raw.rstrip("\r\n")
            if not line.strip():
                continue
            m = _TEXT_LINE_RE.match(line)
            if not m:
                problems.append("line %d: no line number -- skipped (%s)" % (lineno, line.strip()[:40]))
                continue
            number = int(m.group(1))
            if number > 63999:
                problems.append("line %d: line number %d out of range -- skipped" % (lineno, number))
                continue
            tokenized, length = as_tokenize(m.group(2))
            tokens = tokenized.bytes[:length]
            # Only flag genuine grammar errors here. as_check_line runs the
            # line with every variable read as 0 (it hasn't executed yet),
            # so runtime-ish codes like DIVISION BY ZERO or ILLEGAL QUANTITY
            # routinely fire on perfectly good lines (e.g. "A = B/C" before
            # B and C are ever assigned) and would be false positives.
            rc, err_at = as_check_line(tokens)
            if rc == AS_ERR_SYNTAX:
                problems.append("line %d (%d): %s" % (lineno, number, as_error_text(rc)))
            parsed.append((number, tokens))

        if not parsed:
            messagebox.showwarning("Open Text", "No BASIC lines found in that file.")
            return

        self.machine.stop()
        self.prog.clear()
        for number, tokens in parsed:
            self.prog.upsert(number, tokens, 0)
        self.prog.dirty = 1
        self.machine.edited()
        self._reset_screen()
        self.file_path = None  # a text import isn't tied to a .abas save path
        self.refresh_listing()
        if problems:
            shown = "\n".join(problems[:20])
            if len(problems) > 20:
                shown += "\n... and %d more" % (len(problems) - 20)
            messagebox.showwarning("Open Text", "Imported %d line(s) with %d issue(s):\n\n%s"
                                    % (len(parsed), len(problems), shown))
            self._set_status("Imported with %d issue(s)" % len(problems))
        else:
            self._set_status("Imported %d line(s)" % len(parsed))

    def cmd_save(self):
        if not self.file_path:
            return self.cmd_save_as()
        self._save_to(self.file_path)

    def cmd_save_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".abas",
                                             filetypes=[("AppleSoft programs", "*.abas"), ("All files", "*.*")])
        if not path:
            return
        self._save_to(path)

    def _save_to(self, path):
        try:
            data = self.prog.save()
            with open(path, "wb") as f:
                f.write(data)
            self.prog.mark_clean()
            self.file_path = path
        except (AsError, OSError) as e:
            messagebox.showerror("Save", "Could not save program:\n%s" % e)

    def cmd_save_as_text(self):
        path = filedialog.asksaveasfilename(defaultextension=".bas",
                                             filetypes=[("BASIC text", "*.bas *.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            lines = ["%d %s" % (ln.number, as_detokenize(ln.tokens)) for ln in self.prog.lines]
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(lines) + ("\n" if lines else ""))
        except OSError as e:
            messagebox.showerror("Save As Text", "Could not save file:\n%s" % e)


def main():
    root = tk.Tk()
    app = EditorApp(root)
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        try:
            with open(sys.argv[1], "rb") as f:
                app.prog.load(f.read())
            app.file_path = sys.argv[1]
            app.refresh_listing()
        except Exception:
            pass
    root.mainloop()


if __name__ == "__main__":
    main()
