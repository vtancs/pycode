import pygame
import numpy as np
import math

# --- Pygame setup ---
pygame.init()
WIDTH, HEIGHT = 900, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spinning F-16 Jetfighter - Wireframe")
clock = pygame.time.Clock()

# --- F-16 Vertices (scaled & simplified) ---
vertices = np.array([
    [0, 0, 4],       # Nose tip
    [0, 0, 2],       # Cockpit front
    [0, 0.3, 1.5],   # Canopy top
    [0, -0.3, 1.5],  # Canopy bottom
    [1.5, 0, 0.5],   # Right wingtip front
    [-1.5, 0, 0.5],  # Left wingtip front
    [1.5, 0, -0.5],  # Right wingtip back
    [-1.5, 0, -0.5], # Left wingtip back
    [0.5, 0, -2],    # Tail right
    [-0.5, 0, -2],   # Tail left
    [0, 0.5, -2.5],  # Tail fin top
    [0, -0.5, -2.5], # Tail fin bottom
    [0, 0, -3.5]     # Engine exhaust
])

# --- Edges connecting vertices ---
edges = [
    (0, 1), (1, 2), (1, 3),           # Nose to cockpit
    (2, 4), (3, 4),                   # Cockpit to right wing front
    (2, 5), (3, 5),                   # Cockpit to left wing front
    (4, 6), (5, 7),                   # Wing edges
    (6, 8), (7, 9),                   # Wings to tail base
    (8, 12), (9, 12),                 # Tail to engine exhaust
    (8, 10), (9, 11),                 # Tail supports to fin
    (10, 12), (11, 12)                # Fin to exhaust
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
def project(points, scale=300, distance=8):
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

    # Rotate F-16
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
    clock.tick(60)

pygame.quit()
