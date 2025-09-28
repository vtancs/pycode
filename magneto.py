import pygame
import math
import sys
import random

# Initialize pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Magnetospheres of Earth and Neptune (real textures)")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
FIELD_COLOR = (100, 200, 255)
SOLAR_WIND = (255, 255, 100)

# Positions
earth_pos = (WIDTH // 4, HEIGHT // 2)
neptune_pos = (3 * WIDTH // 4, HEIGHT // 2)

# Radii
earth_radius = 40
earth_magnetosphere = 120
neptune_radius = 45
neptune_magnetosphere = 220

clock = pygame.time.Clock()

# Solar wind particles
particles = [{"x": random.randint(-200, WIDTH), "y": random.randint(0, HEIGHT)} for _ in range(200)]

# Background stars
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 3)) for _ in range(150)]

# Animation phase
phase = 0
frame_count = 0

# Load planet textures
earth_img = pygame.image.load("earth.jpg").convert_alpha()
neptune_img = pygame.image.load("neptune.jpg").convert_alpha()

# Scale textures to radii
earth_img = pygame.transform.smoothscale(earth_img, (earth_radius * 2, earth_radius * 2))
neptune_img = pygame.transform.smoothscale(neptune_img, (neptune_radius * 2, neptune_radius * 2))

def draw_background():
    """Draw stars and a faint Milky Way gradient"""
    screen.fill(BLACK)

    for i in range(HEIGHT):
        alpha = int(40 * math.exp(-((i - HEIGHT // 2) ** 2) / (2 * (HEIGHT // 3) ** 2)))
        pygame.draw.line(screen, (80, 80, 120, alpha), (0, i), (WIDTH, i))

    for (x, y, size) in stars:
        pygame.draw.circle(screen, WHITE, (x, y), size)

def draw_dotted_ellipse(center, left_radius, right_radius, vertical_radius, color, phase_shift):
    steps = 60
    for i in range(steps):
        if (i + phase_shift) % 4 < 2:
            angle = 2 * math.pi * i / steps
            x = center[0] + (right_radius if math.cos(angle) > 0 else left_radius) * math.cos(angle)
            y = center[1] + vertical_radius * math.sin(angle)
            pygame.draw.circle(screen, color, (int(x), int(y)), 2)

def draw_tail(center, right_radius, color, tail_strength=1.0):
    global frame_count
    line_spacing = int(20 * tail_strength)
    wave_amplitude = int(10 * tail_strength)
    wave_length = 80
    num_lines = int(3 * tail_strength)

    for i in range(-num_lines, num_lines + 1):
        tail_points = []
        for t in range(0, 400, 20):
            x = center[0] + (right_radius // 2) + t
            y = center[1] + i * line_spacing + int(
                wave_amplitude * math.sin((t / wave_length) + frame_count / 20)
            )
            tail_points.append((x, y))
        if len(tail_points) > 1:
            pygame.draw.lines(screen, color, False, tail_points, 1)

def draw_planet_with_magnetosphere(center, planet_img, planet_radius, magnetosphere_radius,
                                   compression_factor=1.0, field_strength=1.0,
                                   tail_strength=1.0, phase_shift=0):
    left_radius = int(magnetosphere_radius * (1 - 0.5 * compression_factor))
    right_radius = int(magnetosphere_radius * (1 + 0.2 * compression_factor))

    # Magnetosphere
    draw_dotted_ellipse(center, left_radius, right_radius, magnetosphere_radius // 2,
                        FIELD_COLOR, phase_shift)

    # Tail
    draw_tail(center, right_radius, FIELD_COLOR, tail_strength)

    # Planet texture
    rect = planet_img.get_rect(center=center)
    screen.blit(planet_img, rect)

    return left_radius, right_radius, magnetosphere_radius, field_strength

def update_solar_wind(planet_data):
    for p in particles:
        p["x"] += 4
        for (cx, cy, left_r, right_r, vert_r, field_strength) in planet_data:
            dx = p["x"] - cx
            dy = p["y"] - cy
            rx = left_r if dx < 0 else right_r
            dist = (dx / rx) ** 2 + (dy / (vert_r // 2)) ** 2
            if dist < 1.2:
                angle = math.atan2(dy, dx)
                p["y"] += math.sin(angle) * 2 * field_strength
                p["x"] += math.cos(angle) * 2 * field_strength
        if p["x"] > WIDTH + 10:
            p["x"] = -10
            p["y"] = random.randint(0, HEIGHT)
        pygame.draw.circle(screen, SOLAR_WIND, (p["x"], p["y"]), 2)

def main():
    global phase, frame_count
    running = True
    while running:
        frame_count += 1
        draw_background()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        phase = (phase + 1) % 20

        # Earth
        earth_left, earth_right, earth_vert, earth_strength = draw_planet_with_magnetosphere(
            earth_pos, earth_img, earth_radius, earth_magnetosphere,
            compression_factor=1.0, field_strength=1.0,
            tail_strength=0.5, phase_shift=phase
        )

        # Neptune
        neptune_left, neptune_right, neptune_vert, neptune_strength = draw_planet_with_magnetosphere(
            neptune_pos, neptune_img, neptune_radius, neptune_magnetosphere,
            compression_factor=0.05, field_strength=0.5,
            tail_strength=2.0, phase_shift=phase + 5
        )

        update_solar_wind([
            (earth_pos[0], earth_pos[1], earth_left, earth_right, earth_vert, earth_strength),
            (neptune_pos[0], neptune_pos[1], neptune_left, neptune_right, neptune_vert, neptune_strength)
        ])

        font = pygame.font.SysFont(None, 36)
        screen.blit(font.render("Earth", True, WHITE),
                    (earth_pos[0] - 40, earth_pos[1] + earth_radius + 20))
        screen.blit(font.render("Neptune", True, WHITE),
                    (neptune_pos[0] - 60, neptune_pos[1] + neptune_radius + 20))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
