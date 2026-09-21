import math
import random
import sys

import pygame


# ============================================================
# MY LITTLE SOLAR SYSTEM v0.1
#
# Original: Commodore 64 BASIC
# Converted to Python + Pygame
#
# Features:
#   - 8 planets
#   - Elliptical orbits
#   - Different orbital speeds
#   - C64-inspired colours
#   - Stars
#   - Selectable planets
#   - Green bounding box around selected planet
#   - Planet name display
#   - Saturn's rings
#
# Controls:
#   SPACE / ENTER / RIGHT ARROW = Next planet
#   ESC                         = Quit
# ============================================================


# ============================================================
# INITIALISE PYGAME
# ============================================================

pygame.init()


# ============================================================
# DISPLAY
# ============================================================

WIDTH = 800
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("My Little Solar System v0.1")

clock = pygame.time.Clock()


# ============================================================
# FONTS
# ============================================================

font = pygame.font.SysFont("consolas", 22, bold=True)
small_font = pygame.font.SysFont("consolas", 16)


# ============================================================
# COLOURS
# ============================================================

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

GREEN = (0, 255, 0)
YELLOW = (255, 220, 40)

DIM_GREY = (150, 150, 150)
ORBIT_GREY = (30, 30, 50)


# ============================================================
# C64-INSPIRED PLANET COLOURS
# ============================================================

C64_COLORS = {
    "mercury": (170, 170, 170),
    "venus":   (255, 180, 70),
    "earth":   (70, 150, 255),
    "mars":    (220, 70, 50),
    "jupiter": (210, 170, 120),
    "saturn":  (230, 210, 130),
    "uranus":  (100, 220, 220),
    "neptune": (70, 100, 230),
}


# ============================================================
# PLANET DATA
#
# Directly based on the original BASIC:
#
# 32 dx(0)=12:dy(0)=10:sp(0)=0.123
# 34 dx(1)=24:dy(1)=20:sp(1)=0.101
# 36 dx(2)=36:dy(2)=30:sp(2)=0.091
# 38 dx(3)=48:dy(3)=40:sp(3)=0.077
# 40 dx(4)=60:dy(4)=60:sp(4)=0.063
# 42 dx(5)=70:dy(5)=70:sp(5)=0.049
# 44 dx(6)=80:dy(6)=80:sp(6)=0.033
# 46 dx(7)=90:dy(7)=90:sp(7)=0.017
# ============================================================

planets = [

    {
        "name": "Mercury",
        "dx": 12,
        "dy": 10,
        "speed": 0.123,
        "angle": 0.0,
        "color": C64_COLORS["mercury"],
        "radius": 4,
    },

    {
        "name": "Venus",
        "dx": 24,
        "dy": 20,
        "speed": 0.101,
        "angle": 0.0,
        "color": C64_COLORS["venus"],
        "radius": 6,
    },

    {
        "name": "Earth",
        "dx": 36,
        "dy": 30,
        "speed": 0.091,
        "angle": 0.0,
        "color": C64_COLORS["earth"],
        "radius": 7,
    },

    {
        "name": "Mars",
        "dx": 48,
        "dy": 40,
        "speed": 0.077,
        "angle": 0.0,
        "color": C64_COLORS["mars"],
        "radius": 5,
    },

    {
        "name": "Jupiter",
        "dx": 60,
        "dy": 60,
        "speed": 0.063,
        "angle": 0.0,
        "color": C64_COLORS["jupiter"],
        "radius": 11,
    },

    {
        "name": "Saturn",
        "dx": 70,
        "dy": 70,
        "speed": 0.049,
        "angle": 0.0,
        "color": C64_COLORS["saturn"],
        "radius": 9,
    },

    {
        "name": "Uranus",
        "dx": 80,
        "dy": 80,
        "speed": 0.033,
        "angle": 0.0,
        "color": C64_COLORS["uranus"],
        "radius": 8,
    },

    {
        "name": "Neptune",
        "dx": 90,
        "dy": 90,
        "speed": 0.017,
        "angle": 0.0,
        "color": C64_COLORS["neptune"],
        "radius": 8,
    },
]


# ============================================================
# SOLAR SYSTEM POSITION
#
# Original C64:
#
#     X = 145
#     Y = 147
#
# On our larger display we put the Sun in the centre.
# ============================================================

CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2


# ============================================================
# ORBIT SCALING
#
# The original C64 coordinates are very small.
# We enlarge them for a modern 800x600 window.
# ============================================================

ORBIT_SCALE_X = 2.25
ORBIT_SCALE_Y = 1.65


# ============================================================
# SELECTED PLANET
#
# Original:
#
#     w = 0
#
# and:
#
#     if w < 7 then w = w + 1
#
# ============================================================

selected_planet = 0


# ============================================================
# CREATE STAR FIELD
# ============================================================

random.seed(42)

stars = []

for _ in range(180):

    x = random.randrange(WIDTH)
    y = random.randrange(HEIGHT)

    brightness = random.randrange(80, 220)

    stars.append(
        (x, y, brightness)
    )


