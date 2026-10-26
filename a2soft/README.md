# AppleSoft BASIC for Windows

A pure-Python port of [applesoft26](https://github.com/jawaidbazyar2/applesoft26),
a native macOS AppleSoft BASIC editor/interpreter. This port runs on Windows
(and anywhere else Python runs) with **no compiler and no third-party
packages** -- only the Python standard library (including `tkinter`, which
ships with the standard Windows installer).

The original project splits cleanly into a portable C interpreter core
(tokenizer, program storage, variables, screen model, expression evaluator,
statement executor -- about 4,300 lines) and a macOS-only Cocoa UI
(editor window, run window, ~2,300 lines of Objective-C). This port
translates the portable core line-for-line into Python (`applesoft/as_*.py`)
and replaces the Cocoa UI with a Tkinter equivalent (`applesoft/gui_*.py`).
Behavior of the interpreter -- tokenization, statement semantics, error
messages, the DOS 3.3 `.abas` save format -- matches the original C code
as closely as a faithful translation allows. One upstream bug was fixed:
`SCRN(x,y)` could never parse (see the comment in `as_exec.py`).

## Requirements

- Python 3.8+ (Windows installer from python.org includes Tcl/Tk by default;
  the Microsoft Store build of Python does too)

That's it -- no `pip install` needed.

## Running

```
python AppleSoft.py
python AppleSoft.py Samples\LEMONADE.abas
```

Double-clicking `AppleSoft.py` also works if `.py` files are associated with
Python on your system.

## Using the program

The editor window is the listing: `line# source`. Breakpoint lines are
highlighted pink.

| Action | How |
| --- | --- |
| Type/replace a program line | Type `<number> <code>` in the Immediate field, press Enter |
| Delete a line | Type just its number in the Immediate field, press Enter |
| Run a command immediately | Type it (no leading number) in the Immediate field, press Enter |
| Edit an existing line | Double-click it in the listing -- it's loaded into the Immediate field |
| Toggle a breakpoint | Right-click the line in the listing |
| Run / Pause / Stop / Step | Toolbar buttons, or the Program menu |
| New / Open / Save | File menu. Programs use the `.abas` extension (same binary format as the original app, interchangeable with it) |
| Open a plain-text listing | File > Open Text... -- reads a `.bas`/`.txt` file of `<number> <statement>` lines (e.g. as produced by `LIST`, or typed in any text editor). Lines with no number or a bad line number are skipped and reported; lines with a syntax error are still imported (so you can fix them in the editor) but reported too. |
| Save a plain-text listing | File > Save As Text... -- writes the current listing out the same way `LIST` would print it, one line per row |

The Output window is the Apple II screen: 40x24 text, plus `GR`, `HGR`,
`HGR2`, and the extended `GR(80,50)` / `HGR(320,200)` / `HGR(640,400)` modes.
Click/drag in it for paddle input (`PDL(0)`/`PDL(1)`, button via left/right
click); keyboard focus follows the window for `INPUT`/`GET`.

`& DELAY seconds` and `& TONE hz,seconds` work as timed pauses; `& TONE`
does not currently produce sound (the original used CoreAudio, which has
no portable equivalent here -- consider it a silent rest).

## Layout

```
windows/
  AppleSoft.py          entry point
  applesoft/
    as_common.py        error codes, AsValue (as_common.h / common.c)
    as_token.py          token bytes + keyword text (as_token.h / token.c)
    as_font.py           character-generator ROM (as_font.h / font.c)
    as_tokenize.py       source <-> tokens (as_tokenize.h / tokenize.c)
    as_program.py        listing storage, renumber, .abas I/O (as_program.h / program.c)
    as_vars.py           scalars + arrays (as_vars.h / vars.c)
    as_screen.py         text/lores/hires screen model (as_screen.h / screen.c, peekpoke.c)
    as_exec.py           expression evaluator + statement executor
                         (expr.c + exec.c + as_internal.h's AsMachine)
    gui_run.py           Output window (replaces RunWindow.m)
    gui_app.py           Editor window + app entry (replaces EditorController.m / main.m)
  Samples/               copied from the original repo
  tests/                 a few sanity tests (not the original ctest suite)
```

## Known gaps vs. the original

- `& TONE` is silent (no portable low-latency audio API in the stdlib).
- `DRAW`/`XDRAW`/`ROT=`/`SCALE=`/`SHLOAD` and `RECALL`/`STORE`/`WAIT`/
  `LOAD`/`SAVE` remain unsupported, same as upstream.
- The editor's inline syntax highlighting (color per character class from
  the tokenizer) isn't wired into the Tkinter listing yet -- the listing
  renders as plain monospace text with breakpoint highlighting only.
- Extended graphics modes (`GR(80,50)`, `HGR(320,200)`, `HGR(640,400)`)
  render correctly but redraw more slowly than the classic modes, since
  pixel blitting is pure-Python.
