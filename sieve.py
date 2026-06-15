import math
from collections import deque

import pygame

# ============================================================
# QBASIC SCREEN 12 Prime Curves
# Faithful Pygame recreation
# Esc = Quit
# ============================================================

WIDTH = 640
HEIGHT = 480

INTERVAL = 9
DOT_SIZE = 3

PI = math.pi

# ------------------------------------------------------------
# VGA palette approximations
# ------------------------------------------------------------

BLACK = (0, 0, 0)

# Color 4 was reprogrammed:
# OUT &H3C8,4
# OUT &H3C9,28
# OUT &H3C9,0
# OUT &H3C9,0
#
# VGA DAC range is 0-63, so:
# 28 * 255 / 63 ≈ 113
RED_GLOW = (113, 0, 0)

# Standard VGA palette approximations
MAGENTA = (170, 0, 170)      # color 5
PINK = (255, 85, 255)        # color 13
YELLOW = (255, 255, 85)      # color 14


# ------------------------------------------------------------
# QBASIC-style PAINT
# ------------------------------------------------------------

def flood_fill(surface, x, y, fill_color, border_color):
    w, h = surface.get_size()

    if not (0 <= x < w and 0 <= y < h):
        return

    target = surface.get_at((x, y))[:3]

    if target == fill_color:
        return

    if target == border_color:
        return

    q = deque()
    q.append((x, y))

    while q:
        px, py = q.popleft()

        if px < 0 or px >= w or py < 0 or py >= h:
            continue

        c = surface.get_at((px, py))[:3]

        if c == border_color:
            continue

        if c != target:
            continue

        surface.set_at((px, py), fill_color)

        q.append((px + 1, py))
        q.append((px - 1, py))
        q.append((px, py + 1))
        q.append((px, py - 1))


# ------------------------------------------------------------
# QBASIC-style arc drawing
# ------------------------------------------------------------

def qbasic_arc(surface, color, cx, cy, radius, start_angle, end_angle):
    """
    Rasterized arc similar to QBASIC's CIRCLE arc.
    """

    if radius <= 0:
        return

    step = 1.0 / radius

    a = start_angle

    while a <= end_angle:
        x = round(cx + radius * math.cos(a))
        y = round(cy - radius * math.sin(a))

        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            surface.set_at((x, y), color)

        a += step


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Prime Curves (QBASIC Recreation)")

screen.fill(BLACK)

# Drawing is top-heavy
y_center = 300

# Equivalent to:
# DIM sieve%(640 \ Interval% + 1)
sieve_size = WIDTH // INTERVAL + 1
sieve = [0] * (sieve_size + 1)

# ------------------------------------------------------------
# Prime sieve and drawing
# ------------------------------------------------------------

for i in range(2, len(sieve)):

    if sieve[i] == 0:

        # Mark composites
        for j in range(i + i, len(sieve), i):
            sieve[j] = 1

        # Prime dot position
        x = (i - 2) * INTERVAL + INTERVAL // 2

        # Outer magenta ring
        pygame.draw.circle(
            screen,
            MAGENTA,
            (x, y_center),
            DOT_SIZE + 2,
            1
        )
        flood_fill(screen, x, y_center, MAGENTA, MAGENTA)

        # Pink ring
        pygame.draw.circle(
            screen,
            PINK,
            (x, y_center),
            DOT_SIZE + 1,
            1
        )
        flood_fill(screen, x, y_center, PINK, PINK)

        # Yellow center
        pygame.draw.circle(
            screen,
            YELLOW,
            (x, y_center),
            DOT_SIZE,
            1
        )
        flood_fill(screen, x, y_center, YELLOW, YELLOW)

        # Draw arcs through multiples
        polarity = 0

        for j in range(i, len(sieve), i):

            cx = ((2 * j + i - 3) * INTERVAL) // 2
            radius = (INTERVAL * i) // 2

            start_angle = PI * polarity
            end_angle = PI * (polarity + 1)

            qbasic_arc(
                screen,
                YELLOW,
                cx,
                y_center,
                radius,
                start_angle,
                end_angle
            )

            polarity ^= 1

        # Hollow out center
        pygame.draw.circle(
            screen,
            BLACK,
            (x, y_center),
            1
        )

# ------------------------------------------------------------
# QBASIC glow pass
# Give yellow pixels a red glow
# ------------------------------------------------------------

for x in range(WIDTH):
    for y in range(HEIGHT):

        if screen.get_at((x, y))[:3] == YELLOW:

            for k in (-1, 1):

                nx = x + k
                ny = y + k

                if 0 <= nx < WIDTH:
                    if screen.get_at((nx, y))[:3] == BLACK:
                        screen.set_at((nx, y), RED_GLOW)

                if 0 <= ny < HEIGHT:
                    if screen.get_at((x, ny))[:3] == BLACK:
                        screen.set_at((x, ny), RED_GLOW)

pygame.display.flip()

# ------------------------------------------------------------
# Event loop
# ------------------------------------------------------------

clock = pygame.time.Clock()
running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

    clock.tick(60)

pygame.quit()