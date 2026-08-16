import pygame
import math
import sys

# ============================================================
# Circle Inversion / Recursive Circle Pattern
# Python + Pygame conversion of the original QBASIC program
# ============================================================

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

WIDTH = 800
HEIGHT = 800

MAX_DEPTH = 6
DELTA = 0.00001

BORDER_WIDTH = 2

# Original QBASIC colours converted from the CMYK palette
# Colours:
# 0 = dark red
# 1 = light cream
# 2 = light brown
# 3 = dark brown
# 4 = brown-green
# 5 = cream
#
# Actual RGB values are calculated from the original CMYK.
# ------------------------------------------------------------


def cmyk_to_rgb(c, m, y, k):
    """
    Convert CMYK values (0..1) to RGB (0..255).

    Original QBASIC:
        r = (1-c) * (1-k)
        g = (1-m) * (1-k)
        b = (1-y) * (1-k)
    """

    r = (1.0 - c) * (1.0 - k)
    g = (1.0 - m) * (1.0 - k)
    b = (1.0 - y) * (1.0 - k)

    return (
        max(0, min(255, int(r * 255))),
        max(0, min(255, int(g * 255))),
        max(0, min(255, int(b * 255)))
    )


# ------------------------------------------------------------
# Original palette
# ------------------------------------------------------------

PALETTE = [
    cmyk_to_rgb(0.50, 1.00, 0.99, 0.0),   # 0 dark red
    cmyk_to_rgb(0.09, 0.26, 0.49, 0.0),   # 1 cream
    cmyk_to_rgb(0.00, 0.18, 0.44, 0.0),   # 2 light cream
    cmyk_to_rgb(0.24, 0.69, 0.86, 0.0),   # 3 light brown
    cmyk_to_rgb(0.75, 0.92, 0.99, 0.0),   # 4 dark brown
    cmyk_to_rgb(0.78, 0.88, 0.97, 0.0),   # 5 brown-green
]

# Mapping from the original BASIC Colours array
# Colours(0)=6 -> dark red
# Colours(1)=2 -> light cream
# Colours(2)=3 -> light brown
# Colours(3)=4 -> dark brown
# Colours(4)=5 -> brown-green
# Colours(5)=1 -> cream
#
# Python indexes directly into our RGB palette.

COLOURS = [
    PALETTE[0],
    PALETTE[2],
    PALETTE[3],
    PALETTE[4],
    PALETTE[5],
    PALETTE[1],
]

BORDER_COLOUR = (255, 255, 255)
BACKGROUND = (0, 0, 0)


# ------------------------------------------------------------
# Coordinate conversion
# ------------------------------------------------------------

# Original QBASIC coordinate system:
#
# VIEW (80,0)-(559,479)
# WINDOW (0,0)-(500,500)
#
# Therefore 500 x 500 drawing area.
#
# We scale it to fit our Pygame window.

DRAW_SIZE = min(WIDTH, HEIGHT) - 40
SCALE = DRAW_SIZE / 500.0

OFFSET_X = (WIDTH - DRAW_SIZE) / 2
OFFSET_Y = (HEIGHT - DRAW_SIZE) / 2


def screen_x(x):
    return int(OFFSET_X + x * SCALE)


def screen_y(y):
    return int(OFFSET_Y + y * SCALE)


def screen_radius(r):
    return max(1, int(r * SCALE))


# ------------------------------------------------------------
# Draw filled circle
# ------------------------------------------------------------

def fill_circle(surface, x, y, r, outline_width, colour_index):
    """
    Equivalent of the QBASIC FillCircle routine.
    """

    colour = COLOURS[colour_index % len(COLOURS)]

    px = screen_x(x)
    py = screen_y(y)
    pr = screen_radius(r)

    # Original program adds a larger black/white border
    # when outlinewidth > 1.

    if outline_width > 1:
        outer_r = screen_radius(r + outline_width)

        pygame.draw.circle(
            surface,
            BORDER_COLOUR,
            (px, py),
            outer_r
        )

        pygame.draw.circle(
            surface,
            BACKGROUND,
            (px, py),
            max(1, outer_r - BORDER_WIDTH)
        )

    # Main filled circle
    pygame.draw.circle(
        surface,
        colour,
        (px, py),
        pr
    )

    # Border
    if outline_width > 0:
        pygame.draw.circle(
            surface,
            BORDER_COLOUR,
            (px, py),
            pr,
            max(1, int(outline_width * SCALE))
        )


# ------------------------------------------------------------
# Invert a point through a circle
# ------------------------------------------------------------

def invert_point(xc, yc, rc, xp, yp):
    """
    Invert point (xp,yp) through circle
    centred at (xc,yc) with radius rc.
    """

    xp -= xc
    yp -= yc

    d = xp * xp + yp * yp

    if d < DELTA:
        d = 1.0

    ir = (rc * rc) / d

    xp = xc + xp * ir
    yp = yc + yp * ir

    return xp, yp


# ------------------------------------------------------------
# Invert a circle through another circle
# ------------------------------------------------------------

def invert_circle(x, y, r, xx, yy, rr):
    """
    Invert circle (xx,yy,rr) in circle (x,y,r).

    Returns:
        xi, yi, ri
    """

    d = math.sqrt(
        (xx - x) ** 2 +
        (yy - y) ** 2
    )

    if d < DELTA:
        d = 1.0

    ir = rr / d

    ix = (xx - x) * ir
    iy = (yy - y) * ir

    xa = xx + ix
    xb = xx - ix

    ya = yy + iy
    yb = yy - iy

    xa, ya = invert_point(
        x, y, r,
        xa, ya
    )

    xb, yb = invert_point(
        x, y, r,
        xb, yb
    )

    xi = (xa + xb) * 0.5
    yi = (ya + yb) * 0.5

    ri = math.sqrt(
        (xa - xb) ** 2 +
        (ya - yb) ** 2
    ) * 0.5

    return xi, yi, ri


