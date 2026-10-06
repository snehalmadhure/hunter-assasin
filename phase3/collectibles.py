import math
from typing import List, Tuple
from cg_math import CGMath, Point, Points

def _draw_wireframe(canvas, points: Points, color: str, width: int = 1, tags: str = ""):
    n = len(points)
    for i in range(n):
        p1, p2 = points[i], points[(i + 1) % n]
        canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=color, width=width, tags=tags)

class FloatingText:
    def __init__(self, x: float, y: float, text: str, duration_frames: int = 60):
        self.x, self.y, self.text = float(x), float(y), text
        self.life, self.max_life = duration_frames, duration_frames
        self.vy = -1.4

    def update(self) -> bool:
        self.y += self.vy
        self.life -= 1
        return self.life > 0

    def render(self, canvas):
        font_size = 11 if self.life > 15 else 9
        canvas.create_text(self.x, self.y, text=self.text, fill="#FFFFFF", font=("Consolas", font_size, "bold"), tags="floating_text")

class Coin:
    def __init__(self, x: float, y: float, radius: float = 10.0):
        self.x, self.y, self.base_radius = float(x), float(y), float(radius)
        self.pulse_phase, self.pulse_speed = 0.0, 0.08
        self.base_polygon: Points = []
        num_segments = 16
        for i in range(num_segments):
            ang = (2.0 * math.pi / num_segments) * i
            self.base_polygon.append((self.x + self.base_radius * math.cos(ang), self.y + self.base_radius * math.sin(ang)))
        self.current_polygon = list(self.base_polygon)
        self.current_aura_polygon = list(self.base_polygon)
        self.current_scale = 1.0

    def update(self):
        self.pulse_phase += self.pulse_speed
        self.current_scale = 1.0 + 0.18 * math.sin(self.pulse_phase)
        self.current_polygon = CGMath.scale(self.base_polygon, self.current_scale, self.x, self.y)
        self.current_aura_polygon = CGMath.scale(self.base_polygon, self.current_scale * 1.35, self.x, self.y)

    def collides_with_player_bresenham(self, player_hitbox_pts: List[Tuple[int, int]], player_x: float, player_y: float, player_r: float) -> bool:
        center_dist = CGMath.distance(self.x, self.y, player_x, player_y)
        if center_dist > (player_r + self.base_radius * self.current_scale + 4.0): return False
        coin_hit_r_sq = (self.base_radius * self.current_scale) ** 2
        for bx, by in player_hitbox_pts:
            if (bx - self.x) ** 2 + (by - self.y) ** 2 <= coin_hit_r_sq: return True
        return center_dist <= (player_r + self.base_radius)

    def render(self, canvas):
        _draw_wireframe(canvas, self.current_aura_polygon, "#777777", 1, "coin_glow")
        _draw_wireframe(canvas, self.current_polygon, "#DDDDDD", 2, "coin_body")

class HealthKit:
    def __init__(self, x: float, y: float, size: float = 20.0):
        self.x, self.y, self.radius = float(x), float(y), float(size) / 2.0
        self.pulse_phase, self.pulse_speed = 0.0, 0.05
        hw, hs, s = 2.5, 7.0, self.radius
        self.base_plus: Points = [
            (self.x - hw, self.y - hs), (self.x + hw, self.y - hs), (self.x + hw, self.y - hw),
            (self.x + hs, self.y - hw), (self.x + hs, self.y + hw), (self.x + hw, self.y + hw),
            (self.x + hw, self.y + hs), (self.x - hw, self.y + hs), (self.x - hw, self.y + hw),
            (self.x - hs, self.y + hw), (self.x - hs, self.y - hw), (self.x - hw, self.y - hw),
        ]
        self.base_box: Points = [(self.x - s, self.y - s), (self.x + s, self.y - s), (self.x + s, self.y + s), (self.x - s, self.y + s)]
        self.current_plus, self.current_box = list(self.base_plus), list(self.base_box)
        self.current_scale = 1.0

    def update(self):
        self.pulse_phase += self.pulse_speed
        self.current_scale = 1.0 + 0.10 * math.sin(self.pulse_phase)
        self.current_plus = CGMath.scale(self.base_plus, self.current_scale, self.x, self.y)
        self.current_box = CGMath.scale(self.base_box, self.current_scale, self.x, self.y)

    def collides_with_player_bresenham(self, player_hitbox_pts: List[Tuple[int, int]], player_x: float, player_y: float, player_r: float) -> bool:
        center_dist = CGMath.distance(self.x, self.y, player_x, player_y)
        if center_dist > (player_r + self.radius * self.current_scale + 4.0): return False
        kit_r_sq = (self.radius * self.current_scale) ** 2
        for bx, by in player_hitbox_pts:
            if (bx - self.x) ** 2 + (by - self.y) ** 2 <= kit_r_sq: return True
        return center_dist <= (player_r + self.radius)

    def render(self, canvas):
        _draw_wireframe(canvas, self.current_box, "#AAAAAA", 1, "medkit_box")
        _draw_wireframe(canvas, self.current_plus, "#FFFFFF", 2, "medkit_plus")

