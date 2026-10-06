import math
from typing import List, Tuple, Optional
from cg_math import CGMath, Point, Points

def _draw_rect_lines(canvas, x1, y1, x2, y2, color, width=1, tags=""):
    canvas.create_line(x1, y1, x2, y1, fill=color, width=width, tags=tags)
    canvas.create_line(x2, y1, x2, y2, fill=color, width=width, tags=tags)
    canvas.create_line(x2, y2, x1, y2, fill=color, width=width, tags=tags)
    canvas.create_line(x1, y2, x1, y1, fill=color, width=width, tags=tags)

class Wall:
    def __init__(self, x1: float, y1: float, x2: float, y2: float, wall_id: str = "wall"):
        self.x1, self.y1, self.x2, self.y2, self.wall_id = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), wall_id

    def collides_with_circle(self, cx: float, cy: float, r: float) -> bool:
        return ((cx - max(self.x1, min(cx, self.x2))) ** 2 + (cy - max(self.y1, min(cy, self.y2))) ** 2) <= (r * r)

    def render(self, canvas):
        _draw_rect_lines(canvas, self.x1, self.y1, self.x2, self.y2, "#777777", 1, "wall")

class CrossedBox:
    def __init__(self, x1: float, y1: float, x2: float, y2: float, box_id: str = "box"):
        self.x1, self.y1, self.x2, self.y2, self.box_id, self.thickness = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), box_id, 5.0

    def collides_with_circle(self, cx: float, cy: float, r: float) -> bool:
        return ((cx - max(self.x1, min(cx, self.x2))) ** 2 + (cy - max(self.y1, min(cy, self.y2))) ** 2) <= (r * r)

    def render(self, canvas):
        _draw_rect_lines(canvas, self.x1, self.y1, self.x2, self.y2, "#AAAAAA", 1, "obstacle")
        ix1, iy1, ix2, iy2 = self.x1 + 7.0, self.y1 + 7.0, self.x2 - 7.0, self.y2 - 7.0
        _draw_rect_lines(canvas, ix1, iy1, ix2, iy2, "#555555", 1, "obstacle_inner")
        canvas.create_line(ix1, iy1, ix2, iy2, fill="#777777", width=2, tags="obstacle_cross")
        canvas.create_line(ix1, iy2, ix2, iy1, fill="#777777", width=2, tags="obstacle_cross")

