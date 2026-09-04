import math
import pygame

from graphics   import bresenham_line, bresenham_circle
from game_map   import CELL_SIZE
from transforms import (
    apply_transformation,
    translation_matrix,
    rotation_matrix,
    scaling_matrix,
    identity,
)


# ============================================================
# PLAYER ENTITY
# ============================================================

class Player:

    def __init__(self, x, y):

        self.x       = float(x)
        self.y       = float(y)
        self.radius  = 10
        self.speed   = 2.5
        self.health  = 100.0

        # Shield ring radius
        self.shield_radius = 14

        # Current transformation label (shown in HUD)
        self.current_transform = "None"


    # ========================================================
    # UPDATE (MOVEMENT VIA TRANSLATION MATRIX)
    #
    # Instead of directly adding dx/dy to position,
    # we use the 2D translation matrix from transforms.py
    # to compute the new position.  This is the core
    # Phase 3 requirement: movement via transformation matrix.
    # ========================================================

    def update(self, keys, game_map, rep_type):
        """
        Move the player using a 2D Translation Matrix.

        The displacement vector (tx, ty) is computed from
        key input, then a translation matrix T is built and
        applied to the player's current position point.

        rep_type : 1 = Row, 2 = Column (from C++ core)
        """

        tx = 0.0
        ty = 0.0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            ty -= self.speed

        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            ty += self.speed

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            tx -= self.speed

        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            tx += self.speed

        if tx == 0.0 and ty == 0.0:
            self.current_transform = "None"
            return

        self.current_transform = "Translation"

        # ----------------------------------------------------
        # BUILD TRANSLATION MATRIX
        # (from phase3core.cpp: translationMatrix)
        # ----------------------------------------------------

        T = translation_matrix(tx, ty, rep_type)

        # ----------------------------------------------------
        # APPLY TO CURRENT POSITION POINT
        # (from phase3core.cpp: applyTransformation)
        # ----------------------------------------------------

        result = apply_transformation(T, [(self.x, self.y)], rep_type)
        new_x, new_y = result[0]

        # ----------------------------------------------------
        # COLLISION CHECK  (same as Phase 2)
        # ----------------------------------------------------

        if not self._collides(new_x, self.y, game_map):
            self.x = new_x

        if not self._collides(self.x, new_y, game_map):
            self.y = new_y


    def _collides(self, px, py, game_map):
        """
        Corner-based collision against the map grid.
        Identical to Phase 2 check_collision.
        """

        margin = self.radius

        corners = [
            (px - margin, py - margin),
            (px + margin, py - margin),
            (px - margin, py + margin),
            (px + margin, py + margin),
        ]

        for cx, cy in corners:
            col = int(cx // CELL_SIZE)
            row = int(cy // CELL_SIZE)

            if game_map.is_wall(row, col):
                return True

        return False


    # ========================================================
    # DRAW PLAYER
    #
    # Triangle body (Bresenham) + shield circle.
    # Vertices are derived by applying a rotation matrix
    # around the player center — demonstrating rotation
    # transformation in-game (Phase 3 requirement).
    # ========================================================

    def draw(self, screen, rep_type):
        """
        Draw the player triangle using Bresenham lines.

        The three triangle vertices are defined relative to
        center (0, 0) and then translated to (self.x, self.y)
        using the translation matrix.
        """

        ix = int(round(self.x))
        iy = int(round(self.y))

        # -----------------------------------------------
        # DEFINE TRIANGLE VERTICES (relative to origin)
        # -----------------------------------------------

        local_pts = [
            (0,  -8),    # Tip
            (-7,  6),    # Bottom-left
            (7,   6),    # Bottom-right
        ]

        # -----------------------------------------------
        # APPLY TRANSLATION MATRIX to move from
        # local origin → world position (self.x, self.y)
        # -----------------------------------------------

        T   = translation_matrix(self.x, self.y, rep_type)
        pts = apply_transformation(T, local_pts, rep_type)

        p1 = (int(round(pts[0][0])), int(round(pts[0][1])))
        p2 = (int(round(pts[1][0])), int(round(pts[1][1])))
        p3 = (int(round(pts[2][0])), int(round(pts[2][1])))

        # Draw triangle edges via Bresenham
        bresenham_line(screen, p1[0], p1[1], p2[0], p2[1], (255, 255, 255))
        bresenham_line(screen, p2[0], p2[1], p3[0], p3[1], (255, 255, 255))
        bresenham_line(screen, p3[0], p3[1], p1[0], p1[1], (255, 255, 255))

        # Draw shield circle
        bresenham_circle(screen, ix, iy, self.shield_radius, (255, 255, 255))


# ============================================================
# ENEMY ENTITY
# ============================================================

class Enemy:

    def __init__(self, x, y, facing_angle_deg, sight_radius=100):

        self.x                 = float(x)
        self.y                 = float(y)
        self.facing_angle      = float(facing_angle_deg)
        self.sight_radius      = sight_radius
        self.fov_half_angle    = 45.0      # +/- 45 deg cone
        self.is_player_detected = False

        # --------------------------------------------------------
        # PATROL STATE (Phase 3 addition)
        #
        # Enemies now move between two waypoints using a
        # Translation Matrix each frame.
        # --------------------------------------------------------

        # Waypoint A = starting position
        self.patrol_ax = self.x
        self.patrol_ay = self.y

        # Waypoint B = offset from A (set after construction)
        self.patrol_bx = self.x
        self.patrol_by = self.y

        self.patrol_speed    = 0.8
        self.patrol_going_b  = True   # True = moving toward B

        # --------------------------------------------------------
        # ROTATION STATE (Phase 3 addition)
        #
        # Enemy facing angle is updated each frame to match
        # the patrol direction using the Rotation Matrix.
        # A small fixed rotate_speed is used for smooth
        # interpolation toward the target angle.
        # --------------------------------------------------------

        self.rotate_speed = 3.0    # max degrees to turn per frame


    # ========================================================
    # UPDATE PATROL MOVEMENT  (TRANSLATION MATRIX)
    #
    # Each frame we build a translation matrix for
    # a small step toward the current waypoint,
    # apply it to (self.x, self.y), then check if we've
    # reached the waypoint and reverse direction.
    # ========================================================

    def update_patrol(self, rep_type):
        """
        Move enemy along patrol path using Translation Matrix.

        rep_type : 1 = Row, 2 = Column
        """

        # Target waypoint
        if self.patrol_going_b:
            tx_goal = self.patrol_bx
            ty_goal = self.patrol_by
        else:
            tx_goal = self.patrol_ax
            ty_goal = self.patrol_ay

        # Direction vector toward target
        dx = tx_goal - self.x
        dy = ty_goal - self.y
        dist = math.hypot(dx, dy)

        if dist < self.patrol_speed:
            # Reached waypoint — flip direction
            self.x = tx_goal
            self.y = ty_goal
            self.patrol_going_b = not self.patrol_going_b
            return

        # Normalise and scale by patrol speed
        step_x = (dx / dist) * self.patrol_speed
        step_y = (dy / dist) * self.patrol_speed

        # --------------------------------------------------
        # BUILD TRANSLATION MATRIX
        # (phase3core.cpp: translationMatrix)
        # --------------------------------------------------

        T = translation_matrix(step_x, step_y, rep_type)

        # --------------------------------------------------
        # APPLY TO CURRENT ENEMY POSITION
        # (phase3core.cpp: applyTransformation)
        # --------------------------------------------------

        result   = apply_transformation(T, [(self.x, self.y)], rep_type)
        self.x, self.y = result[0]


    # ========================================================
    # UPDATE FACING ROTATION  (ROTATION MATRIX)
    #
    # The enemy facing angle is steered toward its patrol
    # movement direction each frame using a Rotation Matrix.
    # This keeps enemies facing where they walk, and
    # demonstrates in-game rotation transformation.
    # ========================================================

    def update_rotation(self, rep_type):
        """
        Steer enemy facing angle toward patrol movement direction
        using the Rotation Matrix.

        1. Compute target angle from patrol direction vector.
        2. Compute angular difference (delta).
        3. Build a rotation matrix for min(delta, rotate_speed).
        4. Apply to current forward vector → update facing_angle.
        """

        # Target = direction toward current patrol goal
        if self.patrol_going_b:
            tx_goal = self.patrol_bx
            ty_goal = self.patrol_by
        else:
            tx_goal = self.patrol_ax
            ty_goal = self.patrol_ay

        goal_dx = tx_goal - self.x
        goal_dy = ty_goal - self.y
        dist = math.hypot(goal_dx, goal_dy)

        if dist < 1.0:
            return   # At waypoint — no rotation needed

        target_angle = math.degrees(math.atan2(goal_dy, goal_dx))

        # Angular difference, clamped to [-180, 180]
        delta = (target_angle - self.facing_angle + 180) % 360 - 180

        # Clamp rotation step to rotate_speed per frame
        step = max(-self.rotate_speed, min(self.rotate_speed, delta))

        if abs(step) < 0.1:
            return   # Already facing the right way

        # --------------------------------------------------
        # BUILD ROTATION MATRIX
        # (phase3core.cpp: rotationMatrix)
        # --------------------------------------------------

        R = rotation_matrix(step, rep_type)

        # Current forward direction as a unit vector
        rad   = math.radians(self.facing_angle)
        fwd_x = math.cos(rad)
        fwd_y = math.sin(rad)

        # --------------------------------------------------
        # APPLY ROTATION MATRIX TO DIRECTION VECTOR
        # (phase3core.cpp: applyTransformation)
        # --------------------------------------------------

        result        = apply_transformation(R, [(fwd_x, fwd_y)], rep_type)
        new_fx, new_fy = result[0]

        # Recover angle from rotated vector
        self.facing_angle = math.degrees(math.atan2(new_fy, new_fx))


    # ========================================================
    # UPDATE DETECTION  (unchanged from Phase 2)
    # ========================================================

    def update_detection(self, player):
        """
        Check if player is inside enemy FOV cone.
        Uses Euclidean distance and angular comparison.
        Identical to Phase 2.
        """

        dx   = player.x - self.x
        dy   = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist > self.sight_radius:
            self.is_player_detected = False
            return False

        angle_to_player = math.degrees(math.atan2(dy, dx))
        rel_angle = (angle_to_player - self.facing_angle + 180) % 360 - 180

        if abs(rel_angle) <= self.fov_half_angle:
            self.is_player_detected = True
            return True
        else:
            self.is_player_detected = False
            return False


    # ========================================================
    # DRAW ENEMY
    #
    # Triangle body (facing direction) + FOV cone arcs.
    # The triangle vertices are computed by applying a
    # rotation matrix (about center) + translation matrix
    # to move into world space — both Phase 3 transformations.
    # ========================================================

    def draw(self, screen, rep_type):
        """
        Draw enemy using Bresenham lines.

        The enemy triangle body is built from local vertices,
        rotated to the facing angle via rotation matrix,
        then translated to world position via translation matrix.
        The FOV cone rays are computed similarly.
        """

        ix     = int(round(self.x))
        iy     = int(round(self.y))
        color  = (255, 255, 255)

        # -----------------------------------------------
        # TRIANGLE BODY
        #
        # Local vertices (facing right, angle = 0):
        #   tip     = (10, 0)
        #   left    = (-8, -8)
        #   right   = (-8,  8)
        # -----------------------------------------------

        local_body = [
            (10.0,  0.0),
            (-8.0, -8.0),
            (-8.0,  8.0),
        ]

        # -----------------------------------------------
        # 1. ROTATE local vertices to facing angle
        # -----------------------------------------------

        R = rotation_matrix(self.facing_angle, rep_type)
        rotated_body = apply_transformation(R, local_body, rep_type)

        # -----------------------------------------------
        # 2. TRANSLATE to world position
        # -----------------------------------------------

        T = translation_matrix(self.x, self.y, rep_type)
        world_body = apply_transformation(T, rotated_body, rep_type)

        p0 = (int(round(world_body[0][0])), int(round(world_body[0][1])))
        p1 = (int(round(world_body[1][0])), int(round(world_body[1][1])))
        p2 = (int(round(world_body[2][0])), int(round(world_body[2][1])))

        # Draw triangle edges
        bresenham_line(screen, p0[0], p0[1], p1[0], p1[1], color)
        bresenham_line(screen, p1[0], p1[1], p2[0], p2[1], color)
        bresenham_line(screen, p2[0], p2[1], p0[0], p0[1], color)

        # -----------------------------------------------
        # FOV CONE RAYS
        # -----------------------------------------------

        left_angle_rad  = math.radians(self.facing_angle - self.fov_half_angle)
        right_angle_rad = math.radians(self.facing_angle + self.fov_half_angle)

        lx = ix + int(self.sight_radius * math.cos(left_angle_rad))
        ly = iy + int(self.sight_radius * math.sin(left_angle_rad))

        rx = ix + int(self.sight_radius * math.cos(right_angle_rad))
        ry = iy + int(self.sight_radius * math.sin(right_angle_rad))

        bresenham_line(screen, ix, iy, lx, ly, color)
        bresenham_line(screen, ix, iy, rx, ry, color)

        # -----------------------------------------------
        # FOV ARC  (16 segments)
        # -----------------------------------------------

        steps = 16

        for i in range(steps):

            a1 = math.radians(
                self.facing_angle - self.fov_half_angle
                + (i       * 90.0 / steps)
            )
            a2 = math.radians(
                self.facing_angle - self.fov_half_angle
                + ((i + 1) * 90.0 / steps)
            )

            x1 = ix + int(self.sight_radius * math.cos(a1))
            y1 = iy + int(self.sight_radius * math.sin(a1))
            x2 = ix + int(self.sight_radius * math.cos(a2))
            y2 = iy + int(self.sight_radius * math.sin(a2))

            bresenham_line(screen, x1, y1, x2, y2, color)
