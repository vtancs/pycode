import pygame
import random
import sys
from collections import deque

# Maze settings
CELL_SIZE = 20
GRID_WIDTH = 30   # even/odd doesn’t matter now, will be auto-adjusted to odd
GRID_HEIGHT = 20
WINDOW_WIDTH = CELL_SIZE * GRID_WIDTH
WINDOW_HEIGHT = CELL_SIZE * GRID_HEIGHT

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 20, 60)
BLUE = (30, 144, 255)
GREEN = (50, 205, 50)
YELLOW = (255, 215, 0)

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Maze Solver BFS Animation (Press R to regenerate)")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20, bold=True)

# Directions: (dx, dy)
DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]

def make_odd(n):
    """Ensure n is odd (maze works best with odd sizes)."""
    return n if n % 2 == 1 else n + 1

def generate_maze(width, height):
    """Generate a random maze using recursive backtracking."""
    width = make_odd(width)
    height = make_odd(height)

    maze = [[1 for _ in range(width)] for _ in range(height)]  # 1 = wall, 0 = path

    def carve(x, y):
        maze[y][x] = 0
        dirs = DIRECTIONS[:]
        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = x + dx * 2, y + dy * 2
            if 0 <= nx < width and 0 <= ny < height and maze[ny][nx] == 1:
                maze[y + dy][x + dx] = 0
                carve(nx, ny)

    carve(0, height - 1)  # start at bottom-left
    return maze, width, height

def bfs_reachable(maze, start, width, height):
    """Return set of cells reachable from start."""
    q = deque([start])
    seen = {start}
    while q:
        x, y = q.popleft()
        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if maze[ny][nx] == 0 and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    q.append((nx, ny))
    return seen

def carve_random_tunnel(maze, start, end, width, height):
    """Carve a random-walk tunnel from start to end."""
    x, y = start
    ex, ey = end
    while (x, y) != (ex, ey):
        if random.random() < 0.5:  # sometimes move horizontally
            if x < ex: x += 1
            elif x > ex: x -= 1
        else:  # sometimes move vertically
            if y < ey: y += 1
            elif y > ey: y -= 1
        maze[y][x] = 0

def ensure_connected(maze, start, end, width, height):
    """Ensure start and end are open and connected.
    Returns maze and a bool indicating if a tunnel was created."""
    sx, sy = start
    ex, ey = end
    maze[sy][sx] = 0
    maze[ey][ex] = 0

    reachable = bfs_reachable(maze, start, width, height)
    if end in reachable:
        return maze, False  # already connected

    # carve tunnel from nearest reachable cell
    nearest = min(reachable, key=lambda c: abs(c[0] - ex) + abs(c[1] - ey))
    carve_random_tunnel(maze, nearest, end, width, height)
    return maze, True

def bfs_search_steps(maze, start, end, width, height):
    """Run BFS and yield ('explore', explored_list) and ('path', path_list)."""
    queue = deque([start])
    came_from = {start: None}
    explored = []

    while queue:
        x, y = queue.popleft()
        explored.append((x, y))
        yield ("explore", explored[:])

        if (x, y) == end:
            break

        for dx, dy in DIRECTIONS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if maze[ny][nx] == 0 and (nx, ny) not in came_from:
                    queue.append((nx, ny))
                    came_from[(nx, ny)] = (x, y)

    if end not in came_from:
        return  # unreachable (shouldn’t happen after fix)

    # reconstruct path
    path = []
    cur = end
    while cur is not None:
        path.append(cur)
        cur = came_from.get(cur)
    path.reverse()

    for i in range(len(path)):
        yield ("path", path[:i+1])

def draw_maze(maze, explored, path, start, end, width, height, warning_msg):
    screen.fill(WHITE)

    # Draw walls
    for y, row in enumerate(maze):
        for x, cell in enumerate(row):
            if cell == 1:
                pygame.draw.rect(screen, BLACK, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Explored cells
    for (x, y) in explored:
        cx, cy = x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(screen, BLUE, (cx, cy), CELL_SIZE // 4)

    # Path diamonds
    for (x, y) in path:
        cx, cy = x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2
        points = [
            (cx, cy - CELL_SIZE // 3),
            (cx + CELL_SIZE // 3, cy),
            (cx, cy + CELL_SIZE // 3),
            (cx - CELL_SIZE // 3, cy)
        ]
        pygame.draw.polygon(screen, RED, points)

    # Start/end
    sx, sy = start
    ex, ey = end
    pygame.draw.rect(screen, GREEN, (sx * CELL_SIZE, sy * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    pygame.draw.rect(screen, YELLOW, (ex * CELL_SIZE, ey * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Warning text
    if warning_msg:
        text_surface = font.render(warning_msg, True, (255, 0, 0))
        screen.blit(text_surface, (10, WINDOW_HEIGHT - 30))

def main():
    global GRID_WIDTH, GRID_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT
    start = (0, GRID_HEIGHT - 1)
    end = (GRID_WIDTH - 1, 0)

    maze, w, h = generate_maze(GRID_WIDTH, GRID_HEIGHT)
    GRID_WIDTH, GRID_HEIGHT = w, h  # update in case made odd
    WINDOW_WIDTH = CELL_SIZE * GRID_WIDTH
    WINDOW_HEIGHT = CELL_SIZE * GRID_HEIGHT
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    maze, tunnel_made = ensure_connected(maze, start, end, GRID_WIDTH, GRID_HEIGHT)
    steps = bfs_search_steps(maze, start, end, GRID_WIDTH, GRID_HEIGHT)

    explored, path = [], []
    warning_timer = 90 if tunnel_made else 0  # show warning for ~3s at 30 FPS

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    maze, w, h = generate_maze(GRID_WIDTH, GRID_HEIGHT)
                    GRID_WIDTH, GRID_HEIGHT = w, h
                    WINDOW_WIDTH = CELL_SIZE * GRID_WIDTH
                    WINDOW_HEIGHT = CELL_SIZE * GRID_HEIGHT
                    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

                    maze, tunnel_made = ensure_connected(maze, start, end, GRID_WIDTH, GRID_HEIGHT)
                    steps = bfs_search_steps(maze, start, end, GRID_WIDTH, GRID_HEIGHT)
                    explored, path = [], []
                    warning_timer = 90 if tunnel_made else 0

        try:
            kind, data = next(steps)
            if kind == "explore":
                explored = data
            elif kind == "path":
                path = data
        except StopIteration:
            pass

        msg = "Tunnel created to connect start and end!" if warning_timer > 0 else ""
        if warning_timer > 0:
            warning_timer -= 1

        draw_maze(maze, explored, path, start, end, GRID_WIDTH, GRID_HEIGHT, msg)
        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()
