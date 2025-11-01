import pygame
import random
import time
from collections import deque

# --- Pygame setup ---
pygame.init()
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Game (Kruskal + BFS + Text Menu)")

# --- Colors ---
WALL_COLOR = (20, 20, 20)
PATH_COLOR = (240, 240, 240)
ACTIVE_COLOR = (0, 180, 255)
WAVE_COLOR = (255, 180, 80)
SOLUTION_COLOR = (0, 200, 0)
PLAYER_COLOR = (0, 100, 255)
BORDER_COLOR = (0, 0, 0)
START_COLOR = (100, 255, 100)
END_COLOR = (255, 100, 100)
TITLE_COLOR = (0, 200, 255)
TEXT_COLOR = (255, 255, 255)
BG_COLOR = (30, 30, 60)

# --- Maze setup ---
COLS, ROWS = 40, 30
CELL_SIZE = WIDTH // COLS
GEN_DELAY = 0.002
SOLVE_DELAY = 0.01

# --- Fonts ---
FONT = pygame.font.SysFont("consolas", 26)
TITLE_FONT = pygame.font.SysFont("arial", 50, bold=True)
SMALL_FONT = pygame.font.SysFont("consolas", 20)


# --- Disjoint Set ---
class DisjointSet:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            self.parent[rx] = ry
        elif self.rank[rx] > self.rank[ry]:
            self.parent[ry] = rx
        else:
            self.parent[ry] = rx
            self.rank[rx] += 1
        return True


# --- Drawing ---
def draw_cell(x, y, color):
    pygame.draw.rect(SCREEN, color, (x * CELL_SIZE + 1, y * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2))


def draw_walls(vertical_walls, horizontal_walls):
    SCREEN.fill(PATH_COLOR)
    for y in range(ROWS):
        for x in range(COLS - 1):
            if vertical_walls[y][x]:
                x1 = (x + 1) * CELL_SIZE
                y1 = y * CELL_SIZE
                pygame.draw.line(SCREEN, WALL_COLOR, (x1, y1), (x1, y1 + CELL_SIZE), 2)
    for y in range(ROWS - 1):
        for x in range(COLS):
            if horizontal_walls[y][x]:
                x1 = x * CELL_SIZE
                y1 = (y + 1) * CELL_SIZE
                pygame.draw.line(SCREEN, WALL_COLOR, (x1, y1), (x1 + CELL_SIZE, y1), 2)
    pygame.draw.rect(SCREEN, BORDER_COLOR, (0, 0, WIDTH, HEIGHT), 3)


# --- Kruskal Maze Generation ---
def generate_maze_animated(cols, rows):
    num_cells = cols * rows
    dsu = DisjointSet(num_cells)
    edges = []
    for y in range(rows):
        for x in range(cols):
            cell = y * cols + x
            if x < cols - 1:
                edges.append((cell, cell + 1, "H"))
            if y < rows - 1:
                edges.append((cell, cell + cols, "V"))
    random.shuffle(edges)

    vertical_walls = [[True for _ in range(cols - 1)] for _ in range(rows)]
    horizontal_walls = [[True for _ in range(cols)] for _ in range(rows - 1)]

    for cell1, cell2, wtype in edges:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        if dsu.union(cell1, cell2):
            x1, y1 = cell1 % cols, cell1 // cols
            x2, y2 = cell2 % cols, cell2 // cols
            if wtype == "H":
                vertical_walls[y1][x1] = False
            else:
                horizontal_walls[y1][x1] = False

            draw_walls(vertical_walls, horizontal_walls)
            draw_cell(x1, y1, ACTIVE_COLOR)
            draw_cell(x2, y2, ACTIVE_COLOR)
            pygame.display.flip()
            time.sleep(GEN_DELAY)

    draw_walls(vertical_walls, horizontal_walls)
    pygame.display.flip()
    return vertical_walls, horizontal_walls


# --- Build adjacency list ---
def build_adjacency(vertical_walls, horizontal_walls):
    adj = {}
    for y in range(ROWS):
        for x in range(COLS):
            neighbors = []
            if x > 0 and not vertical_walls[y][x - 1]:
                neighbors.append((x - 1, y))
            if x < COLS - 1 and not vertical_walls[y][x]:
                neighbors.append((x + 1, y))
            if y > 0 and not horizontal_walls[y - 1][x]:
                neighbors.append((x, y - 1))
            if y < ROWS - 1 and not horizontal_walls[y][x]:
                neighbors.append((x, y + 1))
            adj[(x, y)] = neighbors
    return adj


