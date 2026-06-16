"""
screens/detail_screen.py
------------------------
Layar detail satu saham — menampilkan semua metrik fundamental
beserta indikator lolos/tidak untuk setiap kriteria Graham.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp

C_BG      = (0.06, 0.09, 0.16, 1)
C_CARD    = (0.10, 0.15, 0.25, 1)
C_PRIMARY = (0.12, 0.25, 0.69, 1)
C_TEXT    = (0.93, 0.95, 0.98, 1)
C_SUBTEXT = (0.55, 0.65, 0.75, 1)
C_GREEN   = (0.09, 0.70, 0.33, 1)
C_YELLOW  = (0.86, 0.60, 0.09, 1)
C_RED     = (0.86, 0.20, 0.20, 1)
C_HEADER  = (0.08, 0.13, 0.22, 1)


def lbl(text, size=13, color=C_TEXT, bold=False, halign="left", height=None):
    l = Label(text=text, font_size=sp(size), color=color,
              bold=bold, halign=halign, size_hint_y=None)
    l.height = height or dp(size * 2.2)
    l.bind(size=lambda w, _: setattr(w, "text_size", (w.width, None)))
    return l


def card_box(spacing=dp(8), padding=dp(14)):
    b = BoxLayout(orientation="vertical", size_hint_y=None,
                  spacing=spacing, padding=padding)
    b.bind(minimum_height=b.setter("height"))
    with b.canvas.before:
        Color(*C_CARD)
        b._rect = RoundedRectangle(pos=b.pos, size=b.size, radius=[dp(12)])
    b.bind(pos=lambda w, v: setattr(w._rect, "pos", v),
           size=lambda w, v: setattr(w._rect, "size", v))
    return b


def fmt(v, dec=2, prefix="", suffix=""):
    return f"{prefix}{round(v, dec)}{suffix}" if v is not None else "—"


def graham_check(metric, value, threshold, op="le"):
    """Return (pass: bool, display_str)."""
    if value is None:
        return None, "Data N/A"
    passed = (value <= threshold) if op == "le" else (value >= threshold)
    icon   = "✅" if passed else "❌"
    op_str = "≤" if op == "le" else "≥"
    return passed, f"{icon}  {metric} {op_str} {threshold}  →  {round(value,2)}"


class DetailScreen(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)
        self._stock = {}

        with self.canvas.before:
            Color(*C_BG)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, v: setattr(w._bg, "pos", v),
                  size=lambda w, v: setattr(w._bg, "size", v))

        root = BoxLayout(orientation="vertical")
        root.add_widget(self._build_topbar())

        scroll = ScrollView(do_scroll_x=False)
        self._content = BoxLayout(orientation="vertical",
                                  padding=dp(12), spacing=dp(10),
                                  size_hint_y=None)
        self._content.bind(minimum_height=self._content.setter("height"))
        scroll.add_widget(self._content)
        root.add_widget(scroll)
        self.add_widget(root)

    # ── Topbar ────────────────────────────────────────────────────────────────
    def _build_topbar(self):
        bar = BoxLayout(size_hint_y=None, height=dp(54),
                        padding=(dp(10), dp(8)), spacing=dp(8))
        with bar.canvas.before:
            Color(*C_HEADER)
            bar._rect = RoundedRectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda w, v: setattr(w._rect, "pos", v),
                 size=lambda w, v: setattr(w._rect, "size", v))

        back = Button(text="← Hasil", font_size=sp(12),
                      size_hint=(None, 1), width=dp(80),
                      background_normal="", background_color=C_PRIMARY)
        back.bind(on_press=lambda _: setattr(self.manager, "current", "result"))

        self._title_lbl = lbl("Detail Saham", size=15, bold=True,
                               halign="center", height=dp(38))
        bar.add_widget(back)
        bar.add_widget(self._title_lbl)
        return bar

    # ── Load data ─────────────────────────────────────────────────────────────
    def load_stock(self, stock: dict):
        self._stock = stock
        self._content.clear_widgets()
        self._title_lbl.text = stock.get("ticker", "Detail")

        self._content.add_widget(self._section_identity())
        self._content.add_widget(self._section_score())
        self._content.add_widget(self._section_graham())
        self._content.add_widget(self._section_all_metrics())
        self._content.add_widget(self._section_disclaimer())

    # ── Identitas ─────────────────────────────────────────────────────────────
    def _section_identity(self):
        s = self._stock
        box = card_box()
        box.add_widget(lbl(s.get("ticker","?"), size=26, bold=True, height=dp(40)))
        box.add_widget(lbl(s.get("company","—"), size=14, color=C_SUBTEXT, height=dp(22)))
        box.add_widget(lbl(s.get("sector","—"),  size=12, color=C_SUBTEXT, height=dp(20)))

        price_row = BoxLayout(size_hint_y=None, height=dp(32))
        price_row.add_widget(lbl("Harga Saham", size=12, color=C_SUBTEXT, height=dp(32)))
        price_row.add_widget(lbl(fmt(s.get("price"), prefix="$"), size=20,
                                 bold=True, halign="right", height=dp(32)))
        box.add_widget(price_row)
        return box

    # ── Value Score ───────────────────────────────────────────────────────────
    def _section_score(self):
        s     = self._stock
        score = s.get("score", 0)
        box   = card_box(padding=dp(16))

        if score >= 65:
            verdict, vcolor = "Sangat Undervalued 🚀", C_GREEN
        elif score >= 40:
            verdict, vcolor = "Cukup Menarik 👀", C_YELLOW
        else:
            verdict, vcolor = "Kurang Menarik ⚠️", C_RED

        box.add_widget(lbl("VALUE SCORE", size=10, color=C_SUBTEXT,
                           bold=True, halign="center", height=dp(16)))
        box.add_widget(lbl(str(score), size=48, bold=True,
                           color=vcolor, halign="center", height=dp(64)))
        box.add_widget(lbl("/ 100", size=12, color=C_SUBTEXT,
                           halign="center", height=dp(18)))
        box.add_widget(lbl(verdict, size=14, bold=True,
                           color=vcolor, halign="center", height=dp(24)))
        return box

    # ── Graham Checklist ──────────────────────────────────────────────────────
    def _section_graham(self):
        s   = self._stock
        box = card_box()
        box.add_widget(lbl("KRITERIA BENJAMIN GRAHAM", size=11,
                           color=C_SUBTEXT, bold=True, height=dp(20)))

        checks = [
            graham_check("P/E", s.get("pe"),  15,  "le"),
            graham_check("P/B", s.get("pb"),  1.5, "le"),
            graham_check("ROE (%)", s.get("roe"), 15, "ge"),
            graham_check("D/E", s.get("de"),  1.0, "le"),
        ]

        for passed, text in checks:
            color = C_GREEN if passed else (C_RED if passed is False else C_SUBTEXT)
            row = BoxLayout(size_hint_y=None, height=dp(28))
            row.add_widget(lbl(text, size=12, color=color, height=dp(28)))
            box.add_widget(row)

        passed_count = sum(1 for p, _ in checks if p is True)
        box.add_widget(lbl(f"Lolos {passed_count}/4 kriteria Graham",
                           size=12, bold=True, color=C_TEXT,
                           halign="right", height=dp(22)))
        return box

    # ── Semua Metrik ──────────────────────────────────────────────────────────
    def _section_all_metrics(self):
        s   = self._stock
        box = card_box()
        box.add_widget(lbl("SEMUA METRIK FUNDAMENTAL", size=11,
                           color=C_SUBTEXT, bold=True, height=dp(20)))

        metrics = [
            ("P/E Ratio",        fmt(s.get("pe"))),
            ("P/B Ratio",        fmt(s.get("pb"))),
            ("ROE",              fmt(s.get("roe"), suffix="%")),
            ("Debt/Equity",      fmt(s.get("de"))),
            ("Market Cap",       fmt(s.get("mktcap"), prefix="$", suffix="B")),
            ("EPS",              fmt(s.get("eps"), prefix="$")),
            ("Dividend Yield",   fmt(s.get("div_yield"), suffix="%")),
            ("Revenue Growth",   fmt(s.get("rev_growth"), suffix="%")),
            ("Gross Margin",     fmt(s.get("gross_margin"), suffix="%")),
        ]

        for name, value in metrics:
            row = BoxLayout(size_hint_y=None, height=dp(30))
            row.add_widget(lbl(name,  size=12, color=C_SUBTEXT, height=dp(30)))
            row.add_widget(lbl(value, size=13, bold=True, halign="right",
                               height=dp(30)))
            box.add_widget(row)

        return box

    # ── Disclaimer ────────────────────────────────────────────────────────────
    def _section_disclaimer(self):
        box = BoxLayout(size_hint_y=None, height=dp(40),
                        padding=(dp(10), 0))
        box.add_widget(lbl(
            "⚠️ Data dari Yahoo Finance. Bukan saran investasi. DYOR.",
            size=10, color=C_SUBTEXT, halign="center", height=dp(40)))
        return box
