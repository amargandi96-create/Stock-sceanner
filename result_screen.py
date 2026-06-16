"""
screens/result_screen.py
------------------------
Layar hasil screening — daftar saham yang lolos filter
dengan Value Score, color coding, dan tombol detail.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
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


def score_color(score):
    if score >= 65: return C_GREEN
    if score >= 40: return C_YELLOW
    return C_RED


def fmt(v, dec=2, suffix=""):
    return f"{round(v, dec)}{suffix}" if v is not None else "—"


class StockCard(BoxLayout):
    """Card satu saham dalam daftar hasil."""

    def __init__(self, stock: dict, rank: int, on_tap=None, **kw):
        super().__init__(orientation="vertical",
                         size_hint_y=None, padding=dp(12),
                         spacing=dp(4), **kw)
        self.height = dp(100)

        with self.canvas.before:
            Color(*C_CARD)
            self._rect = RoundedRectangle(pos=self.pos,
                                          size=self.size, radius=[dp(10)])
        self.bind(pos=lambda w, v: setattr(w._rect, "pos", v),
                  size=lambda w, v: setattr(w._rect, "size", v))

        sc = stock.get("score", 0)

        # Row 1: Rank + Ticker + Company + Score
        row1 = BoxLayout(size_hint_y=None, height=dp(28))
        row1.add_widget(lbl(f"#{rank}", size=11, color=C_SUBTEXT,
                            height=dp(28)))
        row1.add_widget(lbl(stock.get("ticker","?"), size=16, bold=True,
                            height=dp(28)))
        row1.add_widget(lbl(stock.get("company","")[:22], size=11,
                            color=C_SUBTEXT, height=dp(28)))
        score_lbl = lbl(f"⭐ {sc}", size=14, bold=True,
                        color=score_color(sc), halign="right", height=dp(28))
        row1.add_widget(score_lbl)
        self.add_widget(row1)

        # Row 2: Sektor
        self.add_widget(lbl(stock.get("sector","—"), size=11,
                            color=C_SUBTEXT, height=dp(18)))

        # Row 3: Metrik utama
        row3 = BoxLayout(size_hint_y=None, height=dp(22))
        metrics = [
            ("P/E", fmt(stock.get("pe"))),
            ("P/B", fmt(stock.get("pb"))),
            ("ROE", fmt(stock.get("roe"), suffix="%")),
            ("D/E", fmt(stock.get("de"))),
            ("Cap", f"${fmt(stock.get('mktcap'))}B"),
        ]
        for mname, mval in metrics:
            col = BoxLayout(orientation="vertical")
            col.add_widget(lbl(mname, size=9, color=C_SUBTEXT, halign="center", height=dp(12)))
            col.add_widget(lbl(mval,  size=11, bold=True, halign="center", height=dp(16)))
            row3.add_widget(col)
        self.add_widget(row3)

        # Tap seluruh card
        if on_tap:
            btn = Button(
                background_normal="", background_color=(0, 0, 0, 0),
                size_hint=(1, 1), pos_hint={"center_x": .5, "center_y": .5},
            )
            btn.bind(on_press=lambda _: on_tap(stock))
            self.add_widget(btn)


class ResultScreen(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)
        self._raw    = []
        self._result = []
        self._tab    = "filtered"   # "filtered" | "all"

        with self.canvas.before:
            Color(*C_BG)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda w, v: setattr(w._bg, "pos", v),
                  size=lambda w, v: setattr(w._bg, "size", v))

        root = BoxLayout(orientation="vertical")

        root.add_widget(self._build_topbar())
        self._summary_row = self._build_summary()
        root.add_widget(self._summary_row)
        root.add_widget(self._build_tabs())

        self._scroll = ScrollView(do_scroll_x=False)
        self._list   = BoxLayout(orientation="vertical",
                                 spacing=dp(8), padding=dp(10),
                                 size_hint_y=None)
        self._list.bind(minimum_height=self._list.setter("height"))
        self._scroll.add_widget(self._list)
        root.add_widget(self._scroll)

        self.add_widget(root)

    # ── Top bar ──────────────────────────────────────────────────────────────
    def _build_topbar(self):
        bar = BoxLayout(size_hint_y=None, height=dp(54),
                        padding=(dp(10), dp(8)), spacing=dp(8),
                        orientation="horizontal")
        with bar.canvas.before:
            Color(*C_HEADER)
            bar._rect = RoundedRectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda w, v: setattr(w._rect, "pos", v),
                 size=lambda w, v: setattr(w._rect, "size", v))

        back = Button(text="← Kembali", font_size=sp(12),
                      size_hint=(None, 1), width=dp(90),
                      background_normal="", background_color=C_PRIMARY)
        back.bind(on_press=lambda _: setattr(self.manager, "current", "home"))

        title = lbl("Hasil Screening", size=15, bold=True, halign="center",
                    height=dp(38))

        bar.add_widget(back)
        bar.add_widget(title)
        return bar

    # ── Summary cards ─────────────────────────────────────────────────────────
    def _build_summary(self):
        row = GridLayout(cols=4, size_hint_y=None, height=dp(56),
                         padding=(dp(10), dp(4)), spacing=dp(6))
        self._sum_labels = {}
        for key, label in [("total","Dianalisa"), ("pass","Lolos"),
                            ("rate","Pass Rate"), ("top","Top Score")]:
            col = BoxLayout(orientation="vertical")
            val = lbl("—", size=16, bold=True, halign="center",
                      color=C_PRIMARY, height=dp(26))
            sub = lbl(label, size=9, color=C_SUBTEXT, halign="center",
                      height=dp(14))
            col.add_widget(val)
            col.add_widget(sub)
            row.add_widget(col)
            self._sum_labels[key] = val
        return row

    # ── Tabs ─────────────────────────────────────────────────────────────────
    def _build_tabs(self):
        row = BoxLayout(size_hint_y=None, height=dp(40),
                        padding=(dp(10), dp(4)), spacing=dp(8))
        self._tab_filtered = Button(
            text="✅ Lolos Filter", font_size=sp(12),
            background_normal="", background_color=C_PRIMARY)
        self._tab_all = Button(
            text="📋 Semua Data", font_size=sp(12),
            background_normal="", background_color=C_CARD)

        self._tab_filtered.bind(on_press=lambda _: self._switch_tab("filtered"))
        self._tab_all.bind(on_press=lambda _: self._switch_tab("all"))

        row.add_widget(self._tab_filtered)
        row.add_widget(self._tab_all)
        return row

    def _switch_tab(self, tab):
        self._tab = tab
        self._tab_filtered.background_color = C_PRIMARY if tab == "filtered" else C_CARD
        self._tab_all.background_color      = C_PRIMARY if tab == "all" else C_CARD
        self._render_list()

    # ── Load data ─────────────────────────────────────────────────────────────
    def load_data(self, raw: list, result: list):
        self._raw    = raw
        self._result = result

        n    = len(raw)
        p    = len(result)
        rate = f"{round(p/n*100)}%" if n > 0 else "0%"
        top  = f"{result[0]['score']}" if result else "—"

        self._sum_labels["total"].text = str(n)
        self._sum_labels["pass"].text  = str(p)
        self._sum_labels["rate"].text  = rate
        self._sum_labels["top"].text   = top

        self._tab = "filtered"
        self._tab_filtered.background_color = C_PRIMARY
        self._tab_all.background_color      = C_CARD
        self._render_list()

    # ── Render list ──────────────────────────────────────────────────────────
    def _render_list(self):
        self._list.clear_widgets()
        data = self._result if self._tab == "filtered" else self._raw

        if not data:
            empty = lbl("Tidak ada saham yang lolos filter.\nCoba longgarkan threshold.",
                        size=13, color=C_SUBTEXT, halign="center", height=dp(80))
            self._list.add_widget(empty)
            return

        for i, stock in enumerate(data, 1):
            card = StockCard(stock, i, on_tap=self._open_detail)
            self._list.add_widget(card)

    # ── Open detail ───────────────────────────────────────────────────────────
    def _open_detail(self, stock: dict):
        ds = self.manager.get_screen("detail")
        ds.load_stock(stock)
        self.manager.current = "detail"
