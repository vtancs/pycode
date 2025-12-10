import pygame
import math
import sys
import random

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

# Target values for smooth transitions
target_amplitude = amplitude
target_frequency = frequency

# Smoothing factor (lower = smoother transitions)
smoothing = 0.02

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Counter for random parameter changes
frame_count = 0
change_interval = 180  # Change parameters every 3 seconds at 60 FPS

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
    
    # Randomly change target parameters at intervals
    frame_count += 1
    if frame_count >= change_interval:
        target_amplitude = random.uniform(50, 150)
        target_frequency = random.uniform(0.01, 0.04)
        frame_count = 0
    
    # Smoothly interpolate current values toward targets
    amplitude += (target_amplitude - amplitude) * smoothing
    frequency += (target_frequency - frequency) * smoothing
    
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