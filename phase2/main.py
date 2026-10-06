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
        self.root.title("SHADOW HUNT - Grayscale Static Wireframe")
        self.root.geometry("980x820")
        self.root.resizable(False, False)
        
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
        self.security_label = tk.Label(self.header_frame, text="Status: STATIC", font=("Consolas", 10, "bold"), fg="#DDDDDD", bg="#111111")
        self.security_label.pack(side=tk.RIGHT, padx=16, pady=8)

        self.canvas_width, self.canvas_height = 980, 710
        self.canvas = tk.Canvas(root, width=self.canvas_width, height=self.canvas_height, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.origin_x, self.origin_y = (self.canvas_width - 770) / 2.0, (self.canvas_height - 550) / 2.0
        self.keys_pressed: Set[str] = set()

        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        self.footer_label = tk.Label(root, text="Controls: [H] Hitbox | [R] Restart | Static Wireframe Mode Active (Translation Disabled)", font=("Consolas", 9), fg="#555555", bg="#000000")
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
        # PLAYER MOVEMENT DISABLED TO KEEP EVERYTHING STATIC
        pass

    def _update_camera_and_alarm(self):
        # CAMERA SWEEP DISABLED TO KEEP EVERYTHING STATIC
        pass

    def _update_enemies_and_combat(self):
        # ENEMY PATROLS AND COMBAT DISABLED TO KEEP EVERYTHING STATIC
        pass

    def _render_glitch_timer(self):
        text = f"LOCKDOWN: {self.alarm_timer:05.2f}s"
        cx, cy = self.canvas_width / 2.0, 44.0
        
        # GLITCH TRANSLATION/JITTER OFFSET DISABLED
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
        # Update handlers have been bypassed above to ensure a perfectly static scene
        self.render()
        self.root.after(16, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()