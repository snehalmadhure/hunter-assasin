import math
from typing import List, Tuple, Optional
from cg_math import CGMath, Point, Points

def _draw_wireframe(canvas, points: Points, color: str, width: int = 1, tags: str = ""):
    n = len(points)
    for i in range(n):
        p1, p2 = points[i], points[(i + 1) % n]
        canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=color, width=width, tags=tags)

class Enemy:
    def __init__(self, path: List[Point], is_shielded: bool = False, speed: float = 2.0):
        self.path = [tuple(p) for p in path]
        self.is_shielded, self.speed, self.radius, self.is_alive, self.angle = is_shielded, float(speed), 15.0, True, 0.0
        self.x, self.y = self.path[0]
        self.current_wp_index, self.path_direction = 1, 1
        self.damage_per_shot, self.shoot_cooldown_max, self.shoot_timer = (7.0 if self.is_shielded else 5.0), 35, 0
        self.is_alert, self.laser_target, self.laser_linger_frames = False, None, 0
        self.fov_angle, self.cone_range, self.vision_polygon = math.pi / 2.0, 165.0, []
        self.local_triangle: Points = [(16.0, 0.0), (-12.0, -11.0), (-6.0, 0.0), (-12.0, 11.0)]
        self.local_shield_arc: Points = []
        if self.is_shielded:
            shield_radius = 20.0
            num_arc_steps = 14
            for i in range(num_arc_steps + 1):
                ang = -math.pi / 2.0 + (math.pi / num_arc_steps) * i
                self.local_shield_arc.append((shield_radius * math.cos(ang), shield_radius * math.sin(ang)))
        self.hitbox_points: List[Tuple[int, int]] = []
        
        # Determine static facing angle based on initial path vector
        if len(self.path) > 1:
            dx = self.path[1][0] - self.path[0][0]
            dy = self.path[1][1] - self.path[0][1]
            self.angle = math.atan2(dy, dx)
            
        self._update_geometry()

    def _update_geometry(self):
        self.hitbox_points = CGMath.bresenham_circle(self.x, self.y, self.radius)
        head_world = CGMath.transform_point(CGMath.matmul_3x3(CGMath.translation_matrix(self.x, self.y), CGMath.rotation_matrix(self.angle)), self.local_triangle[0])
        self.vision_polygon = CGMath.create_cone_polygon(head_world[0], head_world[1], self.angle, self.fov_angle, self.cone_range, 12)

    def _patrol_step(self):
        # ENEMY TRANSLATION AND PATROL MOVEMENT DISABLED
        pass

    def update(self, player) -> Optional[str]:
        if not self.is_alive: return None
        if self.laser_linger_frames > 0:
            self.laser_linger_frames -= 1
            if self.laser_linger_frames == 0: self.laser_target = None
        if self.shoot_timer > 0: self.shoot_timer -= 1
        
        self._patrol_step() # (Disabled internally)
        
        self.is_alert = CGMath.point_in_polygon(player.x, player.y, self.vision_polygon) if player.is_alive() else False
        if self.is_alert and player.is_alive() and self.shoot_timer == 0:
            player.take_damage(self.damage_per_shot)
            self.shoot_timer, self.laser_target, self.laser_linger_frames = self.shoot_cooldown_max, (player.x, player.y), 6
            return "shot_player"
        return None

    def check_player_contact(self, player) -> Optional[str]:
        if not self.is_alive or not player.is_alive() or CGMath.distance(self.x, self.y, player.x, player.y) > (self.radius + player.radius): return None
        if not self.is_shielded:
            self.is_alive = False
            return "kill"
        dot = math.cos(self.angle) * (player.x - self.x) + math.sin(self.angle) * (player.y - self.y)
        if dot <= 0.0:
            self.is_alive = False
            return "kill"
        return "shield_blocked"

    def render(self, canvas, show_hitbox: bool = False):
        if not self.is_alive:
            canvas.create_line(self.x - 8, self.y - 8, self.x + 8, self.y + 8, fill="#777777", width=2)
            canvas.create_line(self.x - 8, self.y + 8, self.x + 8, self.y - 8, fill="#777777", width=2)
            return

        cone_outline = "#FFFFFF" if self.is_alert else "#666666"
        _draw_wireframe(canvas, self.vision_polygon, cone_outline, 1, "enemy_vision")

        if self.laser_target:
            canvas.create_line(self.x, self.y, self.laser_target[0], self.laser_target[1], fill="#FFFFFF", width=2, tags="enemy_laser")

        if show_hitbox:
            for hx, hy in self.hitbox_points[::4]:
                canvas.create_line(hx, hy, hx + 1, hy + 1, fill="#999999", tags="enemy_hitbox")

        world_body = CGMath.translate(CGMath.rotate(self.local_triangle, self.angle, 0.0, 0.0), self.x, self.y)
        _draw_wireframe(canvas, world_body, "#CCCCCC", 2, "enemy_body")

        if self.is_shielded and len(self.local_shield_arc) > 0:
            shield_pts = CGMath.translate(CGMath.rotate(self.local_shield_arc, self.angle, 0.0, 0.0), self.x, self.y)
            for i in range(len(shield_pts) - 1):
                canvas.create_line(shield_pts[i][0], shield_pts[i][1], shield_pts[i+1][0], shield_pts[i+1][1], fill="#FFFFFF", width=2, tags="enemy_shield")

        canvas.create_text(self.x, self.y - 20, text=("SHIELDED" if self.is_shielded else "GUARD"), fill="#AAAAAA", font=("Consolas", 7, "bold"))