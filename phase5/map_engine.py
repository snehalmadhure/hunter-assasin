"""
MapEngine (Phase 5 - Viewport Polygon & Line Clipping)
Supports 5px walls, 100px corridors, crossed crate boxes, dynamic doors, and exit door.
Clips all floor tiles, walls, crates, and doors to active Camera Viewport window.
"""

import math
from typing import List, Tuple, Optional
from cg_math import CGMath, Point, Points


class Wall:
    def __init__(self, x1: float, y1: float, x2: float, y2: float, wall_id: str = "wall"):
        self.x1, self.y1 = min(x1, x2), min(y1, y2)
        self.x2, self.y2 = max(x1, x2), max(y1, y2)
        self.wall_id = wall_id

    def collides_with_circle(self, cx: float, cy: float, r: float) -> bool:
        closest_x = max(self.x1, min(cx, self.x2))
        closest_y = max(self.y1, min(cy, self.y2))
        return ((cx - closest_x) ** 2 + (cy - closest_y) ** 2) <= (r * r)

    def render(self, canvas, camera, fill_color="#334155", border_color="#64748b"):
        xmin, ymin, xmax, ymax = camera.get_viewport_screen_bounds()
        world_poly = [(self.x1, self.y1), (self.x2, self.y1), (self.x2, self.y2), (self.x1, self.y2)]
        screen_poly = camera.world_to_screen(world_poly)
        clipped = CGMath.clip_polygon_aabb(screen_poly, xmin, ymin, xmax, ymax)
        if len(clipped) >= 3:
            canvas.create_polygon(CGMath.flatten(clipped), fill=fill_color, outline=border_color, width=1, tags="wall")


class CrossedBox:
    def __init__(self, x1: float, y1: float, x2: float, y2: float, box_id: str = "box"):
        self.x1, self.y1 = min(x1, x2), min(y1, y2)
        self.x2, self.y2 = max(x1, x2), max(y1, y2)
        self.box_id = box_id
        self.thickness = 5.0

    def collides_with_circle(self, cx: float, cy: float, r: float) -> bool:
        closest_x = max(self.x1, min(cx, self.x2))
        closest_y = max(self.y1, min(cy, self.y2))
        return ((cx - closest_x) ** 2 + (cy - closest_y) ** 2) <= (r * r)

    def render(self, canvas, camera):
        xmin, ymin, xmax, ymax = camera.get_viewport_screen_bounds()
        box_world = [(self.x1, self.y1), (self.x2, self.y1), (self.x2, self.y2), (self.x1, self.y2)]
        box_screen = camera.world_to_screen(box_world)
        clipped_box = CGMath.clip_polygon_aabb(box_screen, xmin, ymin, xmax, ymax)

        if len(clipped_box) >= 3:
            canvas.create_polygon(CGMath.flatten(clipped_box), fill="#1e2433", outline="#475569", width=2, tags="obstacle")

        # Inner cross lines (Cohen-Sutherland Line Clipping)
        inset = self.thickness + 2.0
        ix1, iy1 = self.x1 + inset, self.y1 + inset
        ix2, iy2 = self.x2 - inset, self.y2 - inset

        line1_s = camera.world_to_screen([(ix1, iy1), (ix2, iy2)])
        c_line1 = CGMath.clip_line_cohen_sutherland(line1_s[0][0], line1_s[0][1], line1_s[1][0], line1_s[1][1], xmin, ymin, xmax, ymax)
        if c_line1:
            canvas.create_line(c_line1[0], c_line1[1], c_line1[2], c_line1[3], fill="#475569", width=3, tags="obstacle_cross")

        line2_s = camera.world_to_screen([(ix1, iy2), (ix2, iy1)])
        c_line2 = CGMath.clip_line_cohen_sutherland(line2_s[0][0], line2_s[0][1], line2_s[1][0], line2_s[1][1], xmin, ymin, xmax, ymax)
        if c_line2:
            canvas.create_line(c_line2[0], c_line2[1], c_line2[2], c_line2[3], fill="#475569", width=3, tags="obstacle_cross")


