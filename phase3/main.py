"""
Phase 3 — Hunter Assassin
=========================
2D Transformation Demo + Playable Game

This phase builds on Phase 1 (map + camera) and Phase 2
(player, enemies, HUD, FOV) by adding the 2D transformation
system from phase3core.cpp, translated to Python.

NEW IN PHASE 3
--------------
- transforms.py  : identity / multiply_matrix / translation_matrix /
                   scaling_matrix / rotation_matrix /
                   apply_transformation / build_composite
- Player movement via Translation Matrix
- Enemy patrol    via Translation Matrix
- Enemy rotation  via Rotation Matrix
- Enemy body/FOV drawn by applying Rotation + Translation matrices
- Interactive pre-game menu:
    Enter any polygon, choose Row/Column, apply T/S/R/Composite,
    see original (white) + transformed (red) drawn with Bresenham.
- Game HUD shows active transformation name each frame.

Controls (Game)
---------------
  W / A / S / D  or  Arrow Keys  — Move player
  ESC                            — Quit
"""

import sys
import builtins
import threading
import time
import pygame

from game_map   import GameMap, MAP_WIDTH, MAP_HEIGHT, CELL_SIZE
from entities   import Player, Enemy
from graphics   import bresenham_line
from transforms import (
    translation_matrix,
    scaling_matrix,
    rotation_matrix,
    build_composite,
    apply_transformation,
    print_matrix,
    print_points,
    identity,
)


# ============================================================
# PYGAME-SAFE INPUT
#
# input() blocks Python's main thread, which stops pygame
# from pumping its event queue — Windows then marks the
# window as "(Not Responding)" and turns it grey.
#
# _pump_events() runs in a daemon thread and calls
# pygame.event.pump() every ~16 ms so the OS keeps the
# window alive while the console waits for a keypress.
#
# We temporarily replace builtins.input with this wrapper
# only during the demo, then restore the original.
# ============================================================

_ORIGINAL_INPUT = builtins.input


def _pump_events(stop_event):
    """Background thread: keep pygame alive during input() blocking."""
    while not stop_event.is_set():
        try:
            pygame.event.pump()
        except Exception:
            pass
        time.sleep(0.016)   # ~60 fps


def _demo_input(prompt=""):
    """
    Drop-in replacement for input() used during the transformation demo.
    Spawns a background thread to keep pygame's event loop alive
    so the window never shows (Not Responding).
    """
    stop = threading.Event()
    t = threading.Thread(target=_pump_events, args=(stop,), daemon=True)
    t.start()

    result = _ORIGINAL_INPUT(prompt)

    stop.set()
    t.join(timeout=0.5)
    return result


# ============================================================
# COLORS
# ============================================================

WHITE = (255, 255, 255)
RED   = (200,  50,  50)
BLACK = (  0,   0,   0)


# ============================================================
# DRAW HUD
#
# Carries forward Phase 2 HUD + adds transformation label.
# All lines drawn via bresenham_line (no pygame.draw shortcuts
# for game objects).
# ============================================================

def draw_hud(screen, player, enemies, rep_type):

    font = pygame.font.SysFont("Consolas", 14, bold=True)

    # --------------------------------------------------------
    # HEALTH TEXT
    # --------------------------------------------------------

    health_text = font.render(
        f"HEALTH: {int(player.health)}%", True, WHITE
    )
    screen.blit(health_text, (15, 10))

    # --------------------------------------------------------
    # HEALTH BAR FRAME  (Bresenham lines)
    # --------------------------------------------------------

    bresenham_line(screen, 120, 12, 220, 12, WHITE)
    bresenham_line(screen, 220, 12, 220, 22, WHITE)
    bresenham_line(screen, 220, 22, 120, 22, WHITE)
    bresenham_line(screen, 120, 22, 120, 12, WHITE)

    # --------------------------------------------------------
    # HEALTH BAR FILL
    # --------------------------------------------------------

    fill_width = int(player.health)

    for y in range(14, 21):
        if fill_width > 0:
            bresenham_line(screen, 121, y, 120 + fill_width, y, WHITE)

    # --------------------------------------------------------
    # DETECTION STATUS
    # --------------------------------------------------------

    any_detected = any(e.is_player_detected for e in enemies)

    status_str = (
        "STATUS: ALERT - PLAYER DETECTED!"
        if any_detected else
        "STATUS: CLEAR"
    )

    status_text = font.render(status_str, True, WHITE)
    screen.blit(status_text, (250, 10))

    # --------------------------------------------------------
    # ACTIVE TRANSFORMATION LABEL  (Phase 3 addition)
    # --------------------------------------------------------

    rep_str  = "Row" if rep_type == 1 else "Column"

    tf_label = font.render(
        f"TRANSFORM: {player.current_transform}  |  REP: {rep_str} Matrix",
        True, WHITE
    )
    screen.blit(tf_label, (15, 30))


