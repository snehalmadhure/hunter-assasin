"""
CGMath: Mathematical Foundation for 2D Top-Down Stealth Game (Phase 5)
Implements fundamental Computer Graphics concepts without third-party engines:
- Homogeneous 3x3 Affine Transformation Matrices (Translation, Rotation, Scaling)
- Bresenham's Circle Algorithm with decision parameter (1 - 2R)
- Point-in-Polygon ray-casting for vision cones & hit detection
- Sutherland-Hodgman Polygon Clipping against AABB Viewport
- Cohen-Sutherland Line Clipping Algorithm
"""

import math
from typing import List, Tuple, Union, Optional

Point = Tuple[float, float]
Points = List[Point]
Matrix3x3 = List[List[float]]


class CGMath:
    """
    Computer Graphics Mathematics utility class.
    All transformations use homogeneous 3x3 matrices.
    """

    # -------------------------------------------------------------------------
    # 1. Matrix Multiplication & Point Transformations
    # -------------------------------------------------------------------------

    @staticmethod
    def identity_matrix() -> Matrix3x3:
        """Returns a 3x3 identity matrix."""
        return [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ]

    @staticmethod
    def matmul_3x3(a: Matrix3x3, b: Matrix3x3) -> Matrix3x3:
        """Multiplies two 3x3 matrices: result = A x B."""
        result = [[0.0, 0.0, 0.0] for _ in range(3)]
        for i in range(3):
            for j in range(3):
                result[i][j] = (
                    a[i][0] * b[0][j] +
                    a[i][1] * b[1][j] +
                    a[i][2] * b[2][j]
                )
        return result

    @staticmethod
    def transform_point(matrix: Matrix3x3, point: Point) -> Point:
        """Multiplies a 3x3 affine matrix with a 2D homogeneous point."""
        x, y = point
        nx = matrix[0][0] * x + matrix[0][1] * y + matrix[0][2] * 1.0
        ny = matrix[1][0] * x + matrix[1][1] * y + matrix[1][2] * 1.0
        w  = matrix[2][0] * x + matrix[2][1] * y + matrix[2][2] * 1.0
        if w != 1.0 and w != 0.0:
            nx /= w
            ny /= w
        return (nx, ny)

    @staticmethod
    def transform_points(matrix: Matrix3x3, points: Points) -> Points:
        """Applies a 3x3 affine matrix to a collection of 2D points."""
        return [CGMath.transform_point(matrix, pt) for pt in points]

    # -------------------------------------------------------------------------
    # 2. Affine Matrix Operations
    # -------------------------------------------------------------------------

    @staticmethod
    def translation_matrix(dx: float, dy: float) -> Matrix3x3:
        return [
            [1.0, 0.0, float(dx)],
            [0.0, 1.0, float(dy)],
            [0.0, 0.0, 1.0]
        ]

    @classmethod
    def translate(cls, points: Points, dx: float, dy: float) -> Points:
        t_mat = cls.translation_matrix(dx, dy)
        return cls.transform_points(t_mat, points)

    @staticmethod
    def rotation_matrix(angle_rad: float) -> Matrix3x3:
        c = math.cos(angle_rad)
        s = math.sin(angle_rad)
        return [
            [c,   -s,   0.0],
            [s,    c,   0.0],
            [0.0, 0.0, 1.0]
        ]

    @classmethod
    def rotate(cls, points: Points, angle: float, center_x: float, center_y: float, in_degrees: bool = False) -> Points:
        angle_rad = math.radians(angle) if in_degrees else angle
        t_to_origin = cls.translation_matrix(-center_x, -center_y)
        r_mat = cls.rotation_matrix(angle_rad)
        t_back = cls.translation_matrix(center_x, center_y)
        m_composite = cls.matmul_3x3(cls.matmul_3x3(t_back, r_mat), t_to_origin)
        return cls.transform_points(m_composite, points)

    @staticmethod
    def scaling_matrix(sx: float, sy: float) -> Matrix3x3:
        return [
            [float(sx), 0.0,       0.0],
            [0.0,       float(sy), 0.0],
            [0.0,       0.0,       1.0]
        ]

    @classmethod
    def scale(cls, points: Points, scale_factor: Union[float, Tuple[float, float]],
              center_x: float, center_y: float) -> Points:
        if isinstance(scale_factor, (int, float)):
            sx = sy = float(scale_factor)
        else:
            sx, sy = float(scale_factor[0]), float(scale_factor[1])

        t_to_origin = cls.translation_matrix(-center_x, -center_y)
        s_mat = cls.scaling_matrix(sx, sy)
        t_back = cls.translation_matrix(center_x, center_y)
        m_composite = cls.matmul_3x3(cls.matmul_3x3(t_back, s_mat), t_to_origin)
        return cls.transform_points(m_composite, points)

    # -------------------------------------------------------------------------
    # 3. Sutherland-Hodgman Polygon Clipping (Phase 5 Requirement)
    # -------------------------------------------------------------------------

    @staticmethod
    def clip_polygon_aabb(polygon: Points, xmin: float, ymin: float, xmax: float, ymax: float) -> Points:
        """
        Sutherland-Hodgman Polygon Clipping algorithm against AABB camera viewport bounds.
        Clips arbitrary 2D polygon vertices to [xmin, ymin, xmax, ymax].
        """
        if not polygon:
            return []

        def intersection(p1: Point, p2: Point, edge_type: int) -> Point:
            x1, y1 = p1
            x2, y2 = p2
            dx = x2 - x1
            dy = y2 - y1

            if edge_type == 0:   # Left: x = xmin
                x = xmin
                y = y1 + dy * (xmin - x1) / dx if dx != 0 else y1
            elif edge_type == 1: # Right: x = xmax
                x = xmax
                y = y1 + dy * (xmax - x1) / dx if dx != 0 else y1
            elif edge_type == 2: # Top: y = ymin
                y = ymin
                x = x1 + dx * (ymin - y1) / dy if dy != 0 else x1
            else:                # Bottom: y = ymax
                y = ymax
                x = x1 + dx * (ymax - y1) / dy if dy != 0 else x1
            return (x, y)

        def clip_edge(poly: Points, edge_type: int) -> Points:
            clipped: Points = []
            if not poly:
                return clipped

            s = poly[-1]
            for p in poly:
                if edge_type == 0:   # Left
                    s_in = (s[0] >= xmin)
                    p_in = (p[0] >= xmin)
                elif edge_type == 1: # Right
                    s_in = (s[0] <= xmax)
                    p_in = (p[0] <= xmax)
                elif edge_type == 2: # Top
                    s_in = (s[1] >= ymin)
                    p_in = (p[1] >= ymin)
                else:                # Bottom
                    s_in = (s[1] <= ymax)
                    p_in = (p[1] <= ymax)

                if p_in:
                    if not s_in:
                        clipped.append(intersection(s, p, edge_type))
                    clipped.append(p)
                elif s_in:
                    clipped.append(intersection(s, p, edge_type))
                s = p
            return clipped

        output = polygon
        for edge in range(4):
            output = clip_edge(output, edge)
        return output

    # -------------------------------------------------------------------------
    # 4. Cohen-Sutherland Line Clipping (Phase 5 Requirement)
    # -------------------------------------------------------------------------

    @staticmethod
    def clip_line_cohen_sutherland(x1: float, y1: float, x2: float, y2: float,
                                   xmin: float, ymin: float, xmax: float, ymax: float) -> Optional[Tuple[float, float, float, float]]:
        """
        Cohen-Sutherland Line Clipping Algorithm against camera viewport bounds.
        Returns clipped line segment (cx1, cy1, cx2, cy2) or None if outside.
        """
        INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8

        def compute_code(x: float, y: float) -> int:
            code = INSIDE
            if x < xmin: code |= LEFT
            elif x > xmax: code |= RIGHT
            if y < ymin: code |= TOP
            elif y > ymax: code |= BOTTOM
            return code

        code1 = compute_code(x1, y1)
        code2 = compute_code(x2, y2)
        accept = False

        while True:
            if code1 == 0 and code2 == 0:
                accept = True
                break
            elif (code1 & code2) != 0:
                break
            else:
                code_out = code1 if code1 != 0 else code2
                if code_out & BOTTOM:
                    x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1) if (y2 - y1) != 0 else x1
                    y = ymax
                elif code_out & TOP:
                    x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1) if (y2 - y1) != 0 else x1
                    y = ymin
                elif code_out & RIGHT:
                    y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1) if (x2 - x1) != 0 else y1
                    x = xmax
                elif code_out & LEFT:
                    y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1) if (x2 - x1) != 0 else y1
                    x = xmin

                if code_out == code1:
                    x1, y1 = x, y
                    code1 = compute_code(x1, y1)
                else:
                    x2, y2 = x, y
                    code2 = compute_code(x2, y2)

        if accept:
            return (x1, y1, x2, y2)
        return None

    # -------------------------------------------------------------------------
    # 5. Bresenham's Circle & Ray Casting
    # -------------------------------------------------------------------------

    @staticmethod
    def bresenham_circle(xc: Union[int, float], yc: Union[int, float], r: Union[int, float]) -> List[Tuple[int, int]]:
        radius = int(round(r))
        cx = int(round(xc))
        cy = int(round(yc))

        if radius <= 0:
            return [(cx, cy)]

        x = 0
        y = radius
        d = 1 - 2 * radius
        circle_points = set()

        def add_octant_points(px: int, py: int):
            circle_points.add((cx + px, cy + py))
            circle_points.add((cx - px, cy + py))
            circle_points.add((cx + px, cy - py))
            circle_points.add((cx - px, cy - py))
            circle_points.add((cx + py, cy + px))
            circle_points.add((cx - py, cy + px))
            circle_points.add((cx + py, cy - px))
            circle_points.add((cx - py, cy - px))

        while x <= y:
            add_octant_points(x, y)
            if d < 0:
                d += 2 * x + 3
                x += 1
            else:
                d += 2 * (x - y) + 5
                x += 1
                y -= 1

        return sorted(list(circle_points))

    @staticmethod
    def point_in_polygon(x: float, y: float, polygon_points: Points) -> bool:
        n = len(polygon_points)
        if n < 3:
            return False

        inside = False
        p1x, p1y = polygon_points[0]

        for i in range(1, n + 1):
            p2x, p2y = polygon_points[i % n]
            if min(p1y, p2y) < y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        x_inters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    else:
                        x_inters = p1x
                    if p1x == p2x or x <= x_inters:
                        inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    @staticmethod
    def distance(x1: float, y1: float, x2: float, y2: float) -> float:
        return math.hypot(x2 - x1, y2 - y1)

    @staticmethod
    def flatten(points: Points) -> List[float]:
        flat = []
        for x, y in points:
            flat.extend([float(x), float(y)])
        return flat

    @staticmethod
    def create_cone_polygon(origin_x: float, origin_y: float, facing_angle: float,
                            fov_angle: float, length: float, num_arc_steps: int = 12) -> Points:
        pts: Points = [(origin_x, origin_y)]
        half_fov = fov_angle / 2.0
        start_ang = facing_angle - half_fov
        step_ang = fov_angle / float(num_arc_steps)

        for i in range(num_arc_steps + 1):
            curr_ang = start_ang + i * step_ang
            px = origin_x + length * math.cos(curr_ang)
            py = origin_y + length * math.sin(curr_ang)
            pts.append((px, py))

        return pts