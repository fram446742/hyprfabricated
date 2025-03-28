import gi
import urllib.parse
import requests
import json
import time
from gi.repository import GLib

from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.utils import invoke_repeater, get_relative_path

gi.require_version("Gtk", "3.0")
import modules.icons as icons
import config.data as data

CONFIG_CACHE = None


class Weather(Button):
    def __init__(self, **kwargs) -> None:
        super().__init__(name="weather", orientation="h", spacing=8, **kwargs)
        self.label = Label(name="weather-label", markup=icons.loader)
        self.add(self.label)
        self.show_all()
        self.enabled = True  # Add a flag to track if the component should be shown
        self.session = requests.Session()  # Reuse HTTP connection
        # Update every 10 minutes
        GLib.timeout_add_seconds(600, self.fetch_weather)
        self.fetch_weather()


    def load_config(_):
        """Load and cache config file to reduce file I/O latency."""
        global CONFIG_CACHE
        if CONFIG_CACHE is None:
            try:
                with open(get_relative_path("../config.json"), "r") as file:
                    CONFIG_CACHE = json.load(file)
            except Exception as e:
                print(f"Error reading config: {e}")
                CONFIG_CACHE = {}
        return CONFIG_CACHE


    def get_location(self):
        """Fetch location from config file or IP API asynchronously."""
        config = self.load_config()
        if city := config.get("city"):
            return city
        try:
            response = self.session.get("https://ipinfo.io/json", timeout=5, stream=True)
            if response.ok:
                return response.json().get("city", "")
        except requests.RequestException:
            pass
        return ""
    
    # def get_location(self):
    #     """Fetch user's city using IP geolocation."""
    #     try:
    #         response = self.session.get("https://ipinfo.io/json", timeout=5, stream=True)
    #         if response.ok:
    #             return response.json().get("city", "")
    #     except requests.RequestException:
    #         pass
    #     return ""


    def set_visible(self, visible):
        """Override to track external visibility setting"""
        self.enabled = visible
        # Only update actual visibility if weather data is available
        if visible and hasattr(self, 'has_weather_data') and self.has_weather_data:
            super().set_visible(True)
        else:
            super().set_visible(visible)

    def fetch_weather(self):
        GLib.Thread.new("weather-fetch", self._fetch_weather_thread, None)
        return True

    def _fetch_weather_thread(self, user_data):
        # Let wttr.in determine location based on IP
        location = self.get_location()
        locsafe = urllib.parse.quote(location)
        if not location:
            return self._update_ui(error=True)
        url = f"https://wttr.in/{locsafe}?format=%c+%t" if not data.VERTICAL else f"https://wttr.in/{locsafe}?format=%c"
        # Get detailed info for tooltip
        tooltip_url = f"https://wttr.in/{locsafe}?format=%l:+%C,+%t+(%f),+Humidity:+%h,+Wind:+%w"

        try:
            response = self.session.get(url, timeout=5)
            if response.ok:
                weather_data = response.text.strip()
                if "Unknown" in weather_data:
                    self.has_weather_data = False
                    GLib.idle_add(super().set_visible, False)
                else:
                    self.has_weather_data = True
                    # Get tooltip data
                    tooltip_response = self.session.get(tooltip_url, timeout=5)
                    if tooltip_response.ok:
                        tooltip_text = tooltip_response.text.strip()
                        GLib.idle_add(self.set_tooltip_text, tooltip_text)

                    GLib.idle_add(self.set_visible, True)
                    GLib.idle_add(self.label.set_label, weather_data.replace(" ", ""))
            else:
                self.has_weather_data = False
                GLib.idle_add(self.label.set_markup, f"{icons.cloud_off} Unavailable")
                GLib.idle_add(super().set_visible, False)
        except Exception as e:
            self.has_weather_data = False
            print(f"Error fetching weather: {e}")
            GLib.idle_add(self.label.set_markup, f"{icons.cloud_off} Error")
            GLib.idle_add(self.set_visible, False)

        def _update_ui(self, text=None, visible=True, error=False):
            """Safely update UI elements from the worker thread."""
            if error:
                text = f"{icons.cloud_off} Unavailable"
                visible = False
            GLib.idle_add(self.label.set_markup if error else self.label.set_label, text)
            GLib.idle_add(self.set_visible, visible)
