import math
import pygame
from graphics import bresenham_line, bresenham_circle
from game_map import CELL_SIZE


class Player:

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.radius = 10
        self.speed = 2.5
        self.health = 100
        self.shield_radius = 14

    def update(self, keys, game_map):
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += self.speed

        new_x = self.x + dx
        if not self.check_collision(new_x, self.y, game_map):
            self.x = new_x

        new_y = self.y + dy
        if not self.check_collision(self.x, new_y, game_map):
            self.y = new_y

    def check_collision(self, px, py, game_map):
        margin = self.radius
        corners = [
            (px - margin, py - margin),
            (px + margin, py - margin),
            (px - margin, py + margin),
            (px + margin, py + margin),
        ]
        for cx, cy in corners:
            col = int(cx // CELL_SIZE)
            row = int(cy // CELL_SIZE)
            if game_map.is_wall(row, col):
                return True
        return False

    def draw(self, screen):
        ix, iy = int(round(self.x)), int(round(self.y))

        p1 = (ix, iy - 8)
        p2 = (ix - 7, iy + 6)
        p3 = (ix + 7, iy + 6)
        bresenham_line(screen, p1[0], p1[1], p2[0], p2[1], (255, 255, 255))
        bresenham_line(screen, p2[0], p2[1], p3[0], p3[1], (255, 255, 255))
        bresenham_line(screen, p3[0], p3[1], p1[0], p1[1], (255, 255, 255))

        bresenham_circle(screen, ix, iy, self.shield_radius, (255, 255, 255))


class Enemy:

    def __init__(self, x, y, facing_angle_deg, sight_radius=100):
        self.x = float(x)
        self.y = float(y)
        self.facing_angle = facing_angle_deg  # In degrees
        self.sight_radius = sight_radius
        self.fov_half_angle = 45.0  # +/- 45 deg FOV Cone
        self.is_player_detected = False

    def update_detection(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist > self.sight_radius:
            self.is_player_detected = False
            return False

        angle_to_player = math.degrees(math.atan2(dy, dx))
        rel_angle = (angle_to_player - self.facing_angle + 180) % 360 - 180

        if abs(rel_angle) <= self.fov_half_angle:
            self.is_player_detected = True
            return True
        else:
            self.is_player_detected = False
            return False

    def draw(self, screen):
        ix, iy = int(round(self.x)), int(round(self.y))
        color = (255, 255, 255)

        # 1. Draw Enemy Triangle Body pointing in facing direction
        rad_facing = math.radians(self.facing_angle)
        tip_x = ix + int(10 * math.cos(rad_facing))
        tip_y = iy + int(10 * math.sin(rad_facing))

        left_base_x = ix + int(8 * math.cos(rad_facing + math.radians(135)))
        left_base_y = iy + int(8 * math.sin(rad_facing + math.radians(135)))

        right_base_x = ix + int(8 * math.cos(rad_facing - math.radians(135)))
        right_base_y = iy + int(8 * math.sin(rad_facing - math.radians(135)))

        bresenham_line(screen, tip_x, tip_y, left_base_x, left_base_y, color)
        bresenham_line(screen, left_base_x, left_base_y, right_base_x, right_base_y, color)
        bresenham_line(screen, right_base_x, right_base_y, tip_x, tip_y, color)

        # 2. Draw 45°-45° FOV Cone Boundary Rays
        left_angle_rad = math.radians(self.facing_angle - self.fov_half_angle)
        right_angle_rad = math.radians(self.facing_angle + self.fov_half_angle)

        lx = ix + int(self.sight_radius * math.cos(left_angle_rad))
        ly = iy + int(self.sight_radius * math.sin(left_angle_rad))

        rx = ix + int(self.sight_radius * math.cos(right_angle_rad))
        ry = iy + int(self.sight_radius * math.sin(right_angle_rad))

        # Ray lines from enemy center to cone edges
        bresenham_line(screen, ix, iy, lx, ly, color)
        bresenham_line(screen, ix, iy, rx, ry, color)

        # 3. Draw Front Arc across the 90° FOV Cone
        steps = 16
        for i in range(steps):
            a1 = math.radians(self.facing_angle - self.fov_half_angle + (i * 90.0 / steps))
            a2 = math.radians(self.facing_angle - self.fov_half_angle + ((i + 1) * 90.0 / steps))

            x1 = ix + int(self.sight_radius * math.cos(a1))
            y1 = iy + int(self.sight_radius * math.sin(a1))
            x2 = ix + int(self.sight_radius * math.cos(a2))
            y2 = iy + int(self.sight_radius * math.sin(a2))

            bresenham_line(screen, x1, y1, x2, y2, color)