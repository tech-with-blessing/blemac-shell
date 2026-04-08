[app]

# ── Identity ───────────────────────────────────────────────────────────────────
title           = BLEMAC Shell
package.name    = blemacshell
package.domain  = org.blemac
version         = 1.0.0

# ── Entry point ────────────────────────────────────────────────────────────────
source.dir      = .
source.include_exts = py,png,jpg,jpeg,json,ttf,ogg,wav,mp3,kv
source.include_patterns = assets/*,games/*,shell/*,sdk/*

main.py         = main.py

# ── Python & Requirements ──────────────────────────────────────────────────────
# python-for-android (p4a) provides CPython + SDL2 + pygame on Android
requirements = python3,kivy==2.3.0,pygame,sdl2,sdl2_image,sdl2_mixer,sdl2_ttf

# ── Android config ────────────────────────────────────────────────────────────
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET,MANAGE_EXTERNAL_STORAGE
android.api         = 33
android.minapi      = 24
android.ndk         = 25b
android.sdk         = 33
android.accept_sdk_license = True

# Orientation: games can override this at runtime
orientation         = portrait

# Allow landscape when game requests it
android.allow_backup = True

# ── Screen ────────────────────────────────────────────────────────────────────
# Fullscreen — the shell manages its own chrome
fullscreen          = 1

# ── Icons ─────────────────────────────────────────────────────────────────────
# icon.filename = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/splash.png
# presplash.color = #080A14

# ── Build ─────────────────────────────────────────────────────────────────────
[buildozer]
log_level   = 2
warn_on_root = 1

# ── HOW TO BUILD ──────────────────────────────────────────────────────────────
# Prerequisites (Ubuntu/WSL):
#   sudo apt install -y git zip unzip openjdk-17-jdk python3-pip
#   pip install buildozer cython
#
# First build (slow ~20min, downloads NDK/SDK):
#   buildozer android debug
#
# Output:
#   bin/blemacshell-1.0.0-debug.apk
#
# Install to phone (USB debugging on):
#   buildozer android deploy run
#
# Or copy the .apk to phone and sideload it.
