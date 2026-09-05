import random
import sys
import pygame

# Initialize Pygame
pygame.init()

# C64 standard 16-color palette (RGB)
C64_PALETTE = [
    (0, 0, 0),  # 0: Black
    (255, 255, 255),  # 1: White
    (136, 0, 0),  # 2: Red
    (170, 255, 238),  # 3: Cyan
    (204, 68, 204),  # 4: Purple
    (0, 204, 85),  # 5: Green
    (0, 0, 170),  # 6: Blue
    (238, 238, 119),  # 7: Yellow
    (221, 136, 85),  # 8: Orange
    (102, 68, 0),  # 9: Brown
    (255, 119, 119),  # 10: Light Red
    (51, 51, 51),  # 11: Dark Grey
    (119, 119, 119),  # 12: Grey
    (170, 255, 102),  # 13: Light Green
    (0, 136, 255),  # 14: Light Blue
    (170, 170, 170),  # 15: Light Grey
]

# C64 Screen Dimensions (320x200 scaled up 3x for modern displays)
BASIC_WIDTH, BASIC_HEIGHT = 320, 200
SCALE = 3
SCREEN_WIDTH, SCREEN_HEIGHT = BASIC_WIDTH * SCALE, BASIC_HEIGHT * SCALE

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("C64 Fast Random Colors - Thinking...")
clock = pygame.time.Clock()

# Render target at native C64 resolution
canvas = pygame.Surface((BASIC_WIDTH, BASIC_HEIGHT))

# C64 grid setup for 40x25 characters (8x8 pixels per char)
COLS, ROWS = 40, 25
CHAR_W, CHAR_H = 8, 8

# Layout positioning
GRID_ROWS = 8
GRID_COLS = 32
GRID_START_COL = (COLS - GRID_COLS) // 2
GRID_START_ROW = 2

TEXT_ROW = 11
TEXT = "THINKING..."
TEXT_COL = (COLS - len(TEXT)) // 2

font = pygame.font.SysFont("monospace", 10, bold=True)
small_font = pygame.font.SysFont("monospace", 8, bold=True)

# Pre-generate color array for top block section
grid_colors = [
    [random.randint(0, 15) for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)
]

# Speed control variables
speed = 30  # FPS / Flash rate (range: 1 to 120)
MIN_SPEED = 1
MAX_SPEED = 120

running = True
while running:
    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_UP:
                speed = min(MAX_SPEED, speed + 5)
            elif event.key == pygame.K_DOWN:
                speed = max(MIN_SPEED, speed - 5)

    # Randomize grid colors per frame
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            grid_colors[r][c] = random.randint(0, 15)

    canvas.fill(C64_PALETTE[0])  # Black background

    # 1. Draw top grid with rapidly flashing colors
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            color_idx = grid_colors[r][c]
            x = (GRID_START_COL + c) * CHAR_W
            y = (GRID_START_ROW + r) * CHAR_H
            color = C64_PALETTE[color_idx]
            pygame.draw.rect(canvas, color, (x + 1, y + 1, 6, 6), border_radius=2)

    # 2. Draw "THINKING..." text
    text_surface = font.render(TEXT, True, C64_PALETTE[1])
    canvas.blit(text_surface, (TEXT_COL * CHAR_W, TEXT_ROW * CHAR_H))

    # 3. Draw key instructions and speed readout at bottom
    info_line1 = "[UP/DOWN] SPEED"
    info_line2 = f"SPEED: {speed} FPS | [ESC] QUIT"

    instr1_surf = small_font.render(info_line1, True, C64_PALETTE[7])  # Yellow
    instr2_surf = small_font.render(info_line2, True, C64_PALETTE[3])  # Cyan

    canvas.blit(
        instr1_surf, ((COLS * CHAR_W - instr1_surf.get_width()) // 2, 17 * CHAR_H)
    )
    canvas.blit(
        instr2_surf, ((COLS * CHAR_W - instr2_surf.get_width()) // 2, 19 * CHAR_H)
    )

    # Upscale canvas to window size
    scaled_surface = pygame.transform.scale(canvas, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_surface, (0, 0))

    pygame.display.flip()
    clock.tick(speed)

pygame.quit()
sys.exit()