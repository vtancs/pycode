import sys
import numpy as np
import pygame

# Initialize pygame
pygame.init()

# --- Setup Constants and Arrays (From original BASIC) ---
A1 = np.array([[0.62367, -0.40337], [0.40337, 0.62367]])
A2 = np.array([[-0.37633, -0.40337], [0.40337, -0.37633]])
C2 = np.array([[1.0], [0.0]])
WH = np.array([[1200.0], [650.0]])
SCL = np.array([[1.4], [2.3]]) * WH
TRNSL = np.array([[-0.58], [-0.43]]) * WH
Npoints = 200000

width = int(WH[0, 0])
height = int(WH[1, 0])
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Golden Dragon - Interactive")

# Colors
BLACK = (0, 0, 0)
COLOR1 = (255, 215, 0)   # Gold
COLOR2 = (0, 255, 215)   # Cyan-ish

# --- Interactive States ---
zoom_factor = 1.0
origin_offset_x = width // 2
origin_offset_y = height // 2
is_dragging = False
last_mouse_pos = (0, 0)

# --- Pre-calculate Fractal Points ---
# Instead of storing raw NumPy arrays for color loops, we store Python tuples/lists 
# which Pygame blits natively without array overhead.
points_data = np.zeros((Npoints, 2))
colors_data = []

print("Calculating fractal points... Please wait a moment.")
XY = np.array([[0.0], [0.0]])
for t in range(Npoints):
    if np.random.rand() < 0.6445:
        XY = np.dot(A1, XY)
        colors_data.append(COLOR1)
    else:
        XY = np.dot(A2, XY) + C2
        colors_data.append(COLOR2)
    
    SCR = XY * SCL + TRNSL
    points_data[t] = [SCR[0, 0], SCR[1, 0]]
print("Calculation complete! Use mouse to drag, wheel to zoom.")

# --- Main Application Loop ---
clock = pygame.time.Clock()
running = True

while running:
    # 1. Handle Events (Mouse and Keyboard)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click
                is_dragging = True
                last_mouse_pos = event.pos
            elif event.button == 4: # Scroll Up
                zoom_factor *= 1.15
            elif event.button == 5: # Scroll Down
                zoom_factor /= 1.15
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                is_dragging = False
                
        elif event.type == pygame.MOUSEMOTION:
            if is_dragging:
                dx = event.pos[0] - last_mouse_pos[0]
                dy = event.pos[1] - last_mouse_pos[1]
                origin_offset_x += dx
                origin_offset_y += dy
                last_mouse_pos = event.pos

    # 2. Rendering
    screen.fill(BLACK)

    # Scale the coordinates
    scaled_points = points_data * zoom_factor
    
    # Process calculations using fast vector math
    plot_x = (origin_offset_x + scaled_points[:, 0]).astype(np.int32)
    plot_y = (origin_offset_y - scaled_points[:, 1]).astype(np.int32)

    # Plot the points directly onto the surface map
    for i in range(Npoints):
        px = plot_x[i]
        py = plot_y[i]
        # Only draw if the point lands inside our window boundaries
        if 0 <= px < width and 0 <= py < height:
            screen.set_at((px, py), colors_data[i])

    pygame.display.flip()
    clock.tick(60) 

pygame.quit()
sys.exit()