"""
Collectibles Module (Phase 5 - Viewport Polygon Clipping)
- Coins (pulsing with CGMath.scale)
- HealthKits (+)
- Floating announcements
- All items clipped to active Camera Viewport window
"""

import math
from typing import List, Tuple
from cg_math import CGMath, Point, Points


class FloatingText:
    def __init__(self, x: float, y: float, text: str, color: str = "#facc15", duration_frames: int = 60):
        self.x = float(x)
        self.y = float(y)
        self.text = text
        self.color = color
        self.life = duration_frames
        self.vy = -1.4

    def update(self) -> bool:
        self.y += self.vy
        self.life -= 1
        return self.life > 0

    def render(self, canvas, camera):
        xmin, ymin, xmax, ymax = camera.get_viewport_screen_bounds()
        sx, sy = camera.world_to_screen_pt(self.x, self.y)
        if xmin <= sx <= xmax and ymin <= sy <= ymax:
            font_size = 11 if self.life > 15 else 9
            canvas.create_text(sx + 1, sy + 1, text=self.text, fill="#000000", font=("Consolas", font_size, "bold"))
            canvas.create_text(sx, sy, text=self.text, fill=self.color, font=("Consolas", font_size, "bold"))


class Coin:
    def __init__(self, x: float, y: float, radius: float = 10.0):
        self.x = float(x)
        self.y = float(y)
        self.base_radius = float(radius)
        self.pulse_phase = 0.0
        self.pulse_speed = 0.08

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
        if CGMath.distance(self.x, self.y, player_x, player_y) > (player_r + self.base_radius * self.current_scale + 4.0):
            return False
        coin_hit_r_sq = (self.base_radius * self.current_scale) ** 2
        for bx, by in player_hitbox_pts:
            if ((bx - self.x) ** 2 + (by - self.y) ** 2) <= coin_hit_r_sq:
                return True
        return CGMath.distance(self.x, self.y, player_x, player_y) <= (player_r + self.base_radius)

    def render(self, canvas, camera):
        xmin, ymin, xmax, ymax = camera.get_viewport_screen_bounds()
        body_screen = camera.world_to_screen(self.current_polygon)
        clipped_body = CGMath.clip_polygon_aabb(body_screen, xmin, ymin, xmax, ymax)

        if len(clipped_body) >= 3:
            canvas.create_polygon(CGMath.flatten(clipped_body), fill="#eab308", outline="#fef08a", width=2, tags="coin")


class HealthKit:
    def __init__(self, x: float, y: float, size: float = 20.0):
        self.x, self.y = float(x), float(y)
        self.size = float(size)
        self.radius = self.size / 2.0
        self.pulse_phase = 0.0
        self.pulse_speed = 0.05

        hw, hs = 2.5, 7.0
        self.base_plus: Points = [
            (self.x - hw, self.y - hs), (self.x + hw, self.y - hs),
            (self.x + hw, self.y - hw), (self.x + hs, self.y - hw),
            (self.x + hs, self.y + hw), (self.x + hw, self.y + hw),
            (self.x + hw, self.y + hs), (self.x - hw, self.y + hs),
            (self.x - hw, self.y + hw), (self.x - hs, self.y + hw),
            (self.x - hs, self.y - hw), (self.x - hw, self.y - hw)
        ]
        s = self.radius
        self.base_box: Points = [(self.x - s, self.y - s), (self.x + s, self.y - s), (self.x + s, self.y + s), (self.x - s, self.y + s)]

        self.current_plus = list(self.base_plus)
        self.current_box = list(self.base_box)
        self.current_scale = 1.0

    def update(self):
        self.pulse_phase += self.pulse_speed
        self.current_scale = 1.0 + 0.10 * math.sin(self.pulse_phase)
        self.current_plus = CGMath.scale(self.base_plus, self.current_scale, self.x, self.y)
        self.current_box = CGMath.scale(self.base_box, self.current_scale, self.x, self.y)

    def collides_with_player_bresenham(self, player_hitbox_pts: List[Tuple[int, int]], player_x: float, player_y: float, player_r: float) -> bool:
        if CGMath.distance(self.x, self.y, player_x, player_y) > (player_r + self.radius * self.current_scale + 4.0):
            return False
        kit_r_sq = (self.radius * self.current_scale) ** 2
        for bx, by in player_hitbox_pts:
            if ((bx - self.x) ** 2 + (by - self.y) ** 2) <= kit_r_sq: return True
        return CGMath.distance(self.x, self.y, player_x, player_y) <= (player_r + self.radius)

    def render(self, canvas, camera):
        xmin, ymin, xmax, ymax = camera.get_viewport_screen_bounds()
        box_screen = camera.world_to_screen(self.current_box)
        clipped_box = CGMath.clip_polygon_aabb(box_screen, xmin, ymin, xmax, ymax)

        if len(clipped_box) >= 3:
            canvas.create_polygon(CGMath.flatten(clipped_box), fill="#f8fafc", outline="#cbd5e1", width=1.5, tags="medkit_box")

        plus_screen = camera.world_to_screen(self.current_plus)
        clipped_plus = CGMath.clip_polygon_aabb(plus_screen, xmin, ymin, xmax, ymax)
        if len(clipped_plus) >= 3:
            canvas.create_polygon(CGMath.flatten(clipped_plus), fill="#ef4444", outline="#dc2626", width=1, tags="medkit_plus")


