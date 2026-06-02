import pygame
import math

# ==========================================================
# Newton's Cradle (Pygame)
#
# Controls:
#   SPACE  -> Reset cradle
#   ESC    -> Quit
#
# Inspired by the provided reference image:
# - Dark background
# - Green frame
# - Glossy 3D-looking spheres
# - Blue strings
# ==========================================================

pygame.init()

# ----------------------------------------------------------
# Configuration
# ----------------------------------------------------------
WIDTH = 1200
HEIGHT = 800

FPS = 60

BG_COLOR = (5, 5, 12)

FRAME_COLOR = (35, 180, 35)
FRAME_HIGHLIGHT = (90, 255, 90)

STRING_COLOR = (120, 120, 255)

BALL_RADIUS = 32
STRING_LENGTH = 260

# Faster motion
GRAVITY = 35.0
DAMPING = 0.9995

# ----------------------------------------------------------
# Window
# ----------------------------------------------------------
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Newton's Cradle")

clock = pygame.time.Clock()

# ----------------------------------------------------------
# Ball Class
# ----------------------------------------------------------
class Ball:
    def __init__(self, pivot_x, pivot_y, angle=0):
        self.pivot_x = pivot_x
        self.pivot_y = pivot_y

        self.angle = angle
        self.angular_velocity = 0.0

    def update(self, dt):
        accel = -(GRAVITY / STRING_LENGTH) * math.sin(self.angle)

        self.angular_velocity += accel * dt
        self.angular_velocity *= DAMPING

        self.angle += self.angular_velocity * dt

    @property
    def x(self):
        return self.pivot_x + STRING_LENGTH * math.sin(self.angle)

    @property
    def y(self):
        return self.pivot_y + STRING_LENGTH * math.cos(self.angle)


