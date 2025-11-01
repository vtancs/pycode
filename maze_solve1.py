import pygame
import random
import time
from collections import deque

# --- Pygame setup ---
pygame.init()
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Generator & Solver - Kruskal + BFS")

# --- Colors ---
WALL_COLOR = (20, 20, 20)
PATH_COLOR = (240, 240, 240)
ACTIVE_COLOR = (0, 180, 255)
VISITED_COLOR = (255, 210, 80)
WAVE_COLOR = (255, 100, 50)
SOLUTION_COLOR = (50, 200, 50)
BORDER_COLOR = (0, 0, 0)

# --- Maze setup ---
COLS, ROWS = 40, 30  # grid of 20x20 px cells
CELL_SIZE = WIDTH // COLS
GEN_DELAY = 0.002   # delay during maze generation
SOLVE_DELAY = 0.005  # delay during solving

# --- Union-Find structure ---
class DisjointSet:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x == root_y:
            return False
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        return True


# --- Drawing helpers ---
def draw_cell(x, y, color):
    pygame.draw.rect(
        SCREEN, color,
        (x * CELL_SIZE + 1, y * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2)
    )


def draw_walls(vertical_walls, horizontal_walls):
    SCREEN.fill(PATH_COLOR)

    # Vertical walls
    for y in range(ROWS):
        for x in range(COLS - 1):
            if vertical_walls[y][x]:
                x1 = (x + 1) * CELL_SIZE
                y1 = y * CELL_SIZE
                pygame.draw.line(SCREEN, WALL_COLOR, (x1, y1), (x1, y1 + CELL_SIZE), 2)

    # Horizontal walls
    for y in range(ROWS - 1):
        for x in range(COLS):
            if horizontal_walls[y][x]:
                x1 = x * CELL_SIZE
                y1 = (y + 1) * CELL_SIZE
                pygame.draw.line(SCREEN, WALL_COLOR, (x1, y1), (x1 + CELL_SIZE, y1), 2)

    # Border
    pygame.draw.rect(SCREEN, BORDER_COLOR, (0, 0, WIDTH, HEIGHT), 3)


# --- Maze generation (animated Kruskal) ---
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
                return None, None

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


# --- Build adjacency graph ---
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


# --- Solve using BFS (wave animation) ---
def solve_maze_wave(adj):
    start = (0, 0)
    goal = (COLS - 1, ROWS - 1)

    queue = deque([start])
    visited = {start: None}
    wave_layers = [[start]]

    found = False
    while queue and not found:
        layer = []
        for _ in range(len(queue)):
            current = queue.popleft()
            draw_cell(current[0], current[1], WAVE_COLOR)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            if current == goal:
                found = True
                break

            for nx, ny in adj[current]:
                if (nx, ny) not in visited:
                    visited[(nx, ny)] = current
                    queue.append((nx, ny))
                    layer.append((nx, ny))

        pygame.display.flip()
        time.sleep(SOLVE_DELAY)
        wave_layers.append(layer)

    # Draw final visited cells
    for cell in visited:
        draw_cell(cell[0], cell[1], VISITED_COLOR)
    pygame.display.flip()

    # Trace back the solution
    cur = goal
    while cur:
        draw_cell(cur[0], cur[1], SOLUTION_COLOR)
        pygame.display.flip()
        time.sleep(0.005)
        cur = visited[cur]


# --- Main loop ---
def main():
    clock = pygame.time.Clock()
    running = True

    # Generate maze
    vertical_walls, horizontal_walls = generate_maze_animated(COLS, ROWS)
    if vertical_walls is None:
        return

    adj = build_adjacency(vertical_walls, horizontal_walls)

    # Solve maze with animated BFS
    solve_maze_wave(adj)

    # Keep display until closed
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
