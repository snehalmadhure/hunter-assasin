import math
from typing import List, Tuple
from cg_math import CGMath, Point, Points

def _draw_wireframe(canvas, points: Points, color: str, width: int = 1, tags: str = ""):
    n = len(points)
    for i in range(n):
        p1, p2 = points[i], points[(i + 1) % n]
        canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=color, width=width, tags=tags)

class SecurityCamera:
    def __init__(self, x: float, y: float, base_angle: float, sweep_amplitude: float, sweep_speed: float = 0.025, fov_angle: float = math.radians(65), cone_range: float = 230.0):
        self.x, self.y = float(x), float(y)
        self.base_angle, self.sweep_amplitude, self.sweep_speed = float(base_angle), float(sweep_amplitude), float(sweep_speed)
        self.fov_angle, self.cone_range = float(fov_angle), float(cone_range)
        self.sweep_phase, self.current_angle = 0.0, self.base_angle
        self.vision_polygon: Points = []
        self.is_alarm_triggered = False
        self._update_cone()

    def _update_cone(self):
        self.current_angle = self.base_angle + self.sweep_amplitude * math.sin(self.sweep_phase)
        self.vision_polygon = CGMath.create_cone_polygon(origin_x=self.x, origin_y=self.y, facing_angle=self.current_angle, fov_angle=self.fov_angle, length=self.cone_range, num_arc_steps=16)

    def update(self, player) -> bool:
        # SWEEP ANIMATION TRANSLATION DISABLED
        # self.sweep_phase += self.sweep_speed
        
        self._update_cone()
        if not player.is_alive(): return False
        detected = CGMath.point_in_polygon(player.x, player.y, self.vision_polygon)
        if detected: self.is_alarm_triggered = True
        return detected

    def render(self, canvas, alarm_active: bool = False):
        cone_outline = "#FFFFFF" if (alarm_active or self.is_alarm_triggered) else "#666666"
        _draw_wireframe(canvas, self.vision_polygon, cone_outline, 1, "camera_cone")
        
        # Camera Lens line
        lx = self.x + 16.0 * math.cos(self.current_angle)
        ly = self.y + 16.0 * math.sin(self.current_angle)
        canvas.create_line(self.x, self.y, lx, ly, fill="#AAAAAA", width=3, capstyle="round", tags="camera_lens")