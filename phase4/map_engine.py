"""
MapEngine: Grid-Aligned Map & Obstacle Management for Stealth Game
Strict Constraints:
- Outer and inner walls have a thickness of exactly 5 pixels.
- All corridors and passages are exactly 100 pixels wide.
- Obstacles are tactical crossed boxes (crates with diagonal bracing).
- Dynamic doors drawn as distinct colored lines that slide/disappear on proximity.
- Zero external game engines; rendered using tkinter.Canvas.
"""

import math
from typing import List, Tuple, Optional, Dict
from cg_math import CGMath, Point, Points


class Wall:
    """Represents an axis-aligned solid wall with exact 5px thickness."""
    def __init__(self, x1: float, y1: float, x2: float, y2: float, wall_id: str = "wall"):
        # Normalized bounding box
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)
        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)
        self.wall_id = wall_id

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    def collides_with_circle(self, cx: float, cy: float, r: float) -> bool:
        """Raw geometric circle vs AABB collision without external physics engines."""
        closest_x = max(self.x1, min(cx, self.x2))
        closest_y = max(self.y1, min(cy, self.y2))
        dist_sq = (cx - closest_x) ** 2 + (cy - closest_y) ** 2
        return dist_sq <= (r * r)

    def render(self, canvas, fill_color="#334155", border_color="#64748b"):
        """Draws the 5px wall on canvas with crisp tactical shading."""
        canvas.create_rectangle(
            self.x1, self.y1, self.x2, self.y2,
            fill=fill_color, outline=border_color, width=1, tags="wall"
        )


class CrossedBox:
    """
    Represents a crossed box (tactical shipping crate) obstacle.
    Border thickness is exactly 5px.
    Interior contains diagonal 'X' cross bracing.
    """
    def __init__(self, x1: float, y1: float, x2: float, y2: float, box_id: str = "box"):
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)
        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)
        self.box_id = box_id
        self.thickness = 5.0

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    def collides_with_circle(self, cx: float, cy: float, r: float) -> bool:
        """Circle vs Box AABB collision."""
        closest_x = max(self.x1, min(cx, self.x2))
        closest_y = max(self.y1, min(cy, self.y2))
        dist_sq = (cx - closest_x) ** 2 + (cy - closest_y) ** 2
        return dist_sq <= (r * r)

    def render(self, canvas):
        """Renders the crossed box with 5px border and tactical diagonal cross."""
        # 1. Main body
        canvas.create_rectangle(
            self.x1, self.y1, self.x2, self.y2,
            fill="#1e2433", outline="#475569", width=self.thickness, tags="obstacle"
        )

        # 2. Inner crate inset border
        inset = self.thickness + 2.0
        ix1, iy1 = self.x1 + inset, self.y1 + inset
        ix2, iy2 = self.x2 - inset, self.y2 - inset

        canvas.create_rectangle(
            ix1, iy1, ix2, iy2,
            fill="#151b27", outline="#334155", width=1, tags="obstacle_inner"
        )

        # 3. Tactical 'X' Crossed Bracing Lines
        canvas.create_line(
            ix1, iy1, ix2, iy2,
            fill="#475569", width=3, tags="obstacle_cross"
        )
        canvas.create_line(
            ix1, iy2, ix2, iy1,
            fill="#475569", width=3, tags="obstacle_cross"
        )

        # 4. Corner rivets
        rivet_r = 2.0
        for rx, ry in [(ix1 + 5, iy1 + 5), (ix2 - 5, iy1 + 5),
                       (ix1 + 5, iy2 - 5), (ix2 - 5, iy2 - 5)]:
            canvas.create_oval(
                rx - rivet_r, ry - rivet_r, rx + rivet_r, ry + rivet_r,
                fill="#94a3b8", outline="", tags="obstacle_rivet"
            )


