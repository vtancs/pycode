"""Apple II text/lores/hires screen model. Port of as_screen.h / screen.c.

Errors are returned as int codes here (matching the C API), since callers in
as_exec.py want the exact AS_ERR_ILLEGAL_QUANTITY semantics for PLOT/HLIN/etc.
"""

from .as_common import AS_OK, AS_ERR_ILLEGAL_QUANTITY, AS_ERR_OUT_OF_MEMORY

AS_DISP_TEXT = 0
AS_DISP_GR = 1
AS_DISP_GR80 = 2
AS_DISP_HGR = 3
AS_DISP_HGR2 = 4
AS_DISP_H320 = 5
AS_DISP_H640 = 6

_LORES = [
    0x000000, 0x9A2155, 0x3C22A0, 0xC847E0, 0x0B7A30, 0x777777, 0x1B7FDB, 0x6EC4FF,
    0x8B4E00, 0xFF6A00, 0xBBBBBB, 0xFF7AD5, 0x1CC000, 0xFFE000, 0x4BE3C5, 0xFFFFFF,
]


def as_lores_rgb(index):
    if index < 0 or index > 15:
        index = 0
    return _LORES[index]


class AsCell:
    __slots__ = ("ch", "style")

    def __init__(self, ch=ord(' '), style=0):
        self.ch = ch
        self.style = style


