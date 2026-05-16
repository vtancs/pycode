import math
import pygame

# ------------------------------------------------------------
# Fractal tree with organic branch thickness using circles
# ------------------------------------------------------------

pygame.init()

# Screen setup
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fractal Tree with Organic CIRCLE Thickness")

clock = pygame.time.Clock()

# Background color
BG_COLOR = (0, 0, 0)

# ------------------------------------------------------------
# Stack arrays
# ------------------------------------------------------------
stack_x = []
stack_y = []
stack_a = []
stack_l = []
stack_state = []

# ------------------------------------------------------------
# Initial parameters
# ------------------------------------------------------------
current_x = WIDTH // 2
current_y = HEIGHT
current_a = 90          # angle
current_l = 100         # branch length

# Push initial dummy root
stack_x.append(current_x)
stack_y.append(current_y)
stack_a.append(current_a)
stack_l.append(current_l)
stack_state.append(0)

stack_pointer = 1

running = True
tree_finished = False

screen.fill(BG_COLOR)

font = pygame.font.SysFont(None, 24)
text = font.render(
    "Fractal tree with organic CIRCLE",
    True,
    (210, 210, 250),
)
screen.blit(text, (10, 10))

# ------------------------------------------------------------
# Main fractal generation loop
# ------------------------------------------------------------
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not tree_finished:

        # ----------------------------------------------------
        # Branch too small -> backtrack
        # ----------------------------------------------------
        if current_l < 4:

            while True:

                # Entire tree finished
                if stack_pointer == 1:
                    tree_finished = True
                    break

                branch_state = stack_state[stack_pointer - 1]

                # Draw right branch
                if branch_state == 1:

                    stack_state[stack_pointer - 1] = 2

                    current_x = stack_x[stack_pointer - 1]
                    current_y = stack_y[stack_pointer - 1]
                    current_a = stack_a[stack_pointer - 1] - 25
                    current_l = stack_l[stack_pointer - 1] * 0.75

                    break

                # Both branches done -> pop stack
                elif branch_state == 2:
                    stack_x.pop()
                    stack_y.pop()
                    stack_a.pop()
                    stack_l.pop()
                    stack_state.pop()

                    stack_pointer -= 1

        else:

            # ------------------------------------------------
            # Dynamic branch color
            # ------------------------------------------------
            red = max(30, 120 - (stack_pointer * 8))
            green = min(230, 40 + (stack_pointer * 15))
            blue = 20

            color = (red, green, blue)

            # ------------------------------------------------
            # Angle to radians
            # ------------------------------------------------
            radian = math.radians(current_a)

            # End point
            x1 = current_x + current_l * math.cos(radian)
            y1 = current_y - current_l * math.sin(radian)

            # ------------------------------------------------
            # Organic thickness using circles
            # ------------------------------------------------
            step_radius = max(1, 14 - stack_pointer)

            steps = 20

            for n in range(steps):

                step_x = current_x + (x1 - current_x) * n / steps
                step_y = current_y + (y1 - current_y) * n / steps

                pygame.draw.circle(
                    screen,
                    color,
                    (int(step_x), int(step_y)),
                    int(step_radius),
                )

            # ------------------------------------------------
            # Push current state before left branch
            # ------------------------------------------------
            stack_x.append(x1)
            stack_y.append(y1)
            stack_a.append(current_a)
            stack_l.append(current_l)
            stack_state.append(1)

            stack_pointer += 1

            # ------------------------------------------------
            # Left branch
            # ------------------------------------------------
            current_x = x1
            current_y = y1
            current_a = current_a + 25
            current_l = current_l * 0.75

    pygame.display.flip()
    clock.tick(120)

pygame.quit()