# --- BFS Solver ---
def solve_maze_bfs(adj):
    start, goal = (0, 0), (COLS - 1, ROWS - 1)
    queue = deque([start])
    visited = {start: None}
    wave = [start]

    while queue:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        next_wave = []
        for _ in range(len(wave)):
            current = queue.popleft()
            draw_cell(current[0], current[1], WAVE_COLOR)
            if current == goal:
                queue.clear()
                break
            for nx, ny in adj[current]:
                if (nx, ny) not in visited:
                    visited[(nx, ny)] = current
                    queue.append((nx, ny))
                    next_wave.append((nx, ny))

        pygame.display.flip()
        time.sleep(SOLVE_DELAY)
        wave = next_wave

    cur = goal
    while cur:
        draw_cell(cur[0], cur[1], SOLUTION_COLOR)
        pygame.display.flip()
        time.sleep(0.005)
        cur = visited[cur]


# --- Fade-in/out translucent message ---
def fade_message(message="Press any key to return"):
    alpha = 0
    fading_in = True
    clock = pygame.time.Clock()

    msg_surface = pygame.Surface((400, 40), pygame.SRCALPHA)
    text = SMALL_FONT.render(message, True, (255, 255, 255))

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN or event.type == pygame.QUIT:
                waiting = False

        msg_surface.fill((0, 0, 0, alpha))
        msg_surface.blit(text, (10, 8))
        SCREEN.blit(msg_surface, (20, HEIGHT - 60))
        pygame.display.flip()

        if fading_in:
            alpha += 5
            if alpha >= 128:
                alpha = 128
                fading_in = False
        else:
            alpha -= 3
            if alpha <= 40:
                alpha = 40
                fading_in = True

        clock.tick(30)


# --- Player Mode ---
def play_maze(adj, vertical_walls, horizontal_walls):
    player = (0, 0)
    goal = (COLS - 1, ROWS - 1)
    clock = pygame.time.Clock()
    playing = True

    while playing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                playing = False
            elif event.type == pygame.KEYDOWN:
                x, y = player
                if event.key == pygame.K_ESCAPE:  # 🔹 ESC to abort
                    playing = False
                    return
                if event.key == pygame.K_UP and (x, y - 1) in adj[player]:
                    player = (x, y - 1)
                elif event.key == pygame.K_DOWN and (x, y + 1) in adj[player]:
                    player = (x, y + 1)
                elif event.key == pygame.K_LEFT and (x - 1, y) in adj[player]:
                    player = (x - 1, y)
                elif event.key == pygame.K_RIGHT and (x + 1, y) in adj[player]:
                    player = (x + 1, y)

        draw_walls(vertical_walls, horizontal_walls)
        draw_cell(0, 0, START_COLOR)
        draw_cell(COLS - 1, ROWS - 1, END_COLOR)
        draw_cell(player[0], player[1], PLAYER_COLOR)
        pygame.display.flip()

        if player == goal:
            win_text = FONT.render("🎉 You Win! 🎉", True, (0, 200, 0))
            SCREEN.blit(win_text, (WIDTH // 2 - 80, HEIGHT // 2 - 20))
            pygame.display.flip()
            time.sleep(1.2)
            fade_message()
            playing = False

        clock.tick(30)


# --- Text Menu ---
def text_menu():
    maze_ready = False
    vertical_walls = horizontal_walls = adj = None
    running = True

    while running:
        SCREEN.fill(BG_COLOR)
        title = TITLE_FONT.render("Maze Game", True, TITLE_COLOR)
        SCREEN.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))

        lines = [
            "Press a key to choose an option:",
            "",
            "1 - Generate Maze",
            "2 - Auto Solve (BFS)",
            "3 - Play Manually",
            "4 - Quit"
        ]
        for i, line in enumerate(lines):
            text = FONT.render(line, True, TEXT_COLOR)
            SCREEN.blit(text, (WIDTH // 2 - 200, 240 + i * 40))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    vertical_walls, horizontal_walls = generate_maze_animated(COLS, ROWS)
                    adj = build_adjacency(vertical_walls, horizontal_walls)
                    maze_ready = True
                    fade_message("Maze generated. Press key to return")
                elif event.key == pygame.K_2 and maze_ready:
                    draw_walls(vertical_walls, horizontal_walls)
                    draw_cell(0, 0, START_COLOR)
                    draw_cell(COLS - 1, ROWS - 1, END_COLOR)
                    pygame.display.flip()
                    solve_maze_bfs(adj)
                    fade_message()
                elif event.key == pygame.K_3 and maze_ready:
                    play_maze(adj, vertical_walls, horizontal_walls)
                    fade_message("Press a key to return")
                elif event.key == pygame.K_4:
                    running = False


if __name__ == "__main__":
    text_menu()
    pygame.quit()
