import math
from typing import List, Tuple
from cg_math import CGMath, Point, Points

def _draw_wireframe(canvas, points: Points, color: str, width: int = 1, tags: str = ""):
    n = len(points)
    for i in range(n):
        p1, p2 = points[i], points[(i + 1) % n]
        canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=color, width=width, tags=tags)

class Player:
    def __init__(self, x: float, y: float, speed: float = 4.5):
        self.x, self.y, self.speed = float(x), float(y), float(speed)
        self.max_health, self.health, self.radius, self.angle = 100.0, 100.0, 15.0, 0.0
        self.local_body_triangle: Points = [(16.0, 0.0), (-12.0, -11.0), (-6.0, 0.0), (-12.0, 11.0)]
        self.local_inner_triangle: Points = [(11.0, 0.0), (-7.0, -6.0), (-3.0, 0.0), (-7.0, 6.0)]
        self.hitbox_points: List[Tuple[int, int]] = []
        self._update_hitbox()

    def _update_hitbox(self):
        self.hitbox_points = CGMath.bresenham_circle(self.x, self.y, self.radius)

    def get_transformed_vertices(self, local_pts: Points) -> Points:
        return CGMath.translate(CGMath.rotate(local_pts, self.angle, 0.0, 0.0), self.x, self.y)

    def set_facing(self, dx: float, dy: float):
        if dx != 0.0 or dy != 0.0: self.angle = math.atan2(dy, dx)

    def move(self, dx: float, dy: float, map_engine) -> bool:
        if dx == 0.0 and dy == 0.0: return False
        self.set_facing(dx, dy)
        moved = False
        if not map_engine.is_blocked(self.x + dx, self.y, self.radius):
            self.x, self.y = CGMath.translate([(self.x, self.y)], dx, 0.0)[0]
            moved = True
        if not map_engine.is_blocked(self.x, self.y + dy, self.radius):
            self.x, self.y = CGMath.translate([(self.x, self.y)], 0.0, dy)[0]
            moved = True
        if moved: self._update_hitbox()
        return moved

    def take_damage(self, amount: float):
        self.health = max(0.0, self.health - amount)

    def heal(self, amount: float):
        self.health = min(self.max_health, self.health + amount)

    def is_alive(self) -> bool:
        return self.health > 0.0

    def render(self, canvas, show_hitbox: bool = False):
        body_world = self.get_transformed_vertices(self.local_body_triangle)
        inner_world = self.get_transformed_vertices(self.local_inner_triangle)

        if show_hitbox:
            for hx, hy in self.hitbox_points[::4]:
                canvas.create_line(hx, hy, hx + 1, hy + 1, fill="#777777", tags="player_hitbox")

        _draw_wireframe(canvas, body_world, "#FFFFFF", 2, "player_body")
        _draw_wireframe(canvas, inner_world, "#AAAAAA", 1, "player_core")

        # Head indicator crosshair
        hw = body_world[0]
        canvas.create_line(hw[0]-2, hw[1], hw[0]+2, hw[1], fill="#FFFFFF", width=1)
        canvas.create_line(hw[0], hw[1]-2, hw[0], hw[1]+2, fill="#FFFFFF", width=1)

        # Health bar (Wireframe lines)
        bar_w, bar_h, bx, by = 26.0, 3.5, self.x - 13.0, self.y - self.radius - 8.0
        canvas.create_line(bx, by, bx + bar_w, by, fill="#555555")
        canvas.create_line(bx, by + bar_h, bx + bar_w, by + bar_h, fill="#555555")
        hp_pct = max(0.0, min(1.0, self.health / self.max_health))
        if hp_pct > 0:
            fill_len = bar_w * hp_pct
            canvas.create_line(bx, by + 1, bx + fill_len, by + 1, fill="#FFFFFF", width=2)