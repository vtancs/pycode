import pygame
import math

# Initialization
pygame.init()
WIDTH, HEIGHT = 1280, 1024
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BBC BASIC Spirograph Clone")
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (128, 128, 255)
PALETTE = [(255, 50, 50), (50, 255, 50), (50, 50, 255), (255, 255, 50), (255, 50, 255)]

# Constants
R, r = 500, 250
OFFSET_X, OFFSET_Y = WIDTH // 2, HEIGHT // 2
last_pos = [[None for _ in range(5)] for _ in range(6)]
angle = 0
running = True

# Persistent surface for the trace lines
trace_surface = pygame.Surface((WIDTH, HEIGHT))

while running:
    # --- Keyboard and Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:  # ESC to quit
                running = False
            if event.key == pygame.K_SPACE:   # SPACE to clear drawing
                trace_surface.fill((0, 0, 0))
                last_pos = [[None for _ in range(5)] for _ in range(6)]

    # --- Logic ---
    c_index = (angle // 360) % 5
    c_scale = (c_index + 1) / 5
    current_color = PALETTE[c_index]

    rad_a = math.radians(angle)
    ox = (R - r) * math.cos(rad_a)
    oy = (R - r) * math.sin(rad_a)

    # --- Rendering ---
    screen.fill(BLACK)
    
    # Static boundary and rolling circle
    pygame.draw.circle(screen, CYAN, (OFFSET_X, OFFSET_Y), R, 1)
    pygame.draw.circle(screen, WHITE, (int(ox + OFFSET_X), int(oy + OFFSET_Y)), int(r), 1)

    for b_idx in range(5):
        b_angle = angle * (R - r) / r + b_idx * 72
        rad_b = math.radians(b_angle)
        
        px, py = r * math.cos(rad_b), -r * math.sin(rad_b)
        tx, ty = ox + px * c_scale, oy + py * c_scale
        
        actual_x, actual_y = int(tx + OFFSET_X), int(ty + OFFSET_Y)

        # Draw spokes on the main screen
        pygame.draw.line(screen, (60, 60, 60), (ox + OFFSET_X, oy + OFFSET_Y), (px + ox + OFFSET_X, py + oy + OFFSET_Y), 1)
        pygame.draw.circle(screen, WHITE, (actual_x, actual_y), 4)

        # Draw the permanent trace to the trace_surface
        if last_pos[c_index][b_idx] is not None:
            pygame.draw.line(trace_surface, current_color, last_pos[c_index][b_idx], (actual_x, actual_y), 2)
        
        last_pos[c_index][b_idx] = (actual_x, actual_y)

    # Combine the trace surface with the moving circles
    screen.blit(trace_surface, (0, 0), special_flags=pygame.BLEND_ADD)
    
    pygame.display.flip()
    angle += 2  
    clock.tick(60)

pygame.quit()