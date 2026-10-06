import tkinter as tk
import math
import random
from typing import Set, List
from cg_math import CGMath
from map_engine import MapEngine
from player import Player
from collectibles import CollectibleManager, FloatingText
from enemy import Enemy
from security_camera import SecurityCamera

class GameApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SHADOW HUNT - Grayscale Wireframe Edition")
        self.root.geometry("980x820")
        self.root.resizable(False, False)
        
        # STRICT GRAYSCALE BACKGROUNDS
        self.root.configure(bg="#000000")

        self.score, self.show_hitbox, self.game_over, self.victory, self.game_over_reason = 0, False, False, False, ""
        self.alarm_active, self.alarm_timer, self.alarm_flasher = False, 10.0, 0.0
        self.replay_btn_bounds = (400, 440, 580, 490)

        self.header_frame = tk.Frame(root, bg="#111111", height=52)
        self.header_frame.pack(fill=tk.X, side=tk.TOP)
        self.title_label = tk.Label(self.header_frame, text="SHADOW HUNT", font=("Consolas", 14, "bold"), fg="#FFFFFF", bg="#111111")
        self.title_label.pack(side=tk.LEFT, padx=16, pady=8)
        self.health_label = tk.Label(self.header_frame, text="HP: 100%", font=("Consolas", 11, "bold"), fg="#CCCCCC", bg="#111111")
        self.health_label.pack(side=tk.LEFT, padx=10, pady=8)
        self.score_label = tk.Label(self.header_frame, text="SCORE: 0", font=("Consolas", 12, "bold"), fg="#FFFFFF", bg="#111111")
        self.score_label.pack(side=tk.LEFT, padx=12, pady=8)
        self.enemy_label = tk.Label(self.header_frame, text="Targets: 2/2", font=("Consolas", 10, "bold"), fg="#AAAAAA", bg="#111111")
        self.enemy_label.pack(side=tk.LEFT, padx=10, pady=8)
        self.items_label = tk.Label(self.header_frame, text="Coins: 7 | MedKits: 3", font=("Consolas", 10), fg="#777777", bg="#111111")
        self.items_label.pack(side=tk.LEFT, padx=10, pady=8)
        self.security_label = tk.Label(self.header_frame, text="Status: SECURE", font=("Consolas", 10, "bold"), fg="#DDDDDD", bg="#111111")
        self.security_label.pack(side=tk.RIGHT, padx=16, pady=8)

        self.canvas_width, self.canvas_height = 980, 710
        self.canvas = tk.Canvas(root, width=self.canvas_width, height=self.canvas_height, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.origin_x, self.origin_y = (self.canvas_width - 770) / 2.0, (self.canvas_height - 550) / 2.0
        self.keys_pressed: Set[str] = set()

        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        self.footer_label = tk.Label(root, text="Controls: [WASD] Move | [H] Hitbox | [R] Restart | Wireframe Render Mode Active", font=("Consolas", 9), fg="#555555", bg="#000000")
        self.footer_label.pack(side=tk.BOTTOM, pady=4)

        self._reset_game()
        self.update_loop()

    def _reset_game(self):
        self.score, self.game_over, self.victory, self.alarm_active, self.alarm_timer = 0, False, False, False, 10.0
        self.map_engine = MapEngine(origin_x=self.origin_x, origin_y=self.origin_y)
        self.player = Player(self.origin_x + 55.0, self.origin_y + 55.0, speed=4.5)
        self.collectibles = CollectibleManager()
        self.collectibles.populate_map(self.map_engine)
        
        self.enemies: List[Enemy] = []
        # CORRECTION: Replaced absolute 575.0/355.0 with relative 495.0/275.0 offsets from origin_y
        self.enemies.append(Enemy([(self.origin_x + 160.0, self.origin_y + 495.0), (self.origin_x + 610.0, self.origin_y + 495.0)], is_shielded=False, speed=2.0))
        self.enemies.append(Enemy([(self.origin_x + 220.0, self.origin_y + 275.0), (self.origin_x + 550.0, self.origin_y + 275.0)], is_shielded=True, speed=1.8))
        self.camera = SecurityCamera(self.origin_x + self.map_engine.room_w - 18.0, self.origin_y + 18.0, 2.45, 0.65, 0.022)

    def _on_key_press(self, event):
        key = event.keysym.lower()
        self.keys_pressed.add(key)
        if key == "h": self.show_hitbox = not self.show_hitbox
        elif key == "r": self._reset_game()

    def _on_key_release(self, event): self.keys_pressed.discard(event.keysym.lower())

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
            if dx != 0.0 and dy != 0.0: dx, dy = dx * 0.7071, dy * 0.7071
            self.player.move(dx * self.player.speed, dy * self.player.speed, self.map_engine)

    def _update_camera_and_alarm(self):
        if self.game_over or self.victory: return
        if self.camera.update(self.player) and not self.alarm_active:
            self.alarm_active = True
            self.collectibles.announcements.append(FloatingText(self.player.x, self.player.y - 20.0, "ALARM TRIGGERED!"))
        if self.alarm_active:
            self.alarm_flasher += 0.15
            self.alarm_timer = max(0.0, self.alarm_timer - (1.0 / 60.0))
            if self.map_engine.exit_door and self.map_engine.exit_door.is_reached(self.player.x, self.player.y, self.player.radius):
                self.victory, self.score = True, self.score + 200
            elif self.alarm_timer <= 0.0:
                self.game_over, self.game_over_reason = True, "LOCKDOWN SEALED - 10s EVACUATION FAILED"

    def _update_enemies_and_combat(self):
        if self.game_over or self.victory: return
        for enemy in self.enemies:
            if not enemy.is_alive: continue
            if enemy.update(self.player) == "shot_player" and not self.player.is_alive():
                self.game_over, self.game_over_reason = True, "KIA - OPERATIVE ELIMINATED BY ENEMY FIRE"
            contact = enemy.check_player_contact(self.player)
            if contact == "kill": self.score += 100 if enemy.is_shielded else 50
            elif contact == "shield_blocked": self.player.move(math.cos(enemy.angle) * 8.0, math.sin(enemy.angle) * 8.0, self.map_engine)
        if sum(1 for e in self.enemies if e.is_alive) == 0 and self.map_engine.exit_door and self.map_engine.exit_door.is_reached(self.player.x, self.player.y, self.player.radius):
            if not self.victory: self.victory, self.score = True, self.score + 150

    def _render_glitch_timer(self):
        text = f"LOCKDOWN: {self.alarm_timer:05.2f}s"
        cx, cy = self.canvas_width / 2.0, 44.0
        self.canvas.create_text(CGMath.translate([(cx, cy)], random.uniform(-4.0, 4.0), random.uniform(-1.5, 1.5))[0][0], cy, text=text, fill="#777777", font=("Consolas", 26, "bold"))
        self.canvas.create_text(CGMath.translate([(cx, cy)], random.uniform(-4.0, 4.0), random.uniform(-1.5, 1.5))[0][0], cy, text=text, fill="#AAAAAA", font=("Consolas", 26, "bold"))
        self.canvas.create_text(cx, cy, text=text, fill="#FFFFFF", font=("Consolas", 26, "bold"))

    def render(self):
        self.canvas.delete("all")
        if self.alarm_active and not (self.game_over or self.victory) and math.sin(self.alarm_flasher) > 0.0:
            self.canvas.create_line(0, 0, self.canvas_width, 0, fill="#FFFFFF", width=3)
            self.canvas.create_line(0, self.canvas_height, self.canvas_width, self.canvas_height, fill="#FFFFFF", width=3)

        self.map_engine.render(self.canvas, alarm_active=self.alarm_active)
        self.collectibles.render(self.canvas)
        self.camera.render(self.canvas, alarm_active=self.alarm_active)
        
        for enemy in self.enemies: enemy.render(self.canvas, show_hitbox=self.show_hitbox)
        
        if self.player.is_alive(): self.player.render(self.canvas, show_hitbox=self.show_hitbox)
        else:
            self.canvas.create_line(self.player.x - 10, self.player.y - 10, self.player.x + 10, self.player.y + 10, fill="#AAAAAA", width=2)
            self.canvas.create_line(self.player.x - 10, self.player.y + 10, self.player.x + 10, self.player.y - 10, fill="#AAAAAA", width=2)
            
        if self.alarm_active and not (self.game_over or self.victory): self._render_glitch_timer()
        
        if self.game_over or self.victory:
            bx1, by1, bx2, by2 = self.replay_btn_bounds
            title = "M I S S I O N   S U C C E S S" if self.victory else "G A M E   O V E R"
            
            self.canvas.create_line(160, 240, 820, 240, fill="#FFFFFF", width=2)
            self.canvas.create_line(820, 240, 820, 520, fill="#FFFFFF", width=2)
            self.canvas.create_line(820, 520, 160, 520, fill="#FFFFFF", width=2)
            self.canvas.create_line(160, 520, 160, 240, fill="#FFFFFF", width=2)
            self.canvas.create_text(490, 290, text=title, fill="#FFFFFF", font=("Consolas", 22, "bold"))
            
            self.canvas.create_line(bx1, by1, bx2, by1, fill="#FFFFFF", width=2)
            self.canvas.create_line(bx2, by1, bx2, by2, fill="#FFFFFF", width=2)
            self.canvas.create_line(bx2, by2, bx1, by2, fill="#FFFFFF", width=2)
            self.canvas.create_line(bx1, by2, bx1, by1, fill="#FFFFFF", width=2)
            self.canvas.create_text((bx1 + bx2) / 2.0, (by1 + by2) / 2.0, text="[ REPLAY ]", fill="#FFFFFF", font=("Consolas", 13, "bold"))
            
        self.health_label.config(text=f"HP: {max(0, int((self.player.health / self.player.max_health) * 100))}%")
        self.score_label.config(text=f"SCORE: {self.score}")
        self.enemy_label.config(text=f"Targets: {sum(1 for e in self.enemies if e.is_alive)}/2")

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

if __name__ == "__main__":
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()