import pygame
import random
import sys

# Maze settings
CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 20
WINDOW_WIDTH = CELL_SIZE * GRID_WIDTH
WINDOW_HEIGHT = CELL_SIZE * GRID_HEIGHT

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Random Maze (Press R to regenerate)")

# Directions: (dx, dy)
DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]

def generate_maze(width, height):
    """Generate a random maze using recursive backtracking"""
    maze = [[1 for _ in range(width)] for _ in range(height)]  # 1 = wall, 0 = path

    def carve(x, y):
        maze[y][x] = 0
        dirs = DIRECTIONS[:]
        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = x + dx*2, y + dy*2
            if 0 <= nx < width and 0 <= ny < height and maze[ny][nx] == 1:
                maze[y + dy][x + dx] = 0
                carve(nx, ny)

    carve(0, 0)
    return maze

def draw_maze(maze):
    screen.fill(WHITE)
    for y, row in enumerate(maze):
        for x, cell in enumerate(row):
            if cell == 1:
                pygame.draw.rect(screen, BLACK, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

def main():
    maze = generate_maze(GRID_WIDTH, GRID_HEIGHT)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Press R to regenerate
                    maze = generate_maze(GRID_WIDTH, GRID_HEIGHT)

        draw_maze(maze)
        pygame.display.flip()

if __name__ == "__main__":
    main()