class Door:
    def __init__(self, x1: float, y1: float, x2: float, y2: float, door_id: str, color: str = "#00f0ff", trigger_radius: float = 75.0):
        self.x1, self.y1 = float(x1), float(y1)
        self.x2, self.y2 = float(x2), float(y2)
        self.door_id = door_id
        self.color = color
        self.trigger_radius = trigger_radius
        self.mid_x = (self.x1 + self.x2) / 2.0
        self.mid_y = (self.y1 + self.y2) / 2.0
        self.slide_progress = 0.0
        self.is_open = False
        self.slide_speed = 0.12

    def update_proximity(self, player_x: float, player_y: float) -> bool:
        dist = CGMath.distance(player_x, player_y, self.mid_x, self.mid_y)
        self.is_open = (dist <= self.trigger_radius)
        target = 1.0 if self.is_open else 0.0
        if self.slide_progress < target:
            self.slide_progress = min(1.0, self.slide_progress + self.slide_speed)
        elif self.slide_progress > target:
            self.slide_progress = max(0.0, self.slide_progress - self.slide_speed)
        return self.is_open

    def collides_with_circle(self, cx: float, cy: float, r: float) -> bool:
        if self.slide_progress >= 0.75:
            return False
        cur_x2 = self.x1 + (self.x2 - self.x1) * (1.0 - self.slide_progress)
        cur_y2 = self.y1 + (self.y2 - self.y1) * (1.0 - self.slide_progress)
        dx, dy = cur_x2 - self.x1, cur_y2 - self.y1
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq == 0:
            return CGMath.distance(cx, cy, self.x1, self.y1) <= r
        t = max(0.0, min(1.0, ((cx - self.x1) * dx + (cy - self.y1) * dy) / seg_len_sq))
        proj_x, proj_y = self.x1 + t * dx, self.y1 + t * dy
        return CGMath.distance(cx, cy, proj_x, proj_y) <= (r + 2.5)

    def render(self, canvas, camera):
        xmin, ymin, xmax, ymax = camera.get_viewport_screen_bounds()
        cur_x2 = self.x1 + (self.x2 - self.x1) * (1.0 - self.slide_progress)
        cur_y2 = self.y1 + (self.y2 - self.y1) * (1.0 - self.slide_progress)

        door_s = camera.world_to_screen([(self.x1, self.y1), (cur_x2, cur_y2)])
        c_line = CGMath.clip_line_cohen_sutherland(door_s[0][0], door_s[0][1], door_s[1][0], door_s[1][1], xmin, ymin, xmax, ymax)

        if c_line and self.slide_progress < 0.98:
            canvas.create_line(c_line[0], c_line[1], c_line[2], c_line[3], fill=self.color, width=5, capstyle="round", tags="door")

        # Sensor LED
        smx, smy = camera.world_to_screen_pt(self.mid_x, self.mid_y)
        if xmin <= smx <= xmax and ymin <= smy <= ymax:
            led_color = "#22c55e" if self.is_open else "#ef4444"
            canvas.create_oval(smx - 3, smy - 3, smx + 3, smy + 3, fill=led_color, outline="#ffffff", tags="door_led")


class ExitDoor:
    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        self.x1, self.y1 = min(x1, x2), min(y1, y2)
        self.x2, self.y2 = max(x1, x2), max(y1, y2)
        self.mid_x = (self.x1 + self.x2) / 2.0
        self.mid_y = (self.y1 + self.y2) / 2.0
        self.pulse = 0.0

    def is_reached(self, px: float, py: float, radius: float = 15.0) -> bool:
        closest_x = max(self.x1, min(px, self.x2))
        closest_y = max(self.y1, min(py, self.y2))
        return ((px - closest_x) ** 2 + (py - closest_y) ** 2) <= (radius * radius)

    def render(self, canvas, camera, alarm_active: bool = False):
        xmin, ymin, xmax, ymax = camera.get_viewport_screen_bounds()
        self.pulse += 0.1
        border_color = "#34d399" if not alarm_active else ("#22c55e" if math.sin(self.pulse) > 0 else "#ffffff")
        fill_color = "#064e3b" if not alarm_active else "#047857"

        pad_world = [(self.x1, self.y1), (self.x2, self.y1), (self.x2, self.y2), (self.x1, self.y2)]
        pad_screen = camera.world_to_screen(pad_world)
        clipped_pad = CGMath.clip_polygon_aabb(pad_screen, xmin, ymin, xmax, ymax)

        if len(clipped_pad) >= 3:
            canvas.create_polygon(CGMath.flatten(clipped_pad), fill=fill_color, outline=border_color, width=2, tags="exit_door")

        smx, smy = camera.world_to_screen_pt(self.mid_x, self.y1 - 12)
        if xmin <= smx <= xmax and ymin <= smy <= ymax:
            canvas.create_text(smx, smy, text="[ EXIT DOOR ]", fill=border_color, font=("Consolas", 9, "bold"), tags="exit_text")


