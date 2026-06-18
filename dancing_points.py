"""
Dancing Points - Python/pygame conversion
Original BBC BASIC by KMoerman 2026

Not an accurate physics simulation - made for visual effect.
Based on charged particles attracted to 'attractors' while influenced
by a simulated magnetic field perpendicular to the screen, generating
a force 90 degrees to the direction of travel, proportional to velocity.
"""

import pygame
import numpy as np
import sys

# --- Constants ---
W, H = 700, 650          # Window size
N_POINTS = 400           # Number of particles
N_ATTRACT = 2            # Number of attractors
R = 280                  # Max start radius from center
B = 0.01                 # Magnetic field strength (causes rotation)
G = 40                   # Gravitational constant (attraction strength)
OVERLAY_INTERVAL = 15    # How often to apply semi-transparent overlay
DRAW_INTERVAL = 5        # How often to draw points
OVERLAY_ALPHA = 16       # Transparency of fade overlay (0-255)
POINT_SIZE = 8           # Radius of each rendered point

def init_points():
    """Initialise all particle positions, velocities, and colors."""
    rad = 0.7 * R + 0.3 * R * np.random.rand(N_POINTS)
    angle = 2 * np.pi * np.random.rand(N_POINTS)
    x = rad * np.cos(angle)
    y = rad * np.sin(angle)
    vx = np.zeros(N_POINTS)
    vy = np.zeros(N_POINTS)
    # Assign colors cycling through hues
    colors = []
    for k in range(N_POINTS):
        hue = (k % 127) / 127.0
        color = pygame.Color(0)
        color.hsva = (hue * 360, 90, 90, 100)
        colors.append((color.r, color.g, color.b))
    return x, y, vx, vy, colors

def update_pos(x, y, vx, vy, xattract, yattract):
    """Update velocities from attractors and magnetic field, then update positions."""
    # Attraction from each attractor
    for n in range(N_ATTRACT):
        dx = x - xattract[n]
        dy = y - yattract[n]
        # Avoid singularity at zero distance
        mask = (dx != 0) | (dy != 0)
        rsq = np.where(mask, dx * dx + dy * dy, 1.0)
        r = np.sqrt(rsq)
        f = np.where(mask, G / (r * rsq), 0.0)
        vx -= f * dx
        vy -= f * dy

    # Magnetic field effect: force perpendicular to velocity
    vx -= vy * B
    vy += vx * B

    # Update positions
    x += vx
    y += vy
    return x, y, vx, vy

def world_to_screen(x, y):
    """Convert world coords (centered at 0,0) to screen pixel coords."""
    return int(x + W // 2), int(H // 2 - y)

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Dancing Points")
    clock = pygame.time.Clock()

    # Overlay surface: semi-transparent black rectangle for fading trails
    overlay = pygame.Surface((W, H))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(OVERLAY_ALPHA)

    # Attractor positions
    xattract = np.array([-R / 3, R / 3])
    yattract = np.array([-R / 3, R / 3])

    x, y, vx, vy, colors = init_points()

    screen.fill((0, 0, 0))
    t = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                pygame.quit()
                sys.exit()

        x, y, vx, vy = update_pos(x, y, vx, vy, xattract, yattract)

        if t % OVERLAY_INTERVAL == 0:
            # Fade existing trails
            screen.blit(overlay, (0, 0))
            # Redraw attractors as white filled circles
            for n in range(N_ATTRACT):
                sx, sy = world_to_screen(xattract[n], yattract[n])
                pygame.draw.circle(screen, (255, 255, 255), (sx, sy), 8)

        if t % DRAW_INTERVAL == 0:
            # Draw all particles
            for k in range(N_POINTS):
                sx, sy = world_to_screen(x[k], y[k])
                if 0 <= sx < W and 0 <= sy < H:
                    pygame.draw.circle(screen, colors[k], (sx, sy), 2)

            pygame.display.flip()
            clock.tick(60)

        t += 1
        if t > 1200:
            t = 0

if __name__ == "__main__":
    main()