# ----------------------------------------------------------
# Create glossy sphere
# ----------------------------------------------------------
def draw_sphere(surface, x, y, radius):
    sphere = pygame.Surface(
        (radius * 2 + 10, radius * 2 + 10),
        pygame.SRCALPHA
    )

    cx = radius + 5
    cy = radius + 5

    # Main radial gradient
    for r in range(radius, 0, -1):
        t = r / radius

        shade = int(15 + 65 * t)

        color = (
            shade,
            shade,
            shade + 10,
            255
        )

        pygame.draw.circle(
            sphere,
            color,
            (cx, cy),
            r
        )

    # Rim
    pygame.draw.circle(
        sphere,
        (15, 15, 15),
        (cx, cy),
        radius,
        2
    )

    # Specular highlights
    pygame.draw.circle(
        sphere,
        (255, 255, 255),
        (cx - radius // 3, cy - radius // 3),
        radius // 6
    )

    pygame.draw.circle(
        sphere,
        (220, 220, 220),
        (cx - radius // 2, cy + radius // 8),
        radius // 10
    )

    pygame.draw.circle(
        sphere,
        (210, 210, 210),
        (cx + radius // 4, cy + radius // 3),
        radius // 12
    )

    surface.blit(
        sphere,
        (x - radius - 5, y - radius - 5)
    )


# ----------------------------------------------------------
# Shadow under sphere
# ----------------------------------------------------------
def draw_shadow(surface, x, y):
    shadow = pygame.Surface((120, 40), pygame.SRCALPHA)

    pygame.draw.ellipse(
        shadow,
        (0, 0, 0, 80),
        (0, 0, 120, 40)
    )

    surface.blit(
        shadow,
        (x - 60, y - 20)
    )


# ----------------------------------------------------------
# Draw frame
# ----------------------------------------------------------
def draw_frame(surface):
    left = WIDTH // 2 - 260
    right = WIDTH // 2 + 260

    top = 120
    bottom = 690

    thickness = 5

    # Outer frame
    pygame.draw.line(surface, FRAME_COLOR,
                     (left, top), (right, top), thickness)

    pygame.draw.line(surface, FRAME_COLOR,
                     (left, top), (left, bottom), thickness)

    pygame.draw.line(surface, FRAME_COLOR,
                     (right, top), (right, bottom), thickness)

    pygame.draw.line(surface, FRAME_COLOR,
                     (left, bottom), (right, bottom), thickness)

    # Inner frame
    inset = 30

    pygame.draw.line(surface, FRAME_HIGHLIGHT,
                     (left + inset, top + inset),
                     (right - inset, top + inset), 2)

    pygame.draw.line(surface, FRAME_HIGHLIGHT,
                     (left + inset, top + inset),
                     (left + inset, bottom - inset), 2)

    pygame.draw.line(surface, FRAME_HIGHLIGHT,
                     (right - inset, top + inset),
                     (right - inset, bottom - inset), 2)

    pygame.draw.line(surface, FRAME_HIGHLIGHT,
                     (left + inset, bottom - inset),
                     (right - inset, bottom - inset), 2)

    # Base glow
    glow = pygame.Surface((600, 40), pygame.SRCALPHA)

    pygame.draw.rect(
        glow,
        (50, 255, 50, 30),
        glow.get_rect()
    )

    surface.blit(glow, (WIDTH // 2 - 300, bottom - 20))


# ----------------------------------------------------------
# Collision handling
# ----------------------------------------------------------
def handle_collisions(balls):
    for i in range(len(balls) - 1):
        b1 = balls[i]
        b2 = balls[i + 1]

        dx = b2.x - b1.x
        distance = abs(dx)

        min_distance = BALL_RADIUS * 2

        if distance < min_distance:

            overlap = min_distance - distance

            correction = overlap * 0.0008

            if dx > 0:
                b1.angle -= correction
                b2.angle += correction
            else:
                b1.angle += correction
                b2.angle -= correction

            # Exchange angular velocities
            b1.angular_velocity, b2.angular_velocity = (
                b2.angular_velocity,
                b1.angular_velocity
            )


# ----------------------------------------------------------
# Reset cradle
# ----------------------------------------------------------
def reset_cradle(balls):
    for ball in balls:
        ball.angle = 0.0
        ball.angular_velocity = 0.0

    # Pull leftmost ball back
    balls[0].angle = -1.0


# ----------------------------------------------------------
# Create balls
# ----------------------------------------------------------
pivot_y = 150

spacing = BALL_RADIUS * 2
center_x = WIDTH // 2

balls = []

for i in range(5):
    pivot_x = center_x + (i - 2) * spacing
    balls.append(Ball(pivot_x, pivot_y))

reset_cradle(balls)

# ----------------------------------------------------------
# Main Loop
# ----------------------------------------------------------
running = True

while running:

    dt = clock.tick(FPS) / 1000.0

    # ------------------------------------------------------
    # Events
    # ------------------------------------------------------
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            # ESC -> quit
            if event.key == pygame.K_ESCAPE:
                running = False

            # SPACE -> reset
            elif event.key == pygame.K_SPACE:
                reset_cradle(balls)

    # ------------------------------------------------------
    # Physics
    # ------------------------------------------------------
    for ball in balls:
        ball.update(dt)

    handle_collisions(balls)

    # ------------------------------------------------------
    # Draw
    # ------------------------------------------------------
    screen.fill(BG_COLOR)

    draw_frame(screen)

    # Strings
    for ball in balls:
        pygame.draw.line(
            screen,
            STRING_COLOR,
            (int(ball.pivot_x), int(ball.pivot_y)),
            (int(ball.x), int(ball.y)),
            2
        )

    # Shadows first
    for ball in balls:
        draw_shadow(
            screen,
            int(ball.x),
            700
        )

    # Draw spheres from back to front
    for ball in sorted(balls, key=lambda b: b.y):
        draw_sphere(
            screen,
            int(ball.x),
            int(ball.y),
            BALL_RADIUS
        )

    pygame.display.flip()

pygame.quit()