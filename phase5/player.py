"""
Player Class (Phase 5 - Camera Tracking & Clipping)
- Green triangle (~30px footprint)
- Rotated using CGMath.rotate
- Positioned via CGMath.translate
- Clipped using CGMath.clip_polygon_aabb
"""

import math
from typing import List, Tuple
from cg_math import CGMath, Point, Points


class Player:
    def __init__(self, x: float, y: float, speed: float = 4.5):
        self.x = float(x)
        self.y = float(y)
        self.speed = float(speed)

        self.max_health = 100.0
        self.health = 100.0
        self.radius = 15.0
        self.angle = 0.0

        self.local_body_triangle: Points = [
            (16.0, 0.0),    # Head tip
            (-12.0, -11.0), # Rear-left
            (-6.0, 0.0),    # Notch
            (-12.0, 11.0)   # Rear-right
        ]

        self.local_inner_triangle: Points = [
            (11.0, 0.0),
            (-7.0, -6.0),
            (-3.0, 0.0),
            (-7.0, 6.0)
        ]

        self.hitbox_points: List[Tuple[int, int]] = []
        self._update_hitbox()

    def _update_hitbox(self):
        self.hitbox_points = CGMath.bresenham_circle(self.x, self.y, self.radius)

    def get_transformed_vertices(self, local_pts: Points) -> Points:
        rotated = CGMath.rotate(local_pts, self.angle, 0.0, 0.0)
        return CGMath.translate(rotated, self.x, self.y)

    def set_facing(self, dx: float, dy: float):
        if dx != 0.0 or dy != 0.0:
            self.angle = math.atan2(dy, dx)

    def move(self, dx: float, dy: float, map_engine) -> bool:
        if dx == 0.0 and dy == 0.0:
            return False

        self.set_facing(dx, dy)
        moved = False

        target_x = self.x + dx
        if not map_engine.is_blocked(target_x, self.y, self.radius):
            translated = CGMath.translate([(self.x, self.y)], dx, 0.0)
            self.x, self.y = translated[0]
            moved = True

        target_y = self.y + dy
        if not map_engine.is_blocked(self.x, target_y, self.radius):
            translated = CGMath.translate([(self.x, self.y)], 0.0, dy)
            self.x, self.y = translated[0]
            moved = True

        if moved:
            self._update_hitbox()

        return moved

    def take_damage(self, amount: float):
        self.health = max(0.0, self.health - amount)

    def heal(self, amount: float):
        self.health = min(self.max_health, self.health + amount)

    def is_alive(self) -> bool:
        return self.health > 0.0

    def render(self, canvas, camera, show_hitbox: bool = False):
        xmin, ymin, xmax, ymax = camera.get_viewport_screen_bounds()

        # Transform to World then to Camera Screen Space
        body_world = self.get_transformed_vertices(self.local_body_triangle)
        body_screen = camera.world_to_screen(body_world)

        # Sutherland-Hodgman Polygon Clipping
        clipped_body = CGMath.clip_polygon_aabb(body_screen, xmin, ymin, xmax, ymax)

        # Render shadow/aura
        sx, sy = camera.world_to_screen_pt(self.x, self.y)
        if xmin - 20 <= sx <= xmax + 20 and ymin - 20 <= sy <= ymax + 20:
            canvas.create_oval(
                sx - self.radius, sy - self.radius,
                sx + self.radius, sy + self.radius,
                fill="#062e20", outline="#059669", width=1, tags="player_aura"
            )

        # Outer Green Triangle Body (Clipped)
        if len(clipped_body) >= 3:
            canvas.create_polygon(
                CGMath.flatten(clipped_body),
                fill="#10b981", outline="#34d399", width=2, joinstyle="round", tags="player_body"
            )

        # Inner Accent Triangle (Clipped)
        inner_world = self.get_transformed_vertices(self.local_inner_triangle)
        inner_screen = camera.world_to_screen(inner_world)
        clipped_inner = CGMath.clip_polygon_aabb(inner_screen, xmin, ymin, xmax, ymax)
        if len(clipped_inner) >= 3:
            canvas.create_polygon(
                CGMath.flatten(clipped_inner),
                fill="#047857", outline="#6ee7b7", width=1, tags="player_core"
            )

        # Head Dot
        if len(body_screen) > 0:
            hx, hy = body_screen[0]
            if xmin <= hx <= xmax and ymin <= hy <= ymax:
                canvas.create_oval(
                    hx - 2.5, hy - 2.5, hx + 2.5, hy + 2.5,
                    fill="#ffffff", outline="#a7f3d0", width=1, tags="player_head"
                )

        # Optional Hitbox
        if show_hitbox:
            for hx, hy in self.hitbox_points[::3]:
                shx, shy = camera.world_to_screen_pt(hx, hy)
                if xmin <= shx <= xmax and ymin <= shy <= ymax:
                    canvas.create_rectangle(shx, shy, shx + 1, shy + 1, fill="#38bdf8", outline="", tags="player_hitbox")

        # Mini Health Bar above player
        bar_w, bar_h = 26.0, 3.5
        bx, by = sx - bar_w / 2.0, sy - self.radius - 8.0
        if xmin <= bx <= xmax and ymin <= by <= ymax:
            canvas.create_rectangle(bx, by, bx + bar_w, by + bar_h, fill="#1f2937", outline="#111827", width=1, tags="player_hp_bg")
            hp_pct = max(0.0, min(1.0, self.health / self.max_health))
            hp_color = "#22c55e" if hp_pct > 0.5 else ("#eab308" if hp_pct > 0.25 else "#ef4444")
            if hp_pct > 0:
                canvas.create_rectangle(bx, by, bx + bar_w * hp_pct, by + bar_h, fill=hp_color, outline="", tags="player_hp_fill")