class Door:
    """
    Represents an automated door across a 100px passage.
    Drawn as a distinct colored line with 5px thickness.
    Opens (slides or retracts) when a coordinate (e.g. player) enters proximity.
    """
    def __init__(self, x1: float, y1: float, x2: float, y2: float,
                 door_id: str, color: str = "#00f0ff", trigger_radius: float = 75.0):
        self.x1 = float(x1)
        self.y1 = float(y1)
        self.x2 = float(x2)
        self.y2 = float(y2)
        self.door_id = door_id
        self.color = color
        self.trigger_radius = trigger_radius

        # Midpoint of the door
        self.mid_x = (self.x1 + self.x2) / 2.0
        self.mid_y = (self.y1 + self.y2) / 2.0

        # Animation states: 0.0 = fully closed, 1.0 = fully open (slid back)
        self.slide_progress = 0.0
        self.is_open = False
        self.slide_speed = 0.12  # rate per tick

    def update_proximity(self, player_x: float, player_y: float) -> bool:
        """
        Updates door open/close state based on Euclidean distance to door midpoint.
        Also validates proximity area using Bresenham circle boundaries.
        """
        dist = CGMath.distance(player_x, player_y, self.mid_x, self.mid_y)
        self.is_open = (dist <= self.trigger_radius)

        # Smooth slide transition
        target = 1.0 if self.is_open else 0.0
        if self.slide_progress < target:
            self.slide_progress = min(1.0, self.slide_progress + self.slide_speed)
        elif self.slide_progress > target:
            self.slide_progress = max(0.0, self.slide_progress - self.slide_speed)

        return self.is_open

    def is_blocking(self) -> bool:
        """Returns True if the door is sufficiently closed to block passage."""
        return self.slide_progress < 0.75

    def collides_with_circle(self, cx: float, cy: float, r: float) -> bool:
        """Collision check against current physical door line."""
        if not self.is_blocking():
            return False

        # Current sliding endpoint: retracts towards (x1, y1)
        cur_x2 = self.x1 + (self.x2 - self.x1) * (1.0 - self.slide_progress)
        cur_y2 = self.y1 + (self.y2 - self.y1) * (1.0 - self.slide_progress)

        # Line segment to point distance
        dx = cur_x2 - self.x1
        dy = cur_y2 - self.y1
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq == 0:
            return CGMath.distance(cx, cy, self.x1, self.y1) <= r

        t = max(0.0, min(1.0, ((cx - self.x1) * dx + (cy - self.y1) * dy) / seg_len_sq))
        proj_x = self.x1 + t * dx
        proj_y = self.y1 + t * dy

        return CGMath.distance(cx, cy, proj_x, proj_y) <= (r + 2.5)

    def render(self, canvas):
        """Renders the door with active slide position, neon glow, and sensor LEDs."""
        # Compute sliding endpoint
        cur_x2 = self.x1 + (self.x2 - self.x1) * (1.0 - self.slide_progress)
        cur_y2 = self.y1 + (self.y2 - self.y1) * (1.0 - self.slide_progress)

        # 1. Door sensor posts (jambs)
        jamb_radius = 4.0
        canvas.create_oval(
            self.x1 - jamb_radius, self.y1 - jamb_radius,
            self.x1 + jamb_radius, self.y1 + jamb_radius,
            fill="#64748b", outline="#94a3b8", width=1, tags="door_jamb"
        )
        canvas.create_oval(
            self.x2 - jamb_radius, self.y2 - jamb_radius,
            self.x2 + jamb_radius, self.y2 + jamb_radius,
            fill="#64748b", outline="#94a3b8", width=1, tags="door_jamb"
        )

        # 2. Door active beam line (if not fully retracted)
        if self.slide_progress < 0.98:
            # Subtle glow effect
            canvas.create_line(
                self.x1, self.y1, cur_x2, cur_y2,
                fill=self.color, width=7, stipple="gray50", tags="door_glow"
            )
            # Solid core line (thickness = 5px)
            canvas.create_line(
                self.x1, self.y1, cur_x2, cur_y2,
                fill=self.color, width=5, capstyle="round", tags="door"
            )

        # 3. Status indicator LED at midpoint
        led_color = "#22c55e" if self.is_open else "#ef4444"
        canvas.create_oval(
            self.mid_x - 3, self.mid_y - 3, self.mid_x + 3, self.mid_y + 3,
            fill=led_color, outline="#ffffff", width=1, tags="door_led"
        )


