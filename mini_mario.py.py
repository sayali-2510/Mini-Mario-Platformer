# -*- coding: utf-8 -*-
"""
Mini Mario-Style Platformer Game
=================================
A beginner-friendly, well-commented 2D platformer using:
  - tkinter  : GUI window, canvas rendering, buttons
  - numpy    : grid-based level representation

Controls:
  Arrow Keys / A-D : Move Left / Right
  Space / Up Arrow : Jump
  On-screen buttons also work.

File Handling:
  leaderboard.txt: stores all-time top scores

Author: Generated for Mini Project
"""

import tkinter as tk
import numpy as np
import os

# ===========================================================
#  LEVEL DESIGN  (numpy 2D array)
# ===========================================================
# Grid legend:
#   0 = empty air
#   1 = platform/ground tile
#   2 = coin
#   3 = enemy spawn point

LEVEL_1 = np.array([
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 2, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0],
    [0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # ground
])

LEVEL_2 = np.array([
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0],
    [0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
    [0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 3, 0, 0, 0, 0],
    [0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
])

LEVELS = [LEVEL_1, LEVEL_2]   # add more levels here easily

# ===========================================================
#  CONSTANTS  (easy to tweak)
# ===========================================================
TILE_SIZE    = 48     # pixels per grid cell
COLS         = 16      # grid columns (must match level arrays above)
ROWS         = 8       # grid rows
WIN_W        = TILE_SIZE * COLS   # 768
WIN_H        = TILE_SIZE * ROWS   # 384

GRAVITY      = 0.5     # pulls player down each frame (lower = floatier jump)
JUMP_FORCE   = -17     # initial upward velocity on jump (more negative = higher jump)
MOVE_SPEED   = 4       # horizontal pixels per frame
FPS_DELAY    = 33      # ~30 fps  (milliseconds between frames)

# Colours
COL_SKY      = "#87CEEB"
COL_GROUND   = "#8B4513"
COL_PLATFORM = "#A0522D"
COL_PLAYER   = "#FF0000"
COL_COIN     = "#FFD700"
COL_ENEMY    = "#32CD32"
COL_SCORE    = "white"


# ===========================================================
#  FILE HANDLING HELPERS
# ===========================================================

def update_leaderboard(name: str, score: int):
    """Append this game's score to leaderboard.txt."""
    with open("leaderboard.txt", "a") as f:
        f.write(f"{name}:{score}\n")


def get_leaderboard():
    """
    Read leaderboard.txt and return sorted list of (name, score) tuples.
    Returns top 10 highest scores.
    """
    if not os.path.exists("leaderboard.txt"):
        return []
    entries = []
    with open("leaderboard.txt", "r") as f:
        for line in f:
            line = line.strip()
            if ":" in line:
                n, s = line.split(":", 1)
                try:
                    entries.append((n, int(s)))
                except ValueError:
                    pass
    # Sort by score descending, take top 10
    entries.sort(key=lambda x: x[1], reverse=True)
    return entries[:10]


# ===========================================================
#  PLAYER CLASS
# ===========================================================

class Player:
    """
    Represents the Mario-like player character.

    Attributes:
        col, row  : grid position (float for smooth movement)
        vx, vy    : velocity in x and y directions
        on_ground : True when standing on a platform
        alive     : False when hit by enemy
        score     : coins collected
    """

    def __init__(self, canvas: tk.Canvas, start_col: int = 1, start_row: int = 6):
        self.canvas = canvas

        # Position in pixel space (col * TILE_SIZE, row * TILE_SIZE)
        self.x = float(start_col * TILE_SIZE)
        self.y = float(start_row * TILE_SIZE)

        self.vx = 0.0          # horizontal velocity
        self.vy = 0.0          # vertical velocity
        self.on_ground = False
        self.alive = True
        self.score = 0

        # Size of the player rectangle (slightly smaller than a tile)
        self.w = TILE_SIZE - 8
        self.h = TILE_SIZE - 4

        # Draw the player on the canvas; store the item id so we can move it
        self.body = canvas.create_rectangle(
            self.x, self.y,
            self.x + self.w, self.y + self.h,
            fill=COL_PLAYER, outline="darkred", width=2, tags="player"
        )
        # Simple "hat" to look a bit like Mario
        self.hat = canvas.create_rectangle(
            self.x + 4, self.y - 10,
            self.x + self.w - 4, self.y,
            fill="darkred", outline="", tags="player"
        )

    def jump(self):
        """Make the player jump (only if standing on ground)."""
        if self.on_ground:
            self.vy = JUMP_FORCE
            self.on_ground = False

    def move_left(self):
        """Start moving left."""
        self.vx = -MOVE_SPEED

    def move_right(self):
        """Start moving right."""
        self.vx = MOVE_SPEED

    def stop_horizontal(self):
        """Stop horizontal movement."""
        self.vx = 0

    def apply_physics(self, grid: np.ndarray):
        """
        Move the player by (vx, vy), apply gravity, and handle collisions
        with platform tiles in the numpy grid.
        """
        # ----- Gravity -----
        self.vy += GRAVITY

        # ----- Horizontal movement -----
        self.x += self.vx
        # Clamp inside canvas
        self.x = max(0, min(self.x, WIN_W - self.w))
        # Horizontal tile collision
        self._resolve_horizontal(grid)

        # ----- Vertical movement -----
        # Reset on_ground BEFORE vertical resolution each frame
        self.on_ground = False
        self.y += self.vy
        self._resolve_vertical(grid)

        # Update canvas positions
        self.canvas.coords(self.body,
                           self.x, self.y,
                           self.x + self.w, self.y + self.h)
        self.canvas.coords(self.hat,
                           self.x + 4, self.y - 10,
                           self.x + self.w - 4, self.y)

    def _resolve_horizontal(self, grid: np.ndarray):
        """
        Push player out of solid tiles horizontally.
        We sample points on the LEFT or RIGHT edge at three vertical heights
        (top, middle, near-bottom) to avoid false hits at the very corners.
        """
        if self.vx == 0:
            return

        # Three sample points along the vertical span (avoid very top/bottom edge)
        sample_ys = [
            self.y + 4,
            self.y + self.h // 2,
            self.y + self.h - 6,
        ]

        if self.vx > 0:
            # Moving right — check right edge
            check_x = self.x + self.w
            for sy in sample_ys:
                col = int(check_x // TILE_SIZE)
                row = int(sy // TILE_SIZE)
                if _is_solid(grid, row, col):
                    self.x = col * TILE_SIZE - self.w
                    self.vx = 0
                    break
        else:
            # Moving left — check left edge
            check_x = self.x
            for sy in sample_ys:
                col = int(check_x // TILE_SIZE)
                row = int(sy // TILE_SIZE)
                if _is_solid(grid, row, col):
                    self.x = (col + 1) * TILE_SIZE
                    self.vx = 0
                    break

    def _resolve_vertical(self, grid: np.ndarray):
        """
        Push player out of solid tiles vertically.
        Sample three points along the bottom (or top) edge.
        A small inset on left/right avoids snagging on platform corners.
        """
        # Three sample points across the horizontal span
        inset = 4
        sample_xs = [
            self.x + inset,
            self.x + self.w // 2,
            self.x + self.w - inset,
        ]

        if self.vy > 0:
            # Falling — check bottom edge
            check_y = self.y + self.h
            for sx in sample_xs:
                col = int(sx // TILE_SIZE)
                row = int(check_y // TILE_SIZE)
                if _is_solid(grid, row, col):
                    # Snap player on top of the tile
                    self.y = row * TILE_SIZE - self.h
                    self.vy = 0
                    self.on_ground = True
                    break
        elif self.vy < 0:
            # Rising — check top edge
            check_y = self.y
            for sx in sample_xs:
                col = int(sx // TILE_SIZE)
                row = int(check_y // TILE_SIZE)
                if _is_solid(grid, row, col):
                    # Bounce off the underside of the tile
                    self.y = (row + 1) * TILE_SIZE
                    self.vy = 0
                    break

    def get_grid_pos(self):
        """Return (row, col) of the player's centre in the grid."""
        cx = self.x + self.w / 2
        cy = self.y + self.h / 2
        return int(cy // TILE_SIZE), int(cx // TILE_SIZE)

    def rect(self):
        """Return (x1, y1, x2, y2) bounding box in pixels."""
        return self.x, self.y, self.x + self.w, self.y + self.h

    def destroy(self):
        """Remove player from canvas."""
        self.canvas.delete("player")


# ===========================================================
#  PLATFORM CLASS
# ===========================================================

class Platform:
    """
    Represents a single platform tile drawn on the canvas.
    Platforms are parsed from the numpy level grid.
    """

    def __init__(self, canvas: tk.Canvas, row: int, col: int):
        self.row = row
        self.col = col
        x1 = col * TILE_SIZE
        y1 = row * TILE_SIZE
        x2 = x1 + TILE_SIZE
        y2 = y1 + TILE_SIZE

        # Slightly different colours for ground row vs floating platforms
        colour = COL_GROUND if row == ROWS - 1 else COL_PLATFORM
        self.tile = canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=colour, outline="#5C3317", width=1, tags="tile"
        )
        # Simple grass stripe on top
        canvas.create_line(x1, y1 + 4, x2, y1 + 4,
                           fill="#228B22", width=3, tags="tile")


# ===========================================================
#  COIN CLASS
# ===========================================================

class Coin:
    """
    A collectible coin placed at a specific grid position.
    Removed from canvas when the player touches it.
    """

    def __init__(self, canvas: tk.Canvas, row: int, col: int):
        self.row = row
        self.col = col
        self.collected = False

        cx = col * TILE_SIZE + TILE_SIZE // 2
        cy = row * TILE_SIZE + TILE_SIZE // 2
        r  = TILE_SIZE // 3

        self.circle = canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=COL_COIN, outline="#B8860B", width=2, tags="coin"
        )
        # Tiny "$" label
        self.label = canvas.create_text(
            cx, cy, text="$", font=("Arial", 10, "bold"),
            fill="#8B6914", tags="coin"
        )
        self.canvas = canvas

    def pixel_rect(self):
        """Return bounding box for collision checking."""
        x1 = self.col * TILE_SIZE + 4
        y1 = self.row * TILE_SIZE + 4
        return x1, y1, x1 + TILE_SIZE - 8, y1 + TILE_SIZE - 8

    def collect(self):
        """Remove from canvas."""
        self.collected = True
        self.canvas.delete(self.circle)
        self.canvas.delete(self.label)


# ===========================================================
#  ENEMY CLASS
# ===========================================================

class Enemy:
    """
    A simple enemy that walks left and right on a platform.
    Kills the player on contact.
    """

    def __init__(self, canvas: tk.Canvas, row: int, col: int):
        self.canvas = canvas
        self.x = float(col * TILE_SIZE)
        self.y = float(row * TILE_SIZE)
        self.w = TILE_SIZE - 8
        self.h = TILE_SIZE - 4
        self.speed = 1.5
        self.direction = -1      # start moving left
        self.alive = True

        self.body = canvas.create_oval(
            self.x, self.y,
            self.x + self.w, self.y + self.h,
            fill=COL_ENEMY, outline="darkgreen", width=2, tags="enemy"
        )
        # Eyes to show direction
        self.eye = canvas.create_oval(
            self.x + 4, self.y + 6,
            self.x + 12, self.y + 14,
            fill="white", tags="enemy"
        )

    def update(self, grid: np.ndarray):
        """Move enemy back and forth; reverse at edges or walls."""
        if not self.alive:
            return

        self.x += self.speed * self.direction

        # Check wall collision (solid tile ahead)
        next_col = int((self.x + (self.w if self.direction > 0 else 0)) // TILE_SIZE)
        current_row = int((self.y + self.h) // TILE_SIZE)
        if _is_solid(grid, current_row, next_col) or self.x < 0 or self.x > WIN_W - self.w:
            self.direction *= -1

        # Update canvas
        self.canvas.coords(self.body,
                           self.x, self.y,
                           self.x + self.w, self.y + self.h)
        eye_x = self.x + (self.w - 12) if self.direction > 0 else self.x + 4
        self.canvas.coords(self.eye,
                           eye_x, self.y + 6,
                           eye_x + 8, self.y + 14)

    def pixel_rect(self):
        return self.x, self.y, self.x + self.w, self.y + self.h

    def destroy(self):
        self.canvas.delete(self.body)
        self.canvas.delete(self.eye)


# ===========================================================
#  HELPER FUNCTIONS
# ===========================================================

def _is_solid(grid: np.ndarray, row: int, col: int) -> bool:
    """Return True if (row, col) is a solid platform tile (value == 1)."""
    if row < 0 or row >= ROWS or col < 0 or col >= COLS:
        return False
    return grid[row, col] == 1


def _rects_overlap(r1, r2) -> bool:
    """
    Check whether two rectangles overlap.
    Each rect is (x1, y1, x2, y2).
    """
    ax1, ay1, ax2, ay2 = r1
    bx1, by1, bx2, by2 = r2
    return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1


# ===========================================================
#  GAME CLASS  (main game logic)
# ===========================================================

class Game:
    """
    Manages the active game session:
      - Builds the level from the numpy grid
      - Runs the game loop (tkinter .after())
      - Handles input, collision, scoring
      - Advances to next level when all coins are collected
    """

    def __init__(self, root: tk.Tk, player_name: str,
                 start_score: int = 0, start_level: int = 0):
        self.root = root
        self.player_name = player_name
        self.total_score = start_score
        self.level_index = start_level
        self.running = False

        self._build_ui()
        self._load_level()

    # ----------------------------------------------------------
    # UI SETUP
    # ----------------------------------------------------------

    def _build_ui(self):
        """Create the game canvas, score label, and control buttons."""
        # Main frame holds everything
        self.frame = tk.Frame(self.root, bg="black")
        self.frame.pack()

        # Score label at the top
        self.score_var = tk.StringVar(value="Score: 0  |  Level: 1")
        tk.Label(self.frame, textvariable=self.score_var,
                 font=("Courier", 14, "bold"),
                 fg="yellow", bg="black").pack()

        # Game canvas
        self.canvas = tk.Canvas(self.frame,
                                width=WIN_W, height=WIN_H,
                                bg=COL_SKY, highlightthickness=0)
        self.canvas.pack()

        # On-screen control buttons
        btn_frame = tk.Frame(self.frame, bg="black")
        btn_frame.pack(pady=4)

        btn_style = {"font": ("Courier", 12, "bold"),
                     "bg": "#333", "fg": "white",
                     "width": 6, "relief": "raised"}

        self.btn_left  = tk.Button(btn_frame, text="◀ Left",  **btn_style)
        self.btn_jump  = tk.Button(btn_frame, text="▲ Jump",  **btn_style)
        self.btn_right = tk.Button(btn_frame, text="Right ▶", **btn_style)

        self.btn_left .grid(row=0, column=0, padx=4)
        self.btn_jump .grid(row=0, column=1, padx=4)
        self.btn_right.grid(row=0, column=2, padx=4)

        # Bind button press/release for smooth movement
        self.btn_left .bind("<ButtonPress>",   lambda e: self._key_left_press())
        self.btn_left .bind("<ButtonRelease>", lambda e: self._key_stop())
        self.btn_right.bind("<ButtonPress>",   lambda e: self._key_right_press())
        self.btn_right.bind("<ButtonRelease>", lambda e: self._key_stop())
        self.btn_jump .bind("<ButtonPress>",   lambda e: self._key_jump())

        # Keyboard bindings
        self.root.bind("<Left>",             lambda e: self._key_left_press())
        self.root.bind("<KeyRelease-Left>",  lambda e: self._key_stop())
        self.root.bind("<a>",                lambda e: self._key_left_press())
        self.root.bind("<KeyRelease-a>",     lambda e: self._key_stop())
        self.root.bind("<Right>",            lambda e: self._key_right_press())
        self.root.bind("<KeyRelease-Right>", lambda e: self._key_stop())
        self.root.bind("<d>",                lambda e: self._key_right_press())
        self.root.bind("<KeyRelease-d>",     lambda e: self._key_stop())
        self.root.bind("<space>",            lambda e: self._key_jump())
        self.root.bind("<Up>",               lambda e: self._key_jump())

    # ----------------------------------------------------------
    # KEY HANDLERS
    # ----------------------------------------------------------

    def _key_left_press(self):
        if self.player:
            self.player.move_left()

    def _key_right_press(self):
        if self.player:
            self.player.move_right()

    def _key_stop(self):
        if self.player:
            self.player.stop_horizontal()

    def _key_jump(self):
        if self.player:
            self.player.jump()

    # ----------------------------------------------------------
    # LEVEL LOADING
    # ----------------------------------------------------------

    def _load_level(self):
        """Parse the numpy grid for the current level and create game objects."""
        self.canvas.delete("all")   # clear previous level

        # Get level grid (wrap around if out of range)
        idx = self.level_index % len(LEVELS)
        self.grid = LEVELS[idx].copy()

        self.platforms = []
        self.coins     = []
        self.enemies   = []
        self.player    = None

        for row in range(ROWS):
            for col in range(COLS):
                cell = self.grid[row, col]

                if cell == 1:   # platform tile
                    self.platforms.append(Platform(self.canvas, row, col))

                elif cell == 2:  # coin
                    self.coins.append(Coin(self.canvas, row, col))

                elif cell == 3:  # enemy spawn
                    # Spawn enemy one row above the spawn marker
                    self.enemies.append(Enemy(self.canvas, row - 1, col))

        # Create player at a fixed starting position
        self.player = Player(self.canvas, start_col=1, start_row=6)

        # Update HUD
        self._refresh_hud()

        self.running = True
        self._game_loop()

    # ----------------------------------------------------------
    # MAIN GAME LOOP
    # ----------------------------------------------------------

    def _game_loop(self):
        """Called every FPS_DELAY ms; updates physics, enemies, collisions."""
        if not self.running:
            return

        # 1. Move player (physics + collision with platforms)
        self.player.apply_physics(self.grid)

        # 2. Move enemies
        for enemy in self.enemies:
            enemy.update(self.grid)

        # 3. Check all collisions
        self._check_coin_collisions()
        self._check_enemy_collisions()
        self._check_fall_off()

        # 4. Check level complete (all coins collected)
        if all(c.collected for c in self.coins):
            self._level_complete()
            return

        # 5. Refresh score display
        self._refresh_hud()

        # Schedule next frame
        self.root.after(FPS_DELAY, self._game_loop)

    # ----------------------------------------------------------
    # COLLISION DETECTION
    # ----------------------------------------------------------

    def _check_coin_collisions(self):
        """Collect any coin the player overlaps."""
        pr = self.player.rect()
        for coin in self.coins:
            if not coin.collected and _rects_overlap(pr, coin.pixel_rect()):
                coin.collect()
                self.total_score += 10
                self._refresh_hud()

    def _check_enemy_collisions(self):
        """End game if player touches an enemy."""
        pr = self.player.rect()
        for enemy in self.enemies:
            if enemy.alive and _rects_overlap(pr, enemy.pixel_rect()):
                self.total_score = max(0, self.total_score - 5)
                self._game_over()
                return

    def _check_fall_off(self):
        """End game if player falls below the canvas."""
        if self.player.y > WIN_H + TILE_SIZE:
            self._game_over()

    # ----------------------------------------------------------
    # GAME STATE TRANSITIONS
    # ----------------------------------------------------------

    def _level_complete(self):
        """Show congratulations, advance to next level."""
        self.running = False
        self.canvas.create_text(WIN_W // 2, WIN_H // 2,
                                text="✓ Level Complete! +50 Bonus",
                                font=("Courier", 22, "bold"),
                                fill="yellow")
        self.total_score += 50
        self.level_index += 1
        # Move to next level after 2 seconds
        self.root.after(2000, self._load_level)

    def _game_over(self):
        """Handle game-over: save leaderboard, show message, return to menu."""
        self.running = False

        # Save to leaderboard
        update_leaderboard(self.player_name, self.total_score)

        self.canvas.create_text(WIN_W // 2, WIN_H // 2,
                                text=f"GAME OVER\nScore: {self.total_score}",
                                font=("Courier", 24, "bold"),
                                fill="red", justify="center")
        # Return to menu after 2.5 seconds
        self.root.after(2500, self._back_to_menu)

    def _back_to_menu(self):
        """Destroy game frame and show the main menu again."""
        self.running = False
        self.frame.destroy()
        MainMenu(self.root)

    # ----------------------------------------------------------
    # HUD
    # ----------------------------------------------------------

    def _refresh_hud(self):
        self.score_var.set(
            f"Player: {self.player_name}  |  "
            f"Score: {self.total_score}  |  "
            f"Level: {self.level_index + 1}"
        )


# ===========================================================
#  LEADERBOARD WINDOW
# ===========================================================

class LeaderboardWindow:
    """Popup window showing the top 10 scores from leaderboard.txt."""

    def __init__(self, root: tk.Tk):
        win = tk.Toplevel(root)
        win.title("🏆 Leaderboard")
        win.configure(bg="black")
        win.resizable(False, False)

        tk.Label(win, text="TOP SCORES", font=("Courier", 16, "bold"),
                 fg="gold", bg="black").pack(pady=(12, 4))

        entries = get_leaderboard()
        if not entries:
            tk.Label(win, text="No scores yet. Play a game!",
                     font=("Courier", 12), fg="white", bg="black").pack(pady=8)
        else:
            for i, (name, score) in enumerate(entries, 1):
                medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f" {i}."
                tk.Label(win,
                         text=f"{medal}  {name:<15} {score:>6}",
                         font=("Courier", 12),
                         fg="white", bg="black").pack(anchor="w", padx=20)

        tk.Button(win, text="Close", font=("Courier", 11),
                  bg="#333", fg="white", command=win.destroy).pack(pady=12)


# ===========================================================
#  MAIN MENU
# ===========================================================

class MainMenu:
    """
    The first screen the player sees.
    Options: New Game | Leaderboard | Exit
    """

    def __init__(self, root: tk.Tk):
        self.root.configure(bg="black")
        self.root.configure(bg="black")

        self.frame = tk.Frame(root, bg="black", padx=40, pady=10)
        self.frame.pack()

        # Title
        tk.Label(self.frame, text="🍄 MINI MARIO 🍄",
                 font=("Courier", 28, "bold"),
                 fg="#FF4500", bg="black").pack(pady=(0, 4))

        tk.Label(self.frame,
                 text="A Python Mini Project",
                 font=("Courier", 11), fg="gray", bg="black").pack(pady=(0, 20))

        # Name entry
        tk.Label(self.frame, text="Your Name:",
                 font=("Courier", 12), fg="white", bg="black").pack()
        self.name_entry = tk.Entry(self.frame, font=("Courier", 12),
                                   bg="#222", fg="white",
                                   insertbackground="white",
                                   justify="center", width=20)
        self.name_entry.insert(0, "Mario")
        self.name_entry.pack(pady=(4, 16))

        # Buttons
        btn_cfg = {"font": ("Courier", 13, "bold"),
                   "bg": "#E74C3C", "fg": "white",
                   "activebackground": "#C0392B",
                   "width": 18, "pady": 4, "cursor": "hand2"}

        tk.Button(self.frame, text="▶  New Game",
                  **btn_cfg, command=self._new_game).pack(pady=4)

        btn_cfg["bg"] = "#27AE60"
        btn_cfg["activebackground"] = "#1E8449"
        tk.Button(self.frame, text="🏆 Leaderboard",
                  **btn_cfg, command=self._show_leaderboard).pack(pady=4)

        btn_cfg["bg"] = "#7F8C8D"
        btn_cfg["activebackground"] = "#626567"
        tk.Button(self.frame, text="✕  Exit",
                  **btn_cfg, command=root.quit).pack(pady=(4, 0))

        # Controls hint
        tk.Label(self.frame,
                 text="\nControls:  ← → (or A/D) to move  |  Space / ↑ to jump",
                 font=("Courier", 9), fg="#888", bg="black").pack()

    def _new_game(self):
        name = self.name_entry.get().strip() or "Mario"
        self.frame.destroy()
        Game(self.root, player_name=name)

    def _show_leaderboard(self):
        LeaderboardWindow(self.root)


# ===========================================================
#  ENTRY POINT
# ===========================================================

if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)
    MainMenu(root)
    root.mainloop()
# -*- coding: utf-8 -*-
