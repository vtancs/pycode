import pygame
import math
import sys


# ============================================================
# RECAMAN'S SEQUENCE
# Diagonal View
#
# Original program:
# K. Moerman - Apple II BASIC
#
# Python / Pygame conversion
# ============================================================


# ------------------------------------------------------------
# PYGAME INITIALIZATION
# ------------------------------------------------------------

pygame.init()

BASE_WIDTH = 256
BASE_HEIGHT = 192

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

screen = pygame.display.set_mode(
    (WINDOW_WIDTH, WINDOW_HEIGHT),
    pygame.RESIZABLE
)

pygame.display.set_caption("Recamán's Sequence - Diagonal View")

clock = pygame.time.Clock()


# ------------------------------------------------------------
# COLORS
# ------------------------------------------------------------

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Main drawing color
ARC_COLOR = (255, 255, 255)

# Optional slightly dimmer axis
AXIS_COLOR = (150, 150, 150)

# Text
TEXT_COLOR = (220, 220, 220)


# ------------------------------------------------------------
# ORIGINAL SCREEN PARAMETERS
# ------------------------------------------------------------

XZ = BASE_WIDTH
YZ = BASE_HEIGHT

XA = 0
YA = 0
XB = XZ - 1
YB = YZ - 1

# Original:
# SC = 2
#
# pixels per Recaman unit
SC = 2.0

D = math.sqrt(XZ * XZ + YZ * YZ)

IS = int((D - 1) / SC)

AA = math.atan(YZ / XZ)

CA = math.cos(AA)
SA = math.sin(AA)

SX = SC * CA
SY = SC * SA


# ------------------------------------------------------------
# RECAMAN PARAMETERS
# ------------------------------------------------------------

MP = 1000

visited = [False] * (MP + 1)

P = 0
visited[P] = True

S = 0

# Original:
# AP = FALSE
#
# Alternates every step.
AP = False


# ------------------------------------------------------------
# DRAWING / ANIMATION PARAMETERS
# ------------------------------------------------------------

# Number of Recaman steps calculated per second.
steps_per_second = 10.0

paused = False

fullscreen = False

# How much the original 256x192 coordinate system is
# magnified on the display.
visual_scale = 3.0


# ------------------------------------------------------------
# STORE COMPLETED ARCS
# ------------------------------------------------------------

arcs = []


# Each arc contains:
#
#     center_x
#     center_y
#     radius
#     start_angle
#     end_angle
#     direction
#
# Angles are stored exactly in the coordinate convention
# used by the original BASIC program:
#
#     x = cx + cos(a) * r
#     y = cy - sin(a) * r
#
# Pygame itself uses a different Y direction, so we convert
# when generating points.


# ------------------------------------------------------------
# COORDINATE CONVERSION
# ------------------------------------------------------------

def screen_coordinates(x, y):
    """
    Convert original 256x192 BASIC coordinates into
    the current Pygame window.
    """

    global visual_scale

    # Center the original coordinate system in the window.
    w, h = screen.get_size()

    scaled_w = BASE_WIDTH * visual_scale
    scaled_h = BASE_HEIGHT * visual_scale

    offset_x = (w - scaled_w) / 2
    offset_y = (h - scaled_h) / 2

    px = offset_x + x * visual_scale
    py = offset_y + y * visual_scale

    return int(px), int(py)


# ------------------------------------------------------------
# BASIC FN AC
# ------------------------------------------------------------

def acos_original(x):
    """
    Equivalent to:

        FN AC(X) = HP - ATN(X / SQR(1-X*X))

    which evaluates arccos(X).

    Python has math.acos(), so use that directly.
    """

    # Floating point rounding can occasionally result
    # in values such as 1.00000000001.
    x = max(-1.0, min(1.0, x))

    return math.acos(x)


# ------------------------------------------------------------
# CREATE AN ARC
# ------------------------------------------------------------

