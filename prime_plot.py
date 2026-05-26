import pygame
import numpy as np
from math import sin, cos
from pygame.locals import *

# =========================================================
# SETTINGS
# =========================================================
WIDTH, HEIGHT = 1400, 900
BACKGROUND = (8, 8, 12)

NUM_PRIMES = 1000

SCALE = 0.09
FOV = 700
VIEW_DISTANCE = 5000

ROT_SPEED_X = 0.003
ROT_SPEED_Y = 0.008

POINT_SIZE = 4

# =========================================================
# PRIME GENERATOR
# =========================================================
def generate_primes(n):
    primes = []
    num = 2

    while len(primes) < n:
        is_prime = True

        for p in primes:
            if p * p > num:
                break

            if num % p == 0:
                is_prime = False
                break

        if is_prime:
            primes.append(num)

        num += 1

    return np.array(primes)

# =========================================================
# TRANSFORM PRIME POINTS
# =========================================================
def create_points(primes):

    pts = []

    for p in primes:

        # Similar transformation to original graph
        x = p * sin(p) * cos(p)
        y = p * (sin(p) ** 2)
        z = p * cos(p)

        pts.append(np.array([x, y, z]))

    return pts

# =========================================================
# ROTATION
# =========================================================
def rotate_x(point, angle):

    x, y, z = point

    ry = y * cos(angle) - z * sin(angle)
    rz = y * sin(angle) + z * cos(angle)

    return np.array([x, ry, rz])

def rotate_y(point, angle):

    x, y, z = point

    rx = x * cos(angle) + z * sin(angle)
    rz = -x * sin(angle) + z * cos(angle)

    return np.array([rx, y, rz])

# =========================================================
# 3D -> 2D PROJECTION
# =========================================================
def project(point):

    x, y, z = point

    z += VIEW_DISTANCE

    factor = FOV / z

    px = x * factor * SCALE + WIDTH // 2
    py = -y * factor * SCALE + HEIGHT // 2

    return int(px), int(py), factor

# =========================================================
# COLOR MAPPING
# =========================================================
def color_map(index, total):

    t = index / total

    r = int(255 * t)
    g = int(255 * (1 - abs(t - 0.5) * 2))
    b = int(255 * (1 - t))

    return (r, g, b)

# =========================================================
# DRAW AXES
# =========================================================
def draw_axes(screen, angle_x, angle_y):

    axis_length = 2500

    axes = [
        (np.array([ axis_length,0,0]), (255,80,80)),   # X
        (np.array([0, axis_length,0]), (80,255,80)),   # Y
        (np.array([0,0, axis_length]), (80,160,255)),  # Z
    ]

    origin = np.array([0,0,0])

    # Rotate origin
    origin_r = rotate_x(origin, angle_x)
    origin_r = rotate_y(origin_r, angle_y)

    ox, oy, _ = project(origin_r)

    for axis, color in axes:

        pt = rotate_x(axis, angle_x)
        pt = rotate_y(pt, angle_y)

        px, py, _ = project(pt)

        pygame.draw.line(screen, color, (ox, oy), (px, py), 3)

# =========================================================
# MAIN
# =========================================================
pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Prime Transformation")

clock = pygame.time.Clock()

# Generate data
primes = generate_primes(NUM_PRIMES)
points = create_points(primes)

angle_x = 0
angle_y = 0

font = pygame.font.SysFont("Arial", 22)

running = True

while running:

    clock.tick(60)

    # =====================================================
    # EVENTS
    # =====================================================
    for event in pygame.event.get():

        if event.type == QUIT:
            running = False

        if event.type == KEYDOWN:

            # ESC exits program
            if event.key == K_ESCAPE:
                running = False

    # =====================================================
    # CLEAR SCREEN
    # =====================================================
    screen.fill(BACKGROUND)

    # =====================================================
    # DRAW AXES
    # =====================================================
    draw_axes(screen, angle_x, angle_y)

    # =====================================================
    # ROTATE + PROJECT POINTS
    # =====================================================
    render_points = []

    for i, point in enumerate(points):

        rotated = rotate_x(point, angle_x)
        rotated = rotate_y(rotated, angle_y)

        x2d, y2d, factor = project(rotated)

        render_points.append(
            (rotated[2], x2d, y2d, factor, i)
        )

    # Depth sort
    render_points.sort(reverse=True)

    # =====================================================
    # DRAW POINTS
    # =====================================================
    for depth, x, y, factor, i in render_points:

        radius = max(1, int(POINT_SIZE * factor * 2))

        color = color_map(i, NUM_PRIMES)

        pygame.draw.circle(screen, color, (x, y), radius)

    # =====================================================
    # INFO TEXT
    # =====================================================
    title = font.render(
        "3D Prime Transformation Plot  |  ESC = Exit",
        True,
        (230, 230, 230)
    )

    screen.blit(title, (20, 20))

    # Axis labels
    x_label = font.render("X", True, (255, 80, 80))
    y_label = font.render("Y", True, (80, 255, 80))
    z_label = font.render("Z", True, (80, 160, 255))

    screen.blit(x_label, (WIDTH - 100, HEIGHT // 2))
    screen.blit(y_label, (WIDTH // 2 + 20, 60))
    screen.blit(z_label, (WIDTH // 2 + 100, HEIGHT // 2 + 120))

    # =====================================================
    # UPDATE DISPLAY
    # =====================================================
    pygame.display.flip()

    # Animate rotation
    angle_x += ROT_SPEED_X
    angle_y += ROT_SPEED_Y

pygame.quit()