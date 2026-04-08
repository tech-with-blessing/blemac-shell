"""
main.py — BLEMAC Shell entry point.

Kivy is the Android-compatible framework that:
  - manages the window / lifecycle / touch events
  - hosts our shell UI
  - runs Pygame games in the same process via GameRunner

On Android, python-for-android compiles this whole project into an .apk.
On desktop, just run:  python main.py
"""

import os
import sys

# ── Environment flags ──────────────────────────────────────────────────────────
ON_ANDROID = "ANDROID_ARGUMENT" in os.environ or "ANDROID_ROOT" in os.environ

# On Android, internal storage path for sideloaded games
if ON_ANDROID:
    from android.storage import primary_external_storage_path  # type: ignore
    GAMES_DIR = os.path.join(primary_external_storage_path(), "BlemacShell", "games")
else:
    GAMES_DIR = os.path.join(os.path.dirname(__file__), "games")

os.makedirs(GAMES_DIR, exist_ok=True)

# ── Kivy config BEFORE importing kivy ─────────────────────────────────────────
os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

import kivy
kivy.require("2.0.0")

from kivy.config import Config
Config.set("graphics", "resizable", "0")
Config.set("input", "mouse", "mouse,disable_multitouch")

from kivy.app import App
from kivy.core.window import Window

from shell.app import BlemacShellWidget


class BlemacApp(App):
    def build(self):
        Window.clearcolor = (8/255, 10/255, 20/255, 1)
        return BlemacShellWidget(games_dir=GAMES_DIR)

    def on_pause(self):
        """Android: app backgrounded — keep running."""
        return True

    def on_resume(self):
        """Android: app foregrounded again."""
        pass


if __name__ == "__main__":
    BlemacApp().run()