# ============================================================
# DRAW STARS
# ============================================================

def draw_stars():

    for x, y, brightness in stars:

        color = (
            brightness,
            brightness,
            brightness
        )

        screen.set_at(
            (x, y),
            color
        )


# ============================================================
# GET PLANET POSITION
#
# Original C64:
#
#     X = 145 + dx(q) * SIN(cp(q))
#     Y = 147 + dy(q) * COS(cp(q))
#
# ============================================================

def get_planet_position(planet):

    angle = planet["angle"]

    x = (
        CENTER_X
        + planet["dx"]
        * ORBIT_SCALE_X
        * math.sin(angle)
    )

    y = (
        CENTER_Y
        + planet["dy"]
        * ORBIT_SCALE_Y
        * math.cos(angle)
    )

    return int(x), int(y)


# ============================================================
# DRAW ORBIT
# ============================================================

def draw_orbit(planet):

    rx = planet["dx"] * ORBIT_SCALE_X
    ry = planet["dy"] * ORBIT_SCALE_Y

    rect = pygame.Rect(
        int(CENTER_X - rx),
        int(CENTER_Y - ry),
        int(rx * 2),
        int(ry * 2)
    )

    pygame.draw.ellipse(
        screen,
        ORBIT_GREY,
        rect,
        1
    )


# ============================================================
# DRAW SUN
# ============================================================

def draw_sun():

    # --------------------------------------------------------
    # Sun glow
    # --------------------------------------------------------

    for radius in range(40, 15, -4):

        alpha = max(
            10,
            80 - radius
        )

        glow = pygame.Surface(
            (
                radius * 2,
                radius * 2
            ),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            glow,
            (
                255,
                200,
                20,
                alpha
            ),
            (
                radius,
                radius
            ),
            radius
        )

        screen.blit(
            glow,
            (
                CENTER_X - radius,
                CENTER_Y - radius
            )
        )

    # --------------------------------------------------------
    # Main Sun
    # --------------------------------------------------------

    pygame.draw.circle(
        screen,
        YELLOW,
        (
            CENTER_X,
            CENTER_Y
        ),
        16
    )

    # --------------------------------------------------------
    # Hot centre
    # --------------------------------------------------------

    pygame.draw.circle(
        screen,
        (255, 245, 150),
        (
            CENTER_X - 4,
            CENTER_Y - 4
        ),
        5
    )


# ============================================================
# DRAW SATURN RINGS
# ============================================================

def draw_saturn_rings(
    x,
    y,
    radius
):

    pygame.draw.ellipse(
        screen,
        (190, 175, 110),
        (
            x - radius - 8,
            y - radius // 2,
            (radius + 8) * 2,
            radius
        ),
        2
    )


# ============================================================
# DRAW PLANET
#
# If highlighted=True:
#
#     A GREEN BOUNDING BOX
#
# follows the planet around its orbit.
# ============================================================

def draw_planet(
    planet,
    highlighted=False
):

    x, y = get_planet_position(
        planet
    )

    radius = planet["radius"]


    # ========================================================
    # SATURN RINGS
    #
    # Draw behind Saturn itself.
    # ========================================================

    if planet["name"] == "Saturn":

        draw_saturn_rings(
            x,
            y,
            radius
        )


    # ========================================================
    # PLANET BODY
    # ========================================================

    pygame.draw.circle(
        screen,
        planet["color"],
        (
            x,
            y
        ),
        radius
    )


    # ========================================================
    # PLANET HIGHLIGHT
    # ========================================================

    if radius >= 6:

        pygame.draw.circle(
            screen,
            WHITE,
            (
                x - radius // 3,
                y - radius // 3
            ),
            max(
                1,
                radius // 4
            )
        )


    # ========================================================
    # GREEN BOUNDING BOX
    # ========================================================

    if highlighted:

        padding = 10

        box = pygame.Rect(
            x - radius - padding,
            y - radius - padding,
            (radius + padding) * 2,
            (radius + padding) * 2
        )


        # ----------------------------------------------------
        # Main green bounding box
        # ----------------------------------------------------

        pygame.draw.rect(
            screen,
            GREEN,
            box,
            2
        )


        # ----------------------------------------------------
        # Corner markers
        #
        # Makes the selection look more like an object
        # tracking / sprite selection box.
        # ----------------------------------------------------

        corner = 6


        # TOP LEFT

        pygame.draw.line(
            screen,
            GREEN,
            (
                box.left,
                box.top
            ),
            (
                box.left + corner,
                box.top
            ),
            2
        )

        pygame.draw.line(
            screen,
            GREEN,
            (
                box.left,
                box.top
            ),
            (
                box.left,
                box.top + corner
            ),
            2
        )


        # TOP RIGHT

        pygame.draw.line(
            screen,
            GREEN,
            (
                box.right,
                box.top
            ),
            (
                box.right - corner,
                box.top
            ),
            2
        )

        pygame.draw.line(
            screen,
            GREEN,
            (
                box.right,
                box.top
            ),
            (
                box.right,
                box.top + corner
            ),
            2
        )


        # BOTTOM LEFT

        pygame.draw.line(
            screen,
            GREEN,
            (
                box.left,
                box.bottom
            ),
            (
                box.left + corner,
                box.bottom
            ),
            2
        )

        pygame.draw.line(
            screen,
            GREEN,
            (
                box.left,
                box.bottom
            ),
            (
                box.left,
                box.bottom - corner
            ),
            2
        )


        # BOTTOM RIGHT

        pygame.draw.line(
            screen,
            GREEN,
            (
                box.right,
                box.bottom
            ),
            (
                box.right - corner,
                box.bottom
            ),
            2
        )

        pygame.draw.line(
            screen,
            GREEN,
            (
                box.right,
                box.bottom
            ),
            (
                box.right,
                box.bottom - corner
            ),
            2
        )


