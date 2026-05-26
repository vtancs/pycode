import pygame
import random
import sys

# ----------------------------------------
# Moss Maze (C64 "10 PRINT" inspired)
# Converted from Commodore BASIC to pygame
# ----------------------------------------

pygame.init()

WIDTH = 960
HEIGHT = 640

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Moss Maze")

CLOCK = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
MOSS = [
    (80, 120, 60),
    (100, 150, 80),
    (60, 100, 50),
    (140, 180, 90),
]

SCREEN.fill(BLACK)

CELL = 16

cols = WIDTH // CELL
rows = HEIGHT // CELL

x = 0
y = 0

# Draw one "moss character"
def draw_moss(cx, cy):
    px = cx * CELL
    py = cy * CELL

    # choose slash direction
    slash = random.choice(["\\", "/"])

    # draw multiple noisy strands to look mossy
    for _ in range(10):
        color = random.choice(MOSS)

        jitter = 4

        if slash == "\\":
            x1 = px + random.randint(0, jitter)
            y1 = py + random.randint(0, jitter)

            x2 = px + CELL - random.randint(0, jitter)
            y2 = py + CELL - random.randint(0, jitter)

        else:
            x1 = px + CELL - random.randint(0, jitter)
            y1 = py + random.randint(0, jitter)

            x2 = px + random.randint(0, jitter)
            y2 = py + CELL - random.randint(0, jitter)

        pygame.draw.line(SCREEN, color, (x1, y1), (x2, y2), 1)

    # tiny moss blobs
    for _ in range(6):
        mx = px + random.randint(0, CELL - 1)
        my = py + random.randint(0, CELL - 1)
        r = random.randint(1, 2)

        pygame.draw.circle(
            SCREEN,
            random.choice(MOSS),
            (mx, my),
            r
        )


running = True

while running:
    CLOCK.tick(240)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            running = False

    draw_moss(x, y)

    x += 1

    if x >= cols:
        x = 0
        y += 1

    if y >= rows:
        # fade screen slightly instead of clearing hard
        fade = pygame.Surface((WIDTH, HEIGHT))
        fade.set_alpha(25)
        fade.fill(BLACK)
        SCREEN.blit(fade, (0, 0))

        y = 0

    pygame.display.flip()

pygame.quit()
sys.exit()