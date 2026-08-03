import pygame
import math

# --------------------------------------------------
# Poincare Disk
# Original QB64: K Moerman (2026)
# Python/Pygame version with interactive controls
#
# Controls
# --------
# ↑  Increase animation speed
# ↓  Decrease animation speed
# SPACE  Change line colour
# ESC  Quit
# --------------------------------------------------

WIDTH = 950
HEIGHT = WIDTH
FPS = 60

BACKGROUND = (0, 0, 0)

D = 8          # Maximum plane coordinate
S = 0.45       # Size of one line drawing sector

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Poincare Disk")
clock = pygame.time.Clock()

# --------------------------------------------------
# Colours
# --------------------------------------------------

colors = [
    (80, 255, 80),      # Green
    (255, 255, 255),    # White
    (255, 80, 80),      # Red
    (80, 180, 255),     # Blue
    (255, 255, 80),     # Yellow
    (255, 80, 255),     # Magenta
    (80, 255, 255),     # Cyan
    (255, 170, 0),      # Orange
]

color_index = 0
LINE_COLOR = colors[color_index]

# --------------------------------------------------
# Animation controls
# --------------------------------------------------

speed = 1.0
animation_step = S / 120.0
ds = 0.0

# --------------------------------------------------
# Calculate world scaling
# --------------------------------------------------

r = math.sqrt(2) * D
xymax = math.sqrt(2) * math.tanh(r / 2.0) * D / r

SCALE = WIDTH / (2 * xymax)


def world_to_screen(x, y):
    sx = WIDTH / 2 + x * SCALE
    sy = HEIGHT / 2 - y * SCALE
    return int(sx), int(sy)


# --------------------------------------------------

def poincare_transform(x, y):
    r = math.hypot(x, y)

    if r == 0:
        return 0.0, 0.0

    t = math.tanh(r / 2.0)

    return (
        t * x / r,
        t * y / r
    )


# --------------------------------------------------

def poincare_line(x1, y1, x2, y2):

    px1, py1 = poincare_transform(x1, y1)
    px2, py2 = poincare_transform(x2, y2)

    pygame.draw.aaline(
        screen,
        LINE_COLOR,
        world_to_screen(px1, py1),
        world_to_screen(px2, py2),
    )


# --------------------------------------------------

def draw_sector(xs, ys, s):

    step = s / 9.0
    d = 0.0

    while d <= s + 1e-9:

        poincare_line(xs + d, ys,
                      xs, ys + s - d)

        poincare_line(xs + d, ys,
                      xs, ys - s + d)

        poincare_line(xs - d, ys,
                      xs, ys + s - d)

        poincare_line(xs - d, ys,
                      xs, ys - s + d)

        d += step


# --------------------------------------------------
# Main Loop
# --------------------------------------------------

running = True

font = pygame.font.SysFont(None, 24)

while running:

    # -----------------------------
    # Events
    # -----------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_SPACE:
                color_index = (color_index + 1) % len(colors)
                LINE_COLOR = colors[color_index]

            elif event.key == pygame.K_UP:
                speed = min(speed * 1.25, 20.0)

            elif event.key == pygame.K_DOWN:
                speed = max(speed / 1.25, 0.05)

    # -----------------------------
    # Drawing
    # -----------------------------

    screen.fill(BACKGROUND)

    xs = -D

    while xs <= D + 1e-9:

        ys = -D

        while ys <= D + 1e-9:

            draw_sector(xs + ds, ys + ds, S)

            ys += 2 * S

        xs += 2 * S

    # Draw Poincare boundary
    pygame.draw.circle(
        screen,
        (140, 140, 140),
        (WIDTH // 2, HEIGHT // 2),
        int(SCALE),
        2,
    )

    # Information text
    txt1 = font.render(
        f"Speed: {speed:.2f}x",
        True,
        (255, 255, 255),
    )

    txt2 = font.render(
        "UP/DOWN Speed   SPACE Colour   ESC Quit",
        True,
        (200, 200, 200),
    )

    screen.blit(txt1, (10, 10))
    screen.blit(txt2, (10, 35))

    pygame.display.flip()

    # -----------------------------
    # Update animation
    # -----------------------------

    ds += animation_step * speed

    cycle = 2 * S

    while ds >= cycle:
        ds -= cycle

    clock.tick(FPS)

pygame.quit()