# ============================================================
# DRAW ORIGINAL POLYGON
#
# White outline — mirrors C++ drawOriginal (Bresenham lines)
# ============================================================

def draw_original(screen, points):
    """
    Draw the original polygon in WHITE using Bresenham lines.
    Connects points[i] → points[(i+1) % n], wrapping around.
    """

    n = len(points)

    for i in range(n):

        x1 = int(round(points[i][0]))
        y1 = int(round(points[i][1]))

        x2 = int(round(points[(i + 1) % n][0]))
        y2 = int(round(points[(i + 1) % n][1]))

        bresenham_line(screen, x1, y1, x2, y2, WHITE)


# ============================================================
# DRAW TRANSFORMED POLYGON
#
# Red outline — mirrors C++ drawTransformed (Bresenham lines)
# ============================================================

def draw_transformed(screen, points):
    """
    Draw the transformed polygon in RED using Bresenham lines.
    Connects points[i] → points[(i+1) % n], wrapping around.
    """

    n = len(points)

    for i in range(n):

        x1 = int(round(points[i][0]))
        y1 = int(round(points[i][1]))

        x2 = int(round(points[(i + 1) % n][0]))
        y2 = int(round(points[(i + 1) % n][1]))

        bresenham_line(screen, x1, y1, x2, y2, RED)


# ============================================================
# INTERACTIVE TRANSFORMATION DEMO
#
# Console-driven menu that mirrors the C++ main() exactly:
#   - Input points
#   - Choose Row / Column representation
#   - Apply Translation / Scaling / Rotation / Composite
#   - Print matrix + transformed coordinates
#   - Show original (white) + transformed (red) on screen
# ============================================================

