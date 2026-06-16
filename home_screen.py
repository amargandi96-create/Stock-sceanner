"""
screens/home_screen.py
----------------------
Layar utama: input ticker, konfigurasi filter, tombol Screener.
"""

import threading
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.progressbar import ProgressBar
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp

from core.data_fetcher import fetch_multiple
from core.screener import ScreenerConfig, apply_filters

# ── Warna tema ──────────────────────────────────────────────────────────────
C_BG       = (0.06, 0.09, 0.16, 1)
C_CARD     = (0.10, 0.15, 0.25, 1)
C_PRIMARY  = (0.12, 0.25, 0.69, 1)
C_ACCENT   = (0.09, 0.56, 0.26, 1)
C_TEXT     = (0.93, 0.95, 0.98, 1)
C_SUBTEXT  = (0.55, 0.65, 0.75, 1)
C_WARN     = (0.86, 0.15, 0.15, 1)

DEFAULT_US  = "AAPL, MSFT, GOOGL, AMZN, META, JNJ, KO, WMT, JPM, XOM, V, PG, CVX, NVDA, BRK-B"
DEFAULT_IDX = "BBCA.JK, BBRI.JK, TLKM.JK, ASII.JK, BMRI.JK, UNVR.JK, ICBP.JK, HMSP.JK"


def make_card(padding=dp(14), spacing=dp(8), orientation="vertical"):
    layout = BoxLayout(orientation=orientation,
                       padding=padding, spacing=spacing,
                       size_hint_y=None)
    layout.bind(minimum_height=layout.setter("height"))
    with layout.canvas.before:
        Color(*C_CARD)
        layout._rect = RoundedRectangle(pos=layout.pos,
                                        size=layout.size, radius=[dp(12)])
    layout.bind(pos=lambda w, v: setattr(w._rect, "pos", v),
                size=lambda w, v: setattr(w._rect, "size", v))
    return layout


def lbl(text, size=14, color=C_TEXT, bold=False, halign="left", height=None):
    l = Label(text=text, font_size=sp(size), color=color,
              bold=bold, halign=halign, size_hint_y=None)
    l.height = height or dp(size * 2.2)
    l.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
    return l


class SliderRow(BoxLayout):
    """Label + Slider + nilai, dalam satu baris."""

    def __init__(self, title, min_v, max_v, default, step=0.5,
                 on_change=None, **kw):
        super().__init__(orientation="vertical",
                         size_hint_y=None, height=dp(64), **kw)
        self.on_change_cb = on_change

        top = BoxLayout(size_hint_y=None, height=dp(22))
        self._title_lbl = lbl(title, size=12, color=C_SUBTEXT, height=dp(22))
        self._val_lbl   = lbl(str(default), size=12, bold=True,
                              color=C_TEXT, halign="right", height=dp(22))
        top.add_widget(self._title_lbl)
        top.add_widget(self._val_lbl)

        self._slider = Slider(min=min_v, max=max_v, value=default, step=step,
                              size_hint_y=None, height=dp(36),
                              cursor_size=(dp(22), dp(22)))
        self._slider.bind(value=self._on_value)

        self.add_widget(top)
        self.add_widget(self._slider)

    def _on_value(self, _, v):
        self._val_lbl.text = str(round(v, 2))
        if self.on_change_cb:
            self.on_change_cb(v)

    @property
    def value(self):
        return self._slider.value


