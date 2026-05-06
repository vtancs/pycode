import pygame
import random
import sys

# --- Setup ---
pygame.init()
CELL = 32
GRID = 15  # must be odd for maze
WIDTH = HEIGHT = CELL * GRID
screen = pygame.display.set_mode((WIDTH, HEIGHT + 80))
pygame.display.set_caption("Dwarven Maze")

font = pygame.font.SysFont(None, 28)

WALL = 1
SPACE = 0

# --- Maze grid ---
maze = [[WALL for _ in range(GRID)] for _ in range(GRID)]

# --- DFS Maze Generator ---
def generate_maze(x, y):
    directions = [(2,0), (-2,0), (0,2), (0,-2)]
    random.shuffle(directions)

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 1 <= nx < GRID-1 and 1 <= ny < GRID-1:
            if maze[nx][ny] == WALL:
                maze[nx][ny] = SPACE
                maze[x + dx//2][y + dy//2] = SPACE
                generate_maze(nx, ny)

# Start carving
maze[1][1] = SPACE
generate_maze(1, 1)

# --- Player & Treasure ---
player_r, player_c = 1, 1

# Place treasure far from player
while True:
    tr = random.randrange(1, GRID, 2)
    tc = random.randrange(1, GRID, 2)
    if abs(tr - player_r) + abs(tc - player_c) > GRID // 2:
        break

steps = 0
bonk = False

# --- Draw ---
def draw():
    screen.fill((0,0,0))

    for r in range(GRID):
        for c in range(GRID):
            rect = pygame.Rect(c*CELL, r*CELL, CELL, CELL)
            if maze[r][c] == WALL:
                pygame.draw.rect(screen, (90,90,90), rect)
            else:
                pygame.draw.rect(screen, (30,30,30), rect)

    # Treasure (hidden until reached? you can change this)
    pygame.draw.rect(screen, (255, 215, 0), (tc*CELL, tr*CELL, CELL, CELL))

    # Player
    pygame.draw.rect(screen, (0,255,0), (player_c*CELL, player_r*CELL, CELL, CELL))

    # Distance detector (same spirit as original)
    dist = 100 * abs(tr - player_r) + 10 * abs(tc - player_c)

    hud = f"Steps: {steps}   Detector: {dist}"
    img = font.render(hud, True, (255,255,255))
    screen.blit(img, (10, HEIGHT + 10))

    if bonk:
        txt = font.render("BONK!", True, (255,50,50))
        screen.blit(txt, (10, HEIGHT + 40))

    pygame.display.flip()

# --- Game Loop ---
clock = pygame.time.Clock()

while True:
    bonk = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            nr, nc = player_r, player_c

            if event.key == pygame.K_UP:
                nr -= 1
            elif event.key == pygame.K_DOWN:
                nr += 1
            elif event.key == pygame.K_LEFT:
                nc -= 1
            elif event.key == pygame.K_RIGHT:
                nc += 1

            # Move check
            if 0 <= nr < GRID and 0 <= nc < GRID:
                if maze[nr][nc] == WALL:
                    bonk = True
                else:
                    player_r, player_c = nr, nc
                    steps += 1

    # Win condition
    if player_r == tr and player_c == tc:
        print(f"You found the treasure in {steps} steps!")
        pygame.quit()
        sys.exit()

    draw()
    clock.tick(12)