import pygame
import math
import sys

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Animated Sine Wave - Point Cloud")

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)

# Sine wave parameters
amplitude = HEIGHT // 4
frequency = 0.02   # Horizontal spacing frequency
speed = 0.1        # Phase shift per frame

phase = 0

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)

    # Draw sine wave as point cloud
    for x in range(WIDTH):
        y = HEIGHT // 2 + int(amplitude * math.sin(frequency * x + phase))
        pygame.draw.circle(screen, BLUE, (x, y), 2)  # radius=2 for point effect

    # Update phase for animation
    phase += speed

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