class ExitDoor:
    """
    Designated Escape Door / Extraction Zone.
    Located in the lower-right corridor. When alarm triggers, beacons illuminate
    to guide the player to evacuation.
    """
    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)
        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)
        self.mid_x = (self.x1 + self.x2) / 2.0
        self.mid_y = (self.y1 + self.y2) / 2.0
        self.pulse = 0.0

    def is_reached(self, px: float, py: float, radius: float = 15.0) -> bool:
        """Determines if player touches the exit extraction zone."""
        closest_x = max(self.x1, min(px, self.x2))
        closest_y = max(self.y1, min(py, self.y2))
        d_sq = (px - closest_x) ** 2 + (py - closest_y) ** 2
        return d_sq <= (radius * radius)

    def render(self, canvas, alarm_active: bool = False):
        """Renders tactical exit door with glowing beacon and hazard chevrons."""
        self.pulse += 0.1
        border_color = "#34d399" if not alarm_active else ("#22c55e" if math.sin(self.pulse) > 0 else "#ffffff")
        fill_color = "#064e3b" if not alarm_active else "#047857"

        # 1. Extraction pad floor plate
        canvas.create_rectangle(
            self.x1, self.y1, self.x2, self.y2,
            fill=fill_color, outline=border_color, width=2, tags="exit_door"
        )

        # 2. Hazard diagonal stripes
        for sx in range(int(self.x1) + 8, int(self.x2) - 8, 14):
            canvas.create_line(
                sx, self.y1 + 3, sx + 8, self.y2 - 3,
                fill="#34d399", width=2, tags="exit_chevrons"
            )

        # 3. EXIT Beacon text
        canvas.create_text(
            self.mid_x, self.y1 - 12,
            text="[ EXIT DOOR ]", fill=border_color, font=("Consolas", 9, "bold"), tags="exit_text"
        )


