"""
pcsurf.py — animated 3D surface plot with hidden line removal
Based on pcsurf.bas by K Moerman

Animation: a time-offset is added to the sinc radial argument,
making the ripples appear to travel outward like a wave on water.
"""

import math
import pygame
import sys

# ── display / world parameters ───────────────────────────────────────────────
WIDTH, HEIGHT = 640, 350
XMAX, YMAX, ZMAX = 12.0, 12.0, 1.5
NH, NV  = 120, 100
SCALE   = 210

PI    = math.pi
ALPHA = PI / 4
K     = 0.4
CA    = K * math.cos(ALPHA)
SA    = K * math.sin(ALPHA)

HM = WIDTH  // 2
VM = HEIGHT // 2

DX = 2 * XMAX / NH
DY = 2 * YMAX / NV

COLOR_GREEN = (0, 255, 0)
COLOR_BG    = (0, 0,   0)

FPS        = 30
WAVE_SPEED = 2.5   # radians per second


def draw_frame(screen, t):
    screen.fill(COLOR_BG)

    INF  =  9999
    fmax = [ INF] * WIDTH
    fmin = [-INF] * WIDTH

    phase = WAVE_SPEED * t

    yw = -YMAX
    for _v in range(NV + 1):
        xw = -XMAX
        prev_top = None
        prev_bot = None

        for _h in range(NH + 1):
            r = math.sqrt(xw * xw + yw * yw)
            z = 1.0 if r == 0.0 else math.sin(r - phase) / r

            xx = xw / XMAX * SCALE
            yy = yw / YMAX * SCALE
            zz = z  / ZMAX * SCALE
            xs = int(HM + xx + yy * CA)
            ys = int(VM - zz - SA * yy)

            if 0 <= xs < WIDTH and 0 <= ys < HEIGHT:
                # Upper surface
                if ys < fmax[xs]:
                    if prev_top is not None:
                        pygame.draw.line(screen, COLOR_GREEN,
                                         (int(prev_top[0]), int(prev_top[1])),
                                         (xs, ys))
                    fmax[xs] = ys
                    prev_top = (xs, ys)
                else:
                    prev_top = None

                # Lower surface
                if ys > fmin[xs]:
                    if prev_bot is not None:
                        pygame.draw.line(screen, COLOR_GREEN,
                                         (int(prev_bot[0]), int(prev_bot[1])),
                                         (xs, ys))
                    fmin[xs] = ys
                    prev_bot = (xs, ys)
                else:
                    prev_bot = None
            else:
                prev_top = None
                prev_bot = None

            xw += DX
        yw += DY


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("3D Wave Surface — pcsurf")
    clock = pygame.time.Clock()

    t = 0.0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        draw_frame(screen, t)
        pygame.display.flip()

        dt = clock.tick(FPS) / 1000.0
        t += dt


if __name__ == "__main__":
    main()
