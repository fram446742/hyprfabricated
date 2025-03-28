import json
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.datetime import DateTime
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.button import Button
from fabric.widgets.revealer import Revealer
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.hyprland.widgets import Workspaces, WorkspaceButton, Language, get_hyprland_connection
from fabric.hyprland.service import HyprlandEvent
from fabric.utils.helpers import get_relative_path, exec_shell_command_async
import gi
gi.require_version('Gtk', '3.0')
import os
from gi.repository import Gdk
from modules.systemtray import SystemTray
import modules.icons as icons
import config.data as data
from modules.metrics import MetricsSmall, Battery, NetworkApplet
from modules.controls import ControlSmall
from modules.weather import Weather
from modules.systemprofiles import Systemprofiles


class Bar(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="bar",
            layer="top",
            anchor="left top right" if not data.VERTICAL else "top left bottom",
            margin="-4px -4px -8px -4px" if not data.VERTICAL else "-4px -8px -4px -4px",
            exclusivity="auto",
            visible=True,
            all_visible=True,
        )

        self.notch = kwargs.get("notch", None)
        config_path = get_relative_path("../config.json")
        with open(config_path) as config_file:
            config = json.load(config_file)

        self.workspaces = Workspaces(
            name="workspaces",
            invert_scroll=True,
            empty_scroll=True,
            v_align="fill",
            orientation="h" if not data.VERTICAL else "v",
            spacing=8,
            buttons=[WorkspaceButton(id=i, label="") for i in range(1, 11)],
        )

        self.ws_container = Box(
            name="workspaces-container",
            children=self.workspaces,
        )

        self.button_tools = Button(
            name="button-bar",
            on_clicked=lambda *_: self.tools_menu(),
            child=Label(
                name="button-bar-label",
                markup=icons.toolbox
            )
        )

        self.connection = get_hyprland_connection()



        left_children = []
        self.lang_label = Label(name="lang-label")
        self.language = Button(name="language", h_align="center", v_align="center", child=self.lang_label)
        self.switch_on_start()
        self.connection.connect("event::activelayout", self.on_language_switch)
        # self.date_time = DateTime(name="date-time", formatters=["%I:%M%P"] if not data.VERTICAL else ["%I\n%M"], h_align="center" if not data.VERTICAL else "fill", v_align="center", h_expand=True, v_expand=True) # 12-hour format
        self.date_time = DateTime(name="date-time", formatters=["%H:%M %P"] if not data.VERTICAL else ["%H\n%M"], h_align="center" if not data.VERTICAL else "fill", v_align="center", h_expand=True, v_expand=True) # 24-hour format

        self.button_overview = Button(
            name="button-bar",
            on_clicked=lambda *_: self.overview(),
            child=Label(name="button-bar-label", markup=icons.windows),
        )
        self.button_overview.connect("enter_notify_event", self.on_button_enter)
        self.button_overview.connect("leave_notify_event", self.on_button_leave)
        if config["Bar"]["buttonapps"]:
            self.button_apps = Button(
                name="button-bar",
                on_clicked=lambda *_: self.search_apps(),
                child=Label(name="button-bar-label", markup=icons.apps),
            )
            self.button_apps.connect("enter_notify_event", self.on_button_enter)
            self.button_apps.connect("leave_notify_event", self.on_button_leave)
            left_children.append(self.button_apps)


        if config["Bar"]["workspaces"]:
            left_children.append(
               self.ws_container
            )

        start_children = []

        if config["Bar"]["Barleft"]["weather"]:
            self.weather = Weather()
            start_children.append(self.weather)

        if config["Bar"]["Barleft"]["overview"]:
            start_children.append(self.button_overview)

        if config["Bar"]["Barleft"]["networkapplet"]:
            self.network = NetworkApplet()
            start_children.append(self.network)

        self.revealer_left = Revealer(
            name="bar-revealer",
            transition_type="slide-right",
            child_revealed=True,
            child=Box(
                name="bar-revealer-box",
                orientation="h",
                spacing=4,
                children=start_children if not data.VERTICAL else None,
            ),
        )


        self.boxed_revealer_left = Box(
            name="boxed-revealer",
            children=[
                self.revealer_left,
            ],
        )

        end_children = []

        self.control = ControlSmall()

        if config["Bar"]["Barright"]["metrics"]:
            self.metrics = MetricsSmall()
            end_children.append(self.metrics)
        if config["Bar"]["Barright"]["controls"]:
            end_children.append(self.control)
        if config["Bar"]["Barright"]["battery"]:
            self.battery = Battery()
            end_children.append(self.battery)
        if config["Bar"]["Barright"]["systemprofiles"]:
            self.powerctl = Systemprofiles()
            end_children.append(self.powerctl)
        if config["Bar"]["systray"]:
            self.systray = SystemTray()
            end_children.append(self.systray)

        self.revealer_right = Revealer(
            name="bar-revealer",
            transition_type="slide-left",
            child_revealed=True,
            child=Box(
                name="bar-revealer-box",
                orientation="h",
                spacing=4,
                children=end_children if not data.VERTICAL else None,
            ),
        )

        self.boxed_revealer_right = Box(
            name="boxed-revealer",
            children=[
                self.revealer_right,
            ],
        )

        end_children = [self.boxed_revealer_right]

        self.button_tools = Button(
            name="button-bar",
            tooltip_text="Opens Toolbox",
            on_clicked=lambda *_: self.tools_menu(),
            child=Label(name="button-bar-label", markup=icons.toolbox),
        )
        self.button_tools.connect("enter_notify_event", self.on_button_enter)
        self.button_tools.connect("leave_notify_event", self.on_button_leave)
        if config["Bar"]["buttontools"]:
            end_children.append(self.button_tools)

        if config["Bar"]["Barright"]["languageindicator"]:
            end_children.append(self.language)
        if config["Bar"]["buttonapps"]:
            end_children.append(self.date_time)

        self.button_power = Button(
            name="button-bar",
            on_clicked=lambda *_: self.power_menu(),
            child=Label(name="button-bar-label", markup=icons.shutdown),
        )
        self.button_power.connect("enter_notify_event", self.on_button_enter)
        self.button_power.connect("leave_notify_event", self.on_button_leave)
        if config["Bar"]["buttonpower"]:
            end_children.append(self.button_power)

        if data.VERTICAL:
            self.weather = Weather()
            self.systray = SystemTray()
            self.button_apps = Button(
                name="button-bar",
                on_clicked=lambda *_: self.search_apps(),
                child=Label(name="button-bar-label", markup=icons.apps),
            )
            self.button_apps.connect("enter_notify_event", self.on_button_enter)
            self.button_apps.connect("leave_notify_event", self.on_button_leave)
            self.network = NetworkApplet()
            self.battery = Battery()
            self.metrics = MetricsSmall()
            self.v_start_children = [
                self.button_apps,
                self.systray,
                self.control,
                self.button_tools,
            ]

            self.minmal_children = [
                self.button_apps,
                self.button_overview,
                self.ws_container,
                self.weather,
                self.button_power,
            ]
            self.v_center_children = [
                self.button_overview,
                self.ws_container,
                self.weather,
            ]
            self.v_end_children = [
                self.battery,
                self.metrics,
                self.language,
                self.date_time,
                self.button_power,
            ]

            self.v_all_children = []
            self.v_all_children.extend(self.v_start_children)
            self.v_all_children.extend(self.v_center_children)
            self.v_all_children.extend(self.v_end_children)

        # Use centered layout when both vertical and centered_bar are enabled
        is_centered_bar = data.VERTICAL and getattr(data, 'CENTERED_BAR', False)
        self.bar_inner = CenterBox(
            name="bar-inner",
            orientation="h" if not data.VERTICAL else "v",
            h_align="fill",
            v_align="fill",
            start_children=None if is_centered_bar else Box(
                name="start-container",
                spacing=4,
                orientation="h" if not data.VERTICAL else "v",
                children=left_children + [self.boxed_revealer_left] if not data.VERTICAL else self.v_start_children,
            ),
            center_children=Box(
                orientation="h" if not data.VERTICAL else "v",
                spacing=4,
                children=self.v_center_children if not is_centered_bar else self.minmal_children,
            ) if data.VERTICAL else None,
            end_children=None if is_centered_bar else Box(
                name="end-container",
                spacing=4,
                orientation="h" if not data.VERTICAL else "v",
                children=end_children if not data.VERTICAL else self.v_end_children,
            ),
        )

        self.children = self.bar_inner

        self.hidden = False

        self.show_all()
        if config["Bar"]["systray"]:
            self.systray._update_visibility()


    def on_button_enter(self, widget, event):
        window = widget.get_window()
        if window:
            window.set_cursor(Gdk.Cursor(Gdk.CursorType.HAND2))

    def on_button_leave(self, widget, event):
        window = widget.get_window()
        if window:
            window.set_cursor(None)

    def on_button_clicked(self, *args):
        exec_shell_command_async("notify-send 'Botón presionado' '¡Funciona!'")

    def search_apps(self):
        self.notch.open_notch("launcher")

    def overview(self):
        self.notch.open_notch("overview")

    def power_menu(self):
        self.notch.open_notch("power")

    def tools_menu(self):
        self.notch.open_notch("tools")

    def on_language_switch(self, _, event: HyprlandEvent):
        self.language.set_tooltip_text(Language().get_label())
        if not data.VERTICAL:
            self.lang_label.set_label(Language().get_label()[0:3].upper())
        else:
            self.lang_label.add_style_class("icon")
            self.lang_label.set_markup(icons.keyboard)

    def switch_on_start(self):
        self.language.set_tooltip_text(Language().get_label())
        if not data.VERTICAL:
            self.lang_label.set_label(Language().get_label()[0:3].upper())
        else:
            self.lang_label.add_style_class("icon")
            self.lang_label.set_markup(icons.keyboard)

    def toggle_hidden(self):
        self.hidden = not self.hidden
        if self.hidden:
            self.bar_inner.add_style_class("hidden")
        else:
            self.bar_inner.remove_style_class("hidden")
