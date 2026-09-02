import sys
import pygame
from game_map import GameMap, MAP_WIDTH, MAP_HEIGHT


def main():
    pygame.init()
    screen = pygame.display.set_mode((MAP_WIDTH, MAP_HEIGHT))
    pygame.display.set_caption("Monochrome Maze Map with DDA & Bresenham")
    clock = pygame.time.Clock()

    game_map = GameMap()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        game_map.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()