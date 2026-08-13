import pygame

from map import GameMap, MAP_WIDTH, MAP_HEIGHT


# ============================================================
# INITIALIZE PYGAME
# ============================================================

pygame.init()


# ============================================================
# WINDOW / CAMERA SIZE
# ============================================================

# The actual game world is:
#
# 36 columns × 50 = 1800 pixels
# 20 rows    × 50 = 1000 pixels
#
# But we don't want the whole world to fit on the screen.
# This will later become our camera size.

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600

screen = pygame.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT)
)

pygame.display.set_caption(
    "Hunter Assassin - Maze Map"
)


# ============================================================
# CLOCK
# ============================================================

clock = pygame.time.Clock()


# ============================================================
# CREATE MAP
# ============================================================

game_map = GameMap()


# ============================================================
# CAMERA
# ============================================================

# For now the camera starts at the top-left
# of the world.

camera_x = 0
camera_y = 0


# ============================================================
# GAME LOOP
# ============================================================

running = True

while running:

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False


    # --------------------------------------------------------
    # CLEAR SCREEN
    # --------------------------------------------------------

    screen.fill((30, 30, 30))


    # --------------------------------------------------------
    # CREATE CAMERA VIEW
    # --------------------------------------------------------

    camera_surface = pygame.Surface(
        (
            SCREEN_WIDTH,
            SCREEN_HEIGHT
        )
    )


    # --------------------------------------------------------
    # DRAW COMPLETE WORLD
    # --------------------------------------------------------

    world_surface = pygame.Surface(
        (
            MAP_WIDTH,
            MAP_HEIGHT
        )
    )

    game_map.draw(world_surface)


    # --------------------------------------------------------
    # SHOW ONLY CAMERA AREA
    # --------------------------------------------------------

    camera_surface.blit(
        world_surface,
        (
            -camera_x,
            -camera_y
        )
    )


    # --------------------------------------------------------
    # DRAW CAMERA VIEW ON SCREEN
    # --------------------------------------------------------

    screen.blit(
        camera_surface,
        (0, 0)
    )


    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    pygame.display.flip()


    # --------------------------------------------------------
    # FPS
    # --------------------------------------------------------

    clock.tick(60)


# ============================================================
# EXIT
# ============================================================

pygame.quit()
