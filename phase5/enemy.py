"""
Enemy Module (Phase 5 - Viewport Clipping)
- Guard & Shielded Enforcer entities
- Vision cones clipped using Sutherland-Hodgman algorithm
- Laser beams clipped using Cohen-Sutherland algorithm
"""

import math
from typing import List, Tuple, Optional
from cg_math import CGMath, Point, Points


class Enemy:
    def __init__(self, path: List[Point], is_shielded: bool = False, speed: float = 2.0):
        self.path = [tuple(p) for p in path]
        self.is_shielded = is_shielded
        self.speed = float(speed)

        self.x, self.y = self.path[0]
        self.current_wp_index = 1
        self.path_direction = 1

        self.radius = 15.0
        self.is_alive = True
        self.angle = 0.0

        self.damage_per_shot = 7.0 if self.is_shielded else 5.0
        self.shoot_cooldown_max = 35
        self.shoot_timer = 0
        self.is_alert = False
        self.laser_target: Optional[Point] = None
        self.laser_linger_frames = 0

        self.fov_angle = math.pi / 2.0
        self.cone_range = 165.0
        self.vision_polygon: Points = []

        self.local_triangle: Points = [
            (16.0, 0.0), (-12.0, -11.0), (-6.0, 0.0), (-12.0, 11.0)
        ]

        self.local_shield_arc: Points = []
        if self.is_shielded:
            shield_radius = 20.0
            num_arc_steps = 14
            for i in range(num_arc_steps + 1):
                ang = -math.pi / 2.0 + (math.pi / num_arc_steps) * i
                self.local_shield_arc.append((shield_radius * math.cos(ang), shield_radius * math.sin(ang)))

        self.hitbox_points: List[Tuple[int, int]] = []
        self._update_geometry()

    def _update_geometry(self):
        self.hitbox_points = CGMath.bresenham_circle(self.x, self.y, self.radius)
        head_world = CGMath.transform_point(
            CGMath.matmul_3x3(
                CGMath.translation_matrix(self.x, self.y),
                CGMath.rotation_matrix(self.angle)
            ),
            self.local_triangle[0]
        )
        self.vision_polygon = CGMath.create_cone_polygon(
            origin_x=head_world[0], origin_y=head_world[1],
            facing_angle=self.angle, fov_angle=self.fov_angle,
            length=self.cone_range, num_arc_steps=12
        )

    def _patrol_step(self):
        if len(self.path) < 2 or not self.is_alive:
            return

        target_x, target_y = self.path[self.current_wp_index]
        dx, dy = target_x - self.x, target_y - self.y
        dist = math.hypot(dx, dy)

        if dist <= self.speed:
            self.x, self.y = target_x, target_y
            next_idx = self.current_wp_index + self.path_direction
            if next_idx >= len(self.path):
                self.path_direction = -1
                self.current_wp_index = len(self.path) - 2
            elif next_idx < 0:
                self.path_direction = 1
                self.current_wp_index = 1
            else:
                self.current_wp_index = next_idx
            target_x, target_y = self.path[self.current_wp_index]
            dx, dy = target_x - self.x, target_y - self.y
            dist = math.hypot(dx, dy)

        if dist > 0.001:
            step_dx = (dx / dist) * self.speed
            step_dy = (dy / dist) * self.speed
            self.angle = math.atan2(step_dy, step_dx)
            translated = CGMath.translate([(self.x, self.y)], step_dx, step_dy)
            self.x, self.y = translated[0]

        self._update_geometry()

    def update(self, player) -> Optional[str]:
        if not self.is_alive:
            return None

        if self.laser_linger_frames > 0:
            self.laser_linger_frames -= 1
            if self.laser_linger_frames == 0:
                self.laser_target = None

        if self.shoot_timer > 0:
            self.shoot_timer -= 1

        self._patrol_step()

        self.is_alert = CGMath.point_in_polygon(player.x, player.y, self.vision_polygon) if player.is_alive() else False

        if self.is_alert and player.is_alive():
            if self.shoot_timer == 0:
                player.take_damage(self.damage_per_shot)
                self.shoot_timer = self.shoot_cooldown_max
                self.laser_target = (player.x, player.y)
                self.laser_linger_frames = 6
                return "shot_player"

        return None

    def check_player_contact(self, player) -> Optional[str]:
        if not self.is_alive or not player.is_alive():
            return None

        if CGMath.distance(self.x, self.y, player.x, player.y) > (self.radius + player.radius):
            return None

        if not self.is_shielded:
            self.is_alive = False
            return "kill"
        else:
            fx, fy = math.cos(self.angle), math.sin(self.angle)
            vx, vy = player.x - self.x, player.y - self.y
            if (fx * vx + fy * vy) <= 0.0:
                self.is_alive = False
                return "kill"
            else:
                return "shield_blocked"

    def render(self, canvas, camera, show_hitbox: bool = False):
        xmin, ymin, xmax, ymax = camera.get_viewport_screen_bounds()
        smx, smy = camera.world_to_screen_pt(self.x, self.y)

        if not self.is_alive:
            if xmin <= smx <= xmax and ymin <= smy <= ymax:
                canvas.create_oval(smx - 8, smy - 8, smx + 8, smy + 8, fill="#3f1212", outline="#7f1d1d", tags="enemy_dead")
                canvas.create_text(smx, smy, text="X", fill="#ef4444", font=("Consolas", 10, "bold"), tags="enemy_dead")
            return

        # 1. Vision Cone (Sutherland-Hodgman Polygon Clipping)
        cone_screen = camera.world_to_screen(self.vision_polygon)
        clipped_cone = CGMath.clip_polygon_aabb(cone_screen, xmin, ymin, xmax, ymax)
        if len(clipped_cone) >= 3:
            cone_fill = "#ef4444" if self.is_alert else "#eab308"
            cone_outline = "#f87171" if self.is_alert else "#fde047"
            canvas.create_polygon(
                CGMath.flatten(clipped_cone), fill=cone_fill, outline=cone_outline, width=1, stipple="gray25", tags="enemy_vision"
            )

        # 2. Laser Shot Beam (Cohen-Sutherland Line Clipping)
        if self.laser_target is not None:
            lt_screen = camera.world_to_screen([(self.x, self.y), self.laser_target])
            c_laser = CGMath.clip_line_cohen_sutherland(lt_screen[0][0], lt_screen[0][1], lt_screen[1][0], lt_screen[1][1], xmin, ymin, xmax, ymax)
            if c_laser:
                canvas.create_line(c_laser[0], c_laser[1], c_laser[2], c_laser[3], fill="#f43f5e", width=4, tags="enemy_laser")
                canvas.create_line(c_laser[0], c_laser[1], c_laser[2], c_laser[3], fill="#ffffff", width=1.5, tags="enemy_laser_core")

        # 3. Red Body Triangle
        rotated_body = CGMath.rotate(self.local_triangle, self.angle, 0.0, 0.0)
        world_body = CGMath.translate(rotated_body, self.x, self.y)
        screen_body = camera.world_to_screen(world_body)
        clipped_body = CGMath.clip_polygon_aabb(screen_body, xmin, ymin, xmax, ymax)

        if len(clipped_body) >= 3:
            canvas.create_polygon(CGMath.flatten(clipped_body), fill="#dc2626", outline="#f87171", width=2, joinstyle="round", tags="enemy_body")

        # Shield
        if self.is_shielded and len(self.local_shield_arc) > 0:
            rotated_shield = CGMath.rotate(self.local_shield_arc, self.angle, 0.0, 0.0)
            world_shield = CGMath.translate(rotated_shield, self.x, self.y)
            screen_shield = camera.world_to_screen(world_shield)
            flat_shield = CGMath.flatten(screen_shield)
            canvas.create_line(flat_shield, fill="#00e5ff", width=4, capstyle="round", tags="enemy_shield")