# ============================================================
# DRAW PLANET INFORMATION
# ============================================================

def draw_header():

    planet = planets[
        selected_planet
    ]

    text = (
        "PLANET: "
        + planet["name"].upper()
    )

    surface = font.render(
        text,
        True,
        YELLOW
    )

    rect = surface.get_rect(
        center=(
            WIDTH // 2,
            35
        )
    )

    screen.blit(
        surface,
        rect
    )


# ============================================================
# DRAW SELECTED PLANET LABEL
#
# The label follows the currently selected planet.
# ============================================================

def draw_selected_label():

    planet = planets[
        selected_planet
    ]

    x, y = get_planet_position(
        planet
    )

    text = planet["name"]

    surface = small_font.render(
        text,
        True,
        GREEN
    )

    rect = surface.get_rect(
        center=(
            x,
            y - planet["radius"] - 22
        )
    )

    screen.blit(
        surface,
        rect
    )


# ============================================================
# DRAW INSTRUCTIONS
# ============================================================

def draw_instructions():

    text = (
        "SPACE / ENTER / RIGHT = NEXT PLANET     "
        "ESC = QUIT"
    )

    surface = small_font.render(
        text,
        True,
        DIM_GREY
    )

    rect = surface.get_rect(
        center=(
            WIDTH // 2,
            HEIGHT - 25
        )
    )

    screen.blit(
        surface,
        rect
    )


# ============================================================
# MAIN LOOP
# ============================================================

running = True


while running:


    # ========================================================
    # EVENTS
    # ========================================================

    for event in pygame.event.get():


        # ----------------------------------------------------
        # Window close
        # ----------------------------------------------------

        if event.type == pygame.QUIT:

            running = False


        # ----------------------------------------------------
        # Keyboard
        # ----------------------------------------------------

        elif event.type == pygame.KEYDOWN:


            # ------------------------------------------------
            # NEXT PLANET
            # ------------------------------------------------

            if event.key in (
                pygame.K_SPACE,
                pygame.K_RETURN,
                pygame.K_RIGHT
            ):

                selected_planet += 1

                if selected_planet >= len(planets):

                    selected_planet = 0


            # ------------------------------------------------
            # QUIT
            # ------------------------------------------------

            elif event.key == pygame.K_ESCAPE:

                running = False


    # ========================================================
    # UPDATE PLANETS
    #
    # Original:
    #
    #     cp(q)=cp(q)+sp(q)
    #
    # ========================================================

    for planet in planets:

        planet["angle"] += planet["speed"]

        # Keep angle within 0 - 2PI

        if planet["angle"] > math.tau:

            planet["angle"] -= math.tau


    # ========================================================
    # DRAW FRAME
    # ========================================================

    screen.fill(BLACK)


    # --------------------------------------------------------
    # Stars
    # --------------------------------------------------------

    draw_stars()


    # --------------------------------------------------------
    # Orbital paths
    # --------------------------------------------------------

    for planet in planets:

        draw_orbit(
            planet
        )


    # --------------------------------------------------------
    # Sun
    # --------------------------------------------------------

    draw_sun()


    # --------------------------------------------------------
    # Planets
    #
    # The selected planet receives the green bounding box.
    # --------------------------------------------------------

    for index, planet in enumerate(planets):

        draw_planet(
            planet,
            highlighted=(
                index == selected_planet
            )
        )


    # --------------------------------------------------------
    # Top planet name
    # --------------------------------------------------------

    draw_header()


    # --------------------------------------------------------
    # Label next to selected planet
    # --------------------------------------------------------

    draw_selected_label()


    # --------------------------------------------------------
    # Instructions
    # --------------------------------------------------------

    draw_instructions()


    # ========================================================
    # UPDATE DISPLAY
    # ========================================================

    pygame.display.flip()


    # ========================================================
    # 60 FPS
    # ========================================================

    clock.tick(60)


# ============================================================
# SHUTDOWN
# ============================================================

pygame.quit()

sys.exit()