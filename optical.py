import pygame
import sys

pygame.init()

# Match C64-ish resolution scale
WIDTH, HEIGHT = 640, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("STRAIGHT LINES? (C64 Accurate)")

clock = pygame.time.Clock()

# Colors (C64-like)
BLACK = (0, 0, 0)
WHITE = (245, 245, 245)
GRAY = (70, 70, 70)

# Grid size tuned to match the illusion density
CELL_W = 20
CELL_H = 20

COLS = WIDTH // CELL_W
ROWS = 14  # top area only (bottom reserved for text)

def draw_pattern():
    screen.fill(GRAY)

    # --- illusion grid ---
    for y in range(ROWS):
        # key illusion: horizontal offset per row group
        # creates the "warped straight columns" effect
        offset = (y % 2) * (CELL_W // 2)

        for x in range(COLS):
            # alternating vertical striping
            if (x + (y // 2)) % 2 == 0:
                color = WHITE
            else:
                color = BLACK

            rect_x = x * CELL_W + offset
            rect_y = y * CELL_H

            # keep inside bounds (important for C64 look)
            if rect_x < WIDTH:
                pygame.draw.rect(screen, color, (rect_x, rect_y, CELL_W, CELL_H))

    # --- bottom text area ---
    '''
    font = pygame.font.SysFont("courier", 22, bold=True)
    text1 = font.render("STRAIGHT LINES?", True, WHITE)
    text2 = font.render("READY.", True, WHITE)
    screen.blit(text1, (10, HEIGHT - 60))
    screen.blit(text2, (10, HEIGHT - 35))
    # blinking cursor block
    if pygame.time.get_ticks() // 400 % 2 == 0:
        pygame.draw.rect(screen, WHITE, (120, HEIGHT - 32, 10, 14))
    '''

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    draw_pattern()
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()