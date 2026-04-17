"""
Rotating Galaxy - Python/pygame port of galaxyani.bas
Original BASIC code by Eric Schraf & K Moerman (2026)
Converted to Python/pygame maintaining exact behavior.
"""

import pygame
import math
import random
import sys

# --- Constants matching the BASIC original ---
SCREEN_W, SCREEN_H = 800, 600
DROTAT = 2 * math.pi / 900   # rotation step per frame

# World coordinate window: (-32,-24) to (32,24)
WORLD_W = 64.0   # 32 - (-32)
WORLD_H = 48.0   # 24 - (-24)

# Colors (ARGB in QB64 -> RGB in pygame)
BLACK  = (0,   0,   0)
RED    = (255, 0,   0)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
WHITE  = (255, 255, 255)

# Heat-up sequence
HEAT = {
    BLACK:  RED,
    RED:    ORANGE,
    ORANGE: YELLOW,
    YELLOW: WHITE,
    WHITE:  WHITE,
}

def world_to_screen(wx, wy):
    """Map world coords (-32..32, -24..24) to screen pixels (0..800, 0..600)."""
    px = (wx + 32.0) / WORLD_W * SCREEN_W
    py = (24.0 - wy) / WORLD_H * SCREEN_H   # y flipped: world +y is screen top
    return px, py

def screen_to_world(px, py):
    wx = px / SCREEN_W * WORLD_W - 32.0
    wy = 24.0 - py / SCREEN_H * WORLD_H
    return wx, wy

def world_unit_to_pixels():
    """How many pixels correspond to one world unit (for box size)."""
    sx = SCREEN_W / WORLD_W
    sy = SCREEN_H / WORLD_H
    return sx, sy

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Rotating galaxy")
    clock = pygame.time.Clock()

    # Pixel size for the 0.08-world-unit box drawn by LINE ... Step(.08,.08),c,B
    sx, sy = world_unit_to_pixels()
    box_w = max(1, round(0.08 * sx))
    box_h = max(1, round(0.08 * sy))

    rotat = 0.0
    running = True

    while running:
        clock.tick(60)   # _Limit 60

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:   # InKey$ <> "" exits
                running = False

        # Cls
        screen.fill(BLACK)

        # Randomize Using 1  — reset to the same seed every frame
        random.seed(1)

        for _ in range(20000):
            # distance: Log(Rnd + 4.54e-5)  -> negative value in (-10, 0)
            distance = math.log(random.random() + 4.54e-5)

            angle = 2 * math.pi * random.random()

            u = 6 * distance * math.sin(angle)
            v = 5 * distance * math.cos(angle)

            cos_dist = math.cos(3 * distance + rotat)
            sin_dist = math.sin(3 * distance + rotat)

            x = u * cos_dist + v * sin_dist
            y = -u * sin_dist + v * cos_dist

            # fuzziness
            y = y + random.random() * 3 - 1.5

            # 3-D tilt
            xt = 1.4 * x + 0.6 * y
            yt = 0.2 * x + 0.8 * y

            # --- sample pixel colour at (xt, yt) and heat it up ---
            px, py = world_to_screen(xt, yt)
            ipx, ipy = int(px), int(py)

            # Skip if off-screen (matches QB64 Point returning -1 for out-of-window)
            if ipx < 0 or ipx >= SCREEN_W or ipy < 0 or ipy >= SCREEN_H:
                continue

            # Point(xt, yt) — read the pixel colour
            sampled = screen.get_at((ipx, ipy))[:3]   # ignore alpha

            # Heat up: black->red->orange->yellow->white
            new_color = HEAT.get(sampled)
            if new_color is None:
                # Any other colour (treated like white in "Case Else")
                new_color = WHITE

            # LINE (xt,yt)-Step(.08,.08), c, B
            rect = pygame.Rect(ipx, ipy, box_w, box_h)
            pygame.draw.rect(screen, new_color, rect, 1)   # B = box outline

        pygame.display.flip()   # _Display

        rotat += DROTAT
        if rotat > 2 * math.pi - DROTAT:
            rotat = 0.0

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()