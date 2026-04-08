"""
shell/ui/home_screen.py — BLEMAC Shell home screen (Kivy).

PSP XMB-inspired: horizontal scrolling game cards, neon-dark aesthetic,
animated scanlines, metadata strip, and touch-friendly card tap-to-launch.
"""

import os
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.graphics import (Color, Rectangle, RoundedRectangle,
                            Line, Ellipse, Canvas)
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.metrics import dp, sp
from kivy.properties import (NumericProperty, StringProperty,
                               ObjectProperty, BooleanProperty)

from shell.core.manifest import GameManifest


# ── Colour palette ─────────────────────────────────────────────────────────────
BG       = (8/255,  10/255, 20/255,  1)
ACCENT   = (0/255, 220/255, 180/255, 1)   # cyan
ACCENT2  = (220/255, 60/255, 120/255, 1)  # magenta
TEXT     = (220/255, 230/255, 255/255, 1)
DIM      = (60/255,  70/255,  90/255, 1)
DARK     = (12/255,  16/255,  32/255, 1)


# ── Game Card ──────────────────────────────────────────────────────────────────

class GameCard(Button):
    """A tappable game card with icon, title, and selection glow."""

    selected = BooleanProperty(False)

    def __init__(self, manifest: GameManifest, on_select, on_launch, **kwargs):
        super().__init__(**kwargs)
        self.manifest   = manifest
        self._on_select = on_select
        self._on_launch = on_launch

        self.background_normal   = ""
        self.background_down     = ""
        self.background_color    = (0, 0, 0, 0)
        self.size_hint           = (None, None)
        self.size                = (dp(140), dp(170))

        self._build_ui()
        self.bind(selected=self._on_selected_change)

    def _build_ui(self):
        layout = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(8))

        # Icon area
        icon_box = Widget(size_hint=(1, None), height=dp(120))
        if self.manifest.icon_path and os.path.isfile(self.manifest.icon_path):
            img = KivyImage(
                source=self.manifest.icon_path,
                size_hint=(1, 1),
                allow_stretch=True,
                keep_ratio=True,
            )
            icon_box.add_widget(img)
        else:
            # Placeholder with game initial
            with icon_box.canvas:
                Color(*DARK)
                RoundedRectangle(pos=icon_box.pos, size=icon_box.size, radius=[dp(10)])
                Color(*DIM)
                Line(rounded_rectangle=(*icon_box.pos, *icon_box.size, dp(10)), width=1.2)

        # Title label
        lbl = Label(
            text=self.manifest.title[:12],
            font_size=sp(12),
            bold=True,
            color=TEXT,
            size_hint=(1, None),
            height=dp(24),
            halign="center",
        )
        lbl.bind(size=lbl.setter("text_size"))

        layout.add_widget(icon_box)
        layout.add_widget(lbl)
        self.add_widget(layout)

        # Draw card background
        with self.canvas.before:
            self._bg_color = Color(*DARK)
            self._bg_rect  = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(12)]
            )
            self._border_color = Color(*DIM)
            self._border_rect  = Line(
                rounded_rectangle=(*self.pos, *self.size, dp(12)), width=1.2
            )

        self.bind(pos=self._update_graphics, size=self._update_graphics)

    def _update_graphics(self, *args):
        self._bg_rect.pos    = self.pos
        self._bg_rect.size   = self.size
        self._border_rect.rounded_rectangle = (*self.pos, *self.size, dp(12))

    def _on_selected_change(self, *args):
        if self.selected:
            self._bg_color.rgba         = (*ACCENT[:3], 0.12)
            self._border_color.rgba     = (*ACCENT[:3], 1.0)
            Animation(opacity=1.0, duration=0.1).start(self)
        else:
            self._bg_color.rgba         = DARK
            self._border_color.rgba     = DIM
            self.opacity = 0.65

    def on_press(self):
        self._on_select(self)

    def on_release(self):
        # Double-tap = launch; single tap = select
        if self.selected:
            self._on_launch(self.manifest)
        else:
            self._on_select(self)


# ── Home Screen ────────────────────────────────────────────────────────────────

