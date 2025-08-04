import pygame
import numpy as np
import math

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spinning Diamond - Vector Wireframe")
clock = pygame.time.Clock()

# --- Diamond vertices ---
vertices = np.array([
    [0, 0, 1],       # Top point
    [0.5, 0, 0.5],   # Upper middle
    [0, 0.5, 0.5],
    [-0.5, 0, 0.5],
    [0, -0.5, 0.5],
    [0.5, 0, -0.5],  # Lower middle
    [0, 0.5, -0.5],
    [-0.5, 0, -0.5],
    [0, -0.5, -0.5],
    [0, 0, -1]       # Bottom point
])

# --- Diamond edges ---
edges = [
    (0, 1), (0, 2), (0, 3), (0, 4),
    (1, 2), (2, 3), (3, 4), (4, 1),
    (1, 5), (2, 6), (3, 7), (4, 8),
    (5, 6), (6, 7), (7, 8), (8, 5),
    (5, 9), (6, 9), (7, 9), (8, 9)
]

# --- Rotation function ---
def rotate(points, ax, ay):
    Rx = np.array([
        [1, 0, 0],
        [0, math.cos(ax), -math.sin(ax)],
        [0, math.sin(ax), math.cos(ax)]
    ])
    Ry = np.array([
        [math.cos(ay), 0, math.sin(ay)],
        [0, 1, 0],
        [-math.sin(ay), 0, math.cos(ay)]
    ])
    return points @ Rx.T @ Ry.T

# --- Projection function ---
def project(points, scale=300, distance=3):
    projected = []
    for x, y, z in points:
        factor = scale / (z + distance)
        projected.append((WIDTH // 2 + int(x * factor), HEIGHT // 2 - int(y * factor)))
    return projected

# --- Main loop ---
angle_x, angle_y = 0, 0
running = True
frame_count = 0

while running:
    screen.fill((0, 0, 0))  # black background
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Rotate shape
    rotated = rotate(vertices, math.radians(angle_x), math.radians(angle_y))
    projected = project(rotated)

    # Progressive tracing effect
    edges_to_show = min(len(edges), frame_count // 2 + 1)

    for i, (p1_idx, p2_idx) in enumerate(edges):
        if i < edges_to_show:
            pygame.draw.aaline(screen, (0, 255, 255), projected[p1_idx], projected[p2_idx])

    # Update angles for spinning
    angle_x += 1
    angle_y += 0.8
    frame_count += 1

    pygame.display.flip()
    clock.tick(60)  # limit to 60 FPS

pygame.quit()