class AsScreen:
    def __init__(self):
        self.disp = AS_DISP_TEXT
        self.mixed = 0
        self.graphics_on = 0
        self.hires = 0
        self.page2 = 0
        self.gw = 0
        self.gh = 0
        self.pix = None  # bytearray, row-major gw*gh
        self.cell = [[AsCell() for _ in range(40)] for _ in range(24)]
        self.cur_x = 0
        self.cur_y = 0
        self.wnd_left = 0
        self.wnd_width = 40
        self.wnd_top = 0
        self.wnd_btm = 24
        self.style = 0
        self.color = 0
        self.hcolor = 0
        self.hx = 0
        self.hy = 0
        self.hvalid = 0
        self.cursor_on = 0
        self.flash_phase = 0
        self.bell = 0
        self.tone_hz = 0.0
        self.pdl = [0, 0]
        self.btn0 = 0
        self.btn1 = 0
        self.key_strobe = -1
        self._window_full()

    # -- setup helpers --------------------------------------------------
    def _window_full(self):
        self.wnd_left = 0
        self.wnd_width = 40
        self.wnd_top = 0
        self.wnd_btm = 24

    def _window_mixed(self):
        self.wnd_left = 0
        self.wnd_width = 40
        self.wnd_top = 20
        self.wnd_btm = 24
        self.cur_x = 0
        self.cur_y = 20

    def _alloc_pix(self, w, h):
        self.pix = bytearray(w * h)
        self.gw = w
        self.gh = h
        self.hvalid = 0

    def is_lores(self):
        return self.disp == AS_DISP_GR or self.disp == AS_DISP_GR80

    def is_hires(self):
        return self.disp in (AS_DISP_HGR, AS_DISP_HGR2, AS_DISP_H320, AS_DISP_H640)

    # -- text ------------------------------------------------------------
    def _scroll_window(self):
        top = max(self.wnd_top, 0)
        bot = min(self.wnd_btm, 24)
        left = self.wnd_left
        right = min(self.wnd_left + self.wnd_width, 40)
        for y in range(top, bot - 1):
            for x in range(left, right):
                self.cell[y][x].ch = self.cell[y + 1][x].ch
                self.cell[y][x].style = self.cell[y + 1][x].style
        if 0 <= bot - 1 < 24:
            for x in range(left, right):
                self.cell[bot - 1][x].ch = ord(' ')
                self.cell[bot - 1][x].style = 0

    def _cr(self):
        self.cur_x = self.wnd_left
        self.cur_y += 1
        if self.cur_y >= self.wnd_btm:
            self._scroll_window()
            self.cur_y = max(self.wnd_btm - 1, 0)

    def _clear_to_window_end(self):
        left = max(self.wnd_left, 0)
        right = min(self.wnd_left + self.wnd_width, 40)
        top = max(self.wnd_top, 0)
        bot = min(self.wnd_btm, 24)
        for y in range(top, bot):
            if y < self.cur_y:
                continue
            x0 = self.cur_x if y == self.cur_y else left
            x0 = max(x0, left)
            for x in range(x0, right):
                if 0 <= x <= 39:
                    self.cell[y][x].ch = ord(' ')
                    self.cell[y][x].style = 0

    def putc(self, ch):
        if ch in (ord('\r'), ord('\n')):
            self._cr()
            return
        if ch == 8:
            self.backspace()
            return
        if ch == 7:
            self.bell += 1
            return
        if ch == 11:
            self._clear_to_window_end()
            return
        if ch < 32 or ch > 126:
            return
        if self.cur_y < 0:
            self.cur_y = 0
        if self.cur_y > 23:
            self.cur_y = 23
        if self.cur_x < 0:
            self.cur_x = 0
        if self.cur_x > 39:
            self._cr()
        if 0 <= self.cur_x < 40 and 0 <= self.cur_y < 24:
            self.cell[self.cur_y][self.cur_x].ch = ch
            self.cell[self.cur_y][self.cur_x].style = self.style
        self.cur_x += 1
        if self.cur_x >= self.wnd_left + self.wnd_width or self.cur_x >= 40:
            self._cr()

    def puts(self, text):
        for ch in text:
            self.putc(ch if isinstance(ch, int) else ord(ch))

    def backspace(self):
        if self.cur_x > self.wnd_left:
            self.cur_x -= 1

    def comma_tab(self):
        ch = self.cur_x
        if ch >= 24:
            self._cr()
            return
        self.cur_x = (ch + 16) & ~15
        if self.cur_x >= self.wnd_left + self.wnd_width:
            self._cr()

    def home(self):
        right = min(self.wnd_left + self.wnd_width, 40)
        for y in range(self.wnd_top, min(self.wnd_btm, 24)):
            for x in range(self.wnd_left, right):
                self.cell[y][x].ch = ord(' ')
                self.cell[y][x].style = 0
        self.cur_x = self.wnd_left
        self.cur_y = self.wnd_top

    def text_mode(self):
        self.graphics_on = 0
        self.mixed = 0
        self.hires = 0
        self.page2 = 0
        self.disp = AS_DISP_TEXT
        self._window_full()
        self.cur_x = 0
        self.cur_y = 0

    def gr(self, cols, rows):
        self.graphics_on = 1
        self.hires = 0
        self.page2 = 0
        self.mixed = 1
        if cols == 80 and rows == 50:
            self.disp = AS_DISP_GR80
            self._alloc_pix(80, 50)
        else:
            self.disp = AS_DISP_GR
            self._alloc_pix(40, 48)
        self._window_mixed()

    def hgr(self, which):
        self.graphics_on = 1
        self.hires = 1
        if which == 3:
            self.disp = AS_DISP_H320
            self.mixed = 1
            self.page2 = 0
            self._alloc_pix(320, 200)
            self._window_mixed()
            return
        if which == 2:
            self.disp = AS_DISP_H640
            self.mixed = 1
            self.page2 = 0
            self._alloc_pix(640, 400)
            self._window_mixed()
            return
        if which == 1:
            self.disp = AS_DISP_HGR2
            self.mixed = 0
            self.page2 = 1
            self._alloc_pix(280, 192)
            self._window_full()
            return
        self.disp = AS_DISP_HGR
        self.mixed = 1
        self.page2 = 0
        self._alloc_pix(280, 192)
        self._window_mixed()

    # -- graphics ----------------------------------------------------------
    def _in_pix(self, x, y):
        return self.pix is not None and 0 <= x < self.gw and 0 <= y < self.gh

    def plot(self, x, y):
        if not self.is_lores() or not self._in_pix(x, y):
            return AS_ERR_ILLEGAL_QUANTITY
        if self.color < 0 or self.color > 15:
            return AS_ERR_ILLEGAL_QUANTITY
        self.pix[y * self.gw + x] = self.color
        return AS_OK

    def hlin(self, x1, x2, y):
        if x1 > x2:
            x1, x2 = x2, x1
        if not self.is_lores() or y < 0 or y >= self.gh or x1 < 0 or x2 >= self.gw:
            return AS_ERR_ILLEGAL_QUANTITY
        for x in range(x1, x2 + 1):
            self.pix[y * self.gw + x] = self.color
        return AS_OK

    def vlin(self, y1, y2, x):
        if y1 > y2:
            y1, y2 = y2, y1
        if not self.is_lores() or x < 0 or x >= self.gw or y1 < 0 or y2 >= self.gh:
            return AS_ERR_ILLEGAL_QUANTITY
        for y in range(y1, y2 + 1):
            self.pix[y * self.gw + x] = self.color
        return AS_OK

    def _stamp(self, x, y, color):
        if self._in_pix(x, y):
            self.pix[y * self.gw + x] = color

    def _bresenham(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = y0 - y1 if y1 > y0 else y1 - y0  # negative of abs(y1-y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self._stamp(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def _hcolor_ok(self):
        if self.disp in (AS_DISP_H320, AS_DISP_H640):
            return 0 <= self.hcolor <= 15
        return 0 <= self.hcolor <= 7

    def hplot(self, x, y):
        if not self.is_hires() or not self._hcolor_ok() or not self._in_pix(x, y):
            return AS_ERR_ILLEGAL_QUANTITY
        self._stamp(x, y, self.hcolor)
        self.hx, self.hy, self.hvalid = x, y, 1
        return AS_OK

    def hplot_to(self, x, y):
        if not self.is_hires() or not self._hcolor_ok() or not self._in_pix(x, y):
            return AS_ERR_ILLEGAL_QUANTITY
        if not self.hvalid:
            self.hx = 0
            self.hy = 0
        self._bresenham(self.hx, self.hy, x, y, self.hcolor)
        self.hx, self.hy, self.hvalid = x, y, 1
        return AS_OK

    def scrn(self, x, y):
        """Returns (err, color)."""
        if self.pix is None or not self._in_pix(x, y):
            return AS_ERR_ILLEGAL_QUANTITY, 0
        return AS_OK, self.pix[y * self.gw + x]

    # -- soft switches / peek/poke -----------------------------------------
    def _resolve_soft(self):
        if not self.graphics_on:
            self.disp = AS_DISP_TEXT
            self.mixed = 0
            return
        if self.disp in (AS_DISP_GR80, AS_DISP_H320, AS_DISP_H640):
            return
        if self.hires:
            if self.page2 and not self.mixed:
                self.disp = AS_DISP_HGR2
            else:
                self.disp = AS_DISP_HGR
                if self.gw != 280 or self.gh != 192:
                    self._alloc_pix(280, 192)
        else:
            self.disp = AS_DISP_GR
            if self.gw != 40 or self.gh != 48:
                self._alloc_pix(40, 48)

    def soft(self, addr):
        if addr == 0xC050:
            self.graphics_on = 1
        elif addr == 0xC051:
            self.graphics_on = 0
            self.disp = AS_DISP_TEXT
        elif addr == 0xC052:
            self.mixed = 0
        elif addr == 0xC053:
            self.mixed = 1
        elif addr == 0xC054:
            self.page2 = 0
        elif addr == 0xC055:
            self.page2 = 1
        elif addr == 0xC056:
            self.hires = 0
        elif addr == 0xC057:
            self.hires = 1
        else:
            return
        self._resolve_soft()

    def poke(self, addr, value):
        if value < 0 or value > 255:
            return AS_ERR_ILLEGAL_QUANTITY
        if 0xC050 <= addr <= 0xC057:
            self.soft(addr)
            return AS_OK
        if addr == 0xC010 or addr == 49168:
            if self.key_strobe > 0:
                self.key_strobe &= 0x7f
            return AS_OK
        if addr == 32:
            self.wnd_left = min(value, 39)
        elif addr == 33:
            self.wnd_width = max(value, 1)
            if self.wnd_left + self.wnd_width > 40:
                self.wnd_width = 40 - self.wnd_left
        elif addr == 34:
            self.wnd_top = min(value, 23)
            if self.wnd_btm <= self.wnd_top:
                self.wnd_btm = self.wnd_top + 1
        elif addr == 35:
            self.wnd_btm = min(value, 24)
            if self.wnd_btm <= self.wnd_top:
                self.wnd_btm = self.wnd_top + 1
        elif addr == 36:
            self.cur_x = value
        elif addr == 37:
            self.cur_y = min(value, 23)
        elif addr == 50:
            if value == 0x3F:
                self.style = 1
            elif value == 0x7F:
                self.style = 2
            else:
                self.style = 0
        return AS_OK

    def peek(self, addr):
        if 0xC050 <= addr <= 0xC057:
            self.soft(addr)
            return 0
        if addr == 0xC000 or addr == 49152:
            return 0 if self.key_strobe < 0 else self.key_strobe
        if addr == 0xC010 or addr == 49168:
            v = 0 if self.key_strobe < 0 else (self.key_strobe & 0x7f)
            if self.key_strobe > 0:
                self.key_strobe &= 0x7f
            return v
        if addr in (49249, 0xC061):
            return 128 if self.btn0 else 0
        if addr in (49250, 0xC062):
            return 128 if self.btn1 else 0
        if addr == 32:
            return self.wnd_left
        if addr == 33:
            return self.wnd_width
        if addr == 34:
            return self.wnd_top
        if addr == 35:
            return self.wnd_btm
        if addr == 36:
            return self.cur_x
        if addr == 37:
            return self.cur_y
        if addr == 50:
            if self.style == 1:
                return 0x3F
            if self.style == 2:
                return 0x7F
            return 0xFF
        return 0
