
import pygame
import math

# --- Configuration ---
WIDTH, HEIGHT = 800, 600
X0, Y0 = 50, HEIGHT // 2  # Origin
SC = 15                   # Scale factor
LS = 35                   # Last step size
PI = math.pi

# --- Setup ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Recaman Sequence Visualization")
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
ARC_COLOR = (200, 200, 200)

# Visited positions
visited = {0}
p = 0

def draw_arc(p, pp, s):
    # Center and Radius
    cx = X0 + (p + pp) / 2 * SC
    cy = Y0
    radius = abs(p - pp) / 2 * SC
    
    # Angles based on parity and direction (BASIC logic)
    # Even step: upward arc, Odd step: downward arc
    if pp < p: # Backwards
        if s % 2 == 0:
            start_angle, end_angle = math.pi, 0 # Upwards
        else:
            start_angle, end_angle = 0, math.pi # Downwards
    else: # Forwards
        if s % 2 == 0:
            start_angle, end_angle = 0, math.pi # Upwards
        else:
            start_angle, end_angle = math.pi, 0 # Downwards

    # Drawing the arc
    # pygame.draw.arc(surface, color, [x, y, width, height], start_angle, stop_angle, width)
    # Rect is [left, top, width, height]
    rect = [cx - radius, cy - radius, radius * 2, radius * 2]
    
    # Correcting angles for pygame: 0 is right, increases clockwise.
    # BASIC used standard math angles (0 is right, increases counter-clockwise).
    # We invert the y-axis logic naturally with the rect.
    
    # pygame.draw.arc uses radians
    pygame.draw.arc(screen, ARC_COLOR, rect, min(start_angle, end_angle), max(start_angle, end_angle), 1)
    pygame.display.flip()

# Main Loop
screen.fill(BLACK)
pygame.draw.line(screen, WHITE, (0, Y0), (WIDTH, Y0), 1)
pygame.display.flip()

for s in range(1, LS + 1):
    # Step logic
    pp_back = p - s
    if pp_back >= 0 and pp_back not in visited:
        pp = pp_back
    else:
        pp = p + s
    
    # Draw
    draw_arc(p, pp, s)
    
    # Update
    p = pp
    visited.add(p)
    
    # Delay for animation
    pygame.time.delay(100)
    
    # Check for quit
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

# Wait to close
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
pygame.quit()
