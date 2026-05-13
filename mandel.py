import pygame
import sys
import math
import random

# --------------------------------------------------
# Initialize pygame
# --------------------------------------------------
pygame.init()

# --------------------------------------------------
# Window settings
# --------------------------------------------------
WIDTH = 750
HEIGHT = 510

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Interactive Mandelbrot Explorer")

clock = pygame.time.Clock()

# --------------------------------------------------
# Mandelbrot settings
# --------------------------------------------------
max_iter = 120
escape_radius = 4

# Complex plane view
center_x = -0.5
center_y = 0.0
zoom = 1.0

# Mouse crosshair
crosshair_x = WIDTH // 2
crosshair_y = HEIGHT // 2

# --------------------------------------------------
# Random color palette
# --------------------------------------------------
palette_seed = random.random() * 1000

def color_map(iteration, max_iteration):

    if iteration == max_iteration:
        return (0, 0, 0)

    t = iteration / max_iteration

    r_phase = palette_seed
    g_phase = palette_seed + 2
    b_phase = palette_seed + 4

    red = int(127 + 127 * math.sin(8 * t + r_phase))
    green = int(127 + 127 * math.sin(8 * t + g_phase))
    blue = int(127 + 127 * math.sin(8 * t + b_phase))

    return (red, green, blue)

# --------------------------------------------------
# Convert screen coords to Mandelbrot coords
# --------------------------------------------------
def screen_to_complex(px, py):

    view_width = 3.5 / zoom
    view_height = view_width * HEIGHT / WIDTH

    min_x = center_x - view_width / 2
    min_y = center_y - view_height / 2

    x = min_x + (px / WIDTH) * view_width
    y = min_y + (py / HEIGHT) * view_height

    return x, y

# --------------------------------------------------
# Draw crosshair
# --------------------------------------------------
def draw_crosshair():

    color = (255, 255, 255)

    pygame.draw.line(
        screen,
        color,
        (crosshair_x - 15, crosshair_y),
        (crosshair_x + 15, crosshair_y),
        1
    )

    pygame.draw.line(
        screen,
        color,
        (crosshair_x, crosshair_y - 15),
        (crosshair_x, crosshair_y + 15),
        1
    )

    pygame.draw.circle(
        screen,
        color,
        (crosshair_x, crosshair_y),
        20,
        1
    )

# --------------------------------------------------
# Render Mandelbrot
# --------------------------------------------------
def render():

    view_width = 3.5 / zoom
    view_height = view_width * HEIGHT / WIDTH

    min_x = center_x - view_width / 2
    max_x = center_x + view_width / 2

    min_y = center_y - view_height / 2
    max_y = center_y + view_height / 2

    for py in range(HEIGHT):

        y0 = min_y + (py / HEIGHT) * (max_y - min_y)

        for px in range(WIDTH):

            x0 = min_x + (px / WIDTH) * (max_x - min_x)

            x = 0.0
            y = 0.0

            iteration = 0

            while (x * x + y * y <= escape_radius and
                   iteration < max_iter):

                xtemp = x * x - y * y + x0
                y = 2 * x * y + y0
                x = xtemp

                iteration += 1

            color = color_map(iteration, max_iter)

            screen.set_at((px, py), color)

        if py % 10 == 0:
            pygame.display.update()

    draw_crosshair()

    pygame.display.flip()

# --------------------------------------------------
# Initial render
# --------------------------------------------------
render()

# --------------------------------------------------
# Controls
# --------------------------------------------------
#
# Mouse Move      -> Move crosshair
# Left Click      -> Center on crosshair
# Mouse Wheel     -> Zoom toward crosshair
# Arrow Keys      -> Move view
# R               -> Randomize colors
# ESC             -> Quit
#
# --------------------------------------------------

running = True

while running:

    for event in pygame.event.get():

        # Quit
        if event.type == pygame.QUIT:
            running = False

        # --------------------------------------------------
        # Mouse movement updates crosshair
        # --------------------------------------------------
        elif event.type == pygame.MOUSEMOTION:

            crosshair_x, crosshair_y = event.pos

            render()

        # --------------------------------------------------
        # Mouse click centers on selected point
        # --------------------------------------------------
        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                center_x, center_y = screen_to_complex(
                    crosshair_x,
                    crosshair_y
                )

                render()

        # --------------------------------------------------
        # Mouse wheel zooms using crosshair position
        # --------------------------------------------------
        elif event.type == pygame.MOUSEWHEEL:

            target_x, target_y = screen_to_complex(
                crosshair_x,
                crosshair_y
            )

            if event.y > 0:
                zoom *= 1.35
            else:
                zoom /= 1.35

            # Keep target fixed at crosshair
            view_width = 3.5 / zoom
            view_height = view_width * HEIGHT / WIDTH

            min_x = target_x - (crosshair_x / WIDTH) * view_width
            min_y = target_y - (crosshair_y / HEIGHT) * view_height

            center_x = min_x + view_width / 2
            center_y = min_y + view_height / 2

            render()

        # --------------------------------------------------
        # Keyboard controls
        # --------------------------------------------------
        elif event.type == pygame.KEYDOWN:

            move_speed = 0.12 / zoom

            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_LEFT:
                center_x -= move_speed
                render()

            elif event.key == pygame.K_RIGHT:
                center_x += move_speed
                render()

            elif event.key == pygame.K_UP:
                center_y -= move_speed
                render()

            elif event.key == pygame.K_DOWN:
                center_y += move_speed
                render()

            elif event.key == pygame.K_r:

                palette_seed = random.random() * 1000

                render()

    clock.tick(60)

pygame.quit()
sys.exit()