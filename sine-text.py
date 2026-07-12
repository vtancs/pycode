import pygame
import math

# -----------------------------
# Configuration
# -----------------------------
WIDTH = 900
HEIGHT = 700
FPS = 60

FONT_SIZE = 16
LINES = 32
FREQ = 0.30
AMP = 12
OFFSET = 38
SCROLL_SPEED = 0.12

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ASCII DNA")

clock = pygame.time.Clock()

font = pygame.font.SysFont("Consolas", FONT_SIZE)

BG = (45, 0, 70)
FG = (245, 245, 245)

line_height = font.get_height()

phase = 0.0

running = True
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

            elif event.key == pygame.K_UP:
                AMP += 1

            elif event.key == pygame.K_DOWN:
                AMP = max(1, AMP - 1)

            elif event.key == pygame.K_LEFT:
                OFFSET = max(0, OFFSET - 1)

            elif event.key == pygame.K_RIGHT:
                OFFSET += 1

    screen.fill(BG)

    # -----------------------------
    # Header
    # -----------------------------
    header = [
        "ASCII DNA",
        "",
        f"Amplitude : {AMP}",
        f"Offset    : {OFFSET}",
        "",
        "UP/DOWN    = Amplitude",
        "LEFT/RIGHT = Offset",
        "ESC        = Quit",
        ""
    ]

    y = 10
    for text in header:
        img = font.render(text, True, FG)
        screen.blit(img, (10, y))
        y += line_height

    # -----------------------------
    # Draw DNA
    # -----------------------------
    start_y = y + 10

    for n in range(LINES):

        value = math.sin(n * FREQ + phase) * AMP

        t1 = int(round(value + OFFSET))
        t2 = int(round((AMP * 2 - value) + OFFSET))

        left = min(t1, t2)
        right = max(t1, t2)

        if left == right:
            line = " " * left + "*"
        else:
            line = (
                " " * left +
                "*" +
                "-" * (right - left - 1) +
                "*"
            )

        img = font.render(line, True, FG)
        screen.blit(img, (20, start_y + n * line_height))

    phase += SCROLL_SPEED

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()