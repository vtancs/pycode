import pygame
import math
import sys

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 1000, 800
FPS = 60

BASE_SCALE = 130
K = 38.39
DRAW_STEP = 0.002
# ----------------------------------------

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ultra Neon Beating Heart")
clock = pygame.time.Clock()

title_font = pygame.font.SysFont("Arial", 48)
axis_font = pygame.font.SysFont("Arial", 18)

center_x = WIDTH // 2
center_y = HEIGHT // 2


# -------- Heart Function --------
def heart_function(x):
    try:
        return (abs(x) ** (2/3)) + 0.9 * math.sin(K * x) * math.sqrt(3 - x*x)
    except:
        return None


# -------- Color Gradient (HSV → RGB) --------
def hsv_to_rgb(h, s, v):
    return tuple(round(i * 255) for i in pygame.Color(0).hsva_to_color((h, s*100, v*100, 100)))


def shifting_color(time):
    hue = (time * 40) % 360
    color = pygame.Color(0)
    color.hsva = (hue, 100, 100, 100)
    return color.r, color.g, color.b


# -------- Generate Heart Points --------
def generate_heart_points(scale_multiplier):
    points = []
    scale = BASE_SCALE * scale_multiplier

    x = -math.sqrt(3)
    while x <= math.sqrt(3):
        y = heart_function(x)
        if y is not None:
            screen_x = center_x + x * scale
            screen_y = center_y - y * scale
            points.append((screen_x, screen_y))
        x += DRAW_STEP

    return points


# -------- True Radial Glow --------
def draw_true_glow(surface, points, color):
    glow_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    pygame.draw.aalines(glow_surface, color, False, points)

    # Apply blur by scaling down then up
    for i in range(4):
        scale = 0.5
        small = pygame.transform.smoothscale(
            glow_surface,
            (int(WIDTH * scale), int(HEIGHT * scale))
        )
        glow_surface = pygame.transform.smoothscale(
            small,
            (WIDTH, HEIGHT)
        )

    glow_surface.set_alpha(120)
    surface.blit(glow_surface, (0, 0))

    pygame.draw.aalines(surface, color, False, points)


# -------- Double Lub-Dub Beat --------
def heartbeat(time):
    beat = math.sin(time * 2.2)
    double = 0.12 * math.exp(-((beat - 0.8) ** 2) * 25)
    double += 0.07 * math.exp(-((beat + 0.2) ** 2) * 25)
    return 1 + double


# -------- Draw Axes --------
def draw_axes(scale_multiplier):
    scale = BASE_SCALE * scale_multiplier

    max_units_x = WIDTH / scale
    max_units_y = HEIGHT / scale

    for i in range(-int(max_units_x), int(max_units_x) + 1):
        x = center_x + i * scale
        pygame.draw.line(screen, (25, 25, 25), (x, 0), (x, HEIGHT), 1)

    for j in range(-int(max_units_y), int(max_units_y) + 1):
        y = center_y + j * scale
        pygame.draw.line(screen, (25, 25, 25), (0, y), (WIDTH, y), 1)

    pygame.draw.line(screen, (200, 200, 200), (0, center_y), (WIDTH, center_y), 2)
    pygame.draw.line(screen, (200, 200, 200), (center_x, 0), (center_x, HEIGHT), 2)


# -------- Inner Oscillating Wave --------
def draw_inner_wave(scale_multiplier, time):
    scale = BASE_SCALE * scale_multiplier
    wave_points = []

    x = -1.4
    while x <= 1.4:
        y = 0.3 * math.sin(6 * x + time * 5)
        screen_x = center_x + x * scale
        screen_y = center_y - y * scale
        wave_points.append((screen_x, screen_y))
        x += 0.01

    pygame.draw.aalines(screen, (0, 255, 200), False, wave_points)


# -------- Main Loop --------
time = 0
running = True

while running:
    clock.tick(FPS)
    time += 0.03

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))

    pulse = heartbeat(time)
    color = shifting_color(time)

    draw_axes(pulse)

    heart_points = generate_heart_points(pulse)

    if len(heart_points) > 1:
        draw_true_glow(screen, heart_points, color)

    draw_inner_wave(pulse, time)

    title = title_font.render("Happy Valentines!", True, color)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

    pygame.display.flip()

pygame.quit()
sys.exit()