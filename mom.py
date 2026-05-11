import pygame
import math
import sys

pygame.init()

# -------------------------------------------------
# WINDOW
# -------------------------------------------------
WIDTH, HEIGHT = 950, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("I LOVE YOU MOM")

# -------------------------------------------------
# COLORS
# -------------------------------------------------
BG = (242, 242, 242)
BLACK = (0, 0, 0)
RED = (220, 40, 40)

font = pygame.font.SysFont("Arial", 18)

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def axes(cx, cy, w=120, h=120):
    pygame.draw.line(screen, BLACK, (cx - w, cy), (cx + w, cy), 2)
    pygame.draw.line(screen, BLACK, (cx, cy - h), (cx, cy + h), 2)

def text(msg, x, y):
    img = font.render(msg, True, BLACK)
    screen.blit(img, (x, y))

# -------------------------------------------------
# I
# x = 0
# -------------------------------------------------
def draw_I(cx, cy):

    axes(cx, cy)

    pygame.draw.line(
        screen,
        RED,
        (cx, cy - 140),
        (cx, cy + 140),
        5
    )

    text("x = 0", cx - 20, cy + 90)

# -------------------------------------------------
# HEART
# x = 16sin³(t)
# y = 13cos(t)-5cos(2t)-2cos(3t)-cos(4t)
# -------------------------------------------------
def draw_heart(cx, cy):

    axes(cx, cy)

    pts = []

    for i in range(0, 2000):

        t = i * 0.01

        x = 16 * (math.sin(t) ** 3)

        y = (
            13 * math.cos(t)
            - 5 * math.cos(2 * t)
            - 2 * math.cos(3 * t)
            - math.cos(4 * t)
        )

        px = cx + x * 10
        py = cy - y * 10

        pts.append((px, py))

    pygame.draw.lines(screen, RED, False, pts, 5)

    text("x = 16sin³(t)", cx - 60, cy + 100)

# -------------------------------------------------
# U
# y = 1/16 x^6
# -------------------------------------------------
def draw_U(cx, cy):

    axes(cx, cy)

    pts = []

    for i in range(-180, 181):

        x = i / 40

        y = (x ** 6) / 16

        px = cx + x * 42
        py = cy - y * 18

        pts.append((px, py))

    pygame.draw.lines(screen, RED, False, pts, 5)

    text("y = 1/16 x⁶", cx - 48, cy + 95)

# -------------------------------------------------
# M
# y = 6|sin(x)|
# -------------------------------------------------
def draw_M(cx, cy):

    axes(cx, cy)

    pts = []

    # restricted domain for single M shape
    for i in range(-157, 158):

        x = i / 100

        y = 6 * abs(math.sin(2 * x))

        px = cx + x * 70
        py = cy - y * 22

        pts.append((px, py))

    pygame.draw.lines(screen, RED, False, pts, 5)

    text("y = 6|sin(x)|", cx - 58, cy + 95)

# -------------------------------------------------
# O
# x² + y² = r²
# -------------------------------------------------
def draw_O(cx, cy):

    axes(cx, cy)

    pygame.draw.circle(
        screen,
        RED,
        (cx, cy),
        120,
        5
    )

    text("r² = x² + y²", cx - 55, cy + 95)

# -------------------------------------------------
# MAIN LOOP
# -------------------------------------------------
clock = pygame.time.Clock()

while True:

    screen.fill(BG)

    # TOP ROW
    draw_I(140, 180)
    draw_heart(450, 180)
    draw_U(760, 180)

    # BOTTOM ROW
    draw_M(140, 520)
    draw_O(450, 520)
    draw_M(760, 520)

    # EVENTS
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    pygame.display.flip()
    clock.tick(60)