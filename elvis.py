"""
Conversion of QBasic SCREEN 13 / DRAW / PAINT program to Python + pygame.

QBasic SCREEN 13 is 320×200 pixels, 256-colour mode.
Colour 15 = white, colour 0 = black.

DRAW command mini-language used here:
  U/D/L/R/E/F/G/H  – move 1 step in a cardinal/diagonal direction (and draw)
  U#/D#/L#/R#/...  – move # steps
  BM x,y           – Blind Move to absolute position (no draw)
  M+dx,+dy         – move relative (signed); if no sign, absolute
  Cx               – set colour (C0 = black)

All directions draw a line in the current colour unless prefixed with B (blind).

Step size in SCREEN 13 DRAW is 1 pixel by default.
Diagonals (E/F/G/H) move 1 pixel in each axis per step.
"""

import pygame
import sys
import re

# ---------------------------------------------------------------------------
# SCREEN 13 resolution
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 320, 200
SCALE = 3          # display scale so it's visible on modern screens

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ---------------------------------------------------------------------------
# DRAW interpreter
# ---------------------------------------------------------------------------

class DrawState:
    def __init__(self, surface: pygame.Surface):
        self.surf = surface
        self.x = 0.0
        self.y = 0.0
        self.color = WHITE   # default colour 15 = white

    def _put(self, x, y):
        """Draw a pixel at (x,y) – clipped to surface."""
        ix, iy = int(round(x)), int(round(y))
        if 0 <= ix < self.surf.get_width() and 0 <= iy < self.surf.get_height():
            self.surf.set_at((ix, iy), self.color)

    def _line(self, x1, y1, x2, y2):
        """Draw a 1-pixel line between two float positions."""
        pygame.draw.line(self.surf, self.color,
                         (int(round(x1)), int(round(y1))),
                         (int(round(x2)), int(round(y2))), 1)

    def run(self, cmd: str):
        """Parse and execute a DRAW command string."""
        # Normalise: collapse whitespace, upper-case
        s = re.sub(r'\s+', '', cmd).upper()
        i = 0
        n = len(s)

        def peek():
            return s[i] if i < n else ''

        def read_int():
            """Read an optional integer (possibly signed) from s[i]."""
            nonlocal i
            sign = 1
            if i < n and s[i] in ('+', '-'):
                if s[i] == '-':
                    sign = -1
                i += 1
            start = i
            while i < n and s[i].isdigit():
                i += 1
            if i == start:
                return None
            return sign * int(s[start:i])

        def do_step(dx, dy, blind=False, steps=1):
            nonlocal i
            x0, y0 = self.x, self.y
            self.x += dx * steps
            self.y += dy * steps
            if not blind:
                self._line(x0, y0, self.x, self.y)

        while i < n:
            ch = s[i]
            i += 1

            # ---------- Blind prefix ----------
            if ch == 'B':
                if i >= n:
                    break
                nxt = s[i]
                i += 1
                if nxt == 'M':
                    # BM x,y  – blind move absolute
                    x_val = read_int()
                    assert s[i] == ','; i += 1
                    y_val = read_int()
                    self.x = float(x_val)
                    self.y = float(y_val)
                else:
                    # B<dir>[n] – blind move in direction
                    steps = read_int()
                    if steps is None:
                        steps = 1
                    _apply_dir(nxt, steps, blind=True)
                continue

            # ---------- Colour ----------
            if ch == 'C':
                c_num = read_int()
                if c_num == 0:
                    self.color = BLACK
                elif c_num == 15:
                    self.color = WHITE
                else:
                    self.color = WHITE   # default
                continue

            # ---------- Absolute/relative move ----------
            if ch == 'M':
                # M[+/-]x,[+/-]y
                raw_x_sign = ''
                if i < n and s[i] in ('+', '-'):
                    raw_x_sign = s[i]
                x_val = read_int()
                assert i < n and s[i] == ',', f"Expected ',' at {i}: {s}"
                i += 1
                y_val = read_int()
                x0, y0 = self.x, self.y
                if raw_x_sign in ('+', '-'):
                    # relative
                    nx = self.x + (x_val if x_val is not None else 0)
                    ny = self.y + (y_val if y_val is not None else 0)
                else:
                    # absolute
                    nx = float(x_val)
                    ny = float(y_val)
                self._line(self.x, self.y, nx, ny)
                self.x, self.y = nx, ny
                continue

            # ---------- Directional commands ----------
            steps = read_int()
            if steps is None:
                steps = 1

            def _apply_dir(d, st, blind=False):
                DX = {'U': 0, 'D': 0, 'L': -1, 'R': 1,
                      'E': 1, 'F': 1, 'G': -1, 'H': -1}
                DY = {'U': -1, 'D': 1, 'L': 0, 'R': 0,
                      'E': -1, 'F': 1, 'G': 1, 'H': -1}
                do_step(DX.get(d, 0), DY.get(d, 0), blind=blind, steps=st)

            _apply_dir(ch, steps)


# ---------------------------------------------------------------------------
# PAINT  (scanline flood-fill)
# ---------------------------------------------------------------------------

