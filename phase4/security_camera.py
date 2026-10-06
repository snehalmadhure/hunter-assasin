"""
Security Camera Module for 2D Top-Down Stealth Game
Strict Constraints:
- Mounted in corner of room (sweeps a large vision cone back and forth).
- Vision cone created with CGMath.create_cone_polygon.
- Checks player intrusion using CGMath.point_in_polygon.
- Triggers global alarm when player enters sweep cone.
"""

import math
from typing import List, Tuple
from cg_math import CGMath, Point, Points


class SecurityCamera:
    """
    Security Camera mounted in a room corner.
    Oscillates a wide vision cone back and forth.
    """

    def __init__(self, x: float, y: float, base_angle: float, sweep_amplitude: float,
                 sweep_speed: float = 0.025, fov_angle: float = math.radians(65),
                 cone_range: float = 230.0):
        self.x = float(x)
        self.y = float(y)
        self.base_angle = float(base_angle)           # Center direction of sweep
        self.sweep_amplitude = float(sweep_amplitude) # Angular sweep range (+/- rad)
        self.sweep_speed = float(sweep_speed)         # Angular sweep speed
        self.fov_angle = float(fov_angle)             # Vision cone width
        self.cone_range = float(cone_range)           # Range of vision cone

        self.sweep_phase = 0.0
        self.current_angle = self.base_angle
        self.vision_polygon: Points = []
        self.is_alarm_triggered = False

        self._update_cone()

    def _update_cone(self):
        """Updates sweep orientation and constructs cone polygon."""
        self.current_angle = self.base_angle + self.sweep_amplitude * math.sin(self.sweep_phase)
        self.vision_polygon = CGMath.create_cone_polygon(
            origin_x=self.x,
            origin_y=self.y,
            facing_angle=self.current_angle,
            fov_angle=self.fov_angle,
            length=self.cone_range,
            num_arc_steps=16
        )

    def update(self, player) -> bool:
        """
        Advances sweep oscillation and checks if player intersects camera vision cone
        using CGMath.point_in_polygon.
        Returns True if player is detected.
        """
        # Advance sweep angle
        self.sweep_phase += self.sweep_speed
        self._update_cone()

        if not player.is_alive():
            return False

        # Ray-casting Jordan Curve test
        detected = CGMath.point_in_polygon(player.x, player.y, self.vision_polygon)
        if detected:
            self.is_alarm_triggered = True

        return detected

    def render(self, canvas, alarm_active: bool = False):
        """Renders sweeping camera cone, base mount, lens, and status LEDs."""
        flat_cone = CGMath.flatten(self.vision_polygon)

        # 1. Sweeping Vision Cone
        cone_fill = "#ef4444" if (alarm_active or self.is_alarm_triggered) else "#00e5ff"
        cone_outline = "#f87171" if (alarm_active or self.is_alarm_triggered) else "#38bdf8"

        canvas.create_polygon(
            flat_cone,
            fill=cone_fill,
            outline=cone_outline,
            width=1,
            stipple="gray25",
            tags="camera_cone"
        )

        # 2. Camera Bracket / Corner Mount Housing
        mount_radius = 12.0
        canvas.create_oval(
            self.x - mount_radius, self.y - mount_radius,
            self.x + mount_radius, self.y + mount_radius,
            fill="#1e293b", outline="#475569", width=2, tags="camera_mount"
        )

        # 3. Directional Lens barrel pointing in current_angle
        lens_len = 16.0
        lx = self.x + lens_len * math.cos(self.current_angle)
        ly = self.y + lens_len * math.sin(self.current_angle)
        canvas.create_line(
            self.x, self.y, lx, ly,
            fill="#94a3b8", width=5, capstyle="round", tags="camera_lens"
        )

        # 4. Status Indicator LED (Red when alarm active, Cyan when scanning)
        led_color = "#ef4444" if (alarm_active or self.is_alarm_triggered) else "#22c55e"
        canvas.create_oval(
            self.x - 3, self.y - 3, self.x + 3, self.y + 3,
            fill=led_color, outline="#ffffff", width=1, tags="camera_led"
        )