class HomeScreen(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)
        self._market    = "US"
        self._cfg       = ScreenerConfig()
        self._running   = False

        # Root scroll
        scroll = ScrollView(do_scroll_x=False)
        root = BoxLayout(orientation="vertical",
                         padding=dp(12), spacing=dp(10),
                         size_hint_y=None)
        root.bind(minimum_height=root.setter("height"))

        with self.canvas.before:
            Color(*C_BG)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, v: setattr(w._bg, "pos", v),
                  size=lambda w, v: setattr(w._bg, "size", v))

        root.add_widget(self._build_header())
        root.add_widget(self._build_market_card())
        root.add_widget(self._build_ticker_card())
        root.add_widget(self._build_filter_card())
        root.add_widget(self._build_run_section())

        scroll.add_widget(root)
        self.add_widget(scroll)

    # ── Header ──────────────────────────────────────────────────────────────
    def _build_header(self):
        box = BoxLayout(orientation="vertical",
                        size_hint_y=None, height=dp(70),
                        padding=(0, dp(8)))
        box.add_widget(lbl("📊 Value Stock Screener", size=20,
                           bold=True, halign="center"))
        box.add_widget(lbl("Benjamin Graham · Warren Buffett Criteria",
                           size=11, color=C_SUBTEXT, halign="center"))
        return box

    # ── Market selector ─────────────────────────────────────────────────────
    def _build_market_card(self):
        card = make_card(spacing=dp(6))
        card.add_widget(lbl("PILIH PASAR", size=11, color=C_SUBTEXT, bold=True))

        row = GridLayout(cols=3, size_hint_y=None, height=dp(40), spacing=dp(6))
        self._mkt_btns = {}
        for mkt, label in [("US", "🇺🇸 US"), ("IDX", "🇮🇩 IDX"), ("custom", "✏️ Custom")]:
            btn = ToggleButton(text=label, group="market",
                               font_size=sp(12),
                               background_normal="",
                               background_down="",
                               background_color=C_PRIMARY if mkt == "US" else C_CARD)
            if mkt == "US":
                btn.state = "down"
            btn.bind(on_press=lambda b, m=mkt: self._set_market(m))
            row.add_widget(btn)
            self._mkt_btns[mkt] = btn

        card.add_widget(row)
        return card

    def _set_market(self, mkt):
        self._market = mkt
        for k, b in self._mkt_btns.items():
            b.background_color = C_PRIMARY if k == mkt else C_CARD

        if mkt == "US":
            self._ticker_input.text = DEFAULT_US
        elif mkt == "IDX":
            self._ticker_input.text = DEFAULT_IDX
        else:
            self._ticker_input.text = ""

    # ── Ticker input ─────────────────────────────────────────────────────────
    def _build_ticker_card(self):
        card = make_card()
        card.add_widget(lbl("DAFTAR TICKER", size=11, color=C_SUBTEXT, bold=True))
        card.add_widget(lbl("Pisahkan dengan koma. Saham IDX tambahkan .JK",
                            size=11, color=C_SUBTEXT))

        self._ticker_input = TextInput(
            text=DEFAULT_US,
            multiline=True,
            font_size=sp(12),
            size_hint_y=None, height=dp(80),
            background_color=(0.08, 0.12, 0.22, 1),
            foreground_color=C_TEXT,
            cursor_color=C_TEXT,
            padding=(dp(10), dp(8)),
        )
        card.add_widget(self._ticker_input)
        return card

    # ── Filter sliders ───────────────────────────────────────────────────────
    def _build_filter_card(self):
        card = make_card(spacing=dp(12))
        card.add_widget(lbl("FILTER VALUE INVESTING", size=11,
                            color=C_SUBTEXT, bold=True))

        self._sl_pe = SliderRow("P/E Ratio Maks", 1, 50, 15, step=0.5,
                                on_change=lambda v: setattr(self._cfg, "max_pe", v))
        self._sl_pb = SliderRow("P/B Ratio Maks", 0.1, 5, 1.5, step=0.1,
                                on_change=lambda v: setattr(self._cfg, "max_pb", v))
        self._sl_roe = SliderRow("ROE Minimum (%)", 0, 50, 15, step=1,
                                 on_change=lambda v: setattr(self._cfg, "min_roe", v))
        self._sl_de = SliderRow("Debt/Equity Maks", 0, 3, 1.0, step=0.1,
                                on_change=lambda v: setattr(self._cfg, "max_de", v))

        for sl in (self._sl_pe, self._sl_pb, self._sl_roe, self._sl_de):
            card.add_widget(sl)

        return card

    # ── Run section ──────────────────────────────────────────────────────────
    def _build_run_section(self):
        box = BoxLayout(orientation="vertical",
                        size_hint_y=None, height=dp(110),
                        spacing=dp(8))

        self._progress = ProgressBar(max=100, value=0,
                                     size_hint_y=None, height=dp(8))
        self._status_lbl = lbl("", size=11, color=C_SUBTEXT, halign="center")

        self._run_btn = Button(
            text="🔍  JALANKAN SCREENER",
            font_size=sp(14), bold=True,
            size_hint_y=None, height=dp(52),
            background_normal="",
            background_color=C_PRIMARY,
        )
        self._run_btn.bind(on_press=self._start_screening)

        box.add_widget(self._progress)
        box.add_widget(self._status_lbl)
        box.add_widget(self._run_btn)
        return box

    # ── Screening logic ──────────────────────────────────────────────────────
    def _start_screening(self, *_):
        if self._running:
            return

        raw_text = self._ticker_input.text.strip()
        tickers  = [t.strip().upper() for t in raw_text.split(",") if t.strip()]

        if not tickers:
            self._status_lbl.text = "⚠️ Masukkan minimal satu ticker!"
            self._status_lbl.color = C_WARN
            return

        self._running = True
        self._run_btn.text = "⏳  Mengambil data..."
        self._run_btn.background_color = C_SUBTEXT
        self._progress.value = 0
        self._status_lbl.color = C_SUBTEXT

        def worker():
            def on_prog(done, total):
                pct = int(done / total * 80)
                Clock.schedule_once(
                    lambda _: self._update_progress(pct,
                        f"Mengambil data {done}/{total}..."), 0)

            raw, failed = fetch_multiple(tickers, on_progress=on_prog)

            Clock.schedule_once(
                lambda _: self._update_progress(90, "Menerapkan filter..."), 0)

            cfg = ScreenerConfig(
                max_pe    = self._sl_pe.value,
                max_pb    = self._sl_pb.value,
                min_roe   = self._sl_roe.value,
                max_de    = self._sl_de.value,
            )
            result = apply_filters(raw, cfg)

            Clock.schedule_once(
                lambda _: self._done(raw, result, failed), 0)

        threading.Thread(target=worker, daemon=True).start()

    def _update_progress(self, pct, msg):
        self._progress.value = pct
        self._status_lbl.text = msg

    def _done(self, raw, result, failed):
        self._progress.value = 100
        self._running = False
        self._run_btn.text = "🔍  JALANKAN SCREENER"
        self._run_btn.background_color = C_PRIMARY

        msg = f"✅ {len(result)} lolos dari {len(raw)} saham."
        if failed:
            msg += f" ({len(failed)} gagal)"
        self._status_lbl.text  = msg
        self._status_lbl.color = C_ACCENT

        # Kirim data ke ResultScreen
        rs = self.manager.get_screen("result")
        rs.load_data(raw, result)
        self.manager.current = "result"
