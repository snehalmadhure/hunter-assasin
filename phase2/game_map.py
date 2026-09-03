import pygame
from graphics import bresenham_line, dda_line, bresenham_circle

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

BG_COLOR = (0, 0, 0)
DRAW_COLOR = (255, 255, 255)
COIN_COLOR = (255, 255, 255)


class GameMap:

    def __init__(self):
        self.CELL_SIZE = CELL_SIZE
        self.grid = MAP_MATRIX
        self.rows = ROWS
        self.cols = COLS
        self.wall_segments = []
        self.crates = []
        self.coins = []
        self.health_kits = []
        self.generate_walls()
        self.generate_crates()
        self.generate_coins()
        self.generate_health_kits()

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

                    if not touching_border and 1 <= len(comp) <= 2:
                        for row, col in comp:
                            x = col * CELL_SIZE + 4
                            y = row * CELL_SIZE + 4
                            size = CELL_SIZE - 8
                            self.crates.append(pygame.Rect(x, y, size, size))

    def generate_coins(self):
        """Places exactly 4 coins in key maze locations."""
        self.coins = [
            (int(5.5 * CELL_SIZE), int(1.5 * CELL_SIZE)),
            (int(18.5 * CELL_SIZE), int(5.5 * CELL_SIZE)),
            (int(30.5 * CELL_SIZE), int(11.5 * CELL_SIZE)),
            (int(15.5 * CELL_SIZE), int(18.5 * CELL_SIZE)),
        ]

    def generate_health_kits(self):
        """Places 3 Health Kits ('+' signs) across the map."""
        self.health_kits = [
            (int(26.5 * CELL_SIZE), int(3.5 * CELL_SIZE)),
            (int(1.5 * CELL_SIZE), int(8.5 * CELL_SIZE)),
            (int(33.5 * CELL_SIZE), int(14.5 * CELL_SIZE)),
        ]

    def draw_walls_dda(self, screen):
        for x1, y1, x2, y2 in self.wall_segments:
            dda_line(screen, x1, y1, x2, y2, DRAW_COLOR)

    def draw_crate_bresenham(self, screen, rect):
        x, y, w, h = rect.x, rect.y, rect.width - 1, rect.height - 1
        bresenham_line(screen, x, y, x + w, y, DRAW_COLOR)
        bresenham_line(screen, x + w, y, x + w, y + h, DRAW_COLOR)
        bresenham_line(screen, x + w, y + h, x, y + h, DRAW_COLOR)
        bresenham_line(screen, x, y + h, x, y, DRAW_COLOR)
        bresenham_line(screen, x, y, x + w, y + h, DRAW_COLOR)
        bresenham_line(screen, x + w, y, x, y + h, DRAW_COLOR)

    def draw_crates(self, screen):
        for crate in self.crates:
            self.draw_crate_bresenham(screen, crate)

    def draw_coins_bresenham(self, screen):
        for cx, cy in self.coins:
            bresenham_circle(screen, cx, cy, 4, COIN_COLOR)

    def draw_health_kits(self, screen):
        """Draws Health Kits using intersecting Bresenham lines ('+' sign)."""
        size = 6
        for hx, hy in self.health_kits:
            # Horizontal bar
            bresenham_line(screen, hx - size, hy, hx + size, hy, DRAW_COLOR)
            # Vertical bar
            bresenham_line(screen, hx, hy - size, hx, hy + size, DRAW_COLOR)

    def draw(self, screen):
        screen.fill(BG_COLOR)
        self.draw_walls_dda(screen)
        self.draw_crates(screen)
        self.draw_coins_bresenham(screen)
        self.draw_health_kits(screen)