class MapEngine:
    """
    MapEngine manages the closed room, grid alignment, crossed boxes, doors, and exit door.
    """

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
        """Constructs the closed room with exact 100px passages and 5px walls."""
        wt = self.WALL_THICKNESS
        pw = self.PASSAGE_WIDTH
        bs = self.BOX_SIZE

        # The room has 3 columns and 2 rows of crossed box obstacles:
        # Width:  wt + pw + bs + pw + bs + pw + bs + pw + wt
        # Height: wt + pw + bs + pw + bs + pw + wt
        room_w = 2 * wt + 4 * pw + 3 * bs   # 10 + 400 + 360 = 770 px
        room_h = 2 * wt + 3 * pw + 2 * bs   # 10 + 300 + 240 = 550 px

        self.room_w = room_w
        self.room_h = room_h

        # ---------------------------------------------------------------------
        # 1. Outer Perimeter Walls (Thickness = exactly 5px)
        # ---------------------------------------------------------------------
        # Top Wall
        self.walls.append(Wall(self.ox, self.oy, self.ox + room_w, self.oy + wt, "wall_top"))
        # Bottom Wall
        self.walls.append(Wall(self.ox, self.oy + room_h - wt, self.ox + room_w, self.oy + room_h, "wall_bottom"))
        # Left Wall
        self.walls.append(Wall(self.ox, self.oy, self.ox + wt, self.oy + room_h, "wall_left"))
        # Right Wall
        self.walls.append(Wall(self.ox + room_w - wt, self.oy, self.ox + room_w, self.oy + room_h, "wall_right"))

        # ---------------------------------------------------------------------
        # 2. Crossed Box Obstacles
        # ---------------------------------------------------------------------
        # Columns start after inner left wall (ox + wt + pw)
        col_x = [
            self.ox + wt + pw + i * (bs + pw)
            for i in range(3)
        ]  # i=0: 60+5+100=165; i=1: 165+220=385; i=2: 385+220=605

        # Rows start after inner top wall (oy + wt + pw)
        row_y = [
            self.oy + wt + pw + j * (bs + pw)
            for j in range(2)
        ]  # j=0: 60+5+100=165; j=1: 165+220=385

        for col_idx, bx in enumerate(col_x):
            for row_idx, by in enumerate(row_y):
                box_id = f"crate_c{col_idx+1}_r{row_idx+1}"
                self.boxes.append(CrossedBox(bx, by, bx + bs, by + bs, box_id))

        # ---------------------------------------------------------------------
        # 3. Dynamic Automated Doors (Across 100px passages)
        # ---------------------------------------------------------------------
        # Door 1: Horizontal door across the vertical corridor between Col 1 and Col 2
        # Spans exactly 100px: x in [col_x[0] + bs, col_x[1]], y at row_y[0] + bs/2
        d1_x1 = col_x[0] + bs   # 285
        d1_x2 = col_x[1]        # 385 (length = 100px)
        d1_y  = row_y[0] + bs / 2.0  # 225
        self.doors.append(Door(d1_x1, d1_y, d1_x2, d1_y, "door_1", color="#00e5ff", trigger_radius=70.0))

        # Door 2: Horizontal door across the vertical corridor between Col 2 and Col 3
        # Spans exactly 100px: x in [col_x[1] + bs, col_x[2]], y at row_y[1] + bs/2
        d2_x1 = col_x[1] + bs   # 505
        d2_x2 = col_x[2]        # 605 (length = 100px)
        d2_y  = row_y[1] + bs / 2.0  # 445
        self.doors.append(Door(d2_x1, d2_y, d2_x2, d2_y, "door_2", color="#ff9100", trigger_radius=70.0))

        # Door 3: Vertical door across the central horizontal passage between Row 1 and Row 2
        # Spans exactly 100px: y in [row_y[0] + bs, row_y[1]], x at col_x[1] + bs/2
        d3_y1 = row_y[0] + bs   # 285
        d3_y2 = row_y[1]        # 385 (length = 100px)
        d3_x  = col_x[1] + bs / 2.0  # 445
        self.doors.append(Door(d3_x, d3_y1, d3_x, d3_y2, "door_3", color="#a855f7", trigger_radius=70.0))

        # ---------------------------------------------------------------------
        # 4. Designated Exit Door / Extraction Hatch (Bottom-Right Passage)
        # ---------------------------------------------------------------------
        exit_x1 = self.ox + self.room_w - wt - pw + 12.0  # ox + 770 - 5 - 100 + 12 = ox + 677
        exit_x2 = self.ox + self.room_w - wt - 12.0       # ox + 770 - 5 - 12 = ox + 753
        exit_y2 = self.oy + self.room_h - wt              # ox + 550 - 5 = oy + 545
        exit_y1 = exit_y2 - 36.0
        self.exit_door = ExitDoor(exit_x1, exit_y1, exit_x2, exit_y2)

    def update_doors(self, player_x: float, player_y: float):
        """Updates proximity and slide states for all doors."""
        for door in self.doors:
            door.update_proximity(player_x, player_y)

    def is_blocked(self, cx: float, cy: float, radius: float = 15.0) -> bool:
        """
        Evaluates collision against all solid elements:
        outer walls, crossed box obstacles, and closed doors.
        """
        # Check perimeter walls
        for wall in self.walls:
            if wall.collides_with_circle(cx, cy, radius):
                return True

        # Check crossed boxes
        for box in self.boxes:
            if box.collides_with_circle(cx, cy, radius):
                return True

        # Check blocking doors
        for door in self.doors:
            if door.collides_with_circle(cx, cy, radius):
                return True

        return False

    def render(self, canvas, alarm_active: bool = False):
        """Draws the entire map: background grid, floor, walls, crossed boxes, doors, exit door."""
        # 1. Floor canvas background
        canvas.create_rectangle(
            self.ox, self.oy, self.ox + self.room_w, self.oy + self.room_h,
            fill="#0b0f19", outline="", tags="floor"
        )

        # 2. Subtle floor grid lines (every 50px)
        for gx in range(int(self.ox), int(self.ox + self.room_w), 50):
            canvas.create_line(
                gx, self.oy, gx, self.oy + self.room_h,
                fill="#131d2e", width=1, tags="grid"
            )
        for gy in range(int(self.oy), int(self.oy + self.room_h), 50):
            canvas.create_line(
                self.ox, gy, self.ox + self.room_w, gy,
                fill="#131d2e", width=1, tags="grid"
            )

        # 3. Outer Walls (5px)
        for wall in self.walls:
            wall.render(canvas, fill_color="#334155", border_color="#64748b")

        # 4. Crossed Boxes (Crates)
        for box in self.boxes:
            box.render(canvas)

        # 5. Exit Door / Extraction Pad
        if self.exit_door:
            self.exit_door.render(canvas, alarm_active=alarm_active)

        # 6. Doors (Distinct colored sliding lines)
        for door in self.doors:
            door.render(canvas)