# ------------------------------------------------------------
# Recursive inversion of three circles
# ------------------------------------------------------------

def invert_three_circles(
        surface,
        x0, y0, r0,
        x1, y1, r1,
        x2, y2, r2,
        x3, y3, r3,
        depth):
    """
    Recursively inverts each of the three inner circles
    and the outer circle.

    This is the direct Python equivalent of the QBASIC
    InvertThreeCircles routine.
    """

    # --------------------------------------------------------
    # Circle 1
    # --------------------------------------------------------

    x10, y10, r10 = invert_circle(
        x1, y1, r1,
        x0, y0, r0
    )

    fill_circle(
        surface,
        x10, y10, r10,
        0.5,
        depth
    )

    x12, y12, r12 = invert_circle(
        x1, y1, r1,
        x2, y2, r2
    )

    fill_circle(
        surface,
        x12, y12, r12,
        0.5,
        depth
    )

    x13, y13, r13 = invert_circle(
        x1, y1, r1,
        x3, y3, r3
    )

    fill_circle(
        surface,
        x13, y13, r13,
        0.5,
        depth
    )

    # --------------------------------------------------------
    # Circle 2
    # --------------------------------------------------------

    x20, y20, r20 = invert_circle(
        x2, y2, r2,
        x0, y0, r0
    )

    fill_circle(
        surface,
        x20, y20, r20,
        0.5,
        depth
    )

    x21, y21, r21 = invert_circle(
        x2, y2, r2,
        x1, y1, r1
    )

    fill_circle(
        surface,
        x21, y21, r21,
        0.5,
        depth
    )

    x23, y23, r23 = invert_circle(
        x2, y2, r2,
        x3, y3, r3
    )

    fill_circle(
        surface,
        x23, y23, r23,
        0.5,
        depth
    )

    # --------------------------------------------------------
    # Circle 3
    # --------------------------------------------------------

    x30, y30, r30 = invert_circle(
        x3, y3, r3,
        x0, y0, r0
    )

    fill_circle(
        surface,
        x30, y30, r30,
        0.5,
        depth
    )

    x31, y31, r31 = invert_circle(
        x3, y3, r3,
        x1, y1, r1
    )

    fill_circle(
        surface,
        x31, y31, r31,
        0.5,
        depth
    )

    x32, y32, r32 = invert_circle(
        x3, y3, r3,
        x2, y2, r2
    )

    fill_circle(
        surface,
        x32, y32, r32,
        0.5,
        depth
    )

    # --------------------------------------------------------
    # Recursive stage
    # --------------------------------------------------------

    if depth < MAX_DEPTH:

        next_depth = depth + 1

        invert_three_circles(
            surface,
            x1, y1, r1,
            x10, y10, r10,
            x12, y12, r12,
            x13, y13, r13,
            next_depth
        )

        invert_three_circles(
            surface,
            x2, y2, r2,
            x20, y20, r20,
            x21, y21, r21,
            x23, y23, r23,
            next_depth
        )

        invert_three_circles(
            surface,
            x3, y3, r3,
            x30, y30, r30,
            x31, y31, r31,
            x32, y32, r32,
            next_depth
        )


# ------------------------------------------------------------
# Draw complete figure
# ------------------------------------------------------------

def draw_figure(surface):

    surface.fill(BACKGROUND)

    # --------------------------------------------------------
    # Original geometry
    # --------------------------------------------------------

    # Outer circle
    x0 = 250
    y0 = 250
    r0 = 200

    # Inner circles
    x1 = 300
    y1 = 190
    r1 = 121.898

    x2 = 219.85
    y2 = 370.6
    r2 = 75.6884

    x3 = 121.358
    y3 = 262.1941
    r3 = 70.7811

    # --------------------------------------------------------
    # Initial circles
    # --------------------------------------------------------

    fill_circle(
        surface,
        x0, y0, r0,
        2,
        0
    )

    fill_circle(
        surface,
        x1, y1, r1,
        1.5,
        1
    )

    fill_circle(
        surface,
        x2, y2, r2,
        1.5,
        1
    )

    fill_circle(
        surface,
        x3, y3, r3,
        1.5,
        1
    )

    # --------------------------------------------------------
    # Recursive inversion
    # --------------------------------------------------------

    invert_three_circles(
        surface,
        x0, y0, r0,
        x1, y1, r1,
        x2, y2, r2,
        x3, y3, r3,
        2
    )


# ------------------------------------------------------------
# Main program
# ------------------------------------------------------------

def main():

    pygame.init()

    pygame.display.set_caption(
        "Circle Inversion - Recursive Apollonian Pattern"
    )

    screen = pygame.display.set_mode(
        (WIDTH, HEIGHT)
    )

    # Render the figure
    draw_figure(screen)

    pygame.display.flip()

    # --------------------------------------------------------
    # Event loop
    # --------------------------------------------------------

    running = True

    while running:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    # Redraw
                    draw_figure(screen)
                    pygame.display.flip()

    pygame.quit()
    sys.exit()


# ------------------------------------------------------------
# Start
# ------------------------------------------------------------

if __name__ == "__main__":
    main()