"""
Enemy Module for 2D Top-Down Stealth Game (Hunter Assassin inspired)
Strict Constraints:
- Red Triangles (~30px footprint) with top head vertex.
- Patrols back and forth on hardcoded paths using CGMath.translate and CGMath.rotate.
- Vision cone: 90° FOV (45° on both sides from center) projected from head vertex.
- Detection using CGMath.point_in_polygon.
- Non-Shielded Enemy: shoots player (5% damage per shot). Dies on contact from ANY direction.
- Shielded Enemy: has front semicircle shield. Shoots player (7% damage per shot).
  Dies ONLY if player touches its Bresenham circle from the rear (180° behind).
"""

import math
from typing import List, Tuple, Optional
from cg_math import CGMath, Point, Points


class Enemy:
    """
    Patrolling enemy entity with vision cone and directional hit detection.
    """

    def __init__(self, path: List[Point], is_shielded: bool = False, speed: float = 2.0):
        self.path = [tuple(p) for p in path]
        self.is_shielded = is_shielded
        self.speed = float(speed)

        # Initial position at first waypoint
        self.x, self.y = self.path[0]
        self.current_wp_index = 1
        self.path_direction = 1  # +1 moving forward along path, -1 moving backward

        # Dimensions & Attributes
        self.radius = 15.0  # 30px footprint
        self.is_alive = True
        self.angle = 0.0

        # Combat attributes
        self.damage_per_shot = 7.0 if self.is_shielded else 5.0
        self.shoot_cooldown_max = 35  # frames between shots (~0.58s at 60 FPS)
        self.shoot_timer = 0
        self.is_alert = False  # True when player is detected in vision cone
        self.laser_target: Optional[Point] = None
        self.laser_linger_frames = 0

        # Vision Cone parameters: 90° FOV (45° on both sides), length = 160px
        self.fov_angle = math.pi / 2.0  # 90 degrees
        self.cone_range = 165.0
        self.vision_polygon: Points = []

        # Local canonical triangle vertices (facing Right +X, head at (16, 0))
        self.local_triangle: Points = [
            (16.0, 0.0),    # Head vertex (top)
            (-12.0, -11.0), # Rear-left
            (-6.0, 0.0),    # Chevron inset
            (-12.0, 11.0)   # Rear-right
        ]

        # Local semicircle shield points in front of enemy (spanning -90° to +90°)
        self.local_shield_arc: Points = []
        if self.is_shielded:
            shield_radius = 20.0
            num_arc_steps = 14
            for i in range(num_arc_steps + 1):
                # Angle from -pi/2 to +pi/2 in local space (front 180 degrees)
                ang = -math.pi / 2.0 + (math.pi / num_arc_steps) * i
                sx = shield_radius * math.cos(ang)
                sy = shield_radius * math.sin(ang)
                self.local_shield_arc.append((sx, sy))

        # Bresenham circle points for hitbox
        self.hitbox_points: List[Tuple[int, int]] = []
        self._update_geometry()

    def _update_geometry(self):
        """Updates Bresenham circle and vision cone geometry based on current position and facing."""
        # Update Bresenham hitbox perimeter (decision parameter 1 - 2R)
        self.hitbox_points = CGMath.bresenham_circle(self.x, self.y, self.radius)

        # Head vertex in world coordinates
        head_world = CGMath.transform_point(
            CGMath.matmul_3x3(
                CGMath.translation_matrix(self.x, self.y),
                CGMath.rotation_matrix(self.angle)
            ),
            self.local_triangle[0]
        )

        # Construct vision cone originating from head vertex
        self.vision_polygon = CGMath.create_cone_polygon(
            origin_x=head_world[0],
            origin_y=head_world[1],
            facing_angle=self.angle,
            fov_angle=self.fov_angle,
            length=self.cone_range,
            num_arc_steps=12
        )

    def _patrol_step(self):
        """Moves along hardcoded waypoints using CGMath.translate and CGMath.rotate."""
        if len(self.path) < 2 or not self.is_alive:
            return

        target_x, target_y = self.path[self.current_wp_index]
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)

        if dist <= self.speed:
            # Reached waypoint, advance to next or reverse direction
            self.x = target_x
            self.y = target_y
            next_idx = self.current_wp_index + self.path_direction

            if next_idx >= len(self.path):
                self.path_direction = -1
                self.current_wp_index = len(self.path) - 2
            elif next_idx < 0:
                self.path_direction = 1
                self.current_wp_index = 1
            else:
                self.current_wp_index = next_idx

            # Recalculate target direction
            target_x, target_y = self.path[self.current_wp_index]
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)

        if dist > 0.001:
            step_dx = (dx / dist) * self.speed
            step_dy = (dy / dist) * self.speed

            # 1. Update facing direction angle
            self.angle = math.atan2(step_dy, step_dx)

            # 2. Position translation using CGMath.translate
            translated = CGMath.translate([(self.x, self.y)], step_dx, step_dy)
            self.x, self.y = translated[0]

        self._update_geometry()

    def update(self, player) -> Optional[str]:
        """
        Updates enemy patrol, vision cone detection, and combat action.
        Returns combat event string: 'shot_player', 'shield_deflect', or None.
        """
        if not self.is_alive:
            return None

        # Decrement laser linger effect
        if self.laser_linger_frames > 0:
            self.laser_linger_frames -= 1
            if self.laser_linger_frames == 0:
                self.laser_target = None

        if self.shoot_timer > 0:
            self.shoot_timer -= 1

        # 1. Patrol motion
        self._patrol_step()

        # 2. Vision Cone Check using CGMath.point_in_polygon
        if player.is_alive():
            self.is_alert = CGMath.point_in_polygon(player.x, player.y, self.vision_polygon)
        else:
            self.is_alert = False

        # 3. If player in cone, attack/shoot
        if self.is_alert and player.is_alive():
            if self.shoot_timer == 0:
                # Shoot player
                player.take_damage(self.damage_per_shot)
                self.shoot_timer = self.shoot_cooldown_max
                self.laser_target = (player.x, player.y)
                self.laser_linger_frames = 6
                return "shot_player"

        return None

    def check_player_contact(self, player) -> Optional[str]:
        """
        Evaluates physical contact against enemy's Bresenham circular hitbox.
        - Non-shielded: dies from contact in ANY direction.
        - Shielded: dies ONLY if contact is from the rear 180°. Contact in front is blocked by shield.
        Returns: 'kill' (enemy dies), 'shield_blocked', or None.
        """
        if not self.is_alive or not player.is_alive():
            return None

        # Overlap test: distance between centers <= (R_player + R_enemy)
        center_dist = CGMath.distance(self.x, self.y, player.x, player.y)
        if center_dist > (self.radius + player.radius):
            return None

        # Contact verified! Check shield defense
        if not self.is_shielded:
            # Non-shielded enemy dies from ANY direction
            self.is_alive = False
            return "kill"
        else:
            # Shielded enemy: Check if player approached from front (180°) or rear (180°)
            # Enemy facing vector: (cos(angle), sin(angle))
            fx = math.cos(self.angle)
            fy = math.sin(self.angle)

            # Vector from enemy center to player: (px - ex, py - ey)
            vx = player.x - self.x
            vy = player.y - self.y

            # Dot product:
            # > 0 => Player is in FRONT (within ±90° of facing direction) -> SHIELD BLOCKS!
            # <= 0 => Player is in REAR (behind enemy) -> STEALTH KILL!
            dot = fx * vx + fy * vy

            if dot <= 0.0:
                # Rear attack: Assassinated!
                self.is_alive = False
                return "kill"
            else:
                # Front attack: Blocked by shield
                return "shield_blocked"

    def render(self, canvas, show_hitbox: bool = False):
        """Renders vision cone, laser tracers, red triangle body, and shield."""
        if not self.is_alive:
            # Defeated enemy wreckage
            canvas.create_oval(
                self.x - 8, self.y - 8, self.x + 8, self.y + 8,
                fill="#3f1212", outline="#7f1d1d", width=1, tags="enemy_dead"
            )
            canvas.create_text(
                self.x, self.y, text="X", fill="#ef4444", font=("Consolas", 10, "bold"), tags="enemy_dead"
            )
            return

        # ---------------------------------------------------------------------
        # 1. Vision Cone (Translucent yellow when idle, warning red when alert)
        # ---------------------------------------------------------------------
        flat_cone = CGMath.flatten(self.vision_polygon)
        cone_fill = "#ef4444" if self.is_alert else "#eab308"
        cone_outline = "#f87171" if self.is_alert else "#fde047"
        canvas.create_polygon(
            flat_cone,
            fill=cone_fill,
            outline=cone_outline,
            width=1,
            stipple="gray25",  # Canvas transparency emulation
            tags="enemy_vision"
        )

        # ---------------------------------------------------------------------
        # 2. Laser Shot Beam
        # ---------------------------------------------------------------------
        if self.laser_target is not None:
            canvas.create_line(
                self.x, self.y, self.laser_target[0], self.laser_target[1],
                fill="#f43f5e", width=4, tags="enemy_laser"
            )
            canvas.create_line(
                self.x, self.y, self.laser_target[0], self.laser_target[1],
                fill="#ffffff", width=1.5, tags="enemy_laser_core"
            )

        # ---------------------------------------------------------------------
        # 3. Optional Bresenham Hitbox visualization
        # ---------------------------------------------------------------------
        if show_hitbox:
            for hx, hy in self.hitbox_points[::3]:
                canvas.create_rectangle(
                    hx, hy, hx + 1, hy + 1,
                    fill="#f87171", outline="", tags="enemy_hitbox"
                )

        # ---------------------------------------------------------------------
        # 4. Red Triangle Body (Rotated & Translated via CGMath)
        # ---------------------------------------------------------------------
        # Rotate local triangle around (0, 0) by self.angle, then translate to (self.x, self.y)
        rotated_body = CGMath.rotate(self.local_triangle, self.angle, 0.0, 0.0)
        world_body = CGMath.translate(rotated_body, self.x, self.y)
        flat_body = CGMath.flatten(world_body)

        # Base red triangle
        canvas.create_polygon(
            flat_body,
            fill="#dc2626",       # Red body
            outline="#f87171",    # Bright red rim
            width=2,
            joinstyle="round",
            tags="enemy_body"
        )

        # Head vertex indicator
        head_pt = world_body[0]
        canvas.create_oval(
            head_pt[0] - 2.5, head_pt[1] - 2.5,
            head_pt[0] + 2.5, head_pt[1] + 2.5,
            fill="#ffffff", outline="#fca5a5", width=1, tags="enemy_head"
        )

        # ---------------------------------------------------------------------
        # 5. Semicircle Front Shield (For Shielded Enemy)
        # ---------------------------------------------------------------------
        if self.is_shielded and len(self.local_shield_arc) > 0:
            # Rotate shield arc to current facing angle and translate to center
            rotated_shield = CGMath.rotate(self.local_shield_arc, self.angle, 0.0, 0.0)
            world_shield = CGMath.translate(rotated_shield, self.x, self.y)
            flat_shield = CGMath.flatten(world_shield)

            # Draw glowing energy arc in front of enemy
            canvas.create_line(
                flat_shield,
                fill="#00e5ff", width=5, capstyle="round", tags="enemy_shield_glow"
            )
            canvas.create_line(
                flat_shield,
                fill="#ffffff", width=2, capstyle="round", tags="enemy_shield_core"
            )

        # ---------------------------------------------------------------------
        # 6. Type Indicator Label
        # ---------------------------------------------------------------------
        type_str = "SHIELDED" if self.is_shielded else "GUARD"
        type_color = "#38bdf8" if self.is_shielded else "#fca5a5"
        canvas.create_text(
            self.x, self.y - 20,
            text=type_str, fill=type_color, font=("Consolas", 7, "bold"), tags="enemy_label"
        )
