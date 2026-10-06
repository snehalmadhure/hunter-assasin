"""
SHADOW HUNT: 2D Top-Down Stealth Game (Phase 5 Final Release)
Mechanics & Constraints:
- Viewport Camera following Player (space visible on all sides around player)
- Sutherland-Hodgman Polygon Clipping & Cohen-Sutherland Line Clipping
- Raw Affine Matrix Transformations & Bresenham Circular Hitboxes
- Dynamic Enemies, Sweeping Camera, Alarm Timer, and Exit Extraction Pad
"""

import tkinter as tk
import math
import random
from typing import Set, List
from cg_math import CGMath
from camera import Camera
from map_engine import MapEngine
from player import Player
from collectibles import CollectibleManager, FloatingText
from enemy import Enemy
from security_camera import SecurityCamera


class GameApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SHADOW HUNT - Phase 5 (Camera Tracking & Clipping)")
        self.root.geometry("980x820")
        self.root.resizable(False, False)
        self.root.configure(bg="#070a12")

        self.score = 0
        self.show_hitbox = False
        self.game_over = False
        self.victory = False
        self.game_over_reason = ""

        self.alarm_active = False
        self.alarm_timer = 10.0
        self.alarm_flasher = 0.0

        self.replay_btn_bounds = (400, 440, 580, 490)

        # Header Status Bar
        self.header_frame = tk.Frame(root, bg="#0d131f", height=52)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)

        self.title_label = tk.Label(self.header_frame, text="SHADOW HUNT [PHASE 5]", font=("Consolas", 13, "bold"), fg="#10b981", bg="#0d131f")
        self.title_label.pack(side=tk.LEFT, padx=16, pady=8)

        self.health_label = tk.Label(self.header_frame, text="HP: 100%", font=("Consolas", 11, "bold"), fg="#22c55e", bg="#0d131f")
        self.health_label.pack(side=tk.LEFT, padx=10, pady=8)

        self.score_label = tk.Label(self.header_frame, text="SCORE: 0", font=("Consolas", 12, "bold"), fg="#facc15", bg="#0d131f")
        self.score_label.pack(side=tk.LEFT, padx=12, pady=8)

        self.enemy_label = tk.Label(self.header_frame, text="Targets: 2/2", font=("Consolas", 10, "bold"), fg="#ef4444", bg="#0d131f")
        self.enemy_label.pack(side=tk.LEFT, padx=10, pady=8)

        self.items_label = tk.Label(self.header_frame, text="Coins: 7 | MedKits: 3", font=("Consolas", 10), fg="#94a3b8", bg="#0d131f")
        self.items_label.pack(side=tk.LEFT, padx=10, pady=8)

        self.security_label = tk.Label(self.header_frame, text="Status: SECURE", font=("Consolas", 10, "bold"), fg="#38bdf8", bg="#0d131f")
        self.security_label.pack(side=tk.RIGHT, padx=16, pady=8)

        # Main Canvas
        self.canvas_width = 980
        self.canvas_height = 710
        self.canvas = tk.Canvas(root, width=self.canvas_width, height=self.canvas_height, bg="#050811", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Camera Setup (Viewport Size: 740x520 centered in canvas space)
        viewport_w, viewport_h = 740.0, 520.0
        cam_offset_x = (self.canvas_width - viewport_w) / 2.0  # 120.0
        cam_offset_y = (self.canvas_height - viewport_h) / 2.0 # 95.0
        self.camera = Camera(screen_offset_x=cam_offset_x, screen_offset_y=cam_offset_y, viewport_w=viewport_w, viewport_h=viewport_h)

        self.keys_pressed: Set[str] = set()
        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        self.footer_label = tk.Label(
            root,
            text="Phase 5 Viewport Active | [WASD] Move | Camera Tracks Player with Outer Viewport Polygon/Line Clipping",
            font=("Consolas", 9), fg="#64748b", bg="#070a12"
        )
        self.footer_label.pack(side=tk.BOTTOM, pady=4)

        self._reset_game()
        self.update_loop()

    def _reset_game(self):
        self.score = 0
        self.game_over = False
        self.victory = False
        self.game_over_reason = ""
        self.alarm_active = False
        self.alarm_timer = 10.0

        self.origin_x, self.origin_y = 60.0, 60.0
        self.map_engine = MapEngine(origin_x=self.origin_x, origin_y=self.origin_y)

        spawn_x = self.origin_x + 5.0 + 50.0
        spawn_y = self.origin_y + 5.0 + 50.0
        self.player = Player(spawn_x, spawn_y, speed=4.5)

        self.collectibles = CollectibleManager()
        self.collectibles.populate_map(self.map_engine)

        ox, oy = self.origin_x, self.origin_y
        self.enemies: List[Enemy] = []

        patrol_bottom_y = oy + 5.0 + 100.0 + 120.0 + 100.0 + 120.0 + 50.0
        self.enemies.append(Enemy([(ox + 160.0, patrol_bottom_y), (ox + 610.0, patrol_bottom_y)], is_shielded=False, speed=2.0))

        patrol_mid_y = oy + 5.0 + 100.0 + 120.0 + 50.0
        self.enemies.append(Enemy([(ox + 220.0, patrol_mid_y), (ox + 550.0, patrol_mid_y)], is_shielded=True, speed=1.8))

        cam_x = ox + self.map_engine.room_w - 18.0
        cam_y = oy + 18.0
        self.camera_sensor = SecurityCamera(x=cam_x, y=cam_y, base_angle=2.45, sweep_amplitude=0.65, sweep_speed=0.022)

    def _on_key_press(self, event):
        key = event.keysym.lower()
        self.keys_pressed.add(key)
        if key == "h": self.show_hitbox = not self.show_hitbox
        elif key == "r": self._reset_game()

    def _on_key_release(self, event):
        self.keys_pressed.discard(event.keysym.lower())

    def _on_canvas_click(self, event):
        if self.game_over or self.victory:
            bx1, by1, bx2, by2 = self.replay_btn_bounds
            if bx1 <= event.x <= bx2 and by1 <= event.y <= by2:
                self._reset_game()

    def _process_player_movement(self):
        if not self.player.is_alive() or self.game_over or self.victory: return
        dx, dy = 0.0, 0.0
        if "w" in self.keys_pressed or "up" in self.keys_pressed: dy -= 1.0
        if "s" in self.keys_pressed or "down" in self.keys_pressed: dy += 1.0
        if "a" in self.keys_pressed or "left" in self.keys_pressed: dx -= 1.0
        if "d" in self.keys_pressed or "right" in self.keys_pressed: dx += 1.0

        if dx != 0.0 or dy != 0.0:
            if dx != 0.0 and dy != 0.0:
                dx *= 0.7071
                dy *= 0.7071
            dx *= self.player.speed
            dy *= self.player.speed
            self.player.move(dx, dy, self.map_engine)

    def _update_camera_and_alarm(self):
        if self.game_over or self.victory: return

        cam_detected = self.camera_sensor.update(self.player)
        if cam_detected and not self.alarm_active:
            self.alarm_active = True
            self.collectibles.announcements.append(FloatingText(self.player.x, self.player.y - 20.0, "ALARM TRIGGERED!", color="#ef4444"))

        if self.alarm_active:
            self.alarm_flasher += 0.15
            self.alarm_timer = max(0.0, self.alarm_timer - (1.0 / 60.0))

            if self.map_engine.exit_door and self.map_engine.exit_door.is_reached(self.player.x, self.player.y, self.player.radius):
                self.victory = True
                self.score += 200
            elif self.alarm_timer <= 0.0:
                self.game_over = True
                self.game_over_reason = "LOCKDOWN SEALED - 10s EVACUATION FAILED"

    def _update_enemies_and_combat(self):
        if self.game_over or self.victory: return

        for enemy in self.enemies:
            if not enemy.is_alive: continue
            event = enemy.update(self.player)
            if event == "shot_player":
                if not self.player.is_alive():
                    self.game_over = True
                    self.game_over_reason = "KIA - OPERATIVE ELIMINATED BY ENEMY FIRE"

            contact = enemy.check_player_contact(self.player)
            if contact == "kill":
                self.score += 100 if enemy.is_shielded else 50
            elif contact == "shield_blocked":
                push_dx = math.cos(enemy.angle) * 8.0
                push_dy = math.sin(enemy.angle) * 8.0
                self.player.move(push_dx, push_dy, self.map_engine)

        alive_enemies = sum(1 for e in self.enemies if e.is_alive)
        if alive_enemies == 0 and self.map_engine.exit_door and self.map_engine.exit_door.is_reached(self.player.x, self.player.y, self.player.radius):
            if not self.victory:
                self.victory = True
                self.score += 150

    def render(self):
        self.canvas.delete("all")

        # 1. Update Viewport Camera to track player with surrounding space
        self.camera.follow(self.player.x, self.player.y)

        # 2. Render Map Engine (Clipped)
        self.map_engine.render(self.canvas, self.camera, alarm_active=self.alarm_active)

        # 3. Collectibles (Clipped)
        self.collectibles.render(self.canvas, self.camera)

        # 4. Security Camera (Clipped)
        self.camera_sensor.render(self.canvas, self.camera, alarm_active=self.alarm_active)

        # 5. Enemies (Clipped)
        for enemy in self.enemies:
            enemy.render(self.canvas, self.camera, show_hitbox=self.show_hitbox)

        # 6. Player (Clipped & centered in view)
        if self.player.is_alive():
            self.player.render(self.canvas, self.camera, show_hitbox=self.show_hitbox)

        # 7. Render Active Viewport Window Frame Boundary (Shows Phase 5 Clipping Area)
        xmin, ymin, xmax, ymax = self.camera.get_viewport_screen_bounds()
        self.canvas.create_rectangle(
            xmin, ymin, xmax, ymax,
            fill="", outline="#38bdf8", width=3, tags="viewport_frame"
        )
        self.canvas.create_text(
            xmin + 120, ymin - 12,
            text="[ ACTIVE CAMERA VIEWPORT CLIPPING FRAME ]", fill="#38bdf8", font=("Consolas", 8, "bold")
        )

        # 8. Modals for Game Over & Victory
        if self.game_over or self.victory:
            border_c = "#ef4444" if self.game_over else "#22c55e"
            title_t = "G A M E   O V E R" if self.game_over else "M I S S I O N   S U C C E S S"
            self.canvas.create_rectangle(160, 240, 820, 520, fill="#0b0f19", outline=border_c, width=3)
            self.canvas.create_text(490, 290, text=title_t, fill=border_c, font=("Consolas", 22, "bold"))
            self.canvas.create_text(490, 340, text=self.game_over_reason if self.game_over else "OPERATIVE ESCAPED SAFELY", fill="#ffffff", font=("Consolas", 12))
            bx1, by1, bx2, by2 = self.replay_btn_bounds
            self.canvas.create_rectangle(bx1, by1, bx2, by2, fill="#1e293b", outline=border_c, width=2)
            self.canvas.create_text((bx1 + bx2) / 2.0, (by1 + by2) / 2.0, text="[ REPLAY ]", fill="#ffffff", font=("Consolas", 13, "bold"))

        # HUD Labels
        hp_pct = max(0, int((self.player.health / self.player.max_health) * 100))
        self.health_label.config(text=f"HP: {hp_pct}%")
        self.score_label.config(text=f"SCORE: {self.score}")
        alive_enemies = sum(1 for e in self.enemies if e.is_alive)
        self.enemy_label.config(text=f"Targets: {alive_enemies}/2")
        self.items_label.config(text=f"Coins: {len(self.collectibles.coins)} | MedKits: {len(self.collectibles.health_kits)}")

    def update_loop(self):
        self._process_player_movement()
        self.map_engine.update_doors(self.player.x, self.player.y)
        if not self.game_over and not self.victory:
            score_earned, _ = self.collectibles.update_and_collide(self.player)
            self.score += score_earned
        self._update_camera_and_alarm()
        self._update_enemies_and_combat()
        self.render()
        self.root.after(16, self.update_loop)


def main():
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()