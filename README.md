# 🎮 BLEMAC Shell — Android

> Run any Pygame game on Android. No code changes needed.  
> Built with Python + Kivy + Buildozer | by TheAntidote (BLEMAC) 🇿🇼

---

## What This Is

BLEMAC Shell is an **Android app** (real `.apk`) that:
- Shows a PSP-style game library home screen
- Lets anyone **sideload** Pygame games by dropping folders onto their phone
- Runs Pygame games **natively** — no emulation, real CPython + SDL2
- Overlays a **virtual gamepad** so touch controls work in any Pygame game
- Handles game crashes gracefully — shell never dies

---

## How It Works (Technical)

```
Buildozer
  └── python-for-android (p4a)
        ├── CPython 3.11 (compiled for ARM)
        ├── SDL2 + SDL2_image + SDL2_mixer
        ├── pygame (compiled for Android)
        └── kivy (the shell UI framework)

At runtime:
  Kivy manages Android window lifecycle
    └── HomeScreen (Kivy UI) shows game library
          └── on launch: GameRunner.launch(manifest)
                └── importlib loads game's main.py
                      └── game runs its pygame loop
                            ← VirtualPad injects touch→keyboard events
```

The key insight: **Kivy and Pygame both use SDL2**. python-for-android
compiles them together so they share the same native surface.

---

## Build the APK

### Prerequisites (Ubuntu / WSL2 recommended)

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip \
     libssl-dev libffi-dev build-essential libltdl-dev ccache

pip install buildozer cython==0.29.36
```

### Build

```bash
cd blemac_android

# First build: downloads Android NDK/SDK (~3GB), takes 20-40 min
buildozer android debug

# Output:
#   bin/blemacshell-1.0.0-debug.apk

# Install via USB (USB debugging must be ON):
buildozer android deploy run

# Or just copy the .apk to your phone and sideload it
```

### Subsequent builds (much faster)

```bash
buildozer android debug 2>&1 | tail -20
```

---

## Project Structure

```
blemac_android/
├── main.py                  ← Kivy app entry point
├── buildozer.spec           ← Android build config
├── shell/
│   ├── app.py               ← Root widget, state machine (HOME → PLAYING)
│   ├── core/
│   │   ├── manifest.py      ← Reads game.json metadata
│   │   └── game_runner.py   ← Runs Pygame games via importlib
│   └── ui/
│       ├── home_screen.py   ← PSP XMB-style game library UI
│       ├── game_overlay.py  ← Pause menu + virtual pad wrapper
│       └── virtual_pad.py   ← Touch → pygame.KEYDOWN injection ← THE MAGIC
├── games/
│   └── demo_snake/          ← Working demo game
│       ├── main.py
│       └── game.json
└── sdk/                     ← (optional) helpers for game devs
```

---

## Sideloading Games (for users)

1. Install BLEMAC Shell APK on your Android phone
2. Create this folder on your SD card:
   ```
   /sdcard/BlemacShell/games/
   ```
3. Copy your game folder there:
   ```
   /sdcard/BlemacShell/games/
       my_game/
           main.py      ← must have a main() function
           game.json    ← metadata (see below)
           assets/      ← your game's images, sounds, etc.
   ```
4. Open BLEMAC Shell and tap **⟳ SCAN**
5. Your game appears — tap to launch!

---

## game.json Format

```json
{
    "id":           "my_game",
    "title":        "MY GAME",
    "version":      "v1.0",
    "author":       "Your Name",
    "description":  "Short description",
    "entry":        "main.py",
    "icon":         "icon.png",
    "tags":         ["arcade", "platformer"],
    "orientation":  "landscape",
    "touch_profile": "dpad"
}
```

### touch_profile options

| Value | Layout | Best for |
|-------|--------|----------|
| `"dpad"` | D-pad + A + B | Most games |
| `"platformer"` | D-pad + Jump + Attack | Side-scrollers (PIXEL ABYSS!) |
| `"none"` | No overlay | Games with own touch code |

---

## Adding PIXEL ABYSS

1. Copy `PIXEL_ABYSS-v38/` folder to `/sdcard/BlemacShell/games/pixel_abyss/`
2. Put the `game.json` from `games/pixel_abyss_template/game.json` in there
3. Tap SCAN in the shell

The `"touch_profile": "platformer"` gives you:
- D-pad left/right → move  
- D-pad up → jump  
- A button (→ Z key) → alternate jump  
- B button (→ X key) → attack  

---

## Making Your Pygame Game Work on Mobile

Your Pygame game needs **zero changes** if it:
- Uses arrow keys / WASD for movement
- Uses `pygame.K_z` / `pygame.K_x` for actions
- Opens assets with relative paths (`open("assets/sound.wav")`)

If your game uses hardcoded screen sizes, add this to your `main.py`:

```python
import os
# Let BLEMAC Shell scale the window
if os.environ.get("BLEMAC_HOST"):
    W, H = 480, 800   # or whatever fits portrait/landscape
```

---

## Desktop Testing (before building APK)

You can test the shell on desktop before building:

```bash
pip install kivy pygame
python main.py
```

Games in `./games/` load automatically.  
Touch = mouse clicks on desktop.

---

## Known Limitations

| Issue | Status |
|-------|--------|
| Games using `subprocess` internally | Won't work on Android |
| Games using `open()` with absolute paths | Fix: use relative paths |
| Multi-window games | Not supported |
| Games that call `pygame.quit()` + `sys.exit()` | Shell catches this cleanly |
| Sound (pygame.mixer) | Works if SDL2_mixer is included |

---

## Roadmap

- [ ] `.bmg` packaged game format (zip-based, drag-and-drop install)
- [ ] In-app game store / download browser  
- [ ] Save state manager UI
- [ ] Screenshot gallery
- [ ] Custom touch button layouts per game
- [ ] ChiShona (Shona) UI localisation 🇿🇼

---

*BLEMAC Shell — Harare, Zimbabwe 🇿🇼*  
*github.com/tech-with-blessing/*
