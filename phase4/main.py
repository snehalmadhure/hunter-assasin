"""
SHADOW HUNT: 2D Top-Down Stealth Game (Final Production)
Strict CGG Constraints & Mechanics:
- 100% Raw Math & Affine Transformations (CGMath.translate, CGMath.rotate, CGMath.scale).
- Bresenham's Circle Algorithm with mandatory decision parameter (1 - 2R) for hitboxes.
- Grid Standards: 5px walls, 100px passages, 30px entities, 20px collectibles.
- Player: Green Triangle with instant CGMath.rotate directional facing and head vertex.
- Collectibles: Yellow Coins pulsing via CGMath.scale (+10), Health Kits (+15% HP).
- Floating UI Announcements: 1-second upward drifting notifications.
- Enemies: Standard Guard (dies from any angle, 5% dmg) & Shielded Enforcer (rear-only kill, 7% dmg).
- Security Camera: Sweeps large vision cone from corner, triggers Alarm State.
- Glitch Alarm Timer: Huge 10-second timer with chromatic aberration via CGMath.translate.
- Escape Room Mechanic: Player must evacuate to the Exit Door before 10s expires.
- Game Over & Victory States with interactive REPLAY button.
"""

import tkinter as tk
import math
import random
from typing import Set, List, Optional
from cg_math import CGMath, Point, Points
from map_engine import MapEngine
from player import Player
from collectibles import CollectibleManager, FloatingText
from enemy import Enemy
from security_camera import SecurityCamera


class GameApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SHADOW HUNT - Hunter Assassin (CGG Engine)")
        self.root.geometry("980x820")
        self.root.resizable(False, False)
        self.root.configure(bg="#070a12")

        # ---------------------------------------------------------------------
        # Game State
        # ---------------------------------------------------------------------
        self.score = 0
        self.show_hitbox = False
        self.game_over = False
        self.victory = False
        self.game_over_reason = ""

        # Alarm & Escape Room State
        self.alarm_active = False
        self.alarm_timer = 10.0  # 10-second countdown
        self.alarm_flasher = 0.0

        # Interactive Replay Button Bounding Box (Canvas space)
        self.replay_btn_bounds = (400, 440, 580, 490)

        # ---------------------------------------------------------------------
        # Top HUD Status Bar
        # ---------------------------------------------------------------------
        self.header_frame = tk.Frame(root, bg="#0d131f", height=52)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)

        self.title_label = tk.Label(
            self.header_frame,
            text="SHADOW HUNT",
            font=("Consolas", 14, "bold"),
            fg="#10b981",
            bg="#0d131f"
        )
        self.title_label.pack(side=tk.LEFT, padx=16, pady=8)

        # Health Display
        self.health_label = tk.Label(
            self.header_frame,
            text="HP: 100%",
            font=("Consolas", 11, "bold"),
            fg="#22c55e",
            bg="#0d131f"
        )
        self.health_label.pack(side=tk.LEFT, padx=10, pady=8)

        # Score Display
        self.score_label = tk.Label(
            self.header_frame,
            text="SCORE: 0",
            font=("Consolas", 12, "bold"),
            fg="#facc15",
            bg="#0d131f"
        )
        self.score_label.pack(side=tk.LEFT, padx=12, pady=8)

        # Targets Status
        self.enemy_label = tk.Label(
            self.header_frame,
            text="Targets: 2/2",
            font=("Consolas", 10, "bold"),
            fg="#ef4444",
            bg="#0d131f"
        )
        self.enemy_label.pack(side=tk.LEFT, padx=10, pady=8)

        # Collectibles Count
        self.items_label = tk.Label(
            self.header_frame,
            text="Coins: 7 | MedKits: 3",
            font=("Consolas", 10),
            fg="#94a3b8",
            bg="#0d131f"
        )
        self.items_label.pack(side=tk.LEFT, padx=10, pady=8)

        # Security Status
        self.security_label = tk.Label(
            self.header_frame,
            text="Status: SECURE",
            font=("Consolas", 10, "bold"),
            fg="#38bdf8",
            bg="#0d131f"
        )
        self.security_label.pack(side=tk.RIGHT, padx=16, pady=8)

        # ---------------------------------------------------------------------
        # Main Canvas
        # ---------------------------------------------------------------------
        self.canvas_width = 980
        self.canvas_height = 710
        self.canvas = tk.Canvas(
            root,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="#050811",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # MapEngine centered in canvas (Room size: 770 x 550)
        self.origin_x = (self.canvas_width - 770) / 2.0  # 105.0
        self.origin_y = (self.canvas_height - 550) / 2.0  # 80.0

        # Input keys
        self.keys_pressed: Set[str] = set()

        # Bindings
        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Footer control hints
        self.footer_label = tk.Label(
            root,
            text="Controls: [WASD / Arrows] Move | [H] Hitbox | [R] Restart | Avoid the Camera or reach the Exit Door in 10s!",
            font=("Consolas", 9),
            fg="#64748b",
            bg="#070a12"
        )
        self.footer_label.pack(side=tk.BOTTOM, pady=4)

        # Initialize full world
        self._reset_game()

        # Start 60 FPS update loop
        self.update_loop()

    def _reset_game(self):
        """Resets the map, health, score, enemies, camera, collectibles, and alarm."""
        self.score = 0
        self.game_over = False
        self.victory = False
        self.game_over_reason = ""
        self.alarm_active = False
        self.alarm_timer = 10.0

        # 1. MapEngine
        self.map_engine = MapEngine(origin_x=self.origin_x, origin_y=self.origin_y)

        # 2. Player spawn: upper-left corridor (160, 135)
        spawn_x = self.origin_x + 5.0 + 50.0
        spawn_y = self.origin_y + 5.0 + 50.0
        self.player = Player(spawn_x, spawn_y, speed=4.5)

        # 3. Collectibles
        self.collectibles = CollectibleManager()
        self.collectibles.populate_map(self.map_engine)

        # 4. Enemies (Patrol Paths)
        ox, oy = self.origin_x, self.origin_y
        self.enemies: List[Enemy] = []

        # Non-Shielded Enemy: patrols bottom horizontal corridor
        patrol_bottom_y = oy + 5.0 + 100.0 + 120.0 + 100.0 + 120.0 + 50.0  # 80 + 495 = 575
        path_guard = [
            (ox + 160.0, patrol_bottom_y),
            (ox + 610.0, patrol_bottom_y)
        ]
        self.guard_enemy = Enemy(path_guard, is_shielded=False, speed=2.0)
        self.enemies.append(self.guard_enemy)

        # Shielded Enemy: patrols middle horizontal corridor
        patrol_mid_y = oy + 5.0 + 100.0 + 120.0 + 50.0  # 80 + 275 = 355
        path_shielded = [
            (ox + 220.0, patrol_mid_y),
            (ox + 550.0, patrol_mid_y)
        ]
        self.shield_enemy = Enemy(path_shielded, is_shielded=True, speed=1.8)
        self.enemies.append(self.shield_enemy)

        # 5. Security Camera in Top-Right Corner of the Room
        # Corner position: ox + room_w - 20, oy + 20
        cam_x = ox + self.map_engine.room_w - 18.0
        cam_y = oy + 18.0
        self.camera = SecurityCamera(
            x=cam_x,
            y=cam_y,
            base_angle=2.45,                 # ~140° pointing down-left into the room
            sweep_amplitude=0.65,             # +/- 37° sweep
            sweep_speed=0.022,
            fov_angle=math.radians(65),
            cone_range=235.0
        )

    def _on_key_press(self, event):
        key = event.keysym.lower()
        self.keys_pressed.add(key)
        if key == "h":
            self.show_hitbox = not self.show_hitbox
        elif key == "r":
            self._reset_game()

    def _on_key_release(self, event):
        key = event.keysym.lower()
        self.keys_pressed.discard(key)

    def _on_canvas_click(self, event):
        """Handles clicks on interactive REPLAY button when game is over or won."""
        if self.game_over or self.victory:
            bx1, by1, bx2, by2 = self.replay_btn_bounds
            if bx1 <= event.x <= bx2 and by1 <= event.y <= by2:
                self._reset_game()

    def _process_player_movement(self):
        """Processes directional input using CGMath.rotate (facing) & CGMath.translate (movement)."""
        if not self.player.is_alive() or self.game_over or self.victory:
            return

        dx, dy = 0.0, 0.0

        if "w" in self.keys_pressed or "up" in self.keys_pressed:
            dy -= 1.0
        if "s" in self.keys_pressed or "down" in self.keys_pressed:
            dy += 1.0
        if "a" in self.keys_pressed or "left" in self.keys_pressed:
            dx -= 1.0
        if "d" in self.keys_pressed or "right" in self.keys_pressed:
            dx += 1.0

        if dx != 0.0 or dy != 0.0:
            if dx != 0.0 and dy != 0.0:
                inv_len = 1.0 / 1.41421356
                dx *= inv_len
                dy *= inv_len

            dx *= self.player.speed
            dy *= self.player.speed

            # Player move uses CGMath.rotate (instant facing) & CGMath.translate (motion)
            self.player.move(dx, dy, self.map_engine)

    def _update_camera_and_alarm(self):
        """Updates sweeping security camera, alarm state, and evacuation countdown."""
        if self.game_over or self.victory:
            return

        # 1. Update camera sweep and detect player
        cam_detected = self.camera.update(self.player)
        if cam_detected and not self.alarm_active:
            self.alarm_active = True
            self.collectibles.announcements.append(
                FloatingText(self.player.x, self.player.y - 20.0, "ALARM TRIGGERED!", color="#ef4444", duration_frames=80)
            )

        # 2. If alarm is active, countdown 10-second timer
        if self.alarm_active:
            self.alarm_flasher += 0.15
            self.alarm_timer = max(0.0, self.alarm_timer - (1.0 / 60.0))

            # Check if player reached the Exit Door before timer runs out
            if self.map_engine.exit_door and self.map_engine.exit_door.is_reached(self.player.x, self.player.y, self.player.radius):
                self.victory = True
                self.score += 200
                self.collectibles.announcements.append(
                    FloatingText(self.player.x, self.player.y - 20.0, "ESCAPED! +200", color="#22c55e", duration_frames=120)
                )

            # If timer hits 0 before reaching Exit Door -> GAME OVER!
            elif self.alarm_timer <= 0.0:
                self.game_over = True
                self.game_over_reason = "LOCKDOWN SEALED - 10s EVACUATION FAILED"

    def _update_enemies_and_combat(self):
        """Updates enemy patrols, vision detection, shooting, and assassination checks."""
        if self.game_over or self.victory:
            return

        for enemy in self.enemies:
            if not enemy.is_alive:
                continue

            # 1. Update patrol, vision cone, and attack
            event = enemy.update(self.player)
            if event == "shot_player":
                dmg = int(enemy.damage_per_shot)
                self.collectibles.announcements.append(
                    FloatingText(self.player.x, self.player.y - 16.0, f"-{dmg}% HP", color="#f43f5e", duration_frames=45)
                )

                # Check if player health depleted to 0% -> GAME OVER!
                if not self.player.is_alive():
                    self.game_over = True
                    self.game_over_reason = "KIA - OPERATIVE ELIMINATED BY ENEMY FIRE"

            # 2. Check player contact with enemy's Bresenham circular hitbox
            contact = enemy.check_player_contact(self.player)

            if contact == "kill":
                if enemy.is_shielded:
                    # Stealth rear kill on shielded enemy
                    self.score += 100
                    self.collectibles.announcements.append(
                        FloatingText(enemy.x, enemy.y - 18.0, "STEALTH TAKEDOWN! +100", color="#38bdf8", duration_frames=70)
                    )
                else:
                    # Standard kill on non-shielded enemy
                    self.score += 50
                    self.collectibles.announcements.append(
                        FloatingText(enemy.x, enemy.y - 18.0, "ASSASSINATED! +50", color="#22c55e", duration_frames=60)
                    )

            elif contact == "shield_blocked":
                # Shield deflected frontal assault!
                self.collectibles.announcements.append(
                    FloatingText(enemy.x, enemy.y - 18.0, "SHIELD DEFLECTED!", color="#00e5ff", duration_frames=35)
                )
                # Deflect player slightly back
                push_dx = math.cos(enemy.angle) * 8.0
                push_dy = math.sin(enemy.angle) * 8.0
                self.player.move(push_dx, push_dy, self.map_engine)

        # Also check normal escape if all enemies cleared & exit door reached
        alive_enemies = sum(1 for e in self.enemies if e.is_alive)
        if alive_enemies == 0 and self.map_engine.exit_door and self.map_engine.exit_door.is_reached(self.player.x, self.player.y, self.player.radius):
            if not self.victory:
                self.victory = True
                self.score += 150

    def _render_glitch_timer(self):
        """
        Renders a huge 10-Second Countdown Timer in a 'Glitch' style font.
        Uses CGMath.translate for chromatic aberration offsets and jitter.
        """
        text = f"LOCKDOWN: {self.alarm_timer:05.2f}s"
        cx = self.canvas_width / 2.0
        cy = 44.0

        # Layer 1: Red chromatic aberration offset via CGMath.translate
        rx_jitter = random.uniform(-4.0, 4.0)
        ry_jitter = random.uniform(-1.5, 1.5)
        red_pos = CGMath.translate([(cx, cy)], rx_jitter, ry_jitter)[0]
        self.canvas.create_text(
            red_pos[0], red_pos[1],
            text=text, fill="#ff0055", font=("Consolas", 26, "bold"), tags="glitch_r"
        )

        # Layer 2: Cyan chromatic aberration offset via CGMath.translate
        cx_jitter = random.uniform(-4.0, 4.0)
        cy_jitter = random.uniform(-1.5, 1.5)
        cyan_pos = CGMath.translate([(cx, cy)], cx_jitter, cy_jitter)[0]
        self.canvas.create_text(
            cyan_pos[0], cyan_pos[1],
            text=text, fill="#00f0ff", font=("Consolas", 26, "bold"), tags="glitch_c"
        )

        # Layer 3: Yellow jitter layer via CGMath.translate
        yx_jitter = random.uniform(-2.0, 2.0)
        yy_jitter = random.uniform(-2.0, 2.0)
        yellow_pos = CGMath.translate([(cx, cy)], yx_jitter, yy_jitter)[0]
        self.canvas.create_text(
            yellow_pos[0], yellow_pos[1],
            text=text, fill="#facc15", font=("Consolas", 26, "bold"), tags="glitch_y"
        )

        # Layer 4: Crisp white core foreground layer
        wx_jitter = random.uniform(-0.8, 0.8)
        wy_jitter = random.uniform(-0.8, 0.8)
        white_pos = CGMath.translate([(cx, cy)], wx_jitter, wy_jitter)[0]
        self.canvas.create_text(
            white_pos[0], white_pos[1],
            text=text, fill="#ffffff", font=("Consolas", 26, "bold"), tags="glitch_w"
        )

        # Evacuate warning instruction below glitch timer
        sub_text = ">> EVACUATE TO EXIT DOOR BEFORE TIME EXPIRES << "
        sub_pos = CGMath.translate([(cx, cy + 28.0)], random.uniform(-1.5, 1.5), 0.0)[0]
        self.canvas.create_text(
            sub_pos[0], sub_pos[1],
            text=sub_text, fill="#ef4444", font=("Consolas", 10, "bold"), tags="glitch_sub"
        )

    def _render_replay_button(self, is_victory: bool = False):
        """Renders an interactive cyberpunk REPLAY button."""
        bx1, by1, bx2, by2 = self.replay_btn_bounds
        btn_outline = "#22c55e" if is_victory else "#ef4444"
        btn_text_color = "#ffffff"

        # Button Outer Glow
        self.canvas.create_rectangle(
            bx1 - 2, by1 - 2, bx2 + 2, by2 + 2,
            fill="", outline=btn_outline, width=1, tags="replay_btn_glow"
        )
        # Button Body
        self.canvas.create_rectangle(
            bx1, by1, bx2, by2,
            fill="#1e293b", outline=btn_outline, width=2, tags="replay_btn"
        )
        # Button Label
        self.canvas.create_text(
            (bx1 + bx2) / 2.0, (by1 + by2) / 2.0,
            text="[ REPLAY ]", fill=btn_text_color, font=("Consolas", 13, "bold"), tags="replay_btn_txt"
        )

    def render(self):
        """Full frame rendering on tkinter.Canvas."""
        self.canvas.delete("all")

        # 1. Emergency Siren Strobe when alarm is active
        if self.alarm_active and not (self.game_over or self.victory):
            if math.sin(self.alarm_flasher) > 0.0:
                self.canvas.create_rectangle(
                    0, 0, self.canvas_width, self.canvas_height,
                    fill="#3b0707", outline="", tags="alarm_strobe"
                )

        # 2. Map (Floor, 5px walls, crossed box crates, sliding doors, exit door)
        self.map_engine.render(self.canvas, alarm_active=self.alarm_active)

        # 3. Collectibles (Pulsing yellow coins via CGMath.scale, red plus MedKits)
        self.collectibles.render(self.canvas)

        # 4. Security Camera (Sweeping vision cone and corner mount)
        self.camera.render(self.canvas, alarm_active=self.alarm_active)

        # 5. Enemies (Vision cones, laser tracers, red triangles, semicircle shield)
        for enemy in self.enemies:
            enemy.render(self.canvas, show_hitbox=self.show_hitbox)

        # 6. Player (Green triangle with instant rotation and head vertex)
        if self.player.is_alive():
            self.player.render(self.canvas, show_hitbox=self.show_hitbox)
        else:
            # Defeated player marker
            self.canvas.create_oval(
                self.player.x - 10, self.player.y - 10,
                self.player.x + 10, self.player.y + 10,
                fill="#450a0a", outline="#991b1b", width=2, tags="player_dead"
            )
            self.canvas.create_text(
                self.player.x, self.player.y, text="KIA", fill="#f87171", font=("Consolas", 9, "bold"), tags="player_dead"
            )

        # 7. Glitch Countdown Timer (When alarm is active and game ongoing)
        if self.alarm_active and not (self.game_over or self.victory):
            self._render_glitch_timer()

        # 8. Game Over Screen Overlay
        if self.game_over:
            # Dark modal backdrop
            self.canvas.create_rectangle(
                160, 240, 820, 520,
                fill="#0b0f19", outline="#ef4444", width=3, tags="modal_bg"
            )
            # Glitch modal title
            self.canvas.create_text(
                490, 290, text="G A M E   O V E R",
                fill="#ef4444", font=("Consolas", 22, "bold"), tags="modal_title"
            )
            self.canvas.create_text(
                490, 340, text=self.game_over_reason,
                fill="#fca5a5", font=("Consolas", 12), tags="modal_reason"
            )
            self.canvas.create_text(
                490, 385, text=f"Final Score: {self.score}",
                fill="#facc15", font=("Consolas", 14, "bold"), tags="modal_score"
            )
            # Interactive Replay Button
            self._render_replay_button(is_victory=False)

        # 9. Victory Screen Overlay
        elif self.victory:
            self.canvas.create_rectangle(
                160, 240, 820, 520,
                fill="#0b0f19", outline="#22c55e", width=3, tags="modal_bg"
            )
            self.canvas.create_text(
                490, 290, text="M I S S I O N   S U C C E S S",
                fill="#22c55e", font=("Consolas", 22, "bold"), tags="modal_title"
            )
            self.canvas.create_text(
                490, 340, text="OPERATIVE ESCAPED EXTRACTION ZONE SAFELY",
                fill="#86efac", font=("Consolas", 12), tags="modal_reason"
            )
            self.canvas.create_text(
                490, 385, text=f"Total Score: {self.score}",
                fill="#facc15", font=("Consolas", 14, "bold"), tags="modal_score"
            )
            # Interactive Replay Button
            self._render_replay_button(is_victory=True)

        # 10. Update HUD Header Labels
        hp_pct = max(0, int((self.player.health / self.player.max_health) * 100))
        self.health_label.config(
            text=f"HP: {hp_pct}%",
            fg="#22c55e" if hp_pct > 50 else ("#eab308" if hp_pct > 25 else "#ef4444")
        )
        self.score_label.config(text=f"SCORE: {self.score}")
        alive_enemies = sum(1 for e in self.enemies if e.is_alive)
        self.enemy_label.config(
            text=f"Targets: {alive_enemies}/2",
            fg="#ef4444" if alive_enemies > 0 else "#22c55e"
        )
        self.items_label.config(
            text=f"Coins: {len(self.collectibles.coins)} | MedKits: {len(self.collectibles.health_kits)}"
        )

        if self.game_over:
            status_text = "FAILED"
            status_color = "#ef4444"
        elif self.victory:
            status_text = "ESCAPED"
            status_color = "#22c55e"
        elif self.alarm_active:
            status_text = f"LOCKDOWN ({self.alarm_timer:04.1f}s)"
            status_color = "#f43f5e"
        else:
            status_text = "SECURE"
            status_color = "#38bdf8"

        self.security_label.config(text=f"Status: {status_text}", fg=status_color)

    def update_loop(self):
        """Fixed timestep update loop (~60 FPS)."""
        # 1. Process player movement & instant rotation
        self._process_player_movement()

        # 2. Update sliding doors based on player proximity
        self.map_engine.update_doors(self.player.x, self.player.y)

        # 3. Update collectibles & check Bresenham hitbox overlap
        if not self.game_over and not self.victory:
            score_earned, _ = self.collectibles.update_and_collide(self.player)
            self.score += score_earned

        # 4. Update security camera and 10s glitch alarm countdown
        self._update_camera_and_alarm()

        # 5. Update enemies, vision cones, combat & takedowns
        self._update_enemies_and_combat()

        # 6. Render entire scene
        self.render()

        # 7. Schedule next frame (16 ms ~= 60 FPS)
        self.root.after(16, self.update_loop)


def main():
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
