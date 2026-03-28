import pygame
import math
import colorsys
import sys

# --- Constants (exact match) ---
WIDTH, HEIGHT = 800, 600
HALFX, HALFY = WIDTH // 2, HEIGHT // 2
TWOTHIRDSY = 2 * HEIGHT // 3

NITER = 25000
NFRAMES = 900
NROT = 90
FPS = 30

A_START = 3.54
A_END = 4.0
A_SPAN = A_END - A_START
A_SUM = A_START + A_END

HALFPI = math.pi / 2

DSCR = 2
DXYZ = 3
SCALE = 1.6
DSCRSCALE = DSCR * SCALE

YZANGLE = 30 * math.pi / 180
COS_YZ = math.cos(YZANGLE)
SIN_YZ = math.sin(YZANGLE)

# --- Init ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("QB64 Exact Logistic Animation")
clock = pygame.time.Clock()

def logistic(x, a):
    return a * x * (1 - x)

def hsb_to_rgb(h):
    r, g, b = colorsys.hsv_to_rgb(h / 360.0, 1, 1)
    return (int(r * 255), int(g * 255), int(b * 255))

# --- Animation state ---
frame = 460
dframe = 1
rotation = 0

running = True

while running:
    clock.tick(FPS)
    screen.fill((0, 0, 0))  # QB64 DOES clear each frame

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- parameters ---
    ar = A_START + A_SPAN * frame / NFRAMES
    ad1 = A_SUM - ar
    ad2 = ar * 0.4 + ad1 * 0.6

    r = d1 = d2 = 0.5

    for i in range(NITER):
        r  = logistic(r, ar)
        d1 = logistic(d1, ad1)
        d2 = logistic(d2, ad2)

        angle1 = HALFPI * (d1 + rotation / NROT)
        angle2 = HALFPI * d2

        rsin = r * math.sin(angle2)

        x = rsin * math.cos(angle1)
        y = rsin * math.sin(angle1)
        z = r * math.cos(angle2)

        hue = r * 360
        color = hsb_to_rgb(hue)

        # --- 4 sectors ---
        points = [
            (x, y, z),
            (-y, x, z),
            (-x, -y, z),
            (y, -x, z),
        ]

        for px, py, pz in points:
            # rotate
            yr = py * COS_YZ - pz * SIN_YZ
            zr = py * SIN_YZ + pz * COS_YZ

            denom = DXYZ + yr
            if denom <= 0:
                continue

            f = DSCRSCALE / denom

            sx = int(HALFX + HALFY * px * f)
            sy = int(TWOTHIRDSY - HALFY * zr * f)

            if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
                screen.set_at((sx, sy), color)

    pygame.display.flip()

    # --- frame oscillation ---
    if frame == NFRAMES:
        dframe = -1
    elif frame == 0:
        dframe = 1
    frame += dframe

    # --- rotation ---
    rotation = (rotation + 1) % NROT

pygame.quit()
sys.exit()