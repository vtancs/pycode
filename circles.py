import math
import pygame

# --------------------------------------------------
# Configuration (matches values visible in screenshot)
# --------------------------------------------------

W2 = 2                 # checker size
CX = 128               # center x
CY = 88                # center y
R = 30                 # orbit radius
RC = 20                # center circle radius

WIDTH = 320
HEIGHT = 200

BLACK = (0, 0, 0)
WHITE = (220, 220, 220)
RED = (180, 0, 0)

# --------------------------------------------------
# Helper: BASIC-style modulo function
# DEF FN m(a,b)=a-b*INT(a/b)
# --------------------------------------------------

def fn_m(a, b):
    return a - b * int(a / b)

# --------------------------------------------------
# Initialize pygame
# --------------------------------------------------

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Circle Pattern Demo")
clock = pygame.time.Clock()

# --------------------------------------------------
# Draw scene once
# --------------------------------------------------

screen.fill(BLACK)

orbit_centers = []

# Five outer circles
for i in range(5):
    aa = i * W2 * (math.pi / 5.0)

    px = CX + math.cos(aa) * R
    py = CY + math.sin(aa) * R

    orbit_centers.append((px, py))

    pygame.draw.circle(
        screen,
        WHITE,
        (round(px), round(py)),
        R,
        1
    )

# Central circle
pygame.draw.circle(
    screen,
    WHITE,
    (CX, CY),
    RC,
    1
)

# --------------------------------------------------
# Red patterned circle (angle = 0)
# --------------------------------------------------

aa = 0.0

px = CX + math.cos(aa) * R
py = CY + math.sin(aa) * R

for y in range(int(py - R), int(py + R) + 1):

    h = R * R - (y - py) * (y - py)

    if h < 0:
        continue

    w = int(math.sqrt(h))

    x1 = int(px - w)
    x2 = int(px + w)

    for x in range(x1, x2 + 1):

        if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
            continue

        # Skip pixels inside center circle
        dd = (x - CX) ** 2 + (y - CY) ** 2

        if dd < RC * RC:
            continue

        # Checkerboard condition from BASIC code
        if fn_m(x, W2) != fn_m(y, W2):
            continue

        screen.set_at((x, y), RED)

# Draw outlines again so they appear on top
for ox, oy in orbit_centers:
    pygame.draw.circle(
        screen,
        WHITE,
        (round(ox), round(oy)),
        R,
        1
    )

pygame.draw.circle(
    screen,
    WHITE,
    (CX, CY),
    RC,
    1
)

pygame.display.flip()

# --------------------------------------------------
# Main loop
# ESC quits
# --------------------------------------------------

running = True

while running:
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    clock.tick(60)

pygame.quit()