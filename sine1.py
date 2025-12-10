import pygame
import math
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Animated Sine Wave")

# Colors
BLACK = (0, 0, 0)
CYAN = (0, 255, 255)

# Wave parameters
amplitude = 100  # Height of the wave
frequency = 0.02  # How many waves fit on screen
speed = 0.05  # Animation speed
phase = 0  # Starting phase

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Main loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    
    # Clear screen
    screen.fill(BLACK)
    
    # Generate points for the sine wave
    points = []
    for x in range(WIDTH):
        # Calculate y position using sine function
        y = HEIGHT // 2 + amplitude * math.sin(frequency * x + phase)
        points.append((x, y))
    
    # Draw the sine wave
    if len(points) > 1:
        pygame.draw.lines(screen, CYAN, False, points, 2)
    
    # Update phase for animation
    phase += speed
    
    # Update display
    pygame.display.flip()
    
    # Control frame rate (60 FPS)
    clock.tick(60)

# Quit Pygame
pygame.quit()
sys.exit()