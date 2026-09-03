import sys
import pygame
from game_map import GameMap, MAP_WIDTH, MAP_HEIGHT, CELL_SIZE
from entities import Player, Enemy
from graphics import bresenham_line


def draw_hud(screen, player, enemies):
    font = pygame.font.SysFont("Consolas", 14, bold=True)

    # Health Text
    health_text = font.render(f"HEALTH: {int(player.health)}%", True, (255, 255, 255))
    screen.blit(health_text, (15, 10))

    # Health Bar Frame
    bresenham_line(screen, 120, 12, 220, 12, (255, 255, 255))
    bresenham_line(screen, 220, 12, 220, 22, (255, 255, 255))
    bresenham_line(screen, 220, 22, 120, 22, (255, 255, 255))
    bresenham_line(screen, 120, 22, 120, 12, (255, 255, 255))

    # Health Bar Fill
    fill_width = int(player.health)
    for y in range(14, 21):
        if fill_width > 0:
            bresenham_line(screen, 121, y, 120 + fill_width, y, (255, 255, 255))

    # Enemy Detection Status
    any_detected = any(e.is_player_detected for e in enemies)
    status_str = "STATUS: ALERT - PLAYER DETECTED!" if any_detected else "STATUS: CLEAR"
    status_text = font.render(status_str, True, (255, 255, 255))
    screen.blit(status_text, (250, 10))


def main():
    pygame.init()
    screen = pygame.display.set_mode((MAP_WIDTH, MAP_HEIGHT))
    pygame.display.set_caption("Monochrome Maze - Bresenham Geometry & FOV Mechanics")
    clock = pygame.time.Clock()

    game_map = GameMap()

    player = Player(1.5 * CELL_SIZE, 1.5 * CELL_SIZE)

    enemies = [
        Enemy(12.5 * CELL_SIZE, 5.5 * CELL_SIZE, facing_angle_deg=180, sight_radius=110),
        Enemy(8.5 * CELL_SIZE, 14.5 * CELL_SIZE, facing_angle_deg=270, sight_radius=100),
        Enemy(25.5 * CELL_SIZE, 8.5 * CELL_SIZE, facing_angle_deg=90, sight_radius=120),
    ]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        player.update(keys, game_map)

        # Update detection for enemies
        for enemy in enemies:
            detected = enemy.update_detection(player)
            if detected:
                player.health = max(0.0, player.health - 0.2)

        # Check Coin Pickups
        player_r = player.radius
        game_map.coins = [
            (cx, cy) for cx, cy in game_map.coins
            if (cx - player.x) ** 2 + (cy - player.y) ** 2 > (player_r + 4) ** 2
        ]

        # Check Health Kit Pickups
        new_health_kits = []
        for hx, hy in game_map.health_kits:
            if (hx - player.x) ** 2 + (hy - player.y) ** 2 <= (player_r + 8) ** 2:
                # Restore Health up to 100%
                player.health = min(100.0, player.health + 30.0)
            else:
                new_health_kits.append((hx, hy))
        game_map.health_kits = new_health_kits

        # Render Phase
        game_map.draw(screen)
        player.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)

        draw_hud(screen, player, enemies)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()