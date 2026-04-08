"""
shell/ui/virtual_pad.py — On-screen virtual gamepad for mobile Pygame gaming.

This is the KEY piece that makes Pygame games playable on mobile.

HOW IT WORKS
============
1.  This Kivy Widget draws transparent touch buttons OVER the Pygame game surface
2.  When a button is pressed/released, it injects pygame.KEYDOWN / pygame.KEYUP
    events directly into Pygame's event queue
3.  The running game sees normal keyboard events — zero code changes needed

TOUCH PROFILES
==============
Defined in game.json as "touch_profile":
  "dpad"       → D-pad + A/B buttons  (most games)
  "platformer" → D-pad + Jump + Attack (side-scrollers like PIXEL ABYSS)
  "custom"     → game provides its own pad config via game.json "buttons" array
  "none"       → no overlay (for games with their own touch handling)

LAYOUT (portrait mode example)
================================
┌─────────────────────────┐
│                         │
│     [GAME RENDERS]      │
│                         │
│                         │
├─────────────────────────┤
│  ┌───┐       ┌───┬───┐  │
│  │ ↑ │       │ A │ B │  │
│  ├───┤       └───┴───┘  │
│  │←  │→                 │
│  ├───┤   [START][SEL]   │
│  │ ↓ │                  │
│  └───┘                  │
└─────────────────────────┘
"""

import pygame
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.clock import Clock


# ── Key mappings per profile ───────────────────────────────────────────────────

PROFILES = {
    "dpad": {
        "left":   pygame.K_LEFT,
        "right":  pygame.K_RIGHT,
        "up":     pygame.K_UP,
        "down":   pygame.K_DOWN,
        "a":      pygame.K_z,
        "b":      pygame.K_x,
        "start":  pygame.K_RETURN,
        "select": pygame.K_ESCAPE,
    },
    "platformer": {
        "left":   pygame.K_LEFT,
        "right":  pygame.K_RIGHT,
        "up":     pygame.K_UP,      # jump
        "down":   pygame.K_DOWN,    # duck / fall-through
        "a":      pygame.K_z,       # jump (alt)
        "b":      pygame.K_x,       # attack
        "start":  pygame.K_RETURN,
        "select": pygame.K_ESCAPE,
    },
}


def _post_key(key: int, down: bool):
    """Inject a pygame key event into Pygame's event queue."""
    try:
        kind = pygame.KEYDOWN if down else pygame.KEYUP
        event = pygame.event.Event(kind, {
            "key":      key,
            "mod":      0,
            "unicode":  "",
            "scancode": 0,
        })
        pygame.event.post(event)
    except Exception as e:
        print(f"[VPad] Key inject failed: {e}")


# ── Button descriptor ──────────────────────────────────────────────────────────

class VButton:
    """A single virtual button with a touch hit-area and a pygame key."""

    def __init__(self, label: str, key: int, cx: float, cy: float,
                 radius: float = 36, shape: str = "circle"):
        self.label  = label
        self.key    = key
        self.cx     = cx    # 0..1 relative to widget width
        self.cy     = cy    # 0..1 relative to widget height
        self.radius = radius
        self.shape  = shape   # "circle" | "rect"
        self.held   = False
        self._touch_ids = set()

    def abs_rect(self, w, h):
        """Return (x, y, r) in absolute pixels."""
        return self.cx * w, self.cy * h, self.radius

    def hit(self, tx, ty, w, h) -> bool:
        ax, ay, r = self.abs_rect(w, h)
        return ((tx - ax)**2 + (ty - ay)**2) <= r * r

    def press(self, touch_id):
        if touch_id not in self._touch_ids:
            self._touch_ids.add(touch_id)
            if not self.held:
                self.held = True
                _post_key(self.key, True)

    def release(self, touch_id):
        self._touch_ids.discard(touch_id)
        if not self._touch_ids and self.held:
            self.held = False
            _post_key(self.key, False)

    def release_all(self):
        self._touch_ids.clear()
        if self.held:
            self.held = False
            _post_key(self.key, False)


# ── Virtual Pad Widget ─────────────────────────────────────────────────────────