class MapEngine:
    WALL_THICKNESS = 5.0
    PASSAGE_WIDTH = 100.0
    BOX_SIZE = 120.0

    def __init__(self, origin_x: float = 60.0, origin_y: float = 60.0):
        self.ox = origin_x
        self.oy = origin_y

        self.walls: List[Wall] = []
        self.boxes: List[CrossedBox] = []
        self.doors: List[Door] = []
        self.exit_door: Optional[ExitDoor] = None

        self._build_map()

    def _build_map(self):
        wt, pw, bs = self.WALL_THICKNESS, self.PASSAGE_WIDTH, self.BOX_SIZE
        room_w = 2 * wt + 4 * pw + 3 * bs
        room_h = 2 * wt + 3 * pw + 2 * bs
        self.room_w, self.room_h = room_w, room_h

        # Perimeter Walls
        self.walls.append(Wall(self.ox, self.oy, self.ox + room_w, self.oy + wt, "wall_top"))
        self.walls.append(Wall(self.ox, self.oy + room_h - wt, self.ox + room_w, self.oy + room_h, "wall_bottom"))
        self.walls.append(Wall(self.ox, self.oy, self.ox + wt, self.oy + room_h, "wall_left"))
        self.walls.append(Wall(self.ox + room_w - wt, self.oy, self.ox + room_w, self.oy + room_h, "wall_right"))

        # Crossed Crates
        col_x = [self.ox + wt + pw + i * (bs + pw) for i in range(3)]
        row_y = [self.oy + wt + pw + j * (bs + pw) for j in range(2)]

        for col_idx, bx in enumerate(col_x):
            for row_idx, by in enumerate(row_y):
                self.boxes.append(CrossedBox(bx, by, bx + bs, by + bs, f"crate_{col_idx}_{row_idx}"))

        # Sliding Doors
        self.doors.append(Door(col_x[0] + bs, row_y[0] + bs / 2.0, col_x[1], row_y[0] + bs / 2.0, "door_1", color="#00e5ff"))
        self.doors.append(Door(col_x[1] + bs, row_y[1] + bs / 2.0, col_x[2], row_y[1] + bs / 2.0, "door_2", color="#ff9100"))
        self.doors.append(Door(col_x[1] + bs / 2.0, row_y[0] + bs, col_x[1] + bs / 2.0, row_y[1], "door_3", color="#a855f7"))

        # Exit Door
        ex1 = self.ox + self.room_w - wt - pw + 12.0
        ex2 = self.ox + self.room_w - wt - 12.0
        ey2 = self.oy + self.room_h - wt
        self.exit_door = ExitDoor(ex1, ey2 - 36.0, ex2, ey2)

    def update_doors(self, player_x: float, player_y: float):
        for door in self.doors:
            door.update_proximity(player_x, player_y)

    def is_blocked(self, cx: float, cy: float, radius: float = 15.0) -> bool:
        for wall in self.walls:
            if wall.collides_with_circle(cx, cy, radius): return True
        for box in self.boxes:
            if box.collides_with_circle(cx, cy, radius): return True
        for door in self.doors:
            if door.collides_with_circle(cx, cy, radius): return True
        return False

    def render(self, canvas, camera, alarm_active: bool = False):
        xmin, ymin, xmax, ymax = camera.get_viewport_screen_bounds()

        # 1. Floor Canvas Poly (Clipped)
        floor_world = [(self.ox, self.oy), (self.ox + self.room_w, self.oy),
                       (self.ox + self.room_w, self.oy + self.room_h), (self.ox, self.oy + self.room_h)]
        floor_screen = camera.world_to_screen(floor_world)
        clipped_floor = CGMath.clip_polygon_aabb(floor_screen, xmin, ymin, xmax, ymax)
        if len(clipped_floor) >= 3:
            canvas.create_polygon(CGMath.flatten(clipped_floor), fill="#0b0f19", outline="", tags="floor")

        # 2. Render Walls, Boxes, Exit, Doors
        for wall in self.walls: wall.render(canvas, camera)
        for box in self.boxes: box.render(canvas, camera)
        if self.exit_door: self.exit_door.render(canvas, camera, alarm_active=alarm_active)
        for door in self.doors: door.render(canvas, camera)