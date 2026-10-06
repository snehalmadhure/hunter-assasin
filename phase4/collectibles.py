"""
Collectibles Module for 2D Top-Down Stealth Game
Strict Constraints:
- Coins: Yellow circles (~20px footprint). Uses CGMath.scale continuously for pulsing/glowing effect.
- Health Kits: Drawn as a plus sign (+). Restores 15% player health.
- Bresenham Overlap Detection: Checked against player's Bresenham circle hitbox.
- Floating Announcements: Fading/rising text notifications lasting 1.0 second (60 frames).
"""

import math
from typing import List, Tuple, Optional
from cg_math import CGMath, Point, Points


class FloatingText:
    """Floating UI notification that drifts upward for 1.0 second (60 ticks)."""
    def __init__(self, x: float, y: float, text: str, color: str = "#facc15", duration_frames: int = 60):
        self.x = float(x)
        self.y = float(y)
        self.text = text
        self.color = color
        self.life = duration_frames
        self.max_life = duration_frames
        self.vy = -1.4  # Drifts upward

    def update(self) -> bool:
        """Updates position and lifespan. Returns False when expired."""
        self.y += self.vy
        self.life -= 1
        return self.life > 0

    def render(self, canvas):
        """Draws floating text with a drop-shadow effect."""
        # Visual fade/size effect based on life fraction
        font_size = 11 if self.life > 15 else 9

        # Shadow
        canvas.create_text(
            self.x + 1, self.y + 1,
            text=self.text,
            fill="#000000",
            font=("Consolas", font_size, "bold"),
            tags="floating_text_shadow"
        )
        # Main text
        canvas.create_text(
            self.x, self.y,
            text=self.text,
            fill=self.color,
            font=("Consolas", font_size, "bold"),
            tags="floating_text"
        )


class Coin:
    """
    Collectible Coin: Yellow circular entity (~20px diameter).
    Continuously pulses/glows using CGMath.scale.
    """
    def __init__(self, x: float, y: float, radius: float = 10.0):
        self.x = float(x)
        self.y = float(y)
        self.base_radius = float(radius)  # 10px radius = 20px base size
        self.pulse_phase = 0.0
        self.pulse_speed = 0.08  # Radians per frame

        # Construct canonical 16-point circle polygon vertices around (self.x, self.y)
        self.base_polygon: Points = []
        num_segments = 16
        for i in range(num_segments):
            ang = (2.0 * math.pi / num_segments) * i
            px = self.x + self.base_radius * math.cos(ang)
            py = self.y + self.base_radius * math.sin(ang)
            self.base_polygon.append((px, py))

        # Current transformed polygon vertices after scaling
        self.current_polygon: Points = list(self.base_polygon)
        self.current_aura_polygon: Points = list(self.base_polygon)
        self.current_scale = 1.0

    def update(self):
        """
        Updates pulse oscillation and applies CGMath.scale around (self.x, self.y).
        """
        self.pulse_phase += self.pulse_speed
        # Oscillates between 0.85 and 1.20
        self.current_scale = 1.0 + 0.18 * math.sin(self.pulse_phase)

        # Scale coin body using CGMath.scale
        self.current_polygon = CGMath.scale(
            self.base_polygon, self.current_scale, self.x, self.y
        )

        # Scale glowing outer aura using CGMath.scale
        aura_scale = self.current_scale * 1.35
        self.current_aura_polygon = CGMath.scale(
            self.base_polygon, aura_scale, self.x, self.y
        )

    def collides_with_player_bresenham(self, player_hitbox_pts: List[Tuple[int, int]],
                                       player_x: float, player_y: float, player_r: float) -> bool:
        """
        Determines overlap between coin and player's Bresenham circular hitbox.
        1. Fast Euclidean distance bounding check.
        2. Exact check against player's rasterized Bresenham circle boundary points.
        """
        # Fast bounding check: distance between centers <= player_r + effective coin radius
        center_dist = CGMath.distance(self.x, self.y, player_x, player_y)
        if center_dist > (player_r + self.base_radius * self.current_scale + 4.0):
            return False

        # Exact Bresenham perimeter point overlap check
        coin_hit_r_sq = (self.base_radius * self.current_scale) ** 2
        for bx, by in player_hitbox_pts:
            d_sq = (bx - self.x) ** 2 + (by - self.y) ** 2
            if d_sq <= coin_hit_r_sq:
                return True

        # Center inside test
        return center_dist <= (player_r + self.base_radius)

    def render(self, canvas):
        """Renders glowing outer aura and scaled yellow coin."""
        flat_aura = CGMath.flatten(self.current_aura_polygon)
        flat_body = CGMath.flatten(self.current_polygon)

        # 1. Pulsing Outer Glow Aura
        canvas.create_polygon(
            flat_aura,
            fill="#854d0e", outline="#ca8a04", width=1, stipple="gray25", tags="coin_glow"
        )

        # 2. Main Yellow Coin Body
        canvas.create_polygon(
            flat_body,
            fill="#eab308", outline="#fef08a", width=2, tags="coin_body"
        )

        # 3. Inner Embossed Star / Dollar / Specular Highlight
        hi_r = self.base_radius * self.current_scale * 0.4
        canvas.create_oval(
            self.x - hi_r, self.y - hi_r, self.x + hi_r, self.y + hi_r,
            fill="#facc15", outline="#ffffff", width=1, tags="coin_inner"
        )


