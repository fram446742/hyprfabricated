import os
import shutil
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import urllib.request
import toml
from PIL import Image
from fabric.utils.helpers import get_relative_path
import subprocess
import gi
from fabric.utils.helpers import get_relative_path
from gi.repository import GdkPixbuf


gi.require_version("Gtk", "3.0")

from gi.repository import Gtk  # noqa: E402
from config.data import (
    APP_NAME, APP_NAME_CAP, CONFIG_DIR, HOME_DIR, WALLPAPERS_DIR_DEFAULT,VERTICAL
)
SOURCE_STRING = f"""
# {APP_NAME_CAP}
source = ~/.config/{APP_NAME_CAP}/config/hypr/{APP_NAME}.conf
"""

# Initialize bind_vars with default values
DEFAULTS = {
    'prefix_restart': "SUPER ALT",
    'suffix_restart': "B",
    'prefix_axmsg': "SUPER",
    'suffix_axmsg': "A",
    'prefix_dash': "SUPER",
    'suffix_dash': "D",
    'prefix_bluetooth': "SUPER",
    'suffix_bluetooth': "B",
    'prefix_pins': "SUPER",
    'suffix_pins': "Q",
    'prefix_kanban': "SUPER",
    'suffix_kanban': "N",
    'prefix_launcher': "SUPER",
    'suffix_launcher': "R",
    'prefix_tmux': "SUPER",
    'suffix_tmux': "T",
    'prefix_toolbox': "SUPER",
    'suffix_toolbox': "S",
    'prefix_overview': "SUPER",
    'suffix_overview': "TAB",
    'prefix_wallpapers': "SUPER",
    'suffix_wallpapers': "COMMA",
    'prefix_emoji': "SUPER",
    'suffix_emoji': "PERIOD",
    'prefix_power': "SUPER",
    'suffix_power': "ESCAPE",
    'prefix_toggle': "SUPER CTRL",
    'suffix_toggle': "B",
    'prefix_css': "SUPER SHIFT",
    'suffix_css': "B",
    'wallpapers_dir': WALLPAPERS_DIR_DEFAULT,
    'prefix_restart_inspector': "SUPER CTRL ALT",
    'suffix_restart_inspector': "B",
    'vertical': False,  # New default for vertical layout
    'centered_bar': False,  # New default for centered bar option
    'terminal_command': "kitty -e",  # Default terminal command for tmux
    'dock_enabled': True,  # Default value for dock visibility
    'dock_icon_size': 28,  # Default dock icon size
    "prefix_config": "SUPER",
    "suffix_config": "I"
}

bind_vars = DEFAULTS.copy()


def deep_update(target: dict, update: dict) -> dict:
    """
    Recursively update a nested dictionary with values from another dictionary.
    """
    for key, value in update.items():
        if isinstance(value, dict):
            target[key] = deep_update(target.get(key, {}), value)
        else:
            target[key] = value
    return target


