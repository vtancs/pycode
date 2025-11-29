import pygame
import sys
import random
import math

pygame.init()

# ===== Window =====
W, H = 900, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Magic Number Game - Wooden Bucket Edition")

clock = pygame.time.Clock()
FPS = 60

# ===== Fonts =====
big_font = pygame.font.SysFont(None, 120)
mid_font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 28)

# ===== Colors =====
WHITE = (255, 255, 255)
GRAY = (180, 180, 180)
BLACK = (0, 0, 0)
GLOW_BLUE = (0, 120, 255)
BLUE = (40, 120, 255)
LIGHT_BLUE = (120, 170, 255)
GREEN = (60, 200, 90)
ORANGE = (255, 120, 50)
RED = (220, 50, 50)

# ===== Sound =====
try:
    splash_sound = pygame.mixer.Sound("splash.wav")
except:
    splash_sound = None

# ===== Game Variables =====
def new_game():
    return random.randint(1, 99), 1, 99, [], "", "Enter a number & press ENTER", 1, False

secret, low, high, guesses, input_text, message, current_player, show_winner = new_game()

# ===== Bucket Animation Vars =====
bucket_angle = 0
bucket_sway = 0
bucket_tipping = False
sway_dir = 1

water_particles = []
splash_particles = []

winner_player = None
winner_timer = 0

# ===== Drawing Glowing Border =====
def draw_glow_border():
    for i in range(10):
        alpha = max(0, 255 - i * 25)
        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.rect(glow, (0, 120, 255, alpha), (0+i, 0+i, W-i*2, H-i*2), border_radius=20)
        screen.blit(glow, (0, 0))

# ===== Wooden Bucket =====
def draw_bucket():
    global bucket_sway

    # Sway effect
    bucket_sway += 0.03 * sway_dir
    angle = bucket_angle + math.sin(bucket_sway) * 4

    # Bucket surface
    w, h = 160, 120
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # Wooden planks
    plank_color = (150, 90, 40)
    ring_color = (80, 80, 80)

    pygame.draw.rect(surf, plank_color, (0, 20, w, h-40), border_radius=20)
    pygame.draw.rect(surf, (170, 110, 60), (0, 20, w, h-40), 6, border_radius=20)

    # Top & bottom metal rings
    pygame.draw.rect(surf, ring_color, (0, 30, w, 12), border_radius=20)
    pygame.draw.rect(surf, ring_color, (0, h-40, w, 12), border_radius=20)

    # Rotate
    rotated = pygame.transform.rotate(surf, angle)
    rect = rotated.get_rect(center=(W//2, 140))

    # Rope
    pygame.draw.line(screen, GRAY, (W//2, 0), (rect.centerx, rect.top), 6)

    screen.blit(rotated, rect)
    return rect.centerx, rect.bottom

# ===== Water =====
def spawn_water():
    for _ in range(5):
        water_particles.append([
            W//2 + random.randint(-15, 15),  # x
            150,                             # y
            random.uniform(4, 7)             # speed
        ])

def update_water():
    global splash_particles
    for p in water_particles:
        p[1] += p[2]
        if p[1] >= H - 20:
            if splash_sound: splash_sound.play()
            splash_particles.append([p[0], H-20, random.uniform(-3, 3), random.uniform(-3, -1)])
    water_particles[:] = [p for p in water_particles if p[1] < H - 20]

def update_splash():
    for s in splash_particles:
        s[0] += s[2]
        s[1] += s[3]
        s[3] += 0.2
    splash_particles[:] = [s for s in splash_particles if s[1] < H]

def draw_water():
    for p in water_particles:
        pygame.draw.circle(screen, LIGHT_BLUE, (int(p[0]), int(p[1])), 5)

    for s in splash_particles:
        pygame.draw.circle(screen, BLUE, (int(s[0]), int(s[1])), 4)

# ===== Winner Screen =====
def draw_winner_screen():
    title = big_font.render(f"Player {winner_player} Wins!", True, WHITE)
    prompt = mid_font.render("Press R to play again", True, GRAY)
    screen.blit(title, title.get_rect(center=(W//2, H//2 - 80)))
    screen.blit(prompt, prompt.get_rect(center=(W//2, H//2 + 20)))

# ===== Main Draw =====
def draw():
    screen.fill(BLACK)
    draw_glow_border()

    if show_winner:
        draw_winner_screen()
        pygame.display.flip()
        return

    # Top text
    turn_text = mid_font.render(f"Player {current_player}'s turn", True, WHITE)
    screen.blit(turn_text, (20, 20))

    # Range
    span = high - low
    color = GREEN if span <= 5 else (ORANGE if span <= 20 else BLUE)
    range_text = big_font.render(f"{low} ➜ {high}", True, color)
    screen.blit(range_text, range_text.get_rect(center=(W//2, H//2)))

    # Input
    input_box = mid_font.render("Guess: " + (input_text or "_"), True, WHITE)
    screen.blit(input_box, (20, H - 120))

    msg = mid_font.render(message, True, WHITE)
    screen.blit(msg, (20, H - 70))

    # Bucket
    bx, by = draw_bucket()

    # Water
    draw_water()

    # History
    screen.blit(mid_font.render("Guesses", True, WHITE), (W-250, 40))
    y = 90
    for g in guesses[-10:]:
        c = GREEN if g[1]=="correct" else (BLUE if g[1]=="low" else RED)
        t = small_font.render(f"P{g[2]}: {g[0]} → {g[1]}", True, c)
        screen.blit(t, (W-250, y))
        y += 28

    pygame.display.flip()


# ===== Game Loop =====
running = True
while running:
    clock.tick(FPS)

    # Animate bucket tipping + water
    if bucket_tipping:
        if bucket_angle > -70:
            bucket_angle -= 2.3
            spawn_water()
        update_water()
        update_splash()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if show_winner:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                secret, low, high, guesses, input_text, message, current_player, show_winner = new_game()
                bucket_angle = 0
                water_particles.clear()
                splash_particles.clear()
            continue

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]

            elif event.key == pygame.K_r:
                secret, low, high, guesses, input_text, message, current_player, show_winner = new_game()
                bucket_angle = 0

            elif event.key == pygame.K_RETURN:
                if input_text == "":
                    message = "Enter a number!"
                else:
                    try:
                        g = int(input_text)
                        if g == secret:
                            guesses.append((g, "correct", current_player))
                            bucket_tipping = True
                            winner_player = current_player
                            message = f"Player {current_player} wins!"
                            pygame.time.set_timer(pygame.USEREVENT + 1, 1800)
                        elif g < secret:
                            low = max(low, g)
                            guesses.append((g, "low", current_player))
                            current_player = (current_player % 3) + 1
                            message = "Too low!"
                        else:
                            high = min(high, g)
                            guesses.append((g, "high", current_player))
                            current_player = (current_player % 3) + 1
                            message = "Too high!"
                    except:
                        message = "Invalid number."
                input_text = ""

            else:
                if event.unicode.isdigit() and len(input_text) < 2:
                    input_text += event.unicode

        # Timer for winner screen activation
        if event.type == pygame.USEREVENT + 1:
            show_winner = True
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)

    draw()

pygame.quit()
sys.exit()