class VirtualPad(Widget):
    """
    Transparent Kivy widget drawn over the game surface.
    Handles multi-touch and injects pygame key events.
    """

    # Colours (RGBA 0..1)
    COL_BTN_IDLE  = (0,    0.86, 0.70, 0.30)
    COL_BTN_HELD  = (0,    0.86, 0.70, 0.75)
    COL_DPAD_IDLE = (0.08, 0.60, 0.90, 0.28)
    COL_DPAD_HELD = (0.08, 0.60, 0.90, 0.70)
    COL_LABEL     = (1,    1,    1,    0.80)

    def __init__(self, profile: str = "dpad", **kwargs):
        super().__init__(**kwargs)
        self.profile_name = profile
        self._buttons: list[VButton] = []
        self._visible = True

        self.bind(size=self._rebuild, pos=self._rebuild)
        Clock.schedule_once(lambda dt: self._rebuild(), 0)

    def set_profile(self, profile: str):
        self.profile_name = profile
        self._rebuild()

    def set_visible(self, v: bool):
        self._visible = v
        self.canvas.clear()
        if v:
            self._redraw()

    def _rebuild(self, *args):
        self._buttons.clear()
        keys = PROFILES.get(self.profile_name, PROFILES["dpad"])
        w, h = self.width or 1, self.height or 1

        # ── D-pad (bottom-left) ───────────────────────────────────────────────
        # Positions as fraction of widget size
        dpad_x, dpad_y = 0.18, 0.22   # centre of d-pad cluster
        r = min(w, h) * 0.07           # button radius scales with screen

        self._buttons += [
            VButton("←", keys["left"],  dpad_x - 0.10, dpad_y,        r, "circle"),
            VButton("→", keys["right"], dpad_x + 0.10, dpad_y,        r, "circle"),
            VButton("↑", keys["up"],    dpad_x,        dpad_y + 0.10, r, "circle"),
            VButton("↓", keys["down"],  dpad_x,        dpad_y - 0.10, r, "circle"),
        ]

        # ── Action buttons (bottom-right) ─────────────────────────────────────
        ax, ay = 0.78, 0.22
        self._buttons += [
            VButton("A", keys["a"], ax + 0.08, ay,        r, "circle"),
            VButton("B", keys["b"], ax,        ay + 0.10, r, "circle"),
        ]

        # ── Start / Select (centre-bottom) ────────────────────────────────────
        sr = r * 0.65
        self._buttons += [
            VButton("▶", keys["start"],  0.55, 0.08, sr, "rect"),
            VButton("≡", keys["select"], 0.45, 0.08, sr, "rect"),
        ]

        self._redraw()

    def _redraw(self, *args):
        if not self._visible:
            return
        self.canvas.after.clear()
        w, h = self.width, self.height
        if w == 0 or h == 0:
            return

        with self.canvas.after:
            for btn in self._buttons:
                col = self.COL_BTN_HELD if btn.held else self.COL_BTN_IDLE
                if btn.label in ("←", "→", "↑", "↓"):
                    col = self.COL_DPAD_HELD if btn.held else self.COL_DPAD_IDLE

                Color(*col)
                ax, ay, r = btn.abs_rect(w, h)
                # Kivy Y is bottom-up; convert
                ky = ay   # our cy=0 is bottom, which matches Kivy

                if btn.shape == "rect":
                    RoundedRectangle(
                        pos=(ax - r, ky - r * 0.6),
                        size=(r * 2, r * 1.2),
                        radius=[8]
                    )
                else:
                    Ellipse(pos=(ax - r, ky - r), size=(r * 2, r * 2))

    # ── Touch handling ─────────────────────────────────────────────────────────

    def on_touch_down(self, touch):
        if not self._visible:
            return False
        w, h = self.width, self.height
        hit_any = False
        for btn in self._buttons:
            if btn.hit(touch.x, touch.y, w, h):
                btn.press(touch.uid)
                hit_any = True
        if hit_any:
            self._redraw()
        return hit_any   # True = consume event, don't pass to game

    def on_touch_move(self, touch):
        if not self._visible:
            return False
        w, h = self.width, self.height
        for btn in self._buttons:
            if btn.hit(touch.x, touch.y, w, h):
                btn.press(touch.uid)
            else:
                btn.release(touch.uid)
        self._redraw()
        return False

    def on_touch_up(self, touch):
        if not self._visible:
            return False
        for btn in self._buttons:
            btn.release(touch.uid)
        self._redraw()
        return False

    def release_all(self):
        """Force-release all held buttons (call on game exit)."""
        for btn in self._buttons:
            btn.release_all()
        self._redraw()
