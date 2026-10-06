"""
Security Camera Module (Phase 5 Viewport Clipping)
- Mounted in room corner
- Sweeps vision cone polygon back and forth
- Vision cone clipped against active camera viewport window
"""

import math
from cg_math import CGMath, Points


class SecurityCamera:
    def __init__(self, x: float, y: float, base_angle: float, sweep_amplitude: float,
                 sweep_speed: float = 0.025, fov_angle: float = math.radians(65),
                 cone_range: float = 230.0):
        self.x = float(x)
        self.y = float(y)
        self.base_angle = float(base_angle)
        self.sweep_amplitude = float(sweep_amplitude)
        self.sweep_speed = float(sweep_speed)
        self.fov_angle = float(fov_angle)
        self.cone_range = float(cone_range)

        self.sweep_phase = 0.0
        self.current_angle = self.base_angle
        self.vision_polygon: Points = []
        self.is_alarm_triggered = False

        self._update_cone()

    def _update_cone(self):
        self.current_angle = self.base_angle + self.sweep_amplitude * math.sin(self.sweep_phase)
        self.vision_polygon = CGMath.create_cone_polygon(
            origin_x=self.x, origin_y=self.y,
            facing_angle=self.current_angle,
            fov_angle=self.fov_angle,
            length=self.cone_range,
            num_arc_steps=16
        )

    def update(self, player) -> bool:
        self.sweep_phase += self.sweep_speed
        self._update_cone()

        if not player.is_alive():
            return False

        detected = CGMath.point_in_polygon(player.x, player.y, self.vision_polygon)
        if detected:
            self.is_alarm_triggered = True

        return detected

    def render(self, canvas, camera, alarm_active: bool = False):
        xmin, ymin, xmax, ymax = camera.get_viewport_screen_bounds()

        # Transform and Clip Vision Polygon to Camera Viewport
        cone_screen = camera.world_to_screen(self.vision_polygon)
        clipped_cone = CGMath.clip_polygon_aabb(cone_screen, xmin, ymin, xmax, ymax)

        if len(clipped_cone) >= 3:
            cone_fill = "#ef4444" if (alarm_active or self.is_alarm_triggered) else "#00e5ff"
            cone_outline = "#f87171" if (alarm_active or self.is_alarm_triggered) else "#38bdf8"
            canvas.create_polygon(
                CGMath.flatten(clipped_cone),
                fill=cone_fill, outline=cone_outline, width=1, stipple="gray25", tags="camera_cone"
            )

        # Base Mount
        smx, smy = camera.world_to_screen_pt(self.x, self.y)
        if xmin - 20 <= smx <= xmax + 20 and ymin - 20 <= smy <= ymax + 20:
            mount_radius = 12.0
            canvas.create_oval(
                smx - mount_radius, smy - mount_radius,
                smx + mount_radius, smy + mount_radius,
                fill="#1e293b", outline="#475569", width=2, tags="camera_mount"
            )

            # Lens Barrel
            lx = self.x + 16.0 * math.cos(self.current_angle)
            ly = self.y + 16.0 * math.sin(self.current_angle)
            slx, sly = camera.world_to_screen_pt(lx, ly)
            canvas.create_line(smx, smy, slx, sly, fill="#94a3b8", width=5, capstyle="round", tags="camera_lens")

            # Status LED
            led_color = "#ef4444" if (alarm_active or self.is_alarm_triggered) else "#22c55e"
            canvas.create_oval(smx - 3, smy - 3, smx + 3, smy + 3, fill=led_color, outline="#ffffff", tags="camera_led")