def ensure_matugen_config():
    """
    Ensure that the matugen configuration file exists and is updated
    with the expected settings.
    """
    expected_config = {
        "config": {
            "reload_apps": True,
            "wallpaper": {
                "command": "swww",
                "arguments": [
                    "img",
                    "-t",
                    "outer",
                    "--transition-duration",
                    "1.5",
                    "--transition-step",
                    "255",
                    "--transition-fps",
                    "60",
                    "-f",
                    "Nearest",
                ],
                "set": True,
            },
            "custom_colors": {
                "red": {"color": "#FF0000", "blend": True},
                "green": {"color": "#00FF00", "blend": True},
                "yellow": {"color": "#FFFF00", "blend": True},
                "blue": {"color": "#0000FF", "blend": True},
                "magenta": {"color": "#FF00FF", "blend": True},
                "cyan": {"color": "#00FFFF", "blend": True},
                "white": {"color": "#FFFFFF", "blend": True},
            },
        },
        "templates": {
            "hyprland": {
                "input_path": f"~/.config/{APP_NAME_CAP}/config/matugen/templates/hyprland-colors.conf",
                "output_path": f"~/.config/{APP_NAME_CAP}/config/hypr/colors.conf",
            },
            f"{APP_NAME}": {
                "input_path": f"~/.config/{APP_NAME_CAP}/config/matugen/templates/{APP_NAME}.css",
                "output_path": f"~/.config/{APP_NAME_CAP}/styles/colors.css",
                "post_hook": f"fabric-cli exec {APP_NAME} 'app.set_css()' &",
            },
        },
    }

    config_path = os.path.expanduser("~/.config/matugen/config.toml")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    # Load any existing configuration
    existing_config = {}
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            existing_config = toml.load(f)
        # Backup existing configuration
        shutil.copyfile(config_path, config_path + ".bak")

    # Merge configurations
    merged_config = deep_update(existing_config, expected_config)
    with open(config_path, "w") as f:
        toml.dump(merged_config, f)

    # Expand paths for checking
    current_wall = os.path.expanduser("~/.current.wall")
    hypr_colors = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/config/hypr/colors.conf")
    css_colors = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/styles/colors.css")

    # Check if any of the required files are missing
    if not os.path.exists(current_wall) or not os.path.exists(hypr_colors) or not os.path.exists(css_colors):
        # Ensure the directories exist
        os.makedirs(os.path.dirname(hypr_colors), exist_ok=True)
        os.makedirs(os.path.dirname(css_colors), exist_ok=True)

        # Use the example wallpaper if no current wallpaper
        if not os.path.exists(current_wall):
            image_path = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/assets/wallpapers_example/example-1.jpg")
            # Create symlink to the example wallpaper if it doesn't exist already
            if os.path.exists(image_path) and not os.path.exists(current_wall):
                try:
                    os.symlink(image_path, current_wall)
                except FileExistsError:
                    os.remove(current_wall)
                    os.symlink(image_path, current_wall)
        else:
            # Use the existing wallpaper
            image_path = os.path.realpath(current_wall) if os.path.islink(current_wall) else current_wall

        # Run matugen to generate the color files
        print(f"Generating color theme from wallpaper: {image_path}")
        try:
            subprocess.run(["matugen", "image", image_path], check=True)
            print("Color theme generated successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error generating color theme: {e}")
        except FileNotFoundError:
            print("Error: matugen command not found. Please install matugen.")


def load_bind_vars():
    """
    Load saved key binding variables from JSON, if available.
    """
    config_json = os.path.expanduser(
        f"~/.config/{APP_NAME_CAP}/config/config.json"
    )
    try:
        with open(config_json, "r") as f:
            saved_vars = json.load(f)
            bind_vars.update(saved_vars)
    except FileNotFoundError:
        # Use default values if no saved config exists
        pass