def paint(surf: pygame.Surface, seed_x: int, seed_y: int,
          fill_color, border_color):
    """Flood-fill starting at (seed_x, seed_y), filling until border_color."""
    w, h = surf.get_size()
    if not (0 <= seed_x < w and 0 <= seed_y < h):
        return
    seed_pixel = surf.get_at((seed_x, seed_y))[:3]
    border_rgb = border_color[:3] if len(border_color) == 4 else border_color
    fill_rgb   = fill_color[:3]   if len(fill_color)   == 4 else fill_color

    if seed_pixel == border_rgb or seed_pixel == fill_rgb:
        return

    stack = [(seed_x, seed_y)]
    visited = set()

    while stack:
        cx, cy = stack.pop()
        if (cx, cy) in visited:
            continue
        if not (0 <= cx < w and 0 <= cy < h):
            continue
        px = surf.get_at((cx, cy))[:3]
        if px == border_rgb or px == fill_rgb:
            continue
        visited.add((cx, cy))
        surf.set_at((cx, cy), fill_color)
        stack.extend([(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)])


# ---------------------------------------------------------------------------
# DRAW strings from the original program (verbatim)
# ---------------------------------------------------------------------------

DRAW_COMMANDS = [
    "C0",
    "                       BM104,45                       ",
    "                U6M+2,-6E2U2E3RE2M+7,-3               ",
    "         M+11,-3M+3,-2R7ER19FR3FRM+5,2R5M+3,1         ",
    "       M+10,5FRF4RF3M+4,17M+1,4M-3,+6GM-1,+7D3G2      ",
    "        D5M-2,+3GD14GD7G3M-2,+1M+3,-11U3M-2,-13U9     ",
    "       M-2,-5UHM-2,-6H2M-5,-2M-3,-1L11GL3M-7,-3LH     ",
    "      M-6,-1G3FDM-5,-2L5M-7,+1M-3,+1M-2,+4DM-2,+5     ",
    "  M+2,+1G2DRDGDFM-7,+4D9GD6M+2,7M+8,16DFD10FD2M+4,8F  ",
    "   DF5RF5RF3R3FR14ER2E9R7    M-4,+7M-5,+10M-8,+22DU   ",
    "   M-3,-7M-3,-1                          M-6,-3H11L   ",
    "    H8UH5UH3UH2                           M-2,-4H2U   ",
    "   M-7,-25L3HL                             M-4,-8     ",
    "    M-2,-4U17                              M-3,-7     ",
    "     M+1,-4E2M-3,-7U8EUE4         BM130,81M+5,1R6     ",
    "    FR4FRF3D3GL3FL3M-4,-2G2D    L3HL2DFM+3,1R2L9H     ",
    "      GLEU2L3H3LHLU2E2RER2      M+5,-2BM165,93U2      ",
    "     M+1,-3E4   M+13,-2               RM+7,3D4G3      ",
    "       L3DLD3                             M-7,-1      ",
    "        M+5,-1L4                                      ",
    "         M+4,-1L3       EUHD    LD2L3                 ",
    "          M-3,-1UL      G2L4BM148,113                 ",
    "           M+1,4R5       F2R5M+4,-2                   ",
    "             R2EU5    M+1,2D7GDGLGL5H                 ",
    "             LM-5,-2       L4UHU5                     ",
    "              BM          154,128                     ",
    "               R3FRER2ER            F2RF2R            ",
    "                 DL4HL10HG       L3GL5UER             ",
    "                    EM+5,-1RBM147,133F3               ",
    "                        M+3,1R10E2RE                  ",
    "                          M-3,+6L13                   ",
    "                            M-3,-6                    ",
]

PAINT_CALLS = [
    # (x, y, fill_color, border_color)
    (200, 50,  BLACK, BLACK),
    (140, 85,  BLACK, BLACK),
    (175, 85,  BLACK, BLACK),
    (160, 120, BLACK, BLACK),
    (150, 130, BLACK, BLACK),
    (155, 139, BLACK, BLACK),
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    pygame.init()
    # Internal surface at original SCREEN 13 resolution
    canvas = pygame.Surface((WIDTH, HEIGHT))
    canvas.fill(WHITE)   # PAINT (0,0), 15  → fill entire screen white

    # Run DRAW commands
    state = DrawState(canvas)
    # The first DRAW is "C0" – set colour to black, pen stays at (0,0).
    # The second is BM104,45 – move pen to (104,45) with no draw.
    for cmd in DRAW_COMMANDS:
        state.run(cmd)

    # Run PAINT calls (fill enclosed regions with black, stopping at black border)
    for px, py, fill_col, border_col in PAINT_CALLS:
        paint(canvas, px, py, fill_col, border_col)

    # Scale up for display
    display = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE))
    pygame.display.set_caption("QBasic DRAW → pygame")
    scaled = pygame.transform.scale(canvas, (WIDTH * SCALE, HEIGHT * SCALE))
    display.blit(scaled, (0, 0))
    pygame.display.flip()

    # Event loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
