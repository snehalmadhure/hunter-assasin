import pygame

from graphics import bresenham_line, dda_line, bresenham_circle

# ============================================================
# MAP SETTINGS
# (Same map matrix carried forward from Phase 2)
# ============================================================

CELL_SIZE = 30

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

ROWS = len(MAP_MATRIX)
COLS = len(MAP_MATRIX[0])

MAP_WIDTH  = COLS * CELL_SIZE
MAP_HEIGHT = ROWS * CELL_SIZE


# ============================================================
# COLORS  (monochrome — carried forward from Phase 2)
# ============================================================

BG_COLOR    = (0,   0,   0  )
DRAW_COLOR  = (255, 255, 255)
COIN_COLOR  = (255, 255, 255)


# ============================================================
# GAME MAP CLASS
# ============================================================

class GameMap:

    def __init__(self):

        self.grid      = MAP_MATRIX
        self.rows      = ROWS
        self.cols      = COLS

        self.wall_segments = []
        self.crates        = []
        self.coins         = []
        self.health_kits   = []

        # Build all map objects
        self.generate_walls()
        self.generate_crates()
        self.generate_coins()
        self.generate_health_kits()


    # ========================================================
    # WALL CHECK
    # ========================================================

    def is_wall(self, row, col):

        if row < 0 or row >= self.rows:
            return True

        if col < 0 or col >= self.cols:
            return True

        return self.grid[row][col] == 0


    # ========================================================
    # GENERATE WALL BOUNDARY SEGMENTS
    # ========================================================

    def generate_walls(self):

        self.wall_segments.clear()

        for row in range(self.rows):
            for col in range(self.cols):

                if self.grid[row][col] != 1:
                    continue

                x = col * CELL_SIZE
                y = row * CELL_SIZE

                # Top
                if self.is_wall(row - 1, col):
                    self.wall_segments.append((x, y, x + CELL_SIZE, y))

                # Bottom
                if self.is_wall(row + 1, col):
                    self.wall_segments.append((x, y + CELL_SIZE, x + CELL_SIZE, y + CELL_SIZE))

                # Left
                if self.is_wall(row, col - 1):
                    self.wall_segments.append((x, y, x, y + CELL_SIZE))

                # Right
                if self.is_wall(row, col + 1):
                    self.wall_segments.append((x + CELL_SIZE, y, x + CELL_SIZE, y + CELL_SIZE))


    # ========================================================
    # GENERATE CRATES
    # (Non-border zero regions of size 1-2 → crate)
    # ========================================================

    def generate_crates(self):

        self.crates.clear()
        visited = set()

        for r in range(1, self.rows - 1):
            for c in range(1, self.cols - 1):

                if self.grid[r][c] == 0 and (r, c) not in visited:

                    comp            = []
                    queue           = [(r, c)]
                    touching_border = False

                    visited.add((r, c))

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
                            x    = col * CELL_SIZE + 4
                            y    = row * CELL_SIZE + 4
                            size = CELL_SIZE - 8
                            self.crates.append(pygame.Rect(x, y, size, size))


    # ========================================================
    # GENERATE COINS  (4 fixed positions)
    # ========================================================

    def generate_coins(self):

        self.coins = [
            (int(5.5  * CELL_SIZE), int(1.5  * CELL_SIZE)),
            (int(18.5 * CELL_SIZE), int(5.5  * CELL_SIZE)),
            (int(30.5 * CELL_SIZE), int(11.5 * CELL_SIZE)),
            (int(15.5 * CELL_SIZE), int(18.5 * CELL_SIZE)),
        ]


    # ========================================================
    # GENERATE HEALTH KITS  (3 fixed positions)
    # ========================================================

    def generate_health_kits(self):

        self.health_kits = [
            (int(26.5 * CELL_SIZE), int(3.5  * CELL_SIZE)),
            (int(1.5  * CELL_SIZE), int(8.5  * CELL_SIZE)),
            (int(33.5 * CELL_SIZE), int(14.5 * CELL_SIZE)),
        ]


    # ========================================================
    # DRAW WALLS  (DDA — same as Phase 2)
    # ========================================================

    def draw_walls_dda(self, screen):

        for x1, y1, x2, y2 in self.wall_segments:
            dda_line(screen, x1, y1, x2, y2, DRAW_COLOR)


    # ========================================================
    # DRAW CRATE  (Bresenham box + X — same as Phase 2)
    # ========================================================

    def draw_crate_bresenham(self, screen, rect):

        x = rect.x
        y = rect.y
        w = rect.width  - 1
        h = rect.height - 1

        # Outer box
        bresenham_line(screen, x,     y,     x + w, y,     DRAW_COLOR)
        bresenham_line(screen, x + w, y,     x + w, y + h, DRAW_COLOR)
        bresenham_line(screen, x + w, y + h, x,     y + h, DRAW_COLOR)
        bresenham_line(screen, x,     y + h, x,     y,     DRAW_COLOR)

        # Inner X pattern
        bresenham_line(screen, x,     y,     x + w, y + h, DRAW_COLOR)
        bresenham_line(screen, x + w, y,     x,     y + h, DRAW_COLOR)


    def draw_crates(self, screen):

        for crate in self.crates:
            self.draw_crate_bresenham(screen, crate)


    # ========================================================
    # DRAW COINS  (Bresenham circle — same as Phase 2)
    # ========================================================

    def draw_coins_bresenham(self, screen):

        for cx, cy in self.coins:
            bresenham_circle(screen, cx, cy, 4, COIN_COLOR)


    # ========================================================
    # DRAW HEALTH KITS  (Bresenham '+' sign — same as Phase 2)
    # ========================================================

    def draw_health_kits(self, screen):

        size = 6

        for hx, hy in self.health_kits:

            # Horizontal bar
            bresenham_line(screen, hx - size, hy, hx + size, hy, DRAW_COLOR)

            # Vertical bar
            bresenham_line(screen, hx, hy - size, hx, hy + size, DRAW_COLOR)


    # ========================================================
    # DRAW COMPLETE MAP
    # ========================================================

    def draw(self, screen):

        screen.fill(BG_COLOR)

        # Lock surface for bulk pixel-level drawing (set_at is slow without this)
        screen.lock()
        self.draw_walls_dda(screen)
        self.draw_crates(screen)
        self.draw_coins_bresenham(screen)
        self.draw_health_kits(screen)
        screen.unlock()
