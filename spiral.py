import sys
import math
import pygame
import numpy as np

# Initialize Pygame
pygame.init()

# --- Configuration & Constants ---
W, H = 712, 576
HW, HH = W // 2, H // 2

Wcol = 8
Nspiral = 6
Maxdispl = 50

# Pre-calculated constants
omega = Nspiral * math.pi / HH
d = 10 / Maxdispl
pi_2 = math.pi / 2

# Set up the screen and clock
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Animated Dye Kaleidoscope")
clock = pygame.time.Clock()

# --- Pre-allocate Grid Matrices (Done once to maximize performance) ---
x_range = np.arange(0, W)
y_range = np.arange(0, H)
x_grid, y_grid = np.meshgrid(x_range, y_range, indexing="ij")

# Center coordinates
xx = x_grid - HW
yy = y_grid - HH

# Calculate distance to center and the circular mask
rad = np.hypot(xx, yy)
mask = rad < HH

# Filter static arrays using the mask to save CPU cycles per frame
rad_m = rad[mask]
x_grid_m = x_grid[mask]
xx_m = xx[mask]
yy_m = yy[mask]

# Calculate static angles (BBC BASIC coordinate orientation)
angle = np.arctan2(xx_m, yy_m)

# --- Animation Variable ---
t = 0.0  # Time tracker

# --- Main Application Loop ---
running = True
while running:
    # Frame rate limiter (target 60 FPS)
    clock.tick(60)
    
    # --- Input Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # Check if the pressed key is the Escape key
            if event.key == pygame.K_ESCAPE:
                running = False

    # Create a fresh black background matrix for this frame
    canvas_rgb = np.zeros((W, H, 3), dtype=np.uint8)

    # --- Time-Warped Mathematical Logic ---
    # 1. Animate the spiral wave by factoring in 't'
    radwave = np.sin(omega * rad_m + 0.5 * angle + t * 2.0)
    
    # 2. Warp the physical displacement over time
    displ = 10 / (np.abs(radwave) + d)
    
    # 3. Rotate the angle of displacement fluidly
    angledispl = angle + pi_2 + (t * 0.5)

    # Calculate time-shifted x displacement
    dx = displ * np.cos(angledispl)

    # 4. Phase-shift the color bands using 't' to create a rainbow flow
    col = ((x_grid_m + dx + int(t * 50)) // Wcol) * Wcol

    # 5. Dynamic RGB Generation 
    color_shift = int(t * 30)
    r = (2 * col + color_shift).astype(np.int32) & 255
    g = (11 * col - color_shift).astype(np.int32) & 255
    b = (5 * col + (color_shift // 2)).astype(np.int32) & 255

    # Inject calculations into our frame array
    canvas_rgb[mask] = np.stack((r, g, b), axis=-1)

    # Blit the frame array directly to the display surface
    surface = pygame.surfarray.make_surface(canvas_rgb)
    screen.blit(surface, (0, 0))
    pygame.display.flip()

    # Increment time tracker (adjust this value to change animation speed)
    t += 0.03

pygame.quit()
sys.exit()