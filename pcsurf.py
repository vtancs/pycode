"""
pcsurf.py — 3D surface plot with hidden line removal
Python/pygame conversion of pcsurf.bas by K Moerman

The original algorithm sweeps rows of the surface front-to-back (increasing Y).
For each screen column it maintains:
  fmax[col] = smallest yscr drawn so far (upper/top surface)
  fmin[col] = largest  yscr drawn so far (lower/bottom surface)

Both surfaces draw in the same bright green. Hidden lines are suppressed by
simply not drawing segments that fall inside the already-visible envelope —
the black background shows through as the characteristic "wireframe" gaps.
"""

import math
import pygame
import sys

# ── parameters identical to the BASIC source ─────────────────────────────────
WIDTH, HEIGHT = 640, 350
XMAX, YMAX, ZMAX = 12.0, 12.0, 1.5
NH, NV = 120, 100
SCALE  = 210

PI    = math.pi
ALPHA = PI / 4
K     = 0.4
CA    = K * math.cos(ALPHA)
SA    = K * math.sin(ALPHA)

HM = WIDTH  // 2   # 320
VM = HEIGHT // 2   # 175

DX = 2 * XMAX / NH
DY = 2 * YMAX / NV

COLOR_GREEN = (0, 255, 0)
COLOR_BG    = (0, 0,   0)


def project(xw, yw, z):
    xx = xw / XMAX * SCALE
    yy = yw / YMAX * SCALE
    zz = z  / ZMAX * SCALE
    xs = int(HM + xx + yy * CA)
    ys = int(VM - zz - SA * yy)
    return xs, ys


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("3D Surface Plot — pcsurf")
    screen.fill(COLOR_BG)

    INF  =  9999
    fmax = [ INF] * WIDTH   # upper envelope: smallest yscr seen per column
    fmin = [-INF] * WIDTH   # lower envelope: largest  yscr seen per column

    yw = -YMAX
    for _v in range(NV + 1):
        xw = -XMAX
        prev_top = None
        prev_bot = None

        for _h in range(NH + 1):
            r = math.sqrt(xw * xw + yw * yw)
            z = 1.0 if r == 0.0 else math.sin(r) / r

            xs, ys = project(xw, yw, z)

            if 0 <= xs < WIDTH:
                # Upper surface: visible when this point is ABOVE stored top
                # BASIC: (348-yscr) > FMAX%(xs)  →  yscr < fmax[xs]
                if ys < fmax[xs]:
                    if prev_top is not None:
                        pygame.draw.line(screen, COLOR_GREEN, prev_top, (xs, ys))
                    fmax[xs] = ys
                    prev_top = (xs, ys)
                else:
                    prev_top = None

                # Lower surface: visible when this point is BELOW stored bottom
                # BASIC: yscr > FMIN%(xs)
                if ys > fmin[xs]:
                    if prev_bot is not None:
                        pygame.draw.line(screen, COLOR_GREEN, prev_bot, (xs, ys))
                    fmin[xs] = ys
                    prev_bot = (xs, ys)
                else:
                    prev_bot = None
            else:
                prev_top = None
                prev_bot = None

            xw += DX

        yw += DY

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.flip()

    print("Done. Close the window to exit.")
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        pygame.time.wait(50)


if __name__ == "__main__":
    main()
