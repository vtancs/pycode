import pygame
import math
import random
import sys

# =========================================================
# RETRO TRUE PERLIN DEMO
#
# ESC              = Quit
# UP ARROW         = Increase speed
# DOWN ARROW       = Decrease speed
# MOUSE WHEEL      = Speed control
#
# PLUS (+)         = Increase amplitude
# MINUS (-)        = Decrease amplitude
#
# SPACEBAR         = Randomize colors
# =========================================================

pygame.init()

# ---------------------------------------------------------
# WINDOW
# ---------------------------------------------------------
WIDTH = 1280
HEIGHT = 720

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Retro Perlin Demo")

clock = pygame.time.Clock()

# ---------------------------------------------------------
# INITIAL COLORS
# ---------------------------------------------------------
BLACK = (0, 0, 0)

GOLD = (255, 220, 120)
MID_GOLD = (200, 160, 80)
DARK_GOLD = (120, 90, 40)

# ---------------------------------------------------------
# FONT
# ---------------------------------------------------------
font = pygame.font.SysFont("consolas", 24)

# =========================================================
# TRUE 1D PERLIN NOISE
# =========================================================

perm = list(range(256))
random.shuffle(perm)
perm *= 2


def fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def lerp(a, b, t):
    return a + t * (b - a)


def grad(hash_value, x):
    return x if (hash_value & 1) == 0 else -x


def perlin1d(x):

    xi = int(math.floor(x)) & 255
    xf = x - math.floor(x)

    u = fade(xf)

    a = perm[xi]
    b = perm[xi + 1]

    return lerp(
        grad(a, xf),
        grad(b, xf - 1),
        u
    )


# =========================================================
# RANDOM COLOR FUNCTION
# =========================================================

def random_color(brightness_min=80):

    return (
        random.randint(brightness_min, 255),
        random.randint(brightness_min, 255),
        random.randint(brightness_min, 255)
    )


# =========================================================
# SETTINGS
# =========================================================

time_offset = 0.0

speed = 0.01
amplitude = 180

PARTICLE_SPACING = 6

running = True

# =========================================================
# MAIN LOOP
# =========================================================

while running:

    # -----------------------------------------------------
    # EVENTS
    # -----------------------------------------------------
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        # -------------------------------------------------
        # KEYBOARD
        # -------------------------------------------------
        if event.type == pygame.KEYDOWN:

            # ESCAPE TO QUIT
            if event.key == pygame.K_ESCAPE:
                running = False

            # SPEED UP
            if event.key == pygame.K_UP:
                speed += 0.002

            # SPEED DOWN
            if event.key == pygame.K_DOWN:
                speed = max(0.001, speed - 0.002)

            # AMPLITUDE UP (+)
            if event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                amplitude += 10

            # AMPLITUDE DOWN (-)
            if event.key == pygame.K_MINUS:
                amplitude = max(20, amplitude - 10)

            # -------------------------------------------------
            # SPACEBAR = RANDOM COLORS
            # -------------------------------------------------
            if event.key == pygame.K_SPACE:

                GOLD = random_color(180)
                MID_GOLD = random_color(120)
                DARK_GOLD = random_color(60)

        # -------------------------------------------------
        # MOUSE WHEEL = SPEED
        # -------------------------------------------------
        if event.type == pygame.MOUSEWHEEL:

            if event.y > 0:
                speed += 0.002

            if event.y < 0:
                speed = max(0.001, speed - 0.002)

    # -----------------------------------------------------
    # CLEAR SCREEN
    # -----------------------------------------------------
    screen.fill(BLACK)

    # -----------------------------------------------------
    # RETRO SCANLINES
    # -----------------------------------------------------
    for y in range(0, HEIGHT, 4):

        pygame.draw.line(
            screen,
            (18, 18, 18),
            (0, y),
            (WIDTH, y)
        )

    # -----------------------------------------------------
    # UI TEXT
    # -----------------------------------------------------
    title = font.render(
        "RETRO TRUE PERLIN DEMO",
        True,
        GOLD
    )
    screen.blit(title, (20, 20))

    speed_text = font.render(
        f"SPEED: {speed:.3f}",
        True,
        GOLD
    )
    screen.blit(speed_text, (20, 55))

    amp_text = font.render(
        f"AMPLITUDE: {amplitude}",
        True,
        GOLD
    )
    screen.blit(amp_text, (20, 90))

    controls = font.render(
        "UP/DOWN or WHEEL = SPEED   +/- = AMPLITUDE   SPACE = COLORS   ESC = QUIT",
        True,
        GOLD
    )
    screen.blit(controls, (20, 125))

    # -----------------------------------------------------
    # DRAW WAVE
    # -----------------------------------------------------
    prev = None

    for x in range(0, WIDTH, PARTICLE_SPACING):

        # -------------------------------------------------
        # TRUE PERLIN NOISE
        # -------------------------------------------------
        nx = (x * 0.008) + time_offset

        noise = perlin1d(nx)

        # -------------------------------------------------
        # SINE WAVE MORPHING
        # -------------------------------------------------
        s1 = math.sin((x * 0.010) + time_offset * 2.0)

        s2 = math.sin((x * 0.004) - time_offset)

        morph = (s1 * 0.6) + (s2 * 0.4)

        # -------------------------------------------------
        # COMBINE
        # -------------------------------------------------
        value = (noise * 0.7) + (morph * 0.3)

        y = HEIGHT // 2 + int(value * amplitude)

        # -------------------------------------------------
        # BIG GLOW PARTICLES
        # -------------------------------------------------

        # Outer glow
        pygame.draw.circle(
            screen,
            DARK_GOLD,
            (x, y),
            10
        )

        # Mid glow
        pygame.draw.circle(
            screen,
            MID_GOLD,
            (x, y),
            6
        )

        # Bright center
        pygame.draw.circle(
            screen,
            GOLD,
            (x, y),
            3
        )

        # -------------------------------------------------
        # CONNECTING LINES
        # -------------------------------------------------
        if prev is not None:

            pygame.draw.line(
                screen,
                DARK_GOLD,
                prev,
                (x, y),
                2
            )

        prev = (x, y)

    # -----------------------------------------------------
    # ANIMATION
    # -----------------------------------------------------
    time_offset += speed

    # -----------------------------------------------------
    # DISPLAY UPDATE
    # -----------------------------------------------------
    pygame.display.flip()

    clock.tick(60)

pygame.quit()
sys.exit()