def calculate_arc(p, np, ap):
    """
    Equivalent to BASIC routines 300-1050.

    Calculates the center, radius and angular range of
    the arc connecting Recaman positions P and NP.

    The original program contains complicated clipping
    calculations because Apple II BASIC was plotting pixels
    individually.

    Pygame automatically clips lines to the display, so we
    can generate the complete semicircle and let Pygame's
    drawing system handle the borders.
    """

    # --------------------------------------------------------
    # 400 - CALCULATE ARC PARAMETERS
    # --------------------------------------------------------

    cp = (p + np) / 2.0

    cx = XA + cp * SX
    cy = YB - cp * SY

    r = abs(p - np) / 2.0 * SC

    if r <= 0:
        return None

    # --------------------------------------------------------
    # 500 - DIRECTION AND PHASE
    # --------------------------------------------------------

    if np > p:
        # ----------------------------------------------------
        # STEP FORWARD
        # ----------------------------------------------------

        if ap:
            # ------------------------------------------------
            # STEP FORWARD, ARC ABOVE AXIS
            #
            # BASIC:
            #
            # A0 = AA + PI
            # A1 = AA + 0
            # SI = -1
            # ------------------------------------------------

            start_angle = AA + math.pi
            end_angle = AA

            direction = -1

        else:
            # ------------------------------------------------
            # STEP FORWARD, ARC BELOW AXIS
            #
            # BASIC:
            #
            # A0 = AA - PI
            # A1 = AA - 0
            # SI = +1
            # ------------------------------------------------

            start_angle = AA - math.pi
            end_angle = AA

            direction = +1

    else:
        # ----------------------------------------------------
        # STEP BACKWARD
        # ----------------------------------------------------

        if ap:
            # ------------------------------------------------
            # STEP BACKWARDS, ARC ABOVE AXIS
            #
            # BASIC:
            #
            # A0 = AA + 0
            # A1 = AA + PI
            # SI = +1
            # ------------------------------------------------

            start_angle = AA
            end_angle = AA + math.pi

            direction = +1

        else:
            # ------------------------------------------------
            # STEP BACKWARDS, ARC BELOW AXIS
            #
            # BASIC:
            #
            # A0 = AA - 0
            # A1 = AA - PI
            # SI = -1
            # ------------------------------------------------

            start_angle = AA
            end_angle = AA - math.pi

            direction = -1

    return {
        "cx": cx,
        "cy": cy,
        "r": r,
        "start": start_angle,
        "end": end_angle,
        "direction": direction,
        "p": p,
        "np": np,
    }


# ------------------------------------------------------------
# GENERATE ARC POINTS
# ------------------------------------------------------------

def generate_arc_points(arc):
    """
    Generate points along an arc.

    The original BASIC program used:

        AI = PI / 4 / R

    We preserve that idea, but limit the number of points
    to prevent extremely large arcs from becoming expensive.
    """

    cx = arc["cx"]
    cy = arc["cy"]
    r = arc["r"]

    start = arc["start"]
    end = arc["end"]
    direction = arc["direction"]

    # Original angular increment:
    #
    # AI = PI / 4 / R
    #
    # For small radii this can become quite large.
    if r > 1:
        angular_increment = math.pi / (4.0 * r)
    else:
        angular_increment = math.pi / 32.0

    # Make sure the increment doesn't become excessively tiny.
    angular_increment = max(angular_increment, math.pi / 1000.0)

    total_angle = abs(end - start)

    count = max(
        2,
        int(total_angle / angular_increment) + 1
    )

    # Avoid excessive point counts.
    count = min(count, 1200)

    points = []

    for i in range(count):
        t = i / (count - 1)

        a = start + (end - start) * t

        # Original BASIC:
        #
        # X = INT(CX + COS(A) * R)
        # Y = INT(CY - SIN(A) * R)
        #
        x = int(cx + math.cos(a) * r)
        y = int(cy - math.sin(a) * r)

        points.append(
            screen_coordinates(x, y)
        )

    return points


# ------------------------------------------------------------
# ADD ONE RECAMAN STEP
# ------------------------------------------------------------