class HomeScreen(FloatLayout):
    """
    Full home screen widget:
    - Animated dark background with scanlines
    - Horizontal scrolling game card row
    - Bottom metadata strip
    - Top HUD bar
    - [Launch] button
    """

    def __init__(self, manifests: list, on_launch, on_rescan, **kwargs):
        super().__init__(**kwargs)
        self._manifests  = manifests
        self._on_launch  = on_launch
        self._on_rescan  = on_rescan
        self._selected_card = None
        self._anim_t     = 0.0

        self._draw_bg()
        self._build_hud()
        self._build_card_row()
        self._build_meta_strip()
        self._build_launch_btn()
        self._build_empty_hint()

        Clock.schedule_interval(self._tick, 1/30)

    # ── Background ─────────────────────────────────────────────────────────────

    def _draw_bg(self):
        with self.canvas.before:
            Color(*BG)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self._bg_rect.pos  = self.pos
        self._bg_rect.size = self.size

    # ── HUD Bar ────────────────────────────────────────────────────────────────

    def _build_hud(self):
        hud = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(44),
            padding=(dp(16), dp(8)),
            spacing=dp(12),
            pos_hint={"top": 1},
        )
        with hud.canvas.before:
            Color(5/255, 8/255, 18/255, 0.92)
            self._hud_rect = Rectangle(pos=hud.pos, size=hud.size)
        hud.bind(pos=lambda *a: setattr(self._hud_rect, "pos", hud.pos),
                 size=lambda *a: setattr(self._hud_rect, "size", hud.size))

        title_lbl = Label(
            text="◈  BLEMAC SHELL",
            font_size=sp(15),
            bold=True,
            color=ACCENT,
            size_hint=(1, 1),
            halign="left",
        )
        title_lbl.bind(size=title_lbl.setter("text_size"))

        rescan_btn = Button(
            text="⟳ SCAN",
            font_size=sp(12),
            size_hint=(None, 1),
            width=dp(80),
            background_normal="",
            background_color=(*ACCENT[:3], 0.2),
            color=ACCENT,
        )
        rescan_btn.bind(on_press=lambda *a: self._on_rescan())

        self._game_count_lbl = Label(
            text=f"{len(self._manifests)} GAMES",
            font_size=sp(12),
            color=DIM,
            size_hint=(None, 1),
            width=dp(80),
            halign="right",
        )
        self._game_count_lbl.bind(size=self._game_count_lbl.setter("text_size"))

        hud.add_widget(title_lbl)
        hud.add_widget(self._game_count_lbl)
        hud.add_widget(rescan_btn)
        self.add_widget(hud)

    # ── Card Row ───────────────────────────────────────────────────────────────

    def _build_card_row(self):
        # Scrollable horizontal strip of cards
        self._scroll = ScrollView(
            size_hint=(1, None),
            height=dp(190),
            pos_hint={"center_y": 0.58},
            do_scroll_y=False,
            bar_width=0,
        )

        self._card_box = BoxLayout(
            orientation="horizontal",
            spacing=dp(14),
            padding=(dp(20), dp(10)),
            size_hint=(None, 1),
        )
        self._card_box.bind(minimum_width=self._card_box.setter("width"))

        self._cards: list[GameCard] = []
        self._rebuild_cards()

        self._scroll.add_widget(self._card_box)
        self.add_widget(self._scroll)

    def _rebuild_cards(self):
        self._card_box.clear_widgets()
        self._cards.clear()
        self._selected_card = None

        for m in self._manifests:
            card = GameCard(
                manifest=m,
                on_select=self._select_card,
                on_launch=self._on_launch,
            )
            self._cards.append(card)
            self._card_box.add_widget(card)

        if self._cards:
            self._select_card(self._cards[0])

        # Update game count
        if hasattr(self, "_game_count_lbl"):
            n = len(self._manifests)
            self._game_count_lbl.text = f"{n} GAME{'S' if n != 1 else ''}"

    def refresh(self, manifests: list):
        self._manifests = manifests
        self._rebuild_cards()
        self._update_meta()
        self._update_empty_hint()

    # ── Card Selection ─────────────────────────────────────────────────────────

    def _select_card(self, card: GameCard):
        if self._selected_card:
            self._selected_card.selected = False
        self._selected_card = card
        card.selected = True
        self._update_meta()

    # ── Meta Strip ─────────────────────────────────────────────────────────────

    def _build_meta_strip(self):
        strip = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(80),
            padding=(dp(20), dp(10)),
            spacing=dp(2),
            pos_hint={"y": 0.13},
        )
        with strip.canvas.before:
            Color(5/255, 8/255, 18/255, 0.88)
            self._meta_rect = Rectangle(pos=strip.pos, size=strip.size)
        strip.bind(pos=lambda *a: setattr(self._meta_rect, "pos", strip.pos),
                   size=lambda *a: setattr(self._meta_rect, "size", strip.size))

        self._meta_title = Label(
            text="Select a game",
            font_size=sp(16),
            bold=True,
            color=ACCENT,
            halign="left",
            size_hint=(1, None),
            height=dp(26),
        )
        self._meta_title.bind(size=self._meta_title.setter("text_size"))

        self._meta_desc = Label(
            text="",
            font_size=sp(12),
            color=DIM,
            halign="left",
            size_hint=(1, None),
            height=dp(20),
        )
        self._meta_desc.bind(size=self._meta_desc.setter("text_size"))

        self._meta_author = Label(
            text="",
            font_size=sp(11),
            color=TEXT,
            halign="left",
            size_hint=(1, None),
            height=dp(18),
        )
        self._meta_author.bind(size=self._meta_author.setter("text_size"))

        strip.add_widget(self._meta_title)
        strip.add_widget(self._meta_desc)
        strip.add_widget(self._meta_author)
        self.add_widget(strip)

    def _update_meta(self):
        if not self._selected_card:
            self._meta_title.text  = "No games found"
            self._meta_desc.text   = ""
            self._meta_author.text = ""
            return
        m = self._selected_card.manifest
        self._meta_title.text  = f"{m.title}  {m.version}"
        desc = m.description[:72] + ("…" if len(m.description) > 72 else "")
        self._meta_desc.text   = desc
        tags_str = "  ".join(f"[{t}]" for t in m.tags)
        self._meta_author.text = f"by {m.author}   {tags_str}"

    # ── Launch Button ──────────────────────────────────────────────────────────

    def _build_launch_btn(self):
        self._launch_btn = Button(
            text="▶  LAUNCH",
            font_size=sp(15),
            bold=True,
            size_hint=(None, None),
            size=(dp(160), dp(44)),
            pos_hint={"center_x": 0.5, "y": 0.02},
            background_normal="",
            background_color=(*ACCENT[:3], 0.85),
            color=(8/255, 10/255, 20/255, 1),
        )
        self._launch_btn.bind(on_press=self._press_launch)
        self.add_widget(self._launch_btn)

    def _press_launch(self, *args):
        if self._selected_card:
            self._on_launch(self._selected_card.manifest)

    # ── Empty Hint ─────────────────────────────────────────────────────────────

    def _build_empty_hint(self):
        self._empty_lbl = Label(
            text=(
                "No games found.\n\n"
                "Copy game folders to:\n"
                "[b]/sdcard/BlemacShell/games/[/b]\n\n"
                "Each folder needs a [b]game.json[/b] and [b]main.py[/b].\n"
                "Then tap ⟳ SCAN."
            ),
            markup=True,
            font_size=sp(13),
            color=DIM,
            halign="center",
            valign="middle",
            size_hint=(0.8, None),
            height=dp(200),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self._empty_lbl.bind(size=self._empty_lbl.setter("text_size"))
        self.add_widget(self._empty_lbl)
        self._update_empty_hint()

    def _update_empty_hint(self):
        self._empty_lbl.opacity = 1 if not self._manifests else 0

    # ── Animation tick ─────────────────────────────────────────────────────────

    def _tick(self, dt):
        self._anim_t += dt
        # Could drive scanline overlay here if needed