def generate_hyprconf() -> str:
    """
    Generate the Hypr configuration string using the current bind_vars.
    """
    home = os.path.expanduser('~')
    return f"""exec-once = uwsm-app $(python {home}/.config/{APP_NAME_CAP}/main.py)
exec = pgrep -x "hypridle" > /dev/null || uwsm app -- hypridle
exec = uwsm app -- swww-daemon

$fabricSend = fabric-cli exec {APP_NAME}
$axMessage = notify-send "tr1x_em" "What are you doing?" -i f"{home}/.config/{APP_NAME_CAP}/assets/ax.png" -a "Source Code" -A "Be patient. 🍙"

bind = {bind_vars['prefix_restart']}, {bind_vars['suffix_restart']}, exec, killall {APP_NAME}; uwsm-app $(python {home}/.config/{APP_NAME_CAP}/main.py) # Reload {APP_NAME_CAP} | Default: SUPER ALT + B
bind = {bind_vars['prefix_axmsg']}, {bind_vars['suffix_axmsg']}, exec, $axMessage # Message | Default: SUPER + A
bind = {bind_vars['prefix_dash']}, {bind_vars['suffix_dash']}, exec, $fabricSend 'notch.open_notch("dashboard")' # Dashboard | Default: SUPER + D
bind = {bind_vars['prefix_bluetooth']}, {bind_vars['suffix_bluetooth']}, exec, $fabricSend 'notch.open_notch("bluetooth")' # Bluetooth | Default: SUPER + B
bind = {bind_vars['prefix_pins']}, {bind_vars['suffix_pins']}, exec, $fabricSend 'notch.open_notch("pins")' # Pins | Default: SUPER + Q
bind = {bind_vars['prefix_kanban']}, {bind_vars['suffix_kanban']}, exec, $fabricSend 'notch.open_notch("kanban")' # Kanban | Default: SUPER + N
bind = {bind_vars['prefix_launcher']}, {bind_vars['suffix_launcher']}, exec, $fabricSend 'notch.open_notch("launcher")' # App Launcher | Default: SUPER + R
bind = {bind_vars['prefix_tmux']}, {bind_vars['suffix_tmux']}, exec, $fabricSend 'notch.open_notch("tmux")' # App Launcher | Default: SUPER + T
bind = {bind_vars['prefix_toolbox']}, {bind_vars['suffix_toolbox']}, exec, $fabricSend 'notch.open_notch("tools")' # Toolbox | Default: SUPER + S
bind = {bind_vars['prefix_overview']}, {bind_vars['suffix_overview']}, exec, $fabricSend 'notch.open_notch("overview")' # Overview | Default: SUPER + TAB
bind = {bind_vars['prefix_wallpapers']}, {bind_vars['suffix_wallpapers']}, exec, $fabricSend 'notch.open_notch("wallpapers")' # Wallpapers | Default: SUPER + COMMA
bind = {bind_vars['prefix_emoji']}, {bind_vars['suffix_emoji']}, exec, $fabricSend 'notch.open_notch("emoji")' # Emoji | Default: SUPER + PERIOD
bind = {bind_vars['prefix_power']}, {bind_vars['suffix_power']}, exec, $fabricSend 'notch.open_notch("power")' # Power Menu | Default: SUPER + ESCAPE
bind = {bind_vars['prefix_toggle']}, {bind_vars['suffix_toggle']}, exec, $fabricSend 'bar.toggle_hidden()' # Toggle Bar | Default: SUPER CTRL + B
bind = {bind_vars['prefix_toggle']}, {bind_vars['suffix_toggle']}, exec, $fabricSend 'notch.toggle_hidden()' # Toggle Notch | Default: SUPER CTRL + B
bind = {bind_vars['prefix_css']}, {bind_vars['suffix_css']}, exec, $fabricSend 'app.set_css()' # Reload CSS | Default: SUPER SHIFT + B
bind = {bind_vars['prefix_restart_inspector']}, {bind_vars['suffix_restart_inspector']}, exec, killall {APP_NAME}; uwsm-app $(GTK_DEBUG=interactive python {home}/.config/{APP_NAME_CAP}/main.py) # Restart with inspector | Default: SUPER CTRL ALT + B
bind = {bind_vars["prefix_config"]}, {bind_vars["suffix_config"]}, exec,uwsm app -- python {home}/.config/{APP_NAME_CAP}/config/config.py
# Wallpapers directory: {bind_vars["wallpapers_dir"]}

source = {home}/.config/{APP_NAME_CAP}/config/hypr/colors.conf

layerrule = noanim, fabric

exec = cp $wallpaper ~/.current.wall

general {{
    col.active_border = 0xff$primary
    col.inactive_border = 0xff$surface
    gaps_in = 2
    gaps_out = 4
    border_size = 2
    layout = dwindle
}}

cursor {{
  no_warps=true
}}

decoration {{
    blur {{
        enabled = yes
        size = 8
        passes = 3
        new_optimizations = yes
        contrast = 1
        brightness = 1
    }}
    rounding = 14
    shadow {{
      enabled = true
      range = 10
      render_power = 2
      color = rgba(0, 0, 0, 0.25)
    }}
}}

animations {{
    enabled = yes
    bezier = myBezier, 0.4, 0, 0.2, 1
    animation = windows, 1, 2.5, myBezier, popin 80%
    animation = border, 1, 2.5, myBezier
    animation = fade, 1, 2.5, myBezier
    animation = workspaces, 1, 2.5, myBezier, {'slidefadevert' if bind_vars['vertical'] else 'slidefade'} 20%
}}
"""


