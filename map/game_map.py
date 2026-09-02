import pygame
from graphics import bresenham_line, dda_line

# Matrix dimensions: 20 rows, 36 columns
MAP_MATRIX = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0],
    [0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0],
    [0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0],
    [0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0],
    [0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0],
    [0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0],
    [0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0],
    [0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

CELL_SIZE = 30
ROWS = len(MAP_MATRIX)
COLS = len(MAP_MATRIX[0])
MAP_WIDTH = COLS * CELL_SIZE
MAP_HEIGHT = ROWS * CELL_SIZE

# Monochrome Colors
BG_COLOR = (0, 0, 0)
DRAW_COLOR = (255, 255, 255)


class GameMap:

    def __init__(self):
        self.grid = MAP_MATRIX
        self.rows = ROWS
        self.cols = COLS
        self.wall_segments = []
        self.crates = []
        self.generate_walls()
        self.generate_crates()

    def is_wall(self, row, col):
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return True
        return self.grid[row][col] == 0

    def generate_walls(self):
        self.wall_segments.clear()
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] != 1:
                    continue

                x = col * CELL_SIZE
                y = row * CELL_SIZE

                if self.is_wall(row - 1, col):
                    self.wall_segments.append((x, y, x + CELL_SIZE, y))
                if self.is_wall(row + 1, col):
                    self.wall_segments.append(
                        (x, y + CELL_SIZE, x + CELL_SIZE, y + CELL_SIZE)
                    )
                if self.is_wall(row, col - 1):
                    self.wall_segments.append((x, y, x, y + CELL_SIZE))
                if self.is_wall(row, col + 1):
                    self.wall_segments.append(
                        (x + CELL_SIZE, y, x + CELL_SIZE, y + CELL_SIZE)
                    )

    def generate_crates(self):
        """Finds non-border 0-cell regions of size 1 to 2 in MAP_MATRIX and places crossed crates inside them."""
        self.crates.clear()
        visited = set()

        for r in range(1, self.rows - 1):
            for c in range(1, self.cols - 1):
                if self.grid[r][c] == 0 and (r, c) not in visited:
                    comp = []
                    queue = [(r, c)]
                    visited.add((r, c))
                    touching_border = False

                    while queue:
                        curr_r, curr_c = queue.pop(0)
                        comp.append((curr_r, curr_c))
                        if curr_r in (0, self.rows - 1) or curr_c in (0, self.cols - 1):
                            touching_border = True

                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = curr_r + dr, curr_c + dc
                            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                                if self.grid[nr][nc] == 0 and (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    queue.append((nr, nc))

                    # Place crossed boxes at internal 0-cell positions of size 1 or 2
                    if not touching_border and 1 <= len(comp) <= 2:
                        for row, col in comp:
                            x = col * CELL_SIZE + 4
                            y = row * CELL_SIZE + 4
                            size = CELL_SIZE - 8
                            self.crates.append(pygame.Rect(x, y, size, size))

    def draw_walls_dda(self, screen):
        """Draws wall boundaries using DDA algorithm."""
        for x1, y1, x2, y2 in self.wall_segments:
            dda_line(screen, x1, y1, x2, y2, DRAW_COLOR)

    def draw_crate_bresenham(self, screen, rect):
        """Draws crate wireframes and X-crosses using Bresenham's algorithm."""
        x, y, w, h = rect.x, rect.y, rect.width - 1, rect.height - 1

        # Outer box
        bresenham_line(screen, x, y, x + w, y, DRAW_COLOR)
        bresenham_line(screen, x + w, y, x + w, y + h, DRAW_COLOR)
        bresenham_line(screen, x + w, y + h, x, y + h, DRAW_COLOR)
        bresenham_line(screen, x, y + h, x, y, DRAW_COLOR)

        # Inner X pattern
        bresenham_line(screen, x, y, x + w, y + h, DRAW_COLOR)
        bresenham_line(screen, x + w, y, x, y + h, DRAW_COLOR)

    def draw_crates(self, screen):
        for crate in self.crates:
            self.draw_crate_bresenham(screen, crate)

    def draw(self, screen):
        screen.fill(BG_COLOR)
        self.draw_walls_dda(screen)
        self.draw_crates(screen)