def run_transformation_demo(screen, clock):
    """
    Full menu-driven 2D transformation program.

    Faithfully translates the C++ phase3core.cpp main() loop.
    Runs BEFORE the game starts.  User presses any key or
    closes the window to proceed to the game.
    """

    # --------------------------------------------------------
    # INPUT: Number of Points
    # --------------------------------------------------------

    print("\n" + "=" * 50)
    print("  PHASE 3 — 2D TRANSFORMATION DEMO")
    print("=" * 50)
    print("\nEnter Number of Points : ", end="", flush=True)

    n = int(input())

    if n < 2 or n > 20:
        print("Invalid Number of Points. Using default triangle.")
        n = 3

    # --------------------------------------------------------
    # INPUT: Coordinates (mirrors C++ inputPoints)
    # --------------------------------------------------------

    print("\nEnter Coordinates Matrix")

    ox = []   # Original X
    oy = []   # Original Y

    for i in range(n):
        print(f"Point {i + 1} : ", end="", flush=True)
        raw    = input().replace(',', ' ')
        coords = raw.split()
        ox.append(float(coords[0]))
        oy.append(float(coords[1]))

    # Pack as list of (x, y) tuples (Python style)
    original_points = list(zip(ox, oy))

    # Print original coordinates
    print_points(original_points)

    # --------------------------------------------------------
    # CHOOSE: Row or Column representation
    # --------------------------------------------------------

    print("\nChoose Representation")
    print("1. Row Matrix")
    print("2. Column Matrix")
    print("Choice : ", end="", flush=True)

    rep_type = int(input())

    if rep_type not in (1, 2):
        print("Invalid Choice. Using Column Matrix.")
        rep_type = 2

    # --------------------------------------------------------
    # TRANSFORMATION MENU LOOP
    # (mirrors C++ while(true) + switch(choice))
    # --------------------------------------------------------

    transformed_points = list(original_points)   # start same

    running = True

    while running:

        print("\n1. Translation")
        print("2. Scaling")
        print("3. Rotation")
        print("4. Composite")
        print("5. Proceed to Game")

        print("\nChoice : ", end="", flush=True)

        choice_str = input().strip()

        if not choice_str.isdigit():
            print("\nInvalid Choice")
            continue

        choice = int(choice_str)

        # ====================================================
        # CASE 1: Translation
        # ====================================================

        if choice == 1:

            print("\nEnter tx : ", end="", flush=True)
            tx = float(input())

            print("Enter ty : ", end="", flush=True)
            ty = float(input())

            T = translation_matrix(tx, ty, rep_type)

            print("\nTranslation Matrix")
            print_matrix(T)

            transformed_points = apply_transformation(
                T, original_points, rep_type
            )

            print("\nTranslated Coordinates")
            print_points(transformed_points)


        # ====================================================
        # CASE 2: Scaling
        # ====================================================

        elif choice == 2:

            print("\nEnter sx : ", end="", flush=True)
            sx = float(input())

            print("Enter sy : ", end="", flush=True)
            sy = float(input())

            T = scaling_matrix(sx, sy)

            print("\nScaling Matrix")
            print_matrix(T)

            transformed_points = apply_transformation(
                T, original_points, rep_type
            )

            print("\nScaled Coordinates")
            print_points(transformed_points)


        # ====================================================
        # CASE 3: Rotation
        # ====================================================

        elif choice == 3:

            print("\n1. Clockwise")
            print("2. Anticlockwise")
            print("\nEnter Rotation Direction : ", end="", flush=True)

            direction = int(input())

            if direction not in (1, 2):
                print("\nInvalid Rotation Direction")
                continue

            print("Enter Angle : ", end="", flush=True)
            angle = float(input())

            if direction == 1:
                # Clockwise → negate
                angle = -angle

            T = rotation_matrix(angle, rep_type)

            print("\nRotation Matrix")
            print_matrix(T)

            transformed_points = apply_transformation(
                T, original_points, rep_type
            )

            print("\nRotated Coordinates")
            print_points(transformed_points)


        # ====================================================
        # CASE 4: Composite
        # ====================================================

        elif choice == 4:

            Final = build_composite(rep_type)

            print("\nComposite Matrix")
            print_matrix(Final)

            transformed_points = apply_transformation(
                Final, original_points, rep_type
            )

            print("\nTransformed Coordinates")
            print_points(transformed_points)


        # ====================================================
        # CASE 5: Exit demo → start game
        # ====================================================

        elif choice == 5:
            print("\nProceeding to game...")
            running = False
            break

        else:
            print("\nInvalid Choice")
            continue


        # ----------------------------------------------------
        # RENDER DEMO FRAME
        #
        # Original  → WHITE  (mirrors C++ drawOriginal)
        # Transformed → RED  (mirrors C++ drawTransformed)
        # Both use Bresenham lines (same as all Phase 1/2 drawing)
        # ----------------------------------------------------

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill(BLACK)

        screen.lock()
        draw_original(screen, original_points)
        draw_transformed(screen, transformed_points)
        screen.unlock()

        # Labels
        font = pygame.font.SysFont("Consolas", 14, bold=True)

        orig_label = font.render("ORIGINAL (WHITE)", True, WHITE)
        trans_label = font.render("TRANSFORMED (RED)", True, RED)

        screen.blit(orig_label,  (10, 10))
        screen.blit(trans_label, (10, 30))

        pygame.display.flip()
        clock.tick(60)

        print("\nGraphics updated.")

    return rep_type


# ============================================================
# GAME LOOP
# ============================================================

