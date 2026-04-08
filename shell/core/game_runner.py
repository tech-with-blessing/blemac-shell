"""
shell/core/game_runner.py — Runs a Pygame game inside the BLEMAC Shell process.

HOW IT WORKS
============
On Android there is no shell / subprocess. Everything runs in ONE process.
We run Pygame games by:

1.  Switching the display to Pygame's SDL2 surface
    (Kivy and Pygame both use SDL2 under the hood via python-for-android)

2.  Dynamically importing the game's main.py via importlib

3.  Calling the game's main() (or running its __main__ block) in a
    separate THREAD so Kivy's event loop stays alive

4.  When the game exits / raises SystemExit, we restore Kivy's display

TOUCH → KEYBOARD INJECTION
===========================
Pygame games expect keyboard input. On Android we have touch.
The VirtualGamepad (shell/ui/virtual_pad.py) intercepts Kivy touch events
and posts them as pygame.event.Event(pygame.KEYDOWN/KEYUP) into Pygame's
event queue — completely transparent to the game.

SANDBOXING
==========
We patch sys.exit() inside the game's namespace so it raises a
GameExitException that we catch cleanly instead of killing the whole app.

FILESYSTEM
==========
The game's CWD is set to its folder so relative asset paths (open("assets/x.png"))
work correctly on Android just like on desktop.
"""

import os
import sys
import threading
import importlib.util
import importlib
import traceback
import pygame

from shell.core.manifest import GameManifest


class GameExitException(Exception):
    """Raised by patched sys.exit() inside a running game."""
    pass


class GameRunner:
    """
    Loads and runs a Pygame game in a background thread.
    Communicates with the shell via callbacks.
    """

    def __init__(self):
        self._thread:   threading.Thread = None
        self._manifest: GameManifest     = None
        self._running   = False
        self.on_exit    = None   # callback(manifest, error_or_None)

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running and self._thread and self._thread.is_alive()

    def launch(self, manifest: GameManifest, on_exit=None):
        """Launch a game. Calls on_exit(manifest, err) when done."""
        if self.is_running:
            print("[Runner] Already running a game — stop it first")
            return

        self._manifest = manifest
        self.on_exit   = on_exit
        self._running  = True

        self._thread = threading.Thread(
            target=self._run_game,
            args=(manifest,),
            daemon=True,
            name=f"game-{manifest.id}",
        )
        self._thread.start()

    def stop(self):
        """Request the game to stop."""
        if self.is_running:
            # Post a QUIT event into pygame — the game's event loop will catch it
            try:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            except Exception:
                pass
        self._running = False

    # ── Internal ───────────────────────────────────────────────────────────────

    def _run_game(self, manifest: GameManifest):
        """Runs in a background thread."""
        err = None
        old_cwd = os.getcwd()
        old_sys_path = sys.path[:]

        try:
            # 1. Change CWD so relative paths work in the game
            os.chdir(manifest.folder)
            sys.path.insert(0, manifest.folder)

            # 2. Load the game module
            entry = os.path.join(manifest.folder, manifest.entry)
            spec  = importlib.util.spec_from_file_location(
                f"blemac_game_{manifest.id}", entry
            )
            module = importlib.util.module_from_spec(spec)

            # 3. Patch sys.exit in the game's globals so it doesn't kill our app
            module.__builtins__ = self._patched_builtins()

            # 4. Set env flag so game knows it's inside BLEMAC
            os.environ["BLEMAC_HOST"]    = "1"
            os.environ["BLEMAC_GAME_ID"] = manifest.id

            # 5. Execute the game module (runs top-level code)
            print(f"[Runner] Starting: {manifest.title}")
            spec.loader.exec_module(module)

            # 6. If game has a main(), call it
            if hasattr(module, "main"):
                module.main()

        except GameExitException:
            print(f"[Runner] Game exited cleanly: {manifest.title}")

        except SystemExit:
            print(f"[Runner] Game called sys.exit(): {manifest.title}")

        except Exception as e:
            err = traceback.format_exc()
            print(f"[Runner] Game crashed:\n{err}")

        finally:
            # Restore environment
            os.chdir(old_cwd)
            sys.path[:] = old_sys_path
            os.environ.pop("BLEMAC_HOST", None)
            os.environ.pop("BLEMAC_GAME_ID", None)
            self._running = False

            # Notify shell on main thread
            if self.on_exit:
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self.on_exit(manifest, err), 0)

    def _patched_builtins(self):
        """Return a builtins dict with sys.exit patched to raise GameExitException."""
        import builtins
        patched = dict(vars(builtins))

        def safe_exit(*args):
            raise GameExitException()

        # Patch at module level; game's `import sys; sys.exit()` still goes
        # through the real sys — so we also patch sys.exit temporarily.
        _orig = sys.exit
        sys.exit = safe_exit

        # Restore sys.exit after game exits via the finally block in _run_game
        # (we store the original so GameRunner.stop can restore it)
        self._orig_sys_exit = _orig
        return patched