class HealthKit:
    """
    Collectible Health Kit (~20px footprint).
    Drawn as a distinct '+' Plus Sign inside a tactical med-pack container.
    Restores 15% player health on collection.
    """
    def __init__(self, x: float, y: float, size: float = 20.0):
        self.x = float(x)
        self.y = float(y)
        self.size = float(size)          # 20px footprint
        self.radius = self.size / 2.0    # 10px radius
        self.pulse_phase = 0.0
        self.pulse_speed = 0.05

        # Base 12-vertex '+' cross polygon centered at (self.x, self.y)
        # Plus arms width = 4px, span = 14px
        hw = 2.5   # half bar thickness
        hs = 7.0   # half bar length
        self.base_plus: Points = [
            (self.x - hw, self.y - hs),  # Top stem top-left
            (self.x + hw, self.y - hs),  # Top stem top-right
            (self.x + hw, self.y - hw),  # Corner
            (self.x + hs, self.y - hw),  # Right arm top
            (self.x + hs, self.y + hw),  # Right arm bottom
            (self.x + hw, self.y + hw),  # Corner
            (self.x + hw, self.y + hs),  # Bottom stem bottom-right
            (self.x - hw, self.y + hs),  # Bottom stem bottom-left
            (self.x - hw, self.y + hw),  # Corner
            (self.x - hs, self.y + hw),  # Left arm bottom
            (self.x - hs, self.y - hw),  # Left arm top
            (self.x - hw, self.y - hw),  # Corner
        ]

        # Base square container vertices (20px x 20px)
        s = self.radius
        self.base_box: Points = [
            (self.x - s, self.y - s),
            (self.x + s, self.y - s),
            (self.x + s, self.y + s),
            (self.x - s, self.y + s)
        ]

        self.current_plus = list(self.base_plus)
        self.current_box = list(self.base_box)
        self.current_scale = 1.0

    def update(self):
        """Gentle pulsing animation using CGMath.scale."""
        self.pulse_phase += self.pulse_speed
        self.current_scale = 1.0 + 0.10 * math.sin(self.pulse_phase)

        # Scale plus cross and container box
        self.current_plus = CGMath.scale(
            self.base_plus, self.current_scale, self.x, self.y
        )
        self.current_box = CGMath.scale(
            self.base_box, self.current_scale, self.x, self.y
        )

    def collides_with_player_bresenham(self, player_hitbox_pts: List[Tuple[int, int]],
                                       player_x: float, player_y: float, player_r: float) -> bool:
        """Checks overlap with player's Bresenham hitbox."""
        center_dist = CGMath.distance(self.x, self.y, player_x, player_y)
        if center_dist > (player_r + self.radius * self.current_scale + 4.0):
            return False

        kit_r_sq = (self.radius * self.current_scale) ** 2
        for bx, by in player_hitbox_pts:
            d_sq = (bx - self.x) ** 2 + (by - self.y) ** 2
            if d_sq <= kit_r_sq:
                return True

        return center_dist <= (player_r + self.radius)

    def render(self, canvas):
        """Renders medical pack with red cross on white background."""
        flat_box = CGMath.flatten(self.current_box)
        flat_plus = CGMath.flatten(self.current_plus)

        # Container box (White medical case with clean border)
        canvas.create_polygon(
            flat_box,
            fill="#f8fafc", outline="#cbd5e1", width=1.5, joinstyle="round", tags="medkit_box"
        )

        # Red '+' Plus Sign
        canvas.create_polygon(
            flat_plus,
            fill="#ef4444", outline="#dc2626", width=1, tags="medkit_plus"
        )