def next_step():
    """
    Equivalent to BASIC:

        100 NEXT STEP
        200 WILL STEP BACKWARDS...
        300 DRAW ARC
        1100 MOVE TO NEW POSITION
    """

    global P
    global S
    global AP

    # --------------------------------------------------------
    # 110 - STEP SIZE
    # --------------------------------------------------------

    S += 1

    # --------------------------------------------------------
    # 120 - ALTERNATE ARC PHASE
    # --------------------------------------------------------

    AP = not AP

    # --------------------------------------------------------
    # 210 - TRY BACKWARDS FIRST
    # --------------------------------------------------------

    NP = P - S

    if NP >= 0 and not visited[NP]:
        pass

    else:
        # ----------------------------------------------------
        # 230 - BACKWARDS FAILED, GO FORWARD
        # ----------------------------------------------------

        NP = P + S

    # --------------------------------------------------------
    # 40 - STOP IF MAXIMUM POSITION EXCEEDED
    # --------------------------------------------------------

    if NP > MP:
        return False

    # --------------------------------------------------------
    # 50 - DRAW ARC
    # --------------------------------------------------------

    arc = calculate_arc(P, NP, AP)

    if arc is not None:
        points = generate_arc_points(arc)

        arcs.append({
            "points": points,
            "p": P,
            "np": NP,
            "ap": AP,
        })

    # --------------------------------------------------------
    # 1100 - MOVE TO NEW POSITION
    # --------------------------------------------------------

    P = NP

    visited[P] = True

    return True


# ------------------------------------------------------------
# RESET
# ------------------------------------------------------------

def reset():
    """
    Reset the Recaman sequence.
    """

    global visited
    global P
    global S
    global AP
    global arcs

    visited = [False] * (MP + 1)

    P = 0
    visited[P] = True

    S = 0

    AP = False

    arcs.clear()


# ------------------------------------------------------------
# DRAW AXIS
# ------------------------------------------------------------

def draw_axis(surface):
    """
    Original BASIC:

        PLOT XA,YB TO XB,YA

    Draw the diagonal axis from bottom-left
    to top-right.
    """

    x1, y1 = screen_coordinates(XA, YB)
    x2, y2 = screen_coordinates(XB, YA)

    pygame.draw.line(
        surface,
        AXIS_COLOR,
        (x1, y1),
        (x2, y2),
        max(1, int(visual_scale))
    )


# ------------------------------------------------------------
# DRAW ALL ARCS
# ------------------------------------------------------------

def draw_arcs(surface):
    """
    Draw every completed Recaman arc.
    """

    width = max(1, int(visual_scale * 0.8))

    for arc in arcs:

        points = arc["points"]

        if len(points) >= 2:

            pygame.draw.lines(
                surface,
                ARC_COLOR,
                False,
                points,
                width
            )


# ------------------------------------------------------------
# DRAW INFORMATION
# ------------------------------------------------------------

font = pygame.font.SysFont(
    "Consolas",
    18
)

small_font = pygame.font.SysFont(
    "Consolas",
    15
)


def draw_text(surface):
    """
    Display useful runtime information.
    """

    if paused:
        status = "PAUSED"
    else:
        status = "RUNNING"

    text1 = (
        f"Recaman  P={P}  Step={S}  "
        f"Arcs={len(arcs)}  Speed={steps_per_second:.1f}/s"
    )

    text2 = (
        "UP/DOWN speed   SPACE pause   R reset   "
        "F fullscreen   +/- scale   ESC quit"
    )

    img1 = font.render(
        text1,
        True,
        TEXT_COLOR
    )

    img2 = small_font.render(
        text2,
        True,
        TEXT_COLOR
    )

    # Background panel
    panel_width = max(
        img1.get_width(),
        img2.get_width()
    ) + 20

    panel_height = 65

    pygame.draw.rect(
        surface,
        BLACK,
        (10, 10, panel_width, panel_height)
    )

    surface.blit(
        img1,
        (20, 18)
    )

    surface.blit(
        img2,
        (20, 43)
    )

    if paused:

        pause_img = font.render(
            "PAUSED",
            True,
            TEXT_COLOR
        )

        rect = pause_img.get_rect(
            center=(
                surface.get_width() // 2,
                surface.get_height() // 2
            )
        )

        surface.blit(
            pause_img,
            rect
        )


