def bresenham_line(surface, x1, y1, x2, y2, color):
    """Draws a line on a Pygame surface using Bresenham's Line Algorithm."""
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        if 0 <= x1 < surface.get_width() and 0 <= y1 < surface.get_height():
            surface.set_at((x1, y1), color)
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy


def dda_line(surface, x1, y1, x2, y2, color):
    """Draws a line on a Pygame surface using Digital Differential Analyzer (DDA) Algorithm."""
    x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
    dx = x2 - x1
    dy = y2 - y1
    steps = int(max(abs(dx), abs(dy)))
    if steps == 0:
        if 0 <= int(x1) < surface.get_width() and 0 <= int(y1) < surface.get_height():
            surface.set_at((int(x1), int(y1)), color)
        return

    x_inc = dx / steps
    y_inc = dy / steps
    x, y = x1, y1

    for _ in range(steps + 1):
        ix, iy = int(round(x)), int(round(y))
        if 0 <= ix < surface.get_width() and 0 <= iy < surface.get_height():
            surface.set_at((ix, iy), color)
        x += x_inc
        y += y_inc


def bresenham_circle(surface, xc, yc, r, color):
    """Draws a circle outline using Bresenham's / Midpoint Circle Algorithm with 8-way symmetry."""
    xc, yc, r = int(xc), int(yc), int(r)
    x = 0
    y = r
    d = 3 - 2 * r

    def set_pixel(px, py):
        if 0 <= px < surface.get_width() and 0 <= py < surface.get_height():
            surface.set_at((px, py), color)

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