class CollectibleManager:
    def __init__(self):
        self.coins: List[Coin] = []
        self.health_kits: List[HealthKit] = []
        self.announcements: List[FloatingText] = []

    def populate_map(self, map_engine):
        ox, oy, wt, pw, bs = map_engine.ox, map_engine.oy, map_engine.WALL_THICKNESS, map_engine.PASSAGE_WIDTH, map_engine.BOX_SIZE
        col_centers = [ox + wt + pw / 2.0, ox + wt + pw + bs + pw / 2.0, ox + wt + 2 * pw + 2 * bs + pw / 2.0, ox + wt + 3 * pw + 3 * bs + pw / 2.0]
        row_centers = [oy + wt + pw / 2.0, oy + wt + pw + bs + pw / 2.0, oy + wt + 2 * pw + 2 * bs + pw / 2.0]
        box_col_centers = [ox + wt + pw + bs / 2.0, ox + wt + 2 * pw + 1.5 * bs, ox + wt + 3 * pw + 2.5 * bs]
        coin_positions = [
            (box_col_centers[0], row_centers[0]), (box_col_centers[1], row_centers[0]), (box_col_centers[2], row_centers[0]),
            (col_centers[3], row_centers[1]), (box_col_centers[0], row_centers[2]), (box_col_centers[1], row_centers[2]), (box_col_centers[2], row_centers[2])
        ]
        for cx, cy in coin_positions: self.coins.append(Coin(cx, cy, radius=10.0))
        medkit_positions = [(col_centers[0], row_centers[1]), (col_centers[1], row_centers[1]), (col_centers[2], row_centers[1])]
        for mx, my in medkit_positions: self.health_kits.append(HealthKit(mx, my, size=20.0))

    def update_and_collide(self, player) -> Tuple[int, float]:
        score_gained, hp_healed, remaining_coins, remaining_kits = 0, 0.0, [], []
        for coin in self.coins:
            coin.update()
            if coin.collides_with_player_bresenham(player.hitbox_points, player.x, player.y, player.radius):
                score_gained += 10
                self.announcements.append(FloatingText(coin.x, coin.y - 12.0, "+10 SCORE"))
            else: remaining_coins.append(coin)
        self.coins = remaining_coins

        for kit in self.health_kits:
            kit.update()
            if kit.collides_with_player_bresenham(player.hitbox_points, player.x, player.y, player.radius):
                hp_healed += 15.0
                player.heal(15.0)
                self.announcements.append(FloatingText(kit.x, kit.y - 12.0, "+15% HP"))
            else: remaining_kits.append(kit)
        self.health_kits = remaining_kits
        self.announcements = [a for a in self.announcements if a.update()]
        return score_gained, hp_healed

    def render(self, canvas):
        for coin in self.coins: coin.render(canvas)
        for kit in self.health_kits: kit.render(canvas)
        for announcement in self.announcements: announcement.render(canvas)