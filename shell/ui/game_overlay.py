"""
shell/ui/game_overlay.py — Semi-transparent overlay shown while a game runs.

Provides:
  - Virtual gamepad (VirtualPad widget)
  - Slide-up pause menu with Resume / Restart / Quit
  - FPS counter (optional)
  - A small "⏸" handle the player can tap to open the menu

This widget sits ON TOP of the Pygame SDL surface in the Kivy layer.
"""

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp, sp

from shell.ui.virtual_pad import VirtualPad
from shell.core.manifest import GameManifest

ACCENT  = (0/255, 220/255, 180/255, 1)
ACCENT2 = (220/255, 60/255, 120/255, 1)
BG      = (8/255, 10/255, 20/255, 1)
DIM     = (60/255, 70/255, 90/255, 1)
TEXT    = (220/255, 230/255, 255/255, 1)


class GameOverlay(FloatLayout):
    """
    Overlay widget placed over the Pygame surface.
    Hierarchy (bottom → top):
        VirtualPad          ← receives touch, injects pygame keys
        PauseHandle         ← small tap target top-right
        PauseMenu           ← slides in when pause tapped
    """

    def __init__(self, manifest: GameManifest,
                 on_resume, on_restart, on_quit, **kwargs):
        super().__init__(**kwargs)
        self._manifest   = manifest
        self._on_resume  = on_resume
        self._on_restart = on_restart
        self._on_quit    = on_quit
        self._paused     = False

        self._build_vpad()
        self._build_pause_handle()
        self._build_pause_menu()

    # ── Virtual Gamepad ────────────────────────────────────────────────────────

    def _build_vpad(self):
        profile = getattr(self._manifest, "touch_profile", "dpad")
        self._vpad = VirtualPad(
            profile=profile,
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        self.add_widget(self._vpad)

    # ── Pause Handle ───────────────────────────────────────────────────────────

    def _build_pause_handle(self):
        """Small ⏸ button — top right corner."""
        self._handle = Button(
            text="⏸",
            font_size=sp(18),
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            pos_hint={"right": 1.0, "top": 1.0},
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=(*ACCENT[:3], 0.5),
            opacity=0.6,
        )
        self._handle.bind(on_press=self._toggle_pause)
        self.add_widget(self._handle)

    # ── Pause Menu ─────────────────────────────────────────────────────────────

    def _build_pause_menu(self):
        """Full-screen semi-transparent pause menu, hidden by default."""
        self._menu = FloatLayout(
            size_hint=(1, 1),
            opacity=0,
        )
        # Background
        with self._menu.canvas.before:
            Color(8/255, 10/255, 20/255, 0.88)
            self._menu_bg = Rectangle(
                pos=self._menu.pos, size=self._menu.size
            )
        self._menu.bind(
            pos=lambda *a: setattr(self._menu_bg, "pos", self._menu.pos),
            size=lambda *a: setattr(self._menu_bg, "size", self._menu.size),
        )

        card = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(24),
            size_hint=(None, None),
            size=(dp(240), dp(260)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        with card.canvas.before:
            Color(12/255, 16/255, 32/255, 0.97)
            self._card_rect = RoundedRectangle(
                pos=card.pos, size=card.size, radius=[dp(16)]
            )
        card.bind(
            pos=lambda *a: setattr(self._card_rect, "pos", card.pos),
            size=lambda *a: setattr(self._card_rect, "size", card.size),
        )

        title = Label(
            text="⏸  PAUSED",
            font_size=sp(18),
            bold=True,
            color=ACCENT,
            size_hint=(1, None),
            height=dp(36),
        )
        game_name = Label(
            text=self._manifest.title,
            font_size=sp(13),
            color=DIM,
            size_hint=(1, None),
            height=dp(20),
        )

        def _btn(text, col, cb):
            b = Button(
                text=text,
                font_size=sp(14),
                bold=True,
                size_hint=(1, None),
                height=dp(44),
                background_normal="",
                background_color=(*col[:3], 0.25),
                color=col,
            )
            b.bind(on_press=lambda *a: cb())
            return b

        resume_btn  = _btn("▶  RESUME",  ACCENT,  self._resume)
        restart_btn = _btn("↺  RESTART", TEXT,    self._restart)
        quit_btn    = _btn("✕  QUIT",    ACCENT2, self._quit)

        card.add_widget(title)
        card.add_widget(game_name)
        card.add_widget(resume_btn)
        card.add_widget(restart_btn)
        card.add_widget(quit_btn)

        self._menu.add_widget(card)
        self.add_widget(self._menu)
        # Menu starts hidden
        self._menu.disabled = True

    # ── Actions ────────────────────────────────────────────────────────────────

    def _toggle_pause(self, *args):
        if self._paused:
            self._resume()
        else:
            self._pause()

    def _pause(self):
        self._paused = True
        self._vpad.set_visible(False)
        self._menu.disabled = False
        Animation(opacity=1, duration=0.18).start(self._menu)

    def _resume(self):
        self._paused = False
        anim = Animation(opacity=0, duration=0.15)
        anim.bind(on_complete=lambda *a: setattr(self._menu, "disabled", True))
        anim.start(self._menu)
        self._vpad.set_visible(True)
        self._on_resume()

    def _restart(self):
        self._paused = False
        self._menu.opacity = 0
        self._menu.disabled = True
        self._vpad.release_all()
        self._on_restart()

    def _quit(self):
        self._vpad.release_all()
        self._on_quit()

    # ── External ───────────────────────────────────────────────────────────────

    def force_quit(self):
        self._vpad.release_all()
