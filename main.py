"""
main.py
-------
Aplikasi Stock Screener Value Investing berbasis Kivy untuk Android.
Entry point utama aplikasi.
"""

import threading
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.window import Window
from kivy.utils import platform

# Set ukuran window saat development di PC (diabaikan di Android)
if platform != "android":
    Window.size = (400, 700)

from screens.home_screen import HomeScreen
from screens.result_screen import ResultScreen
from screens.detail_screen import DetailScreen


class StockScreenerApp(App):
    """
    Root aplikasi Kivy — mengelola navigasi antar screen.
    """

    def build(self):
        self.title = "Value Stock Screener"
        self.icon  = "assets/icon.png"

        # Screen manager sebagai navigasi utama
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(ResultScreen(name="result"))
        sm.add_widget(DetailScreen(name="detail"))

        return sm


if __name__ == "__main__":
    StockScreenerApp().run()
