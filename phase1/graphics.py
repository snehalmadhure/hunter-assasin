import pygame


def bresenham_line(surface, x1, y1, x2, y2, color):
    """
    Bresenham's Line Drawing Algorithm
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
