import math


# ============================================================
# BRESENHAM'S LINE DRAWING ALGORITHM
# ============================================================

def bresenham_line(surface, x1, y1, x2, y2, color):
    """
    Bresenham's Line Drawing Algorithm.
    Identical implementation carried forward from Phase 1 & 2.
    """

    x1 = int(x1)
    y1 = int(y1)
    x2 = int(x2)
    y2 = int(y2)

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)

    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1

    error = dx - dy

    while True:

        if (
            0 <= x1 < surface.get_width()
            and 0 <= y1 < surface.get_height()
        ):
            surface.set_at((x1, y1), color)

        if x1 == x2 and y1 == y2:
            break

        e2 = 2 * error

        if e2 > -dy:
            error -= dy
            x1 += sx

        if e2 < dx:
            error += dx
            y1 += sy


# ============================================================
# DDA LINE DRAWING ALGORITHM
# ============================================================

def dda_line(surface, x1, y1, x2, y2, color):
    """
    Digital Differential Analyzer (DDA) Line Algorithm.
    Carried forward from Phase 2.
    """

    x1 = float(x1)
    y1 = float(y1)
    x2 = float(x2)
    y2 = float(y2)

    dx = x2 - x1
    dy = y2 - y1

    steps = int(max(abs(dx), abs(dy)))

    if steps == 0:
        if (
            0 <= int(x1) < surface.get_width()
            and 0 <= int(y1) < surface.get_height()
        ):
            surface.set_at((int(x1), int(y1)), color)
        return

    x_inc = dx / steps
    y_inc = dy / steps

    x = x1
    y = y1

    for _ in range(steps + 1):

        ix = int(round(x))
        iy = int(round(y))

        if (
            0 <= ix < surface.get_width()
            and 0 <= iy < surface.get_height()
        ):
            surface.set_at((ix, iy), color)

        x += x_inc
        y += y_inc


# ============================================================
# BRESENHAM'S MIDPOINT CIRCLE ALGORITHM
# ============================================================

def bresenham_circle(surface, xc, yc, r, color):
    """
    Bresenham's / Midpoint Circle Algorithm.
    Uses 8-way symmetry. Carried forward from Phase 2.
    """

    xc = int(xc)
    yc = int(yc)
    r  = int(r)

    x = 0
    y = r
    d = 3 - 2 * r


    # --------------------------------------------------------
    # HELPER: SET PIXEL SAFELY
    # --------------------------------------------------------

    def set_pixel(px, py):
        if (
            0 <= px < surface.get_width()
            and 0 <= py < surface.get_height()
        ):
            surface.set_at((px, py), color)


    # --------------------------------------------------------
    # HELPER: PLOT ALL 8 OCTANTS
    # --------------------------------------------------------

    def plot_octants(cx, cy, px, py):
        set_pixel(cx + px, cy + py)
        set_pixel(cx - px, cy + py)
        set_pixel(cx + px, cy - py)
        set_pixel(cx - px, cy - py)
        set_pixel(cx + py, cy + px)
        set_pixel(cx - py, cy + px)
        set_pixel(cx + py, cy - px)
        set_pixel(cx - py, cy - px)


    plot_octants(xc, yc, x, y)

    while y >= x:

        x += 1

        if d > 0:
            y -= 1
            d = d + 4 * (x - y) + 10
        else:
            d = d + 4 * x + 6

        plot_octants(xc, yc, x, y)
