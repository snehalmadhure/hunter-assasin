import pygame

from graphics import bresenham_line


# ============================================================
# MAP SETTINGS
# ============================================================

CELL_SIZE = 50

# Matrix = 20 rows x 36 columns
ROWS = 20
COLS = 36

MAP_WIDTH = COLS * CELL_SIZE
MAP_HEIGHT = ROWS * CELL_SIZE

# Wall thickness = 5 pixels
WALL_THICKNESS = 5


# ============================================================
# COLORS
# ============================================================

# ------------------------------------------------------------
# WALL
# ------------------------------------------------------------

WALL_COLOR = (35, 35, 35)


# ------------------------------------------------------------
# WALKABLE FLOOR
# ------------------------------------------------------------

# Light grey path
FLOOR_COLOR = (175, 173, 167)

# Very subtle floor texture
FLOOR_DETAIL = (168, 166, 160)


# ------------------------------------------------------------
# LARGE WOODEN CRATES
# ------------------------------------------------------------

CRATE_COLOR = (145, 85, 25)
CRATE_DARK = (90, 50, 15)
CRATE_LIGHT = (190, 125, 50)


# ------------------------------------------------------------
# SINGLE ZERO PEACH BLOCK
# ------------------------------------------------------------

PEACH_BLOCK = (166, 119, 82)
PEACH_LIGHT = (190, 145, 105)
PEACH_DARK = (82, 55, 40)
PEACH_INNER = (145, 98, 68)


# ------------------------------------------------------------
# DEBUG GRID
# ------------------------------------------------------------

GRID_COLOR = (185, 183, 177)


# ============================================================
# MAP MATRIX
#
# 0 = WALL / BLOCKED
# 1 = WALKABLE PATH
# ============================================================

MAP_MATRIX = [

    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],

    [0,1,1,1,1,1,0,1,1,1,1,1,0,1,1,1,1,0,0,1,1,1,1,0,1,1,1,1,1,0,1,1,1,1,1,0],

    [0,1,0,1,0,1,0,1,0,0,0,1,0,1,0,0,1,0,0,1,0,0,1,0,1,0,0,0,1,0,1,0,1,0,1,0],

    [0,1,1,1,0,1,1,1,0,1,1,1,1,1,0,1,1,0,0,1,1,0,1,1,1,1,1,0,1,1,1,0,1,1,1,0],

    [0,0,0,1,0,0,1,1,0,1,0,1,1,0,0,1,0,0,0,0,1,0,0,1,1,0,1,0,1,1,0,0,1,0,0,0],

    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],

    [0,1,0,0,1,0,0,1,0,0,0,0,0,1,0,0,1,0,0,1,0,0,1,0,0,0,0,0,1,0,0,1,0,0,1,0],

    [0,1,0,0,1,1,1,1,1,1,0,1,1,1,1,1,1,0,0,1,1,1,1,1,1,0,1,1,1,1,1,1,0,0,1,0],

    [0,1,1,1,1,1,0,0,1,1,1,1,0,1,0,0,1,1,1,1,0,0,1,0,1,1,1,0,0,0,1,1,1,1,1,0],

    [0,1,1,0,0,1,0,1,1,0,1,0,0,1,0,0,1,0,0,1,1,1,1,0,0,1,0,1,1,0,1,0,0,0,0,0],

    [0,0,1,0,0,1,0,0,0,0,1,0,0,1,1,1,1,0,0,1,0,0,1,0,0,1,0,0,1,1,1,0,0,0,0,0],

    [0,1,1,1,1,1,0,0,0,1,1,1,0,1,0,0,1,1,1,1,0,0,1,0,1,1,1,0,0,0,1,1,1,1,1,0],

    [0,1,0,0,1,1,1,1,1,1,0,1,1,1,1,1,1,0,0,1,1,1,1,1,1,0,1,1,1,1,1,1,0,0,1,0],

    [0,1,0,0,1,0,0,1,0,0,0,0,0,1,0,0,1,0,0,1,0,0,1,0,0,0,0,0,1,0,0,1,0,0,1,0],

    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],

    [0,0,0,1,0,0,1,1,0,1,0,1,1,0,0,1,0,0,0,0,1,0,0,1,1,0,1,0,1,1,0,0,1,0,0,0],

    [0,1,1,1,0,1,1,1,0,1,1,1,1,1,0,1,1,0,0,1,1,0,1,1,1,1,1,0,1,1,1,0,1,1,1,0],

    [0,1,0,1,0,1,0,1,0,0,0,1,0,1,0,0,1,0,0,1,0,0,1,0,1,0,0,0,1,0,1,0,1,0,1,0],

    [0,1,1,1,1,1,0,1,1,1,1,1,0,1,1,1,1,0,0,1,1,1,1,0,1,1,1,1,1,0,1,1,1,1,1,0],

    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
]