def ensure_face_icon():
    """
    Ensure the face icon exists. If not, copy the default icon.
    """
    face_icon_path = os.path.expanduser("~/.face.icon")
    default_icon_path = os.path.expanduser(
        f"~/.config/{APP_NAME_CAP}/assets/default.png"
    )
    if not os.path.exists(face_icon_path) and os.path.exists(default_icon_path):
        shutil.copy(default_icon_path, face_icon_path)


def backup_and_replace(src: str, dest: str, config_name: str):
    """
    Backup the existing configuration file and replace it with a new one.
    """
    if os.path.exists(dest):
        backup_path = dest + ".bak"
        shutil.copy(dest, backup_path)
        print(f"{config_name} config backed up to {backup_path}")
    shutil.copy(src, dest)
    print(f"{config_name} config replaced from {src}")


class HyprConfGUI(Gtk.Window):
    def __init__(self, show_lock_checkbox: bool, show_idle_checkbox: bool):
        super().__init__(title="Configure Key Binds")
        self.set_border_width(20)
        self.set_default_size(500, 450)
        self.set_resizable(False)

        self.selected_face_icon = None

        # Create a vertical box to hold the dropdown and the content area
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        # Dropdown menu for selecting config type
        self.config_selector = Gtk.ComboBoxText()
        self.config_selector.append_text("Keybinds Config")
        self.config_selector.append_text("General Config")
        self.config_selector.set_active(0)
        self.config_selector.connect("changed", self.on_config_selected)
        vbox.pack_start(self.config_selector, False, False, 0)

        # Stack to switch between different config views
        self.stack = Gtk.Stack()
        vbox.pack_start(self.stack, True, True, 0)

        # Keybinds Config UI
        self.keybinds_grid = self.create_keybinds_grid(
            show_lock_checkbox, show_idle_checkbox
        )
        self.stack.add_titled(self.keybinds_grid, "keybinds", "Keybinds Config")

        # General Config UI
        self.general_grid = self.create_general_grid()
        self.stack.add_titled(self.general_grid, "general", "General Config")



        # Apply and Close buttons
        button_box = Gtk.Box(spacing=10)
        vbox.pack_start(button_box, False, False, 0)

        apply_btn = Gtk.Button(label="Apply")
        apply_btn.connect("clicked", self.on_apply)
        button_box.pack_start(apply_btn, True, True, 0)

        reset_btn = Gtk.Button(label="Reset to Defaults")
        reset_btn.connect("clicked", self.on_reset)
        button_box.pack_start(reset_btn, True, True, 0)

        close_btn = Gtk.Button(label="Close")
        close_btn.connect("clicked", self.on_close)
        button_box.pack_start(close_btn, True, True, 0)


    def create_keybinds_grid(self, show_lock_checkbox, show_idle_checkbox):
        grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        grid.set_margin_start(10)
        grid.set_margin_end(10)

        # Header label spanning across columns
        header = Gtk.Label(label="Configure Key Bindings")
        header.set_halign(Gtk.Align.CENTER)
        grid.attach(header, 0, 0, 4, 1)

        self.entries = []
        bindings = [
            (f"Reload {APP_NAME_CAP}", 'prefix_restart', 'suffix_restart'),
            ("Message", 'prefix_axmsg', 'suffix_axmsg'),
            ("Dashboard", 'prefix_dash', 'suffix_dash'),
            ("Bluetooth", 'prefix_bluetooth', 'suffix_bluetooth'),
            ("Pins", 'prefix_pins', 'suffix_pins'),
            ("Kanban", 'prefix_kanban', 'suffix_kanban'),
            ("App Launcher", 'prefix_launcher', 'suffix_launcher'),
            ("Tmux", 'prefix_tmux', 'suffix_tmux'),
            ("Toolbox", 'prefix_toolbox', 'suffix_toolbox'),
            ("Overview", 'prefix_overview', 'suffix_overview'),
            ("Wallpapers", 'prefix_wallpapers', 'suffix_wallpapers'),
            ("Emoji Picker", 'prefix_emoji', 'suffix_emoji'),
            ("Power Menu", 'prefix_power', 'suffix_power'),
            ("Toggle Bar and Notch", 'prefix_toggle', 'suffix_toggle'),
            ("Reload CSS", 'prefix_css', 'suffix_css'),
            ("Restart with inspector", 'prefix_restart_inspector', 'suffix_restart_inspector'),
        ]

        # Populate grid with key binding rows, starting at row 1
        row = 1
        for label_text, prefix_key, suffix_key in bindings:
            # Binding description
            binding_label = Gtk.Label(label=label_text)
            binding_label.set_halign(Gtk.Align.START)
            grid.attach(binding_label, 0, row, 1, 1)

            # Prefix entry
            prefix_entry = Gtk.Entry()
            prefix_entry.set_text(bind_vars[prefix_key])
            grid.attach(prefix_entry, 1, row, 1, 1)

            # Plus label between entries
            plus_label = Gtk.Label(label=" + ")
            grid.attach(plus_label, 2, row, 1, 1)

            # Suffix entry
            suffix_entry = Gtk.Entry()
            suffix_entry.set_text(bind_vars[suffix_key])
            grid.attach(suffix_entry, 3, row, 1, 1)

            self.entries.append((prefix_key, suffix_key, prefix_entry, suffix_entry))
            row += 1

        # Row for Wallpapers Directory chooser
        wall_label = Gtk.Label(label="Wallpapers Directory")
        wall_label.set_halign(Gtk.Align.START)
        grid.attach(wall_label, 0, row, 1, 1)
        self.wall_dir_chooser = Gtk.FileChooserButton(
            title="Select a folder", action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        self.wall_dir_chooser.set_filename(bind_vars["wallpapers_dir"])
        grid.attach(self.wall_dir_chooser, 1, row, 3, 1)
        row += 1

        # Row for Profile Icon selection
        face_label = Gtk.Label(label="Profile Icon")
        face_label.set_halign(Gtk.Align.START)
        grid.attach(face_label, 0, row, 1, 1)
        face_btn = Gtk.Button(label="Select Image")
        face_btn.connect("clicked", self.on_select_face_icon)
        grid.attach(face_btn, 1, row, 3, 1)
        row += 1

        # Row for optional checkboxes
        if show_lock_checkbox:
            self.lock_checkbox = Gtk.CheckButton(label="Replace Hyprlock config")
            self.lock_checkbox.set_active(False)
            grid.attach(self.lock_checkbox, 0, row, 2, 1)
        if show_idle_checkbox:
            self.idle_checkbox = Gtk.CheckButton(label="Replace Hypridle config")
            self.idle_checkbox.set_active(False)
            grid.attach(self.idle_checkbox, 2, row, 2, 1)
        row += 1
        return grid

    def create_general_grid(self):
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        grid.set_margin_start(10)
        grid.set_margin_end(10)
        scrolled_window.add(grid)

        self.general_entries = []

        # Load general config from JSON
        config_json = get_relative_path("../config.json")
        with open(config_json, "r") as f:
            self.general_config = json.load(f)

        self.add_config_to_grid(grid, self.general_config, 0)

        return scrolled_window

    def add_config_to_grid(self, grid, config, row, parent_key="", tooltips=None):
        if tooltips is None:
            tooltips = config.get("tooltip", {})

        for key, value in config.items():
            if key == "tooltip":
                continue  # Skip the tooltip section

            full_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, dict):
                section_label = Gtk.Label()
                section_label.set_markup(f"<b>{key.replace("_"," ").upper()}</b>")
                section_label.set_halign(Gtk.Align.START)
                section_label.set_margin_top(10)
                section_label.set_margin_bottom(5)
                grid.attach(section_label, 0, row, 2, 1)
                row += 1
                row = self.add_config_to_grid(grid, value, row, full_key, tooltips)
            else:
                # Check for a tooltip in the tooltips section
                comment = tooltips.get(f"{key}_tooltip", "")

                option_label = Gtk.Label(label=key.replace("_"," ").capitalize())
                option_label.set_halign(Gtk.Align.START)
                if comment:
                    option_label.set_tooltip_text(comment)
                grid.attach(option_label, 0, row, 1, 1)

                if isinstance(value, bool):
                    option_widget = Gtk.Switch()
                    option_widget.set_active(value)
                    option_widget.set_size_request(
                        60, 20
                    )  # Set width request to a smaller value
                else:
                    option_widget = Gtk.Entry()
                    option_widget.set_text(str(value))
                    option_widget.set_width_chars(20)  # Set a fixed width for the entry

                if comment:
                    option_widget.set_tooltip_text(comment)

                # Use a Gtk.Box to contain the widget and control its expansion
                box = Gtk.Box()
                box.pack_start(option_widget, False, False, 0)
                grid.attach(box, 1, row, 1, 1)

                self.general_entries.append((full_key, option_widget))
                row += 1
        return row

    def on_config_selected(self, widget):
        active_text = widget.get_active_text()
        if active_text == "Keybinds Config":
            self.stack.set_visible_child(self.keybinds_grid)
        elif active_text == "General Config":
            self.stack.set_visible_child(self.general_grid)

    def on_apply(self, widget):
        active_text = self.config_selector.get_active_text()
        print(f"Applying configuration for: {active_text}")
        if active_text == "Keybinds Config":
            self.save_keybinds_config()
        elif active_text == "General Config":
            self.save_general_config()

    def save_keybinds_config(self):
        print("Saving keybinds configuration...")
        for prefix_key, suffix_key, prefix_entry, suffix_entry in self.entries:
            bind_vars[prefix_key] = prefix_entry.get_text()
            bind_vars[suffix_key] = suffix_entry.get_text()
            print(
                f"Updated {prefix_key}: {bind_vars[prefix_key]}, {suffix_key}: {bind_vars[suffix_key]}"
            )

        # Update wallpaper directory
        bind_vars["wallpapers_dir"] = self.wall_dir_chooser.get_filename()

        config_json = os.path.expanduser(
            f"~/.config/{APP_NAME_CAP}/config/config.json"
        )
        os.makedirs(os.path.dirname(config_json), exist_ok=True)
        try:
            with open(config_json, "w") as f:
                json.dump(bind_vars, f, indent=4)
            print(f"Keybinds configuration saved to {config_json}")
        except Exception as e:
            print(f"Error saving keybinds configuration: {e}")

        # Update the Hyprland configuration file
        hyprland_config_path = os.path.expanduser("~/.config/hypr/hyprland.conf")
        try:
            with open(hyprland_config_path, "r") as f:
                content = f.read()
            if SOURCE_STRING not in content:
                with open(hyprland_config_path, "a") as f:
                    f.write(SOURCE_STRING)
            print(f"Hyprland configuration updated at {hyprland_config_path}")
        except Exception as e:
            print(f"Error updating Hyprland configuration: {e}")
        start_config()

        try:
            subprocess.Popen(
                f"killall {APP_NAME}; uwsm app -- python {HOME_DIR}/.config/{APP_NAME_CAP}/main.py",
                shell=True,
                start_new_session=True,
            )
            print("Hyprfabricated process restarted.")
        except Exception as e:
            print(f"Error restarting Hyprfabricated process: {e}")

    def save_general_config(self):
        print("Saving general configuration...")
        for full_key, widget in self.general_entries:
            keys = full_key.split(".")
            config_section = self.general_config
            for key in keys[:-1]:
                config_section = config_section[key]
            if isinstance(widget, Gtk.Switch):
                config_section[keys[-1]] = widget.get_active()
            else:
                config_section[keys[-1]] = widget.get_text()
            print(f"Updated {full_key}: {config_section[keys[-1]]}")

        config_json = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/config.json")
        try:
            with open(config_json, "w") as f:
                json.dump(self.general_config, f, indent=4)
            print(f"General configuration saved to {config_json}")
        except Exception as e:
            print(f"Error saving general configuration: {e}")

        try:
            subprocess.Popen(
                f"killall {APP_NAME}; uwsm app -- python {HOME_DIR}/.config/{APP_NAME_CAP}/main.py",
                shell=True,
                start_new_session=True,
            )
            print("Hyprfabricated process restarted.")
        except Exception as e:
            print(f"Error restarting Hyprfabricated process: {e}")

    def on_select_face_icon(self, widget):
        """
        Open a file chooser dialog for selecting a new face icon image.
        """
        dialog = Gtk.FileChooserDialog(
            title="Select Face Icon",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )

        # Filter to allow image files only
        image_filter = Gtk.FileFilter()
        image_filter.set_name("Image files")
        image_filter.add_mime_type("image/png")
        image_filter.add_mime_type("image/jpeg")
        image_filter.add_pattern("*.png")
        image_filter.add_pattern("*.jpg")
        image_filter.add_pattern("*.jpeg")
        dialog.add_filter(image_filter)

        if dialog.run() == Gtk.ResponseType.OK:
            self.selected_face_icon = dialog.get_filename()
            print(f"Face icon selected: {self.selected_face_icon}")
        dialog.destroy()

    def on_accept(self, widget):
        """
        Save the configuration and update the necessary files without closing the window.
        """
        # Update bind_vars from user inputs
        for prefix_key, suffix_key, prefix_entry, suffix_entry in self.entries:
            bind_vars[prefix_key] = prefix_entry.get_text()
            bind_vars[suffix_key] = suffix_entry.get_text()

        # Update wallpaper directory
        bind_vars["wallpapers_dir"] = self.wall_dir_chooser.get_filename()

        # Save the updated bind_vars to a JSON file
        config_json = os.path.expanduser(
            f"~/.config/{APP_NAME_CAP}/config/config.json"
        )
        os.makedirs(os.path.dirname(config_json), exist_ok=True)
        with open(config_json, "w") as f:
            json.dump(bind_vars, f)

        # Process face icon if one was selected
        if self.selected_face_icon:
            try:
                img = Image.open(self.selected_face_icon)
                side = min(img.size)
                left = (img.width - side) / 2
                top = (img.height - side) / 2
                cropped_img = img.crop((left, top, left + side, top + side))
                cropped_img.save(os.path.expanduser("~/.face.icon"), format="PNG")
                print("Face icon saved.")
            except Exception as e:
                print("Error processing face icon:", e)

        # Replace hyprlock config if requested
        if hasattr(self, "lock_checkbox") and self.lock_checkbox.get_active():
            src_lock = os.path.expanduser(
                f"~/.config/{APP_NAME_CAP}/config/hypr/hyprlock.conf"
            )
            dest_lock = os.path.expanduser("~/.config/hypr/hyprlock.conf")
            backup_and_replace(src_lock, dest_lock, "Hyprlock")

        # Replace hypridle config if requested
        if hasattr(self, "idle_checkbox") and self.idle_checkbox.get_active():
            src_idle = os.path.expanduser(
                f"~/.config/{APP_NAME_CAP}/config/hypr/hypridle.conf"
            )
            dest_idle = os.path.expanduser("~/.config/hypr/hypridle.conf")
            backup_and_replace(src_idle, dest_idle, "Hypridle")

        # Append the source string to the Hyprland config if not present
        hyprland_config_path = os.path.expanduser("~/.config/hypr/hyprland.conf")
        with open(hyprland_config_path, "r") as f:
            content = f.read()
        if (SOURCE_STRING not in content):
            with open(hyprland_config_path, "a") as f:
                f.write(SOURCE_STRING)

        # Update configuration
        start_config()

        # First prepare the restart command to be executed in background
        restart_script = f"""#!/bin/bash
killall {APP_NAME} 2>/dev/null
python_output=$(python {os.path.expanduser(f"~/.config/{APP_NAME_CAP}/main.py")})
uwsm-app "$python_output" &
"""

        # Create a temporary script file
        restart_path = "/tmp/hyprfabricated_restart.sh"
        with open(restart_path, "w") as f:
            f.write(restart_script)
        os.chmod(restart_path, 0o755)

        # Start the script in the background
        subprocess.Popen(["/bin/bash", restart_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True)

        # Removed confirmation dialog to make the interface cleaner

        # The window remains open - don't call Gtk.main_quit()

    def on_reset(self, widget):
        """
        Reset all settings to default values.
        """
        # Ask for confirmation
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Reset all settings to defaults?"
        )
        dialog.format_secondary_text("This will reset all keybindings and other settings to their default values.")
        response = dialog.run()
        dialog.destroy()

        FILE_URL = "https://raw.githubusercontent.com/tr1xem/hyprfabricated/refs/heads/main/config.json"
        DESTINATION_FILE = get_relative_path("../config.json")
        TEMP_FILE = "/tmp/temp_config.json"

        if response == Gtk.ResponseType.YES:
            # Reset bind_vars to default values
            try:
                urllib.request.urlretrieve(FILE_URL, TEMP_FILE)
                print("Download successful!")

                if os.path.exists(DESTINATION_FILE):
                    os.remove(DESTINATION_FILE)
                shutil.move(TEMP_FILE, DESTINATION_FILE)

            except Exception as e:
                print(f"Error downloading or replacing the file: {e}")
            global bind_vars
            bind_vars = DEFAULTS.copy()

            # Update UI elements
            # Update key binding entries
            for prefix_key, suffix_key, prefix_entry, suffix_entry in self.entries:
                prefix_entry.set_text(bind_vars[prefix_key])
                suffix_entry.set_text(bind_vars[suffix_key])

            # Update wallpaper directory chooser
            self.wall_dir_chooser.set_filename(bind_vars['wallpapers_dir'])

            # Clear face icon selection status
            self.selected_face_icon = None

    def on_close(self, widget):
        self.destroy()