# ------------------------------------------------------------
# FULLSCREEN
# ------------------------------------------------------------

def toggle_fullscreen():
    global fullscreen
    global screen

    fullscreen = not fullscreen

    if fullscreen:

        screen = pygame.display.set_mode(
            (0, 0),
            pygame.FULLSCREEN
        )

    else:

        screen = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            pygame.RESIZABLE
        )


# ------------------------------------------------------------
# MAIN PROGRAM
# ------------------------------------------------------------

def main():

    global paused
    global steps_per_second
    global visual_scale

    running = True

    # Time accumulator for smooth speed control.
    accumulator = 0.0

    while running:

        # ----------------------------------------------------
        # TIME
        # ----------------------------------------------------

        dt = clock.tick(60) / 1000.0

        # ----------------------------------------------------
        # EVENTS
        # ----------------------------------------------------

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                # --------------------------------------------
                # ESC
                # --------------------------------------------

                if event.key == pygame.K_ESCAPE:
                    running = False

                # --------------------------------------------
                # SPACE
                # --------------------------------------------

                elif event.key == pygame.K_SPACE:
                    paused = not paused

                # --------------------------------------------
                # R
                # --------------------------------------------

                elif event.key == pygame.K_r:
                    reset()

                # --------------------------------------------
                # F
                # --------------------------------------------

                elif event.key == pygame.K_f:
                    toggle_fullscreen()

                # --------------------------------------------
                # UP
                # --------------------------------------------

                elif event.key == pygame.K_UP:

                    steps_per_second *= 1.5

                    if steps_per_second > 1000:
                        steps_per_second = 1000

                # --------------------------------------------
                # DOWN
                # --------------------------------------------

                elif event.key == pygame.K_DOWN:

                    steps_per_second /= 1.5

                    if steps_per_second < 0.1:
                        steps_per_second = 0.1

                # --------------------------------------------
                # PLUS
                # --------------------------------------------

                elif event.key in (
                    pygame.K_PLUS,
                    pygame.K_EQUALS
                ):

                    visual_scale += 0.5

                    if visual_scale > 8:
                        visual_scale = 8

                    # Existing points need to be regenerated
                    # because the display scale changed.
                    rebuild_arcs()

                # --------------------------------------------
                # MINUS
                # --------------------------------------------

                elif event.key == pygame.K_MINUS:

                    visual_scale -= 0.5

                    if visual_scale < 1:
                        visual_scale = 1

                    rebuild_arcs()

        # ----------------------------------------------------
        # ANIMATION
        # ----------------------------------------------------

        if not paused:

            accumulator += dt

            step_interval = 1.0 / steps_per_second

            while accumulator >= step_interval:

                if not next_step():

                    paused = True
                    break

                accumulator -= step_interval

        # ----------------------------------------------------
        # CLEAR SCREEN
        # ----------------------------------------------------

        screen.fill(BLACK)

        # ----------------------------------------------------
        # DRAW DIAGONAL
        # ----------------------------------------------------

        draw_axis(screen)

        # ----------------------------------------------------
        # DRAW RECMAN ARCS
        # ----------------------------------------------------

        draw_arcs(screen)

        # ----------------------------------------------------
        # INFO
        # ----------------------------------------------------

        draw_text(screen)

        # ----------------------------------------------------
        # UPDATE
        # ----------------------------------------------------

        pygame.display.flip()

    pygame.quit()

    sys.exit()


# ------------------------------------------------------------
# REBUILD ARCS
# ------------------------------------------------------------

def rebuild_arcs():
    """
    Recalculate the screen coordinates of all existing arcs.

    This is needed if the visual scale changes.
    """

    for arc in arcs:

        # The original P and NP values are retained.
        original_p = arc["p"]
        original_np = arc["np"]
        original_ap = arc["ap"]

        new_arc = calculate_arc(
            original_p,
            original_np,
            original_ap
        )

        if new_arc is not None:

            arc["points"] = generate_arc_points(
                new_arc
            )


# ------------------------------------------------------------
# START
# ------------------------------------------------------------

if __name__ == "__main__":
    main()