import os
import gi
import urllib.parse
import requests
import json
import time
import os  # Import os to work with filesystem
from gi.repository import GLib

from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.utils import invoke_repeater, get_relative_path

gi.require_version("Gtk", "3.0")
import modules.icons as icons
import config.data as data
from config.data import load_config

config = load_config()

WEATHER_CACHE_FILE = os.path.expanduser("~/.cache/.weather_cache")

class Weather(Button):
    def __init__(self, **kwargs) -> None:
        super().__init__(name="weather", orientation="h", spacing=8, **kwargs)
        self.label = Label(name="weather-label", markup=icons.loader)
        self.add(self.label)
        self.enabled = config.get(
            "bar_weather_visible", False
        )  # Add a flag to track if the component should be shown
        self.session = requests.Session()  # Reuse HTTP connection
        # Update every 10 minutes
        GLib.timeout_add_seconds(600, self.fetch_weather)
        self.fetch_weather()

    def get_location(self):
        """Fetch location from config file or IP API asynchronously."""
        if city := config.get("widgets_weather_location"):
            return city
        try:
            response = self.session.get(
                "https://ipinfo.io/json", timeout=5, stream=True
            )
            if response.ok:
                return response.json().get("city", "")
        except requests.RequestException:
            pass
        return ""

    def set_visible(self, visible):
        """Override to track external visibility setting"""
        # Only update actual visibility if weather data is available
        if visible and hasattr(self, "has_weather_data") and self.has_weather_data:
            super().set_visible(self.enabled)
        else:
            super().set_visible(False)

    def fetch_weather(self):
        GLib.Thread.new("weather-fetch", self._fetch_weather_thread, None)
        return True
    
    def _write_cache(self, weather_data, tooltip_text=None):
        """
        Save weather data to a cache file in a human-readable and pretty format.
        Expected format based on the tooltip:
          Madrid: Partly cloudy +12°C (+11°C)
          Humidity: 71% Wind: ↗14km/h
        """
        if tooltip_text is not None:
            tooltip_parts = [part.strip() for part in tooltip_text.split(",")]
            if len(tooltip_parts) >= 4:
                # Replace the numeric temperature with weather_data that holds the icon
                first_line = f"{tooltip_parts[0]} {weather_data} {tooltip_parts[1].split()[1]}"
                second_line = f"{tooltip_parts[2]} {tooltip_parts[3]}"
                cache_text = f"{first_line}\n{second_line}\n"
            else:
                # Fallback to splitting lines if tooltip format is unexpected
                formatted_tooltip = "\n".join(tooltip_parts)
                cache_text = f"{weather_data}\n{formatted_tooltip}\n"
        else:
            cache_text = f"{weather_data}\n"
        
        # Ensure the cache directory exists.
        os.makedirs(os.path.dirname(WEATHER_CACHE_FILE), exist_ok=True)
        try:
            with open(WEATHER_CACHE_FILE, "w") as f:
                f.write(cache_text)
        except Exception as e:
            print(f"Error writing weather cache: {e}")
    
    def _write_cache(self, weather_data, tooltip_text=None):
        """
        Save weather data to a cache file in a human-readable and pretty format.
        Expected format based on the tooltip:
          Madrid: Partly cloudy +12°C (+11°C)
          Humidity: 71% Wind: ↗14km/h
        """
        if tooltip_text is not None:
            tooltip_parts = [part.strip() for part in tooltip_text.split(",")]
            if len(tooltip_parts) >= 4:
                # Replace the numeric temperature with weather_data that holds the icon
                first_line = f"{tooltip_parts[0]} {weather_data} {tooltip_parts[1].split()[1]}"
                second_line = f"{tooltip_parts[2]} {tooltip_parts[3]}"
                cache_text = f"{first_line}\n{second_line}\n"
            else:
                # Fallback to splitting lines if tooltip format is unexpected
                formatted_tooltip = "\n".join(tooltip_parts)
                cache_text = f"{weather_data}\n{formatted_tooltip}\n"
        else:
            cache_text = f"{weather_data}\n"
        
        # Ensure the cache directory exists.
        os.makedirs(os.path.dirname(WEATHER_CACHE_FILE), exist_ok=True)
        try:
            with open(WEATHER_CACHE_FILE, "w") as f:
                f.write(cache_text)
        except Exception as e:
            print(f"Error writing weather cache: {e}")

    def _fetch_weather_thread(self, user_data):
        location = self.get_location()
        locsafe = urllib.parse.quote(location)
        if not location:
            return self._update_ui(error=True)
        url = (
            f"https://wttr.in/{locsafe}?format=%c+%t"
            if not data.VERTICAL
            else f"https://wttr.in/{locsafe}?format=%c"
        )
        # Get detailed info for tooltip
        tooltip_url = (
            f"https://wttr.in/{locsafe}?format=%l:+%C,+%t+(%f),+Humidity:+%h,+Wind:+%w"
        )

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
                    tooltip_text = None
                    tooltip_response = self.session.get(tooltip_url, timeout=5)
                    if tooltip_response.ok:
                        tooltip_text = tooltip_response.text.strip()
                        GLib.idle_add(self.set_tooltip_text, tooltip_text)
                    GLib.idle_add(self.set_visible, True)
                    # Remove spaces in weather data if needed
                    display_data = weather_data.replace(" ", "")
                    GLib.idle_add(self.label.set_label, display_data)
                    # Save the fetched weather info to cache file
                    self._write_cache(display_data, tooltip_text)
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
            GLib.idle_add(
                self.label.set_markup if error else self.label.set_label, text
            )
            GLib.idle_add(self.set_visible, visible)
