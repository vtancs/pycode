import pygame
import math
import sys

pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Sine Wave - 45° Side View with Vertical Motion")

clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
GRAY = (80, 80, 80)

# Wave parameters
horizontal_amplitude = 80   # side-to-side amplitude
vertical_amplitude = 40     # up-down amplitude
frequency = 0.05
speed = 0.1
phase = 0

# Perspective parameters
vanish_y = HEIGHT // 2
depth_start = 50
depth_end = 1000
points_count = 400

# Camera rotation (around Y axis)
camera_angle = math.radians(45)

def rotate_y(x, z, angle):
    """Rotate point around Y-axis"""
    xr = x * math.cos(angle) - z * math.sin(angle)
    zr = x * math.sin(angle) + z * math.cos(angle)
    return xr, zr

def project_point(x, y, z):
    """Project 3D to 2D"""
    scale = 300 / (z + 1)
    px = WIDTH // 2 + x * scale
    py = vanish_y + y * scale
    return int(px), int(py), scale

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)

    # Draw ground grid
    for gz in range(depth_start, depth_end, 50):
        for gx in range(-200, 201, 50):
            rx, rz = rotate_y(gx, gz, camera_angle)
            px, py, _ = project_point(rx, 0, rz)
            pygame.draw.circle(screen, GRAY, (px, py), 1)

    # Draw 3D sine wave points
    for i in range(points_count):
        z = depth_start + (i / points_count) * (depth_end - depth_start)

        # Horizontal + vertical oscillation
        x = math.sin(frequency * z + phase) * horizontal_amplitude
        y = math.cos(frequency * z + phase) * vertical_amplitude

        # Apply camera rotation
        rx, rz = rotate_y(x, z, camera_angle)

        # Project to 2D
        px, py, scale = project_point(rx, y, rz)

        # Draw point
        size = max(1, int(3 * scale / 10))
        pygame.draw.circle(screen, BLUE, (px, py), size)

    phase += speed
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
