import pygame
import numpy as np
import math

# === Config ===
WIDTH, HEIGHT = 1000, 700
FPS = 60
SPACE_COLOR = (5, 5, 20)
GRID_COLOR = (160, 120, 255)
RING_COLOR = (255, 190, 60)
GLOW_COLOR = (255, 100, 40)
FOCAL_LENGTH = 600

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Black Hole Simulation with Gravitational Lensing")
clock = pygame.time.Clock()

# === 3D Utilities ===
def rotate_y(points, angle):
    c, s = np.cos(angle), np.sin(angle)
    R = np.array([[c, 0, s],
                  [0, 1, 0],
                  [-s, 0, c]])
    return points @ R.T

def rotate_x(points, angle):
    c, s = np.cos(angle), np.sin(angle)
    R = np.array([[1, 0, 0],
                  [0, c, -s],
                  [0, s, c]])
    return points @ R.T

def apply_lensing(points, strength=1200, radius=400):
    """Apply gravitational lensing near the black hole center."""
    for i in range(len(points)):
        x, y, z = points[i]
        r = math.sqrt(x**2 + y**2 + z**2) + 1e-6
        if r < radius * 3:
            bend = strength / (r**2 + 100)
            scale = 1 + bend * 0.0005
            points[i, 0] *= scale
            points[i, 1] *= scale
            points[i, 2] *= scale
    return points

def project(points3d):
    projected = []
    for x, y, z in points3d:
        if z <= -FOCAL_LENGTH + 1:
            z = -FOCAL_LENGTH + 1
        f = FOCAL_LENGTH / (FOCAL_LENGTH + z)
        px = WIDTH / 2 + x * f
        py = HEIGHT / 2 - y * f
        projected.append((px, py))
    return projected

# === Generate spacetime grid ===
grid_points = []
size = 300
step = 40
for x in np.arange(-size, size + step, step):
    line = []
    for y in np.arange(-size, size + step, step):
        r = math.sqrt(x**2 + y**2) + 1e-5
        z = -200 / (r + 50)
        line.append([x, y, z])
    grid_points.append(np.array(line))

# === Accretion ring ===
theta = np.linspace(0, 2*np.pi, 300)
ring_radius = 180
ring = np.array([[ring_radius * np.cos(t),
                  40 * np.sin(2*t),
                  ring_radius * np.sin(t)] for t in theta])

# === Event horizon glow ===
def draw_glow(surface, x, y, radius, color, layers=6, alpha_decay=25):
    for i in range(layers):
        glow_radius = int(radius * (1 + i * 0.4))
        alpha = max(0, 180 - i * alpha_decay)
        glow = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, alpha), (glow_radius, glow_radius), glow_radius)
        surface.blit(glow, (x - glow_radius, y - glow_radius), special_flags=pygame.BLEND_PREMULTIPLIED)

# === Camera ===
yaw, pitch = 0, 0.6
mouse_sensitivity = 0.005
pygame.event.set_grab(True)
pygame.mouse.set_visible(False)

# === Main Loop ===
running = True
t = 0
while running:
    dt = clock.tick(FPS) / 1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # === Mouse look ===
    mx, my = pygame.mouse.get_rel()
    yaw += mx * mouse_sensitivity
    pitch -= my * mouse_sensitivity
    pitch = max(-1.2, min(1.2, pitch))

    # === Clear screen ===
    screen.fill(SPACE_COLOR)

    # === Draw warped grid with lensing ===
    for line in grid_points:
        warped = apply_lensing(line.copy())
        rotated = rotate_y(warped, yaw)
        rotated = rotate_x(rotated, pitch)
        pts2d = project(rotated)
        pygame.draw.aalines(screen, GRID_COLOR, False, pts2d, 1)

    # === Draw accretion ring ===
    ring_rot = rotate_y(ring.copy(), yaw + t * 0.5)
    ring_rot = rotate_x(ring_rot, pitch)
    ring_lensed = apply_lensing(ring_rot.copy(), strength=1000, radius=220)
    ring_pts = project(ring_lensed)
    pygame.draw.aalines(screen, RING_COLOR, True, ring_pts, 2)

    # === Draw event horizon ===
    cx, cy = WIDTH // 2, HEIGHT // 2
    draw_glow(screen, cx, cy, 60, GLOW_COLOR)
    pygame.draw.circle(screen, (0, 0, 0), (cx, cy), 45)

    pygame.display.flip()
    t += 1

pygame.quit()