def start_config():
    """
    Run final configuration steps: ensure necessary configs, write the hyprconf, and reload.
    """
    ensure_matugen_config()
    ensure_face_icon()

    # Write the generated hypr configuration to file
    hypr_config_dir = os.path.expanduser(f"~/.config/{APP_NAME_CAP}/config/hypr/")
    os.makedirs(hypr_config_dir, exist_ok=True)
    hypr_conf_path = os.path.join(hypr_config_dir, f"{APP_NAME}.conf")
    with open(hypr_conf_path, "w") as f:
        f.write(generate_hyprconf())

    # Reload Hyprland configuration using subprocess.run instead of os.system
    subprocess.run(["hyprctl", "reload"])


def open_config():
    """
    Entry point for opening the configuration GUI.
    """
    load_bind_vars()

    # Check and copy hyprlock config if needed
    dest_lock = os.path.expanduser("~/.config/hypr/hyprlock.conf")
    src_lock = os.path.expanduser(
        f"~/.config/{APP_NAME_CAP}/config/hypr/hyprlock.conf"
    )
    os.makedirs(os.path.dirname(dest_lock), exist_ok=True)
    show_lock_checkbox = True
    if not os.path.exists(dest_lock):
        shutil.copy(src_lock, dest_lock)
        show_lock_checkbox = False

    # Check and copy hypridle config if needed
    dest_idle = os.path.expanduser("~/.config/hypr/hypridle.conf")
    src_idle = os.path.expanduser(
        f"~/.config/{APP_NAME_CAP}/config/hypr/hypridle.conf"
    )
    show_idle_checkbox = True
    if not os.path.exists(dest_idle):
        shutil.copy(src_idle, dest_idle)
        show_idle_checkbox = False

    # Create and run the GUI
    window = HyprConfGUI(show_lock_checkbox, show_idle_checkbox)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    open_config()
