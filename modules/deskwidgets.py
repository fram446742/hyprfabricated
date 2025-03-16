import psutil
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.overlay import Overlay
from fabric.widgets.datetime import DateTime
from fabric.widgets.circularprogressbar import CircularProgressBar
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.utils import invoke_repeater, get_relative_path
import requests
import urllib.parse
import datetime
import json
from gi.repository import GLib
from concurrent.futures import ThreadPoolExecutor
import time

executor = ThreadPoolExecutor(max_workers=4)

CONFIG_CACHE = None


def load_config():
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


def get_location():
    """Fetch location from config file or IP API asynchronously."""
    config = load_config()
    if city := config.get("city"):
        return city
    for attempt in range(5):
        try:
            response = requests.get("https://ipinfo.io/json", timeout=3)
            if response.status_code == 200:
                return response.json().get("city", "").replace(" ", "")
        except requests.RequestException as e:
            print(f"Error getting location: {e}")
            if attempt < 4:
                time.sleep(10)
            else:
                return ""


def get_location_async(callback):
    """Fetch location asynchronously to prevent UI freeze."""
    executor.submit(lambda: GLib.idle_add(callback, get_location()))


def get_weather(callback):
    """Fetch weather data asynchronously and update UI."""

    def fetch_weather():
        location = get_location()
        if not location:
            return GLib.idle_add(callback, None)

        encoded_location = urllib.parse.quote(location)
        url = f"https://wttr.in/{encoded_location}?format=j1"
        urlemoji = f"https://wttr.in/{encoded_location}?format=%c"

        for attempt in range(5):
            try:
                response = requests.get(urlemoji, timeout=3)
                responseinfo = requests.get(url, timeout=3).json()

                if response.status_code == 200:
                    config = load_config()
                    temp_unit = config.get("Temprature_Unit", "C")
                    temp = (
                        responseinfo["current_condition"][0][f"temp_{temp_unit}"] + "°"
                    )
                    feels_like = (
                        responseinfo["current_condition"][0][f"FeelsLike{temp_unit}"]
                        + "°"
                    )
                    condition = responseinfo["current_condition"][0]["weatherDesc"][0][
                        "value"
                    ]
                    location = responseinfo["nearest_area"][0]["areaName"][0]["value"]
                    emoji = response.text.strip()
                    update_time = datetime.datetime.now().strftime("%I:%M:%S %p")

                    GLib.idle_add(
                        callback,
                        [emoji, temp, condition, feels_like, location, update_time],
                    )
                    return
            except requests.RequestException as e:
                print(f"Error fetching weather (attempt {attempt + 1}): {e}")
                if attempt < 4:
                    time.sleep(10)
                else:
                    GLib.idle_add(callback, None)
                    return

    executor.submit(fetch_weather)


def update_weather(widget):
    def fetch_and_update():
        get_weather(lambda weather_info: update_widget(widget, weather_info))
        return True

    GLib.timeout_add_seconds(600, fetch_and_update)
    fetch_and_update()


def update_widget(widget, weather_info):
    if weather_info:
        widget.weatherinfo = weather_info
        widget.update_labels(weather_info)


