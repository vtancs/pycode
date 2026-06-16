import os
import math
import urllib.request

import pygame
import numpy as np

# ============================================================
# Configuration
# ============================================================

WIDTH = 1000
HEIGHT = 800

OBJ_URL = "https://basicfusion.org/cloud/data_examples/3d/skull.obj"
OBJ_FILE = "skull.obj"

BG_COLOR = (0, 0, 0)
POINT_COLOR = (255, 255, 255)
POINT_SIZE = 2

# ============================================================
# Download model if needed
# ============================================================

if not os.path.exists(OBJ_FILE):
    print("Downloading skull.obj...")
    urllib.request.urlretrieve(OBJ_URL, OBJ_FILE)
    print("Download complete.")

# ============================================================
# OBJ Loader
# ============================================================

def load_obj(filename):
    vertices = []

    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("v "):
                parts = line.split()
                vertices.append([
                    float(parts[1]),
                    float(parts[2]),
                    float(parts[3])
                ])

    return np.array(vertices, dtype=np.float32)

# ============================================================
# Rotation Matrices
# ============================================================

def rot_x(angle):
    c = math.cos(angle)
    s = math.sin(angle)

    return np.array([
        [1, 0, 0],
        [0, c, -s],
        [0, s, c]
    ], dtype=np.float32)

def rot_y(angle):
    c = math.cos(angle)
    s = math.sin(angle)

    return np.array([
        [c, 0, s],
        [0, 1, 0],
        [-s, 0, c]
    ], dtype=np.float32)

def rot_z(angle):
    c = math.cos(angle)
    s = math.sin(angle)

    return np.array([
        [c, -s, 0],
        [s, c, 0],
        [0, 0, 1]
    ], dtype=np.float32)

# ============================================================
# Projection
# ============================================================

def project(points, width, height, zoom, camera_distance):

    z = points[:, 2] + camera_distance

    valid = z > 0.01

    x = points[:, 0] * zoom / z + width / 2
    y = -points[:, 1] * zoom / z + height / 2

    return np.column_stack((x, y)), valid

# ============================================================
# Initialize pygame
# ============================================================

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Interactive Skull OBJ Viewer")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

# ============================================================
# Load Model
# ============================================================

vertices = load_obj(OBJ_FILE)

# Center model
vertices -= np.mean(vertices, axis=0)

# Normalize size
radius = np.max(np.linalg.norm(vertices, axis=1))
vertices /= radius

# Scale model
vertices *= 2.0

# ============================================================
# View State
# ============================================================

rot_x_angle = 0.0
rot_y_angle = 0.0
rot_z_angle = 0.0

zoom = 900.0
camera_distance = 5.0

left_dragging = False
right_dragging = False

last_mouse = (0, 0)

# ============================================================
# Dynamic Auto Spin
# ============================================================

auto_spin = False

spin_speed_x = 0.015
spin_speed_y = 0.023
spin_speed_z = 0.018

# ============================================================
# Main Loop
# ============================================================

running = True

while running:

    # ========================================================
    # Events
    # ========================================================

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_SPACE:
                auto_spin = not auto_spin

            elif event.key == pygame.K_r:

                rot_x_angle = 0.0
                rot_y_angle = 0.0
                rot_z_angle = 0.0

                zoom = 900.0

                auto_spin = False

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:
                left_dragging = True
                last_mouse = event.pos

            elif event.button == 3:
                right_dragging = True
                last_mouse = event.pos

            elif event.button == 4:
                zoom *= 1.1

            elif event.button == 5:
                zoom *= 0.9

        elif event.type == pygame.MOUSEBUTTONUP:

            if event.button == 1:
                left_dragging = False

            elif event.button == 3:
                right_dragging = False

        elif event.type == pygame.MOUSEMOTION:

            mx, my = event.pos

            dx = mx - last_mouse[0]
            dy = my - last_mouse[1]

            if left_dragging:

                rot_y_angle += dx * 0.01
                rot_x_angle += dy * 0.01

            if right_dragging:

                rot_z_angle += dx * 0.01

            last_mouse = event.pos

        elif event.type == pygame.MOUSEWHEEL:

            if event.y > 0:
                zoom *= 1.1
            elif event.y < 0:
                zoom *= 0.9

    # ========================================================
    # Auto Spin
    # ========================================================

    if auto_spin:

        rot_x_angle += spin_speed_x
        rot_y_angle += spin_speed_y
        rot_z_angle += spin_speed_z

        # Gentle variation creates a more natural tumble
        t = pygame.time.get_ticks() * 0.001

        rot_x_angle += math.sin(t * 0.7) * 0.002
        rot_y_angle += math.cos(t * 0.5) * 0.002
        rot_z_angle += math.sin(t * 0.9) * 0.002

    # ========================================================
    # Rotate Model
    # ========================================================

    rotation = (
        rot_z(rot_z_angle)
        @ rot_y(rot_y_angle)
        @ rot_x(rot_x_angle)
    )

    transformed = vertices @ rotation.T

    # ========================================================
    # Project
    # ========================================================

    points2d, valid = project(
        transformed,
        WIDTH,
        HEIGHT,
        zoom,
        camera_distance
    )

    # ========================================================
    # Draw
    # ========================================================

    screen.fill(BG_COLOR)

    for i, visible in enumerate(valid):

        if not visible:
            continue

        x, y = points2d[i]

        if 0 <= x < WIDTH and 0 <= y < HEIGHT:

            pygame.draw.circle(
                screen,
                POINT_COLOR,
                (int(x), int(y)),
                POINT_SIZE
            )

    status = "ON" if auto_spin else "OFF"

    info = (
        f"SPACE: Spin [{status}]   "
        f"LMB: Rotate X/Y   "
        f"RMB: Rotate Z   "
        f"Wheel: Zoom   "
        f"R: Reset   "
        f"ESC: Quit"
    )

    text = font.render(info, True, (220, 220, 220))
    screen.blit(text, (10, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()