class CollectibleManager:
    def __init__(self):
        self.coins: List[Coin] = []
        self.health_kits: List[HealthKit] = []
        self.announcements: List[FloatingText] = []

    def populate_map(self, map_engine):
        ox, oy = map_engine.ox, map_engine.oy
        wt, pw, bs = map_engine.WALL_THICKNESS, map_engine.PASSAGE_WIDTH, map_engine.BOX_SIZE

        col_centers = [ox + wt + pw / 2.0, ox + wt + pw + bs + pw / 2.0, ox + wt + 2 * pw + 2 * bs + pw / 2.0, ox + wt + 3 * pw + 3 * bs + pw / 2.0]
        row_centers = [oy + wt + pw / 2.0, oy + wt + pw + bs + pw / 2.0, oy + wt + 2 * pw + 2 * bs + pw / 2.0]
        box_col_centers = [ox + wt + pw + bs / 2.0, ox + wt + 2 * pw + 1.5 * bs, ox + wt + 3 * pw + 2.5 * bs]

        coin_positions = [
            (box_col_centers[0], row_centers[0]), (box_col_centers[1], row_centers[0]),
            (box_col_centers[2], row_centers[0]), (col_centers[3], row_centers[1]),
            (box_col_centers[0], row_centers[2]), (box_col_centers[1], row_centers[2]),
            (box_col_centers[2], row_centers[2]),
        ]
        for cx, cy in coin_positions:
            self.coins.append(Coin(cx, cy, radius=10.0))

        medkit_positions = [
            (col_centers[0], row_centers[1]), (col_centers[1], row_centers[1]), (col_centers[2], row_centers[1])
        ]
        for mx, my in medkit_positions:
            self.health_kits.append(HealthKit(mx, my, size=20.0))

    def update_and_collide(self, player) -> Tuple[int, float]:
        score_gained, hp_healed = 0, 0.0

        remaining_coins = []
        for coin in self.coins:
            coin.update()
            if coin.collides_with_player_bresenham(player.hitbox_points, player.x, player.y, player.radius):
                score_gained += 10
                self.announcements.append(FloatingText(coin.x, coin.y - 12.0, "+10 SCORE", color="#facc15"))
            else:
                remaining_coins.append(coin)
        self.coins = remaining_coins

        remaining_kits = []
        for kit in self.health_kits:
            kit.update()
            if kit.collides_with_player_bresenham(player.hitbox_points, player.x, player.y, player.radius):
                player.heal(15.0)
                hp_healed += 15.0
                self.announcements.append(FloatingText(kit.x, kit.y - 12.0, "+15% HP", color="#22c55e"))
            else:
                remaining_kits.append(kit)
        self.health_kits = remaining_kits

        self.announcements = [a for a in self.announcements if a.update()]
        return score_gained, hp_healed

    def render(self, canvas, camera):
        for coin in self.coins: coin.render(canvas, camera)
        for kit in self.health_kits: kit.render(canvas, camera)
        for announcement in self.announcements: announcement.render(canvas, camera)