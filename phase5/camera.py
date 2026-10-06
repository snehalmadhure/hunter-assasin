"""
Camera Viewport Module for 2D Stealth Game (Phase 5)
Follows the player while keeping ample surrounding visible space.
Provides World-to-Screen matrix transformations and active viewport clipping bounds.
"""

from typing import Tuple
from cg_math import CGMath, Point, Points


class Camera:
    """
    Camera tracks player position and defines active screen viewport boundaries.
    """

    def __init__(self, screen_offset_x: float, screen_offset_y: float,
                 viewport_w: float = 720.0, viewport_h: float = 520.0):
        self.screen_offset_x = float(screen_offset_x)
        self.screen_offset_y = float(screen_offset_y)
        self.viewport_w = float(viewport_w)
        self.viewport_h = float(viewport_h)

        # Camera world offset (top-left of camera view)
        self.x = 0.0
        self.y = 0.0

    def follow(self, target_x: float, target_y: float):
        """
        Centers the viewport on the player target.
        Leaves space visible on all sides of the player.
        """
        self.x = target_x - (self.viewport_w / 2.0)
        self.y = target_y - (self.viewport_h / 2.0)

    def world_to_screen(self, pts: Points) -> Points:
        """
        Transforms world coordinates to camera viewport screen space:
        screen_pt = world_pt - camera_origin + screen_canvas_offset
        """
        return CGMath.translate(pts, -self.x + self.screen_offset_x, -self.y + self.screen_offset_y)

    def world_to_screen_pt(self, wx: float, wy: float) -> Tuple[float, float]:
        pts = self.world_to_screen([(wx, wy)])
        return pts[0]

    def get_viewport_screen_bounds(self) -> Tuple[float, float, float, float]:
        """Returns (xmin, ymin, xmax, ymax) of active clipping window in screen canvas space."""
        xmin = self.screen_offset_x
        ymin = self.screen_offset_y
        xmax = self.screen_offset_x + self.viewport_w
        ymax = self.screen_offset_y + self.viewport_h
        return (xmin, ymin, xmax, ymax)