def run_game(screen, clock, rep_type):
    """
    Full game combining Phase 1 + Phase 2 + Phase 3 gameplay.

    Player and enemies now use transformation matrices
    (translation, rotation) for all movement and drawing.
    """

    game_map = GameMap()

    player = Player(1.5 * CELL_SIZE, 1.5 * CELL_SIZE)

    # --------------------------------------------------------
    # ENEMIES  (same positions as Phase 2)
    # --------------------------------------------------------

    enemies = [
        Enemy(
            12.5 * CELL_SIZE,
            5.5  * CELL_SIZE,
            facing_angle_deg = 180,
            sight_radius     = 110
        ),
        Enemy(
            8.5  * CELL_SIZE,
            14.5 * CELL_SIZE,
            facing_angle_deg = 270,
            sight_radius     = 100
        ),
        Enemy(
            25.5 * CELL_SIZE,
            8.5  * CELL_SIZE,
            facing_angle_deg = 90,
            sight_radius     = 120
        ),
    ]

    # --------------------------------------------------------
    # SET PATROL WAYPOINTS
    #
    # Each enemy patrols between two world positions.
    # The patrol is driven by translation matrices each frame.
    # --------------------------------------------------------

    enemies[0].patrol_bx = 20.5 * CELL_SIZE
    enemies[0].patrol_by =  5.5 * CELL_SIZE

    # Enemy 1: patrol horizontally along row 14 (cols 4.5 <-> 8.5)
    # Row 14 is a long clear corridor — all cells walkable between these cols.
    # OLD (broken): col 8 -> row 8 — vertical path crossed 4 wall cells
    enemies[1].patrol_bx =  4.5 * CELL_SIZE
    enemies[1].patrol_by = 14.5 * CELL_SIZE

    # Enemy 2: patrol horizontally along row 8 within the valid stretch (cols 22.5 <-> 25.5)
    # Row 8 has a wall gap at cols 27-29, so patrol stays left of it.
    # OLD (broken): col 25 -> col 32 — path crossed wall cells at cols 27, 28, 29
    enemies[2].patrol_bx = 22.5 * CELL_SIZE
    enemies[2].patrol_by =  8.5 * CELL_SIZE

    # --------------------------------------------------------
    # MAIN GAME LOOP
    # --------------------------------------------------------

    running     = True
    grace_frames = 120    # 2-second invincibility at game start (60 fps)

    while running:

        # ----------------------------------------------------
        # EVENTS
        # ----------------------------------------------------

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # ----------------------------------------------------
        # UPDATE PLAYER  (Translation Matrix)
        # ----------------------------------------------------

        keys = pygame.key.get_pressed()
        player.update(keys, game_map, rep_type)

        # ----------------------------------------------------
        # UPDATE ENEMIES
        #   - Patrol via Translation Matrix
        #   - Rotate facing via Rotation Matrix
        #   - Detect player (same as Phase 2)
        # ----------------------------------------------------

        for enemy in enemies:

            enemy.update_patrol(rep_type, game_map)
            enemy.update_rotation(rep_type)

            detected = enemy.update_detection(player)

            if detected and grace_frames <= 0:
                player.health = max(0.0, player.health - 0.2)

        # Tell the player whether any enemy is currently watching them.
        # This flag drives the scaling_matrix pulse in Player.draw().
        player.is_detected = any(e.is_player_detected for e in enemies)

        if grace_frames > 0:
            grace_frames -= 1

        # ----------------------------------------------------
        # COIN PICKUPS  (same as Phase 2)
        # ----------------------------------------------------

        player_r = player.radius

        game_map.coins = [
            (cx, cy) for cx, cy in game_map.coins
            if (cx - player.x) ** 2 + (cy - player.y) ** 2
               > (player_r + 4) ** 2
        ]

        # ----------------------------------------------------
        # HEALTH KIT PICKUPS  (same as Phase 2)
        # ----------------------------------------------------

        new_health_kits = []

        for hx, hy in game_map.health_kits:

            if (hx - player.x) ** 2 + (hy - player.y) ** 2 \
               <= (player_r + 8) ** 2:

                player.health = min(100.0, player.health + 30.0)

            else:
                new_health_kits.append((hx, hy))

        game_map.health_kits = new_health_kits

        # ----------------------------------------------------
        # GAME OVER CHECK
        # ----------------------------------------------------

        if player.health <= 0:
            print("\nGAME OVER — Player health reached 0.")
            running = False

        # ----------------------------------------------------
        # RENDER
        # ----------------------------------------------------

        # game_map.draw() handles its own lock/unlock internally.
        game_map.draw(screen)

        # Lock once for all entity pixel drawing (Bresenham/circle set_at calls)
        screen.lock()
        player.draw(screen, rep_type)
        for enemy in enemies:
            enemy.draw(screen, rep_type)
        screen.unlock()

        # HUD uses surface.blit() for text — must be done AFTER unlock
        draw_hud(screen, player, enemies, rep_type)

        pygame.display.flip()
        clock.tick(60)


# ============================================================
# ENTRY POINT
# ============================================================

def main():

    pygame.init()

    screen = pygame.display.set_mode((MAP_WIDTH, MAP_HEIGHT))
    pygame.display.set_caption(
        "Hunter Assassin — Phase 3: 2D Transformations"
    )

    clock = pygame.time.Clock()

    # --------------------------------------------------------
    # STEP 1: Run the interactive 2D Transformation Demo
    #
    # This is the pre-game menu (previously dead code).
    # The user enters polygon points, picks Row/Column
    # representation, then applies Translation / Scaling /
    # Rotation / Composite transformations via the console.
    # The chosen rep_type carries forward into gameplay so
    # all in-game matrices use the same convention.
    # --------------------------------------------------------

    # Patch input() so the pygame window stays alive (not grey/frozen)
    # while the console is waiting for user input.
    builtins.input = _demo_input
    try:
        rep_type = run_transformation_demo(screen, clock)
    finally:
        # Always restore the real input(), even if the demo crashes
        builtins.input = _ORIGINAL_INPUT

    # --------------------------------------------------------
    # STEP 2: Start the actual game with the chosen rep_type
    # --------------------------------------------------------

    run_game(screen, clock, rep_type)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
