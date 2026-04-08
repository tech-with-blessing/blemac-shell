"""
shell/app.py — Root widget that orchestrates the entire BLEMAC Shell.

State machine:
    HOME  ──launch──►  LOADING  ──ready──►  PLAYING
      ▲                                        │
      └──────────────quit / crash ─────────────┘

In PLAYING state:
  - HomeScreen is hidden
  - GameOverlay (vpad + pause menu) is shown
  - GameRunner runs the Pygame game in a background thread
"""

import os
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle

from shell.core.manifest import scan_games, GameManifest
from shell.core.game_runner import GameRunner
from shell.ui.home_screen import HomeScreen
from shell.ui.game_overlay import GameOverlay

ACCENT2 = (220/255, 60/255, 120/255, 1)
TEXT    = (220/255, 230/255, 255/255, 1)
BG      = (8/255,  10/255, 20/255, 1)


class BlemacShellWidget(FloatLayout):

    def __init__(self, games_dir: str, **kwargs):
        super().__init__(**kwargs)
        self._games_dir = games_dir
        self._runner    = GameRunner()
        self._overlay: GameOverlay = None
        self._state     = "HOME"   # HOME | PLAYING

        self._manifests = scan_games(games_dir)

        self._build_home()
        self._build_error_banner()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_home(self):
        self._home = HomeScreen(
            manifests=self._manifests,
            on_launch=self._launch_game,
            on_rescan=self._rescan,
            size_hint=(1, 1),
        )
        self.add_widget(self._home)

    def _build_error_banner(self):
        """Red crash banner shown at bottom when a game crashes."""
        self._err_banner = Label(
            text="",
            font_size=sp(12),
            color=(1, 0.3, 0.3, 1),
            size_hint=(1, None),
            height=dp(36),
            pos_hint={"x": 0, "y": 0},
            opacity=0,
            halign="center",
        )
        self._err_banner.bind(size=self._err_banner.setter("text_size"))
        self.add_widget(self._err_banner)

    # ── Rescan ─────────────────────────────────────────────────────────────────

    def _rescan(self):
        self._manifests = scan_games(self._games_dir)
        self._home.refresh(self._manifests)

    # ── Launch flow ────────────────────────────────────────────────────────────

    def _launch_game(self, manifest: GameManifest):
        if self._state == "PLAYING":
            return

        print(f"[Shell] Launching: {manifest.title}")
        self._state = "PLAYING"

        # Hide home screen
        Animation(opacity=0, duration=0.2).start(self._home)
        self._home.disabled = True

        # Add game overlay (vpad + pause menu)
        self._overlay = GameOverlay(
            manifest=manifest,
            on_resume=self._on_game_resume,
            on_restart=lambda: self._restart_game(manifest),
            on_quit=self._quit_game,
            size_hint=(1, 1),
        )
        self.add_widget(self._overlay)

        # Launch the game in background thread
        self._runner.launch(manifest, on_exit=self._on_game_exit)

    def _on_game_resume(self):
        pass  # nothing extra needed — vpad re-enables itself

    def _restart_game(self, manifest: GameManifest):
        """Stop current game and relaunch it."""
        self._runner.stop()
        # Wait briefly for thread to stop then relaunch
        Clock.schedule_once(lambda dt: self._runner.launch(
            manifest, on_exit=self._on_game_exit
        ), 0.5)

    def _quit_game(self):
        self._runner.stop()
        # _on_game_exit will be called by runner thread → triggers _return_home

    # ── Game exit ──────────────────────────────────────────────────────────────

    def _on_game_exit(self, manifest: GameManifest, error: str):
        """Called on Kivy main thread when the game's thread ends."""
        print(f"[Shell] Game exited: {manifest.title}  error={bool(error)}")

        if error:
            self._show_error(f"💥 {manifest.title} crashed — check game code")
            print(f"[Shell] Crash details:\n{error}")

        self._return_home()

    def _return_home(self):
        self._state = "HOME"

        if self._overlay:
            self._overlay.force_quit()
            self.remove_widget(self._overlay)
            self._overlay = None

        self._home.disabled = False
        Animation(opacity=1, duration=0.25).start(self._home)

    # ── Error banner ───────────────────────────────────────────────────────────

    def _show_error(self, msg: str):
        self._err_banner.text    = msg
        self._err_banner.opacity = 1
        # Auto-hide after 6 seconds
        Clock.schedule_once(
            lambda dt: Animation(opacity=0, duration=0.5).start(self._err_banner),
            6
        )