class Door:
    def __init__(self, x1: float, y1: float, x2: float, y2: float, door_id: str, trigger_radius: float = 75.0):
        self.x1, self.y1, self.x2, self.y2, self.door_id = float(x1), float(y1), float(x2), float(y2), door_id
        self.mid_x, self.mid_y, self.trigger_radius = (self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0, trigger_radius
        self.slide_progress, self.is_open, self.slide_speed = 0.0, False, 0.12

    def update_proximity(self, player_x: float, player_y: float) -> bool:
        self.is_open = (CGMath.distance(player_x, player_y, self.mid_x, self.mid_y) <= self.trigger_radius)
        target = 1.0 if self.is_open else 0.0
        if self.slide_progress < target: self.slide_progress = min(1.0, self.slide_progress + self.slide_speed)
        elif self.slide_progress > target: self.slide_progress = max(0.0, self.slide_progress - self.slide_speed)
        return self.is_open

    def collides_with_circle(self, cx: float, cy: float, r: float) -> bool:
        if self.slide_progress >= 0.75: return False
        cur_x2, cur_y2 = self.x1 + (self.x2 - self.x1) * (1.0 - self.slide_progress), self.y1 + (self.y2 - self.y1) * (1.0 - self.slide_progress)
        dx, dy = cur_x2 - self.x1, cur_y2 - self.y1
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq == 0: return CGMath.distance(cx, cy, self.x1, self.y1) <= r
        t = max(0.0, min(1.0, ((cx - self.x1) * dx + (cy - self.y1) * dy) / seg_len_sq))
        return CGMath.distance(cx, cy, self.x1 + t * dx, self.y1 + t * dy) <= (r + 2.5)

    def render(self, canvas):
        cur_x2, cur_y2 = self.x1 + (self.x2 - self.x1) * (1.0 - self.slide_progress), self.y1 + (self.y2 - self.y1) * (1.0 - self.slide_progress)
        if self.slide_progress < 0.98:
            canvas.create_line(self.x1, self.y1, cur_x2, cur_y2, fill="#FFFFFF", width=3, capstyle="round", tags="door")
        
        # Draw explicit lines for door jamb points instead of filled ovals
        canvas.create_line(self.x1-3, self.y1-3, self.x1+3, self.y1+3, fill="#888888")
        canvas.create_line(self.x1-3, self.y1+3, self.x1+3, self.y1-3, fill="#888888")
        canvas.create_line(self.x2-3, self.y2-3, self.x2+3, self.y2+3, fill="#888888")
        canvas.create_line(self.x2-3, self.y2+3, self.x2+3, self.y2-3, fill="#888888")

class ExitDoor:
    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        self.x1, self.y1, self.x2, self.y2 = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
        self.mid_x = (self.x1 + self.x2) / 2.0

    def is_reached(self, px: float, py: float, radius: float = 15.0) -> bool:
        return ((px - max(self.x1, min(px, self.x2))) ** 2 + (py - max(self.y1, min(py, self.y2))) ** 2) <= (radius * radius)

    def render(self, canvas, alarm_active: bool = False):
        _draw_rect_lines(canvas, self.x1, self.y1, self.x2, self.y2, "#FFFFFF", 2, "exit_door")
        for sx in range(int(self.x1) + 8, int(self.x2) - 8, 14):
            canvas.create_line(sx, self.y1 + 3, sx + 8, self.y2 - 3, fill="#AAAAAA", width=2, tags="exit_chevrons")
        canvas.create_text(self.mid_x, self.y1 - 12, text="[ EXIT DOOR ]", fill="#FFFFFF", font=("Consolas", 9, "bold"), tags="exit_text")

class MapEngine:
    WALL_THICKNESS, PASSAGE_WIDTH, BOX_SIZE = 5.0, 100.0, 120.0

    def __init__(self, origin_x: float = 60.0, origin_y: float = 60.0):
        self.ox, self.oy = origin_x, origin_y
        self.walls, self.boxes, self.doors, self.exit_door = [], [], [], None
        self._build_map()

    def _build_map(self):
        wt, pw, bs = self.WALL_THICKNESS, self.PASSAGE_WIDTH, self.BOX_SIZE
        self.room_w, self.room_h = 2 * wt + 4 * pw + 3 * bs, 2 * wt + 3 * pw + 2 * bs
        self.walls.extend([
            Wall(self.ox, self.oy, self.ox + self.room_w, self.oy + wt),
            Wall(self.ox, self.oy + self.room_h - wt, self.ox + self.room_w, self.oy + self.room_h),
            Wall(self.ox, self.oy, self.ox + wt, self.oy + self.room_h),
            Wall(self.ox + self.room_w - wt, self.oy, self.ox + self.room_w, self.oy + self.room_h)
        ])
        col_x = [self.ox + wt + pw + i * (bs + pw) for i in range(3)]
        row_y = [self.oy + wt + pw + j * (bs + pw) for j in range(2)]
        for c, bx in enumerate(col_x):
            for r, by in enumerate(row_y):
                self.boxes.append(CrossedBox(bx, by, bx + bs, by + bs, f"crate_{c}_{r}"))
        self.doors.append(Door(col_x[0] + bs, row_y[0] + bs / 2.0, col_x[1], row_y[0] + bs / 2.0, "door_1"))
        self.doors.append(Door(col_x[1] + bs, row_y[1] + bs / 2.0, col_x[2], row_y[1] + bs / 2.0, "door_2"))
        self.doors.append(Door(col_x[1] + bs / 2.0, row_y[0] + bs, col_x[1] + bs / 2.0, row_y[1], "door_3"))
        self.exit_door = ExitDoor(self.ox + self.room_w - wt - pw + 12.0, self.oy + self.room_h - wt - 36.0, self.ox + self.room_w - wt - 12.0, self.oy + self.room_h - wt)

    def update_doors(self, px: float, py: float):
        for door in self.doors: door.update_proximity(px, py)

    def is_blocked(self, cx: float, cy: float, radius: float = 15.0) -> bool:
        return any(w.collides_with_circle(cx, cy, radius) for w in self.walls) or \
               any(b.collides_with_circle(cx, cy, radius) for b in self.boxes) or \
               any(d.collides_with_circle(cx, cy, radius) for d in self.doors)

    def render(self, canvas, alarm_active: bool = False):
        _draw_rect_lines(canvas, self.ox, self.oy, self.ox + self.room_w, self.oy + self.room_h, "#555555", 1, "floor_boundary")
        for w in self.walls: w.render(canvas)
        for b in self.boxes: b.render(canvas)
        if self.exit_door: self.exit_door.render(canvas, alarm_active)
        for d in self.doors: d.render(canvas)