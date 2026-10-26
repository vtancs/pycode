"""Run window: an Apple II text/graphics screen rendered with Tkinter.

Port of RunWindow.m / RunView's drawing logic (draw_text / drawClassic /
drawExtended), using a raw PPM byte buffer fed straight into a Tkinter
PhotoImage -- no third-party imaging library required.
"""

import tkinter as tk

from .as_font import as_glyph_on
from .as_screen import (
    AS_DISP_TEXT, AS_DISP_GR, AS_DISP_GR80, AS_DISP_HGR, AS_DISP_HGR2, AS_DISP_H320, AS_DISP_H640,
    as_lores_rgb,
)

_HIRES = {1: 0x1CC000, 2: 0xC847E0, 3: 0xFFFFFF, 5: 0xFF6A00, 6: 0x1B7FDB, 7: 0xFFFFFF}


def _color_of(screen, idx):
    if screen.disp in (AS_DISP_HGR, AS_DISP_HGR2):
        return _HIRES.get(idx & 7, 0x000000)
    return as_lores_rgb(idx)


class _Buf:
    """RGB24 pixel buffer, row-major, black-filled."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.data = bytearray(w * h * 3)

    def put(self, x, y, rgb):
        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            return
        off = (y * self.w + x) * 3
        self.data[off] = (rgb >> 16) & 255
        self.data[off + 1] = (rgb >> 8) & 255
        self.data[off + 2] = rgb & 255

    def fill_block(self, x, y, bw, bh, rgb):
        if bw <= 0 or bh <= 0:
            return
        px = bytes(((rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255))
        x0, x1 = max(x, 0), min(x + bw, self.w)
        if x1 <= x0:
            return
        row = px * (x1 - x0)
        for yy in range(max(y, 0), min(y + bh, self.h)):
            off = (yy * self.w + x0) * 3
            self.data[off:off + len(row)] = row

    def ppm(self):
        header = ("P6\n%d %d\n255\n" % (self.w, self.h)).encode('ascii')
        return header + bytes(self.data)


def _draw_text(buf, screen, row0, nrows, origin_y, flash):
    for r in range(nrows):
        ycell = row0 + r
        if ycell < 0 or ycell > 23:
            continue
        for x in range(40):
            cell = screen.cell[ycell][x]
            style = cell.style
            cursor = screen.cursor_on and screen.cur_x == x and screen.cur_y == ycell and flash
            if style == 2:
                style = 1 if flash else 0
            if cursor:
                style = 1
            fg = 0x000000 if style else 0xFFFFFF
            bg = 0xFFFFFF if style else 0x000000
            ch = cell.ch if cell.ch else ord(' ')
            base_x = x * 7
            base_y = origin_y + r * 8
            for gy in range(8):
                for gx in range(7):
                    on = as_glyph_on(ch, gy, gx)
                    buf.put(base_x + gx, base_y + gy, fg if on else bg)


def _draw_classic(buf_outer_bounds, screen, flash):
    """Classic lores/hires 280x192-ish frame. Returns a _Buf sized to fit."""
    cell_h = 4 if screen.disp == AS_DISP_GR else 1
    grow = screen.gh
    text_rows = 0
    if screen.mixed and screen.disp != AS_DISP_HGR2:
        text_rows = 4
        if screen.disp == AS_DISP_GR:
            grow = screen.gh - 8 if screen.gh > 8 else 0
        else:
            grow = 160 if screen.gh > 32 else screen.gh
    if grow > screen.gh:
        grow = screen.gh
    bw = 280 if screen.disp == AS_DISP_GR else max(screen.gw, 280)
    bh = grow * cell_h + text_rows * 8
    if bw < 1 or bh < 1:
        return None
    buf = _Buf(bw, bh)
    if screen.pix:
        for y in range(grow):
            for x in range(screen.gw):
                rgb = _color_of(screen, screen.pix[y * screen.gw + x])
                if cell_h == 1 and bw == screen.gw:
                    buf.put(x, y, rgb)
                else:
                    buf.fill_block(x * 7, y * cell_h, 7, cell_h, rgb)
    if text_rows:
        _draw_text(buf, screen, 20, 4, grow * cell_h, flash)
    return buf


def _draw_extended(screen, flash):
    """GR(80,50) / HGR(320,200) / HGR(640,400) share a 640x400 grid."""
    kw, kh = 640, 400
    cell = 1
    if screen.disp == AS_DISP_GR80:
        cell = 8
    elif screen.disp == AS_DISP_H320:
        cell = 2
    buf = _Buf(kw, kh)
    if screen.pix and screen.gw > 0 and screen.gh > 0:
        for y in range(screen.gh):
            for x in range(screen.gw):
                rgb = _color_of(screen, screen.pix[y * screen.gw + x])
                buf.fill_block(x * cell, y * cell, cell, cell, rgb)
    text_buf = None
    if screen.mixed:
        text_buf = _Buf(280, 32)
        _draw_text(text_buf, screen, 20, 4, 0, flash)
    return buf, text_buf


def render_frame(screen, flash):
    """Returns (main_buf, text_buf_or_None, text_frac) where text_frac is the
    fraction of the composed frame height occupied by the mixed-mode text
    strip when the two buffers must be stacked by the caller."""
    if screen.disp == AS_DISP_TEXT or not screen.graphics_on:
        buf = _Buf(280, 192)
        _draw_text(buf, screen, 0, 24, 0, flash)
        return buf, None, 0.0
    if screen.disp in (AS_DISP_GR80, AS_DISP_H320, AS_DISP_H640):
        main_buf, text_buf = _draw_extended(screen, flash)
        return main_buf, text_buf, (32.0 / 192.0) if text_buf else 0.0
    buf = _draw_classic(None, screen, flash)
    return buf, None, 0.0


class RunWindow:
    """Toplevel window showing the Apple II text/graphics screen."""

    def __init__(self, master, machine, on_close=None):
        self.machine = machine
        self.on_close = on_close
        self.top = tk.Toplevel(master)
        self.top.title("Output")
        self.top.geometry("640x480+860+80")
        self.top.minsize(280, 192)
        self.top.configure(bg="black")
        self.canvas = tk.Canvas(self.top, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._photo = None
        self._btn0 = False
        self._btn1 = False
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<Button-1>", self._on_button1_down)
        self.canvas.bind("<ButtonRelease-1>", self._on_button1_up)
        self.canvas.bind("<Button-3>", self._on_button3_down)
        self.canvas.bind("<ButtonRelease-3>", self._on_button3_up)
        self.top.bind("<Key>", self._on_key)
        self.top.bind("<BackSpace>", lambda e: self._send_key(127))
        self.top.bind("<Return>", lambda e: self._send_key(ord('\r')))
        self.top.protocol("WM_DELETE_WINDOW", self._close)
        self._flash = 0
        self._flash_count = 0

    def show(self):
        self.top.deiconify()
        self.top.lift()
        self.canvas.focus_set()

    def _close(self):
        self.top.withdraw()
        if self.on_close:
            self.on_close()

    def _send_key(self, ch):
        self.machine.keydown(ch)

    def _on_key(self, event):
        s = event.char
        if not s:
            return
        c = ord(s[0])
        if c > 127:
            return
        self._send_key(c)

    def _apply_mouse(self, event):
        screen = self.machine.screen
        if not screen:
            return
        w = max(self.canvas.winfo_width(), 1)
        h = max(self.canvas.winfo_height(), 1)
        x = int(event.x / w * 255.0)
        y = int((h - event.y) / h * 255.0)
        screen.pdl[0] = max(0, min(255, x))
        screen.pdl[1] = max(0, min(255, y))
        screen.btn0 = 1 if self._btn0 else 0
        screen.btn1 = 1 if self._btn1 else 0

    def _on_motion(self, event):
        self._apply_mouse(event)

    def _on_button1_down(self, event):
        self.canvas.focus_set()
        self._btn0 = True
        self._apply_mouse(event)

    def _on_button1_up(self, event):
        self._btn0 = False
        self._apply_mouse(event)

    def _on_button3_down(self, event):
        self.canvas.focus_set()
        self._btn1 = True
        self._apply_mouse(event)

    def _on_button3_up(self, event):
        self._btn1 = False
        self._apply_mouse(event)

    def redraw(self):
        screen = self.machine.screen
        self.canvas.delete("all")
        if not screen:
            return
        self._flash_count += 1
        if self._flash_count >= 15:
            self._flash_count = 0
            self._flash ^= 1
        main_buf, text_buf, text_frac = render_frame(screen, self._flash)
        cw = max(self.canvas.winfo_width(), 1)
        ch = max(self.canvas.winfo_height(), 1)
        if main_buf is None:
            return
        if text_buf is not None:
            text_h = int(ch * text_frac)
            gfx_h = ch - text_h
            self._blit(main_buf, 0, text_h, cw, gfx_h)
            self._blit(text_buf, 0, 0, cw, text_h)
        else:
            self._blit(main_buf, 0, 0, cw, ch)

    def _blit(self, buf, x, y, dest_w, dest_h):
        if dest_w < 1 or dest_h < 1:
            return
        scale = max(1, min(dest_w // buf.w, dest_h // buf.h) if buf.w and buf.h else 1)
        photo = tk.PhotoImage(data=buf.ppm(), format="PPM")
        if scale > 1:
            photo = photo.zoom(scale, scale)
        dw, dh = photo.width(), photo.height()
        ox = x + (dest_w - dw) // 2
        oy = y + (dest_h - dh) // 2
        self.canvas.create_image(ox, oy, image=photo, anchor="nw")
        # keep a reference so Tk doesn't garbage-collect the image
        self._photo_refs = getattr(self, "_photo_refs", [])
        self._photo_refs.append(photo)
        if len(self._photo_refs) > 4:
            self._photo_refs = self._photo_refs[-2:]