# ============================================================
# GAME MAP
# ============================================================

class GameMap:

    def __init__(self):

        self.grid = MAP_MATRIX

        self.rows = ROWS
        self.cols = COLS

        # Wall boundaries
        self.wall_segments = []

        # 2-3 connected zero cells
        self.crates = []

        # Single isolated zero cells
        self.peach_blocks = []

        # Generate map objects
        self.generate_walls()
        self.generate_zero_objects()


    # ========================================================
    # CHECK WHETHER CELL IS WALL
    # ========================================================

    def is_wall(self, row, col):

        # Outside the map is also treated as wall
        if row < 0 or row >= self.rows:
            return True

        if col < 0 or col >= self.cols:
            return True

        return self.grid[row][col] == 0


    # ========================================================
    # GENERATE WALL BOUNDARIES
    # ========================================================

    def generate_walls(self):

        self.wall_segments.clear()

        for row in range(self.rows):

            for col in range(self.cols):

                # Only create wall boundaries around
                # walkable cells.

                if self.grid[row][col] != 1:
                    continue

                x = col * CELL_SIZE
                y = row * CELL_SIZE


                # ------------------------------------------------
                # TOP WALL
                # ------------------------------------------------

                if self.is_wall(row - 1, col):

                    self.wall_segments.append(
                        (
                            x,
                            y,
                            x + CELL_SIZE,
                            y
                        )
                    )


                # ------------------------------------------------
                # BOTTOM WALL
                # ------------------------------------------------

                if self.is_wall(row + 1, col):

                    self.wall_segments.append(
                        (
                            x,
                            y + CELL_SIZE,
                            x + CELL_SIZE,
                            y + CELL_SIZE
                        )
                    )


                # ------------------------------------------------
                # LEFT WALL
                # ------------------------------------------------

                if self.is_wall(row, col - 1):

                    self.wall_segments.append(
                        (
                            x,
                            y,
                            x,
                            y + CELL_SIZE
                        )
                    )


                # ------------------------------------------------
                # RIGHT WALL
                # ------------------------------------------------

                if self.is_wall(row, col + 1):

                    self.wall_segments.append(
                        (
                            x + CELL_SIZE,
                            y,
                            x + CELL_SIZE,
                            y + CELL_SIZE
                        )
                    )


    # ========================================================
    # GENERATE OBJECTS FROM ZERO CELLS
    #
    # SINGLE ZERO
    #       -> PEACH BLOCK
    #
    # 2 OR 3 CONNECTED ZEROS
    #       -> WOODEN CRATES
    #
    # 4+ CONNECTED ZEROS
    #       -> NORMAL WALL
    # ========================================================

    def generate_zero_objects(self):

        self.crates.clear()
        self.peach_blocks.clear()

        visited = set()


        for row in range(self.rows):

            for col in range(self.cols):

                # Only process zero cells
                if self.grid[row][col] != 0:
                    continue

                # Already processed
                if (row, col) in visited:
                    continue


                # ------------------------------------------------
                # FIND CONNECTED ZERO GROUP
                # ------------------------------------------------

                stack = [(row, col)]
                group = []


                while stack:

                    r, c = stack.pop()


                    if (r, c) in visited:
                        continue


                    if r < 0 or r >= self.rows:
                        continue


                    if c < 0 or c >= self.cols:
                        continue


                    if self.grid[r][c] != 0:
                        continue


                    visited.add((r, c))

                    group.append((r, c))


                    # Up
                    stack.append((r - 1, c))

                    # Down
                    stack.append((r + 1, c))

                    # Left
                    stack.append((r, c - 1))

                    # Right
                    stack.append((r, c + 1))


                # ------------------------------------------------
                # OUTER BORDER
                #
                # Border zeros remain normal wall.
                # ------------------------------------------------

                touches_boundary = False


                for r, c in group:

                    if (
                        r == 0
                        or r == self.rows - 1
                        or c == 0
                        or c == self.cols - 1
                    ):

                        touches_boundary = True
                        break


                if touches_boundary:
                    continue


                # ------------------------------------------------
                # SINGLE ZERO
                # ------------------------------------------------

                if len(group) == 1:

                    r, c = group[0]

                    x = c * CELL_SIZE
                    y = r * CELL_SIZE


                    self.peach_blocks.append(
                        pygame.Rect(
                            x,
                            y,
                            CELL_SIZE,
                            CELL_SIZE
                        )
                    )


                # ------------------------------------------------
                # 2 OR 3 ZERO CELLS
                # ------------------------------------------------

                elif len(group) <= 3:

                    for r, c in group:

                        x = c * CELL_SIZE
                        y = r * CELL_SIZE


                        self.crates.append(
                            pygame.Rect(
                                x,
                                y,
                                CELL_SIZE,
                                CELL_SIZE
                            )
                        )


                # ------------------------------------------------
                # 4+ ZERO CELLS
                # ------------------------------------------------
                #
                # Nothing is added here.
                # They remain normal wall.
                # ------------------------------------------------

                else:

                    pass


    # ========================================================
    # DRAW FLOOR
    #
    # 1 = LIGHT GREY WALKABLE AREA
    # 0 = DARK BACKGROUND
    # ========================================================

    def draw_floor(self, screen):

        # Start with dark wall/background
        screen.fill(WALL_COLOR)


        # Draw only cells containing 1
        for row in range(self.rows):

            for col in range(self.cols):

                if self.grid[row][col] == 1:

                    x = col * CELL_SIZE
                    y = row * CELL_SIZE


                    # Main floor

                    pygame.draw.rect(
                        screen,
                        FLOOR_COLOR,
                        (
                            x,
                            y,
                            CELL_SIZE,
                            CELL_SIZE
                        )
                    )


                    # Very subtle floor texture

                    pygame.draw.line(
                        screen,
                        FLOOR_DETAIL,
                        (
                            x + 5,
                            y + CELL_SIZE - 5
                        ),
                        (
                            x + CELL_SIZE - 5,
                            y + CELL_SIZE - 5
                        ),
                        1
                    )


    # ========================================================
    # DRAW WALL USING BRESENHAM
    #
    # WALL_THICKNESS = 5 pixels
    # ========================================================

    def draw_wall(
        self,
        screen,
        x1,
        y1,
        x2,
        y2
    ):

        half = WALL_THICKNESS // 2


        # ------------------------------------------------
        # HORIZONTAL WALL
        # ------------------------------------------------

        if y1 == y2:

            for offset in range(
                -half,
                half + 1
            ):

                bresenham_line(
                    screen,
                    x1,
                    y1 + offset,
                    x2,
                    y2 + offset,
                    WALL_COLOR
                )


        # ------------------------------------------------
        # VERTICAL WALL
        # ------------------------------------------------

        else:

            for offset in range(
                -half,
                half + 1
            ):

                bresenham_line(
                    screen,
                    x1 + offset,
                    y1,
                    x2 + offset,
                    y2,
                    WALL_COLOR
                )


    # ========================================================
    # DRAW ALL WALLS
    # ========================================================

    def draw_walls(self, screen):

        for x1, y1, x2, y2 in self.wall_segments:

            self.draw_wall(
                screen,
                x1,
                y1,
                x2,
                y2
            )


    # ========================================================
    # DRAW 50x50 WOODEN CRATE
    # ========================================================

    def draw_crate(self, screen, rect):

        x = rect.x
        y = rect.y

        w = rect.width
        h = rect.height


        # ------------------------------------------------
        # MAIN WOOD
        # ------------------------------------------------

        pygame.draw.rect(
            screen,
            CRATE_COLOR,
            rect
        )


        # ------------------------------------------------
        # DARK BORDER
        # ------------------------------------------------

        pygame.draw.rect(
            screen,
            CRATE_DARK,
            rect,
            2
        )


        # ------------------------------------------------
        # INNER BORDER
        # ------------------------------------------------

        pygame.draw.rect(
            screen,
            CRATE_LIGHT,
            (
                x + 4,
                y + 4,
                w - 8,
                h - 8
            ),
            1
        )


        # ------------------------------------------------
        # X PATTERN
        # ------------------------------------------------

        bresenham_line(
            screen,
            x + 5,
            y + 5,
            x + w - 5,
            y + h - 5,
            CRATE_DARK
        )


        bresenham_line(
            screen,
            x + w - 5,
            y + 5,
            x + 5,
            y + h - 5,
            CRATE_DARK
        )


    # ========================================================
    # DRAW ALL CRATES
    # ========================================================

    def draw_crates(self, screen):

        for crate in self.crates:

            self.draw_crate(
                screen,
                crate
            )


    # ========================================================
    # DRAW SINGLE PEACH BLOCK
    #
    # EXACT SIZE = 50x50
    # ========================================================

    def draw_peach_block(self, screen, rect):

        x = rect.x
        y = rect.y

        w = rect.width
        h = rect.height


        # ------------------------------------------------
        # OUTER DARK BORDER
        # ------------------------------------------------

        pygame.draw.rect(
            screen,
            PEACH_DARK,
            rect,
            border_radius=7
        )


        # ------------------------------------------------
        # MAIN PEACH AREA
        # ------------------------------------------------

        inner = pygame.Rect(
            x + 5,
            y + 5,
            w - 10,
            h - 10
        )

        pygame.draw.rect(
            screen,
            PEACH_BLOCK,
            inner,
            border_radius=4
        )


        # ------------------------------------------------
        # INNER DARK PANEL
        # ------------------------------------------------

        panel = pygame.Rect(
            x + 9,
            y + 9,
            w - 18,
            h - 18
        )

        pygame.draw.rect(
            screen,
            PEACH_INNER,
            panel,
            border_radius=3
        )


        # ------------------------------------------------
        # INNER PEACH PANEL
        # ------------------------------------------------

        highlight_panel = pygame.Rect(
            x + 12,
            y + 12,
            w - 24,
            h - 24
        )

        pygame.draw.rect(
            screen,
            PEACH_BLOCK,
            highlight_panel,
            border_radius=2
        )


        # ------------------------------------------------
        # VERTICAL TEXTURE
        # ------------------------------------------------

        pygame.draw.line(
            screen,
            PEACH_DARK,
            (
                x + w // 2,
                y + 12
            ),
            (
                x + w // 2,
                y + h - 12
            ),
            1
        )


        # ------------------------------------------------
        # HORIZONTAL TEXTURE
        # ------------------------------------------------

        pygame.draw.line(
            screen,
            PEACH_DARK,
            (
                x + 12,
                y + h // 2
            ),
            (
                x + w - 12,
                y + h // 2
            ),
            1
        )


        # ------------------------------------------------
        # TOP HIGHLIGHT
        # ------------------------------------------------

        pygame.draw.line(
            screen,
            PEACH_LIGHT,
            (
                x + 8,
                y + 6
            ),
            (
                x + w - 8,
                y + 6
            ),
            2
        )


        # ------------------------------------------------
        # LEFT HIGHLIGHT
        # ------------------------------------------------

        pygame.draw.line(
            screen,
            PEACH_LIGHT,
            (
                x + 6,
                y + 10
            ),
            (
                x + 6,
                y + h - 10
            ),
            2
        )


    # ========================================================
    # DRAW ALL PEACH BLOCKS
    # ========================================================

    def draw_peach_blocks(self, screen):

        for block in self.peach_blocks:

            self.draw_peach_block(
                screen,
                block
            )


    # ========================================================
    # DEBUG GRID
    #
    # Useful while designing the map.
    # Keep disabled in normal gameplay.
    # ========================================================

    def draw_debug_grid(self, screen):

        for x in range(
            0,
            MAP_WIDTH + 1,
            CELL_SIZE
        ):

            pygame.draw.line(
                screen,
                GRID_COLOR,
                (x, 0),
                (x, MAP_HEIGHT),
                1
            )


        for y in range(
            0,
            MAP_HEIGHT + 1,
            CELL_SIZE
        ):

            pygame.draw.line(
                screen,
                GRID_COLOR,
                (0, y),
                (MAP_WIDTH, y),
                1
            )


    # ========================================================
    # DRAW COMPLETE MAP
    # ========================================================

    def draw(self, screen):

        # ------------------------------------------------
        # 1. FLOOR
        # ------------------------------------------------

        self.draw_floor(screen)


        # ------------------------------------------------
        # 2. WALLS
        # ------------------------------------------------

        self.draw_walls(screen)


        # ------------------------------------------------
        # 3. WOODEN CRATES
        # ------------------------------------------------

        self.draw_crates(screen)


        # ------------------------------------------------
        # 4. SINGLE ZERO PEACH BLOCKS
        # ------------------------------------------------

        self.draw_peach_blocks(screen)


        # ------------------------------------------------
        # DEBUG GRID
        # ------------------------------------------------
        #
        # Uncomment this only if you want to see
        # the 50x50 cell structure.
        #
        # self.draw_debug_grid(screen)


    # ========================================================
    # GET COLLISION RECTANGLES
    # ========================================================

    def get_collision_rects(self):

        collision_rects = []


        # ------------------------------------------------
        # WALLS
        # ------------------------------------------------

        for x1, y1, x2, y2 in self.wall_segments:

            if y1 == y2:

                rect = pygame.Rect(
                    min(x1, x2),
                    y1 - WALL_THICKNESS // 2,
                    abs(x2 - x1),
                    WALL_THICKNESS
                )


            else:

                rect = pygame.Rect(
                    x1 - WALL_THICKNESS // 2,
                    min(y1, y2),
                    WALL_THICKNESS,
                    abs(y2 - y1)
                )


            collision_rects.append(rect)


        # ------------------------------------------------
        # WOODEN CRATES
        # ------------------------------------------------

        collision_rects.extend(
            self.crates
        )


        # ------------------------------------------------
        # PEACH BLOCKS
        # ------------------------------------------------

        collision_rects.extend(
            self.peach_blocks
        )


        return collision_rects
