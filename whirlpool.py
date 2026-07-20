import pygame
import math
import random
import sys

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Interactive Whirlpool Maelstrom")
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)

# Center of the whirlpool
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2

# Color Palette Options (Min RGB, Max RGB) for the particles
COLOR_PALETTES = [
    ((10, 70, 140), (40, 130, 210)),    # 0: Deep Cyan (Original)
    ((40, 10, 80), (120, 30, 180)),    # 1: Abyssal Purple
    ((10, 60, 40), (40, 180, 100)),    # 2: Bio-luminescent Green
    ((80, 10, 10), (190, 40, 40)),     # 3: Crimson Vortex
    ((60, 60, 60), (160, 160, 160))    # 4: Monochromatic Etching
]
current_palette_idx = 0

# Particle Size Scale (1 to 5)
current_size_scale = 1

class MaelstromParticle:
    def __init__(self):
        self.reset()
        self.radius = random.uniform(10, max(WIDTH, HEIGHT))

    def reset(self):
        self.radius = random.uniform(max(WIDTH, HEIGHT) * 0.5, max(WIDTH, HEIGHT))
        self.angle = random.uniform(0, 2 * math.pi)
        self.length = random.randint(3, 15)
        self.speed_factor = random.uniform(0.8, 1.2)
        self.update_color()

    def update_color(self):
        min_c, max_c = COLOR_PALETTES[current_palette_idx]
        self.color = (
            random.randint(min_c[0], max_c[0]),
            random.randint(min_c[1], max_c[1]),
            random.randint(min_c[2], max_c[2])
        )

    def update(self, time_step, speed_multiplier):
        if self.radius < 5:
            self.reset()
            return

        eff_dt = time_step * speed_multiplier

        # Swirl speed increases closer to the center
        angular_velocity = (35 / (self.radius + 20)) * self.speed_factor
        self.angle += angular_velocity * eff_dt

        # Inward suction speed increases closer to the center
        radial_velocity = (15 + (150 / (self.radius + 5))) * self.speed_factor
        self.radius -= radial_velocity * eff_dt

    def draw(self, surface, size_scale):
        x1 = CENTER_X + self.radius * math.cos(self.angle)
        y1 = CENTER_Y + self.radius * math.sin(self.angle)
        
        tail_radius = self.radius + 2
        tail_angle = self.angle - (0.05 * self.length / (self.radius + 1))
        x2 = CENTER_X + tail_radius * math.cos(tail_angle)
        y2 = CENTER_Y + tail_radius * math.sin(tail_angle)

        # Base width calculation dynamically amplified by the selected size scale
        base_width = int(2 * (self.radius / 300) + 1)
        line_thickness = base_width * size_scale

        pygame.draw.line(surface, self.color, (x1, y1), (x2, y2), line_thickness)


class Boat:
    def __init__(self):
        self.radius = 180.0
        self.angle = 4.5
        
    def update(self, time_step, speed_multiplier):
        eff_dt = time_step * speed_multiplier
        
        angular_velocity = 22 / (self.radius + 10)
        self.angle += angular_velocity * eff_dt
        self.radius -= 2.5 * eff_dt
        
        if self.radius < 15:
            self.radius = 220
            self.angle = random.uniform(0, 2 * math.pi)

    def draw(self, surface):
        bx = CENTER_X + self.radius * math.cos(self.angle)
        by = CENTER_Y + self.radius * math.sin(self.angle)
        boat_orientation = self.angle + math.pi / 2 + 0.15
        
        hull_points = [(-20, -4), (20, -4), (14, 6), (-14, 6)]
        cabin_points = [(-6, -4), (4, -4), (4, -10), (-6, -10)]
        
        def rotate_and_translate(points):
            transformed = []
            for pt_x, pt_y in points:
                rx = pt_x * math.cos(boat_orientation) - pt_y * math.sin(boat_orientation)
                ry = pt_x * math.sin(boat_orientation) + pt_y * math.cos(boat_orientation)
                transformed.append((bx + rx, by + ry))
            return transformed

        pygame.draw.polygon(surface, BLACK, rotate_and_translate(hull_points))
        pygame.draw.polygon(surface, BLACK, rotate_and_translate(cabin_points))


# Setup elements
NUM_PARTICLES = 2500
particles = [MaelstromParticle() for _ in range(NUM_PARTICLES)]
boat = Boat()

# Simulation modifiers
global_speed = 1.0
dt = 0.1 
running = True

# For UI feedback text
font = pygame.font.SysFont(None, 24)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            
            # Left/Right arrow keys to cycle through themes
            elif event.key == pygame.K_RIGHT:
                current_palette_idx = (current_palette_idx + 1) % len(COLOR_PALETTES)
                for p in particles: p.update_color()
            elif event.key == pygame.K_LEFT:
                current_palette_idx = (current_palette_idx - 1) % len(COLOR_PALETTES)
                for p in particles: p.update_color()
            
            # + / = Key to increase particle size scale (Max 5)
            elif event.key == pygame.K_EQUALS or event.key == pygame.K_KP_PLUS:
                current_size_scale = min(5, current_size_scale + 1)
            # - Key to decrease particle size scale (Min 1)
            elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                current_size_scale = max(1, current_size_scale - 1)

    # Continuous key press check for smooth speed adjustments
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        global_speed = min(5.0, global_speed + 0.05)  # Cap max speed at 5x
    if keys[pygame.K_DOWN]:
        global_speed = max(0.0, global_speed - 0.05)  # Cap min speed at 0x (Pause)

    # Background Fill
    screen.fill((2, 12, 28))
    
    # Draw central abyss shadow gradient
    for r in range(120, 0, -10):
        shadow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        alpha = int(255 * (1 - (r / 120)))
        pygame.draw.circle(shadow_surf, (0, 3, 10, alpha), (CENTER_X, CENTER_Y), r)
        screen.blit(shadow_surf, (0, 0))

    # Update and draw simulation components
    for particle in particles:
        particle.update(dt, global_speed)
        particle.draw(screen, current_size_scale)

    pygame.draw.circle(screen, BLACK, (CENTER_X, CENTER_Y), 12)

    boat.update(dt, global_speed)
    boat.draw(screen)

    # Visual overlay showing configuration values
    speed_text = font.render(f"Speed: {global_speed:.2f}x (Up/Down)", True, (200, 200, 200))
    color_text = font.render(f"Theme ID: {current_palette_idx} (Left/Right)", True, (200, 200, 200))
    size_text = font.render(f"Particle Scale: {current_size_scale}/5 (+/- Keys)", True, (200, 200, 200))
    
    screen.blit(speed_text, (20, 20))
    screen.blit(color_text, (20, 45))
    screen.blit(size_text, (20, 70))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()