class Sysinfo(Box):
    @staticmethod
    def bake_progress_bar(name: str = "progress-bar", size: int = 45, **kwargs):
        return CircularProgressBar(
            name=name,
            start_angle=180,
            end_angle=540,
            min_value=0,
            max_value=100,
            size=size,
            **kwargs,
        )

    @staticmethod
    def bake_progress_icon(**kwargs):
        return Label(**kwargs).build().add_style_class("progress-icon").unwrap()

    def __init__(self, **kwargs):
        super().__init__(
            layer="bottom",
            title="sysinfo",
            name="sysinfo",
            visible=False,
            all_visible=False,
            **kwargs,
        )

        self.cpu_progress = self.bake_progress_bar()
        self.ram_progress = self.bake_progress_bar()
        self.bat_circular = self.bake_progress_bar().build().set_value(42).unwrap()

        self.progress_container = Box(
            name="progress-bar-container",
            spacing=12,
            children=[
                Box(
                    children=[
                        Overlay(
                            child=self.cpu_progress,
                            tooltip_text="",
                            overlays=[
                                self.bake_progress_icon(
                                    label="",
                                    name="progress-icon-cpu",
                                )
                            ],
                        ),
                    ],
                ),
                Box(
                    children=[
                        Overlay(
                            child=self.ram_progress,
                            tooltip_text="",
                            overlays=[
                                self.bake_progress_icon(
                                    name="progress-icon-ram",
                                    label="󰘚",
                                )
                            ],
                        )
                    ]
                ),
                Box(
                    children=[
                        Overlay(
                            child=self.bat_circular,
                            tooltip_text="",
                            overlays=[
                                self.bake_progress_icon(
                                    label="󱊣",
                                    name="progress-icon-bat",
                                )
                            ],
                        ),
                    ],
                ),
            ],
        )

        self.update_status()
        invoke_repeater(1000, self.update_status)

        self.add(
            Box(
                name="progress-bar-container-main",
                orientation="v",
                spacing=24,
                children=[self.progress_container],
            ),
        )
        self.show_all()

    def update_status(self):
        """Update system info asynchronously to prevent UI lag."""

        def update():
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            battery = (
                psutil.sensors_battery().percent if psutil.sensors_battery() else 80
            )
            GLib.idle_add(self.cpu_progress.set_value, cpu)
            GLib.idle_add(self.ram_progress.set_value, ram)
            GLib.idle_add(self.bat_circular.set_value, battery)

            GLib.idle_add(self.cpu_progress.set_tooltip_text, f"{str(round(cpu))}%")
            GLib.idle_add(self.ram_progress.set_tooltip_text, f"{str(round(ram))}%")
            GLib.idle_add(self.bat_circular.set_tooltip_text, f"{str(round(battery))}%")

        executor.submit(update)
        return True


class weather(Box):
    def __init__(self, **kwargs):
        super().__init__(
            layer="bottom",
            name="weather-widget",
            anchor="center",
            h_align="center",
            v_align="center",
            h_expand=True,
            visible=False,
            v_expand=True,
            **kwargs,
        )
        self.weatherinfo = None
        self.header = Box(
            name="header1",
            orientation="h",
            h_expand=True,
            children=[
                Box(
                    orientation="v",
                    children=[
                        Label(label="", h_align="start", name="headertxt1"),
                        Label(label="", h_align="start", name="headertxt3"),
                        Label(label="", h_align="start", name="headertxt2"),
                    ],
                ),
            ],
        )
        self.temp = Box(
            name="header2",
            orientation="h",
            h_align="center",
            children=[
                Box(
                    orientation="v",
                    children=[
                        Label(label="", name="temptxt"),
                        Label(label="", name="temptxtbt"),
                    ],
                ),
            ],
        )
        self.header_right = Box(
            name="header3",
            orientation="h",
            children=[
                Box(
                    orientation="v",
                    children=[
                        Label(label="", name="headertxt"),
                    ],
                ),
            ],
        )
        self.add(
            Box(
                name="window-inner",
                orientation="h",
                h_align="center",
                v_align="center",
                children=[self.header, self.temp, self.header_right],
            ),
        )
        self.set_visible(False)
        update_weather(self)

    def update_labels(self, weather_info):
        if not self.weatherinfo:
            return

        # Unpack weather info into variables for better readability
        emoji, temp, condition, feels_like, location, update_time = self.weatherinfo

        # Store references to deeply nested children to avoid repeated lookups
        header_left = self.header.children[0].children
        temp_labels = self.temp.children[0].children
        header_right = self.header_right.children[0].children

        # Update labels efficiently
        self.set_visible(True)
        header_left[0].set_label(location)
        header_left[1].set_label(f"Updated {update_time}")
        header_left[2].set_label(condition)
        temp_labels[0].set_label(temp)
        temp_labels[1].set_label(f"Feels like {feels_like}")
        header_right[0].set_label(emoji)


def fetch_quote(callback):
    """Fetch quotes asynchronously."""

    def fetch():
        config = load_config()
        quotes_type = config.get("quotetype", "zen")

        url = (
            "https://stoic-quotes.com/api/quote"
            if quotes_type == "stoic"
            else "https://zenquotes.io/api/random"
        )

        for attempt in range(5):
            try:
                response = requests.get(url, timeout=3)
                response.raise_for_status()
                data = response.json()
                quote = (
                    f"{data[0]['q']} - {data[0]['a']}"
                    if quotes_type == "zen"
                    else f"{data['text']} - {data['author']}"
                )
            except requests.RequestException as e:
                print(f"Error fetching quote: {e}")
                if attempt < 4:
                    time.sleep(10)
                else:
                    quote = (
                        "I learn from the mistakes of people who take my advice - Trix"
                    )

        GLib.idle_add(callback, quote)

    executor.submit(fetch)


def fetch_quote_async(callback):
    GLib.idle_add(lambda: fetch_quote(callback))


class qoute(Label):
    def __init__(self, **kwargs):
        super().__init__(
            name="quote",
            label="",
            anchor="center",
            h_align="center",
            v_align="center",
            h_expand=True,
            justification="center",
            v_expand=True,
            visible=False,
        )
        fetch_quote_async(self.update_label)

    def update_label(self, quote):
        """Update quote asynchronously."""
        max_width = 150  # Set the maximum width for the quote
        if len(quote) > max_width:
            words = quote.split()
            line1, line2 = "", ""
            for word in words:
                if len(line1) + len(word) + 1 <= max_width:
                    line1 += word + " "
                else:
                    line2 += word + " "
            quote = line1.strip() + "\n" + line2.strip()
        self.set_label(quote)
        self.set_visible(True)


def create_widgets(config, widget_type):
    widgets = []
    if widget_type == "full":
        if config.get("desktopwidgets", {}).get("date", False):
            widgets.append(
                DateTime(formatters=["%A, %d %B"], interval=10000, name="date")
            )
        if config.get("desktopwidgets", {}).get("clock", False):
            widgets.append(DateTime(formatters=["%I:%M"], name="clock"))
        if config.get("desktopwidgets", {}).get("quote", False):
            widgets.append(qoute())
        if config.get("desktopwidgets", {}).get("weather", False):
            widgets.append(weather())
    elif widget_type == "basic":
        if config.get("desktopwidgets", {}).get("date", False):
            widgets.append(
                DateTime(formatters=["%A. %d %B"], interval=10000, name="date")
            )
        if config.get("desktopwidgets", {}).get("clock", False):
            widgets.append(DateTime(formatters=["%I:%M"], name="clock"))
    return widgets


class Deskwidgetsfull(Window):
    def __init__(self, **kwargs):
        config = load_config()
        super().__init__(
            name="desktop",
            layer="bottom",
            exclusivity="none",
            child=Box(
                orientation="v",
                v_expand=True,
                v_align="center",
                h_align="center",
                children=create_widgets(config, "full"),
            ),
            all_visible=False,
            **kwargs,
        )
        if config.get("desktopwidgets", {}).get("systeminfo", False):
            sys_widget = Window(
                layer="bottom",
                anchor="bottom center",
                exclusivity="none",
                child=Box(
                    orientation="v",
                    children=[
                        Sysinfo(),
                    ],
                ),
                all_visible=False,
            )
        else:
            sys_widget = None


class Deskwidgetsbasic(Window):
    def __init__(self, **kwargs):
        config = load_config()
        super().__init__(name="desktop", **kwargs)
        desktop_widget = Window(
            layer="bottom",
            anchor="bottom left",
            exclusivity="none",
            child=Box(
                orientation="v",
                children=create_widgets(config, "basic"),
            ),
            all_visible=True,
        )
        if config.get("desktopwidgets", {}).get("systeminfo", False):
            sys_widget = Window(
                layer="bottom",
                anchor="bottom center",
                exclusivity="none",
                child=Box(
                    orientation="v",
                    children=[
                        Sysinfo(),
                    ],
                ),
                all_visible=False,
            )
        else:
            sys_widget = None