class CollectibleManager:
    """Manages spawning, updating, collision, and rendering of all collectibles & announcements."""

    def __init__(self):
        self.coins: List[Coin] = []
        self.health_kits: List[HealthKit] = []
        self.announcements: List[FloatingText] = []

    def populate_map(self, map_engine):
        """
        Populates the map with strategically positioned Coins and Health Kits
        inside the 100px corridors.
        """
        ox = map_engine.ox
        oy = map_engine.oy
        wt = map_engine.WALL_THICKNESS
        pw = map_engine.PASSAGE_WIDTH
        bs = map_engine.BOX_SIZE

        # ---------------------------------------------------------------------
        # Pre-calculated corridor passage centers (all perfectly in 100px paths)
        # ---------------------------------------------------------------------
        # Passage column centers:
        col_centers = [
            ox + wt + pw / 2.0,                  # Left corridor: 60+5+50 = 115
            ox + wt + pw + bs + pw / 2.0,         # Col 1-2 corridor: 165+120+50 = 335
            ox + wt + 2 * pw + 2 * bs + pw / 2.0, # Col 2-3 corridor: 385+120+50 = 555
            ox + wt + 3 * pw + 3 * bs + pw / 2.0  # Right corridor: 605+120+50 = 775
        ]

        # Passage row centers:
        row_centers = [
            oy + wt + pw / 2.0,                  # Top corridor: 60+5+50 = 115
            oy + wt + pw + bs + pw / 2.0,         # Mid corridor: 165+120+50 = 335
            oy + wt + 2 * pw + 2 * bs + pw / 2.0  # Bottom corridor: 385+120+50 = 555
        ]

        # Box column centers (for placing in horizontal corridors):
        box_col_centers = [
            ox + wt + pw + bs / 2.0,              # Box 1 center X: 165+60 = 225
            ox + wt + 2 * pw + 1.5 * bs,          # Box 2 center X: 385+60 = 445
            ox + wt + 3 * pw + 2.5 * bs           # Box 3 center X: 605+60 = 665
        ]

        # Place 7 Yellow Coins
        coin_positions = [
            (box_col_centers[0], row_centers[0]),  # Top corridor (225, 115)
            (box_col_centers[1], row_centers[0]),  # Top corridor (445, 115)
            (box_col_centers[2], row_centers[0]),  # Top corridor (665, 115)
            (col_centers[3], row_centers[1]),      # Right corridor (775, 335)
            (box_col_centers[0], row_centers[2]),  # Bottom corridor (225, 555)
            (box_col_centers[1], row_centers[2]),  # Bottom corridor (445, 555)
            (box_col_centers[2], row_centers[2]),  # Bottom corridor (665, 555)
        ]
        for cx, cy in coin_positions:
            self.coins.append(Coin(cx, cy, radius=10.0))

        # Place 3 Health Kits
        medkit_positions = [
            (col_centers[0], row_centers[1]),      # Left corridor (115, 335)
            (col_centers[1], row_centers[1]),      # Middle corridor (335, 335)
            (col_centers[2], row_centers[1]),      # Middle corridor (555, 335)
        ]
        for mx, my in medkit_positions:
            self.health_kits.append(HealthKit(mx, my, size=20.0))

    def update_and_collide(self, player) -> Tuple[int, float]:
        """
        Updates animation cycles, checks Bresenham circular hitbox overlap,
        removes collected items, and returns (score_earned, hp_healed).
        """
        score_gained = 0
        hp_healed = 0.0

        # 1. Update Coins & Check Collision with Player Bresenham Hitbox
        remaining_coins: List[Coin] = []
        for coin in self.coins:
            coin.update()
            if coin.collides_with_player_bresenham(player.hitbox_points, player.x, player.y, player.radius):
                score_gained += 10
                # Spawn floating announcement
                self.announcements.append(
                    FloatingText(coin.x, coin.y - 12.0, "+10 SCORE", color="#facc15", duration_frames=60)
                )
            else:
                remaining_coins.append(coin)
        self.coins = remaining_coins

        # 2. Update Health Kits & Check Collision
        remaining_kits: List[HealthKit] = []
        for kit in self.health_kits:
            kit.update()
            if kit.collides_with_player_bresenham(player.hitbox_points, player.x, player.y, player.radius):
                heal_amount = 15.0
                player.heal(heal_amount)
                hp_healed += heal_amount
                # Spawn floating announcement
                self.announcements.append(
                    FloatingText(kit.x, kit.y - 12.0, "+15% HP", color="#22c55e", duration_frames=60)
                )
            else:
                remaining_kits.append(kit)
        self.health_kits = remaining_kits

        # 3. Update Floating Announcements
        self.announcements = [a for a in self.announcements if a.update()]

        return score_gained, hp_healed

    def render(self, canvas):
        """Renders all collectibles and floating text announcements."""
        # 1. Coins (Pulsing glowing yellow circles)
        for coin in self.coins:
            coin.render(canvas)

        # 2. Health Kits (Plus sign +)
        for kit in self.health_kits:
            kit.render(canvas)

        # 3. Floating Announcements (Fading / upward drifting text)
        for announcement in self.announcements:
            announcement.render(canvas)
