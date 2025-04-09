import subprocess
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.utils.helpers import exec_shell_command_async
import config.data as data

import modules.icons as icons


class Systemprofiles(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="systemprofiles",
            orientation="h" if not data.VERTICAL else "v",
            spacing=3,
        )

        # Create three buttons for power modes.
        self.bat_save = Button(
            name="battery-save",
            child=Label(name="battery-save-label", markup=icons.power_saving),
            on_clicked=lambda *_: self.set_power_mode("power-saver"),
        )
        self.bat_balanced = Button(
            name="battery-balanced",
            child=Label(name="battery-balanced-label", markup=icons.power_balanced),
            on_clicked=lambda *_: self.set_power_mode("balanced"),
        )
        self.bat_perf = Button(
            name="battery-performance",
            child=Label(
                name="battery-performance-label", markup=icons.power_performance
            ),
            on_clicked=lambda *_: self.set_power_mode("performance"),
        )

        # Attach mouse enter/leave events to buttons as well

        # Group the mode buttons into a container.
        self.add(
            Box(
                name="power-mode-switcher",
                orientation="h" if not data.VERTICAL else "v",
                spacing=4,
                children=[self.bat_save, self.bat_balanced, self.bat_perf],
            )
        )

        self.get_current_power_mode()
        self.hide_timer = None
        self.hover_counter = 0
        # self.set_power_mode("balanced")

    def get_current_power_mode(self):
        try:
            # Run the command to get the current power mode
            result = subprocess.run(
                ["powerprofilesctl", "get"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )

            # Get the output and strip unnecessary whitespace
            output = result.stdout.strip()

            # Validate the output
            if output in ["power-saver", "balanced", "performance"]:
                self.current_mode = output
            else:
                self.current_mode = "balanced"

            # Update button styles based on the current mode
            self.update_button_styles()

        except subprocess.CalledProcessError as err:
            print(f"Command failed: {err}")
            self.current_mode = "balanced"

        except Exception as err:
            print(f"Error retrieving current power mode: {err}")
            self.current_mode = "balanced"

    def set_power_mode(self, mode):
        pass
        """
        Switches power mode by running the corresponding auto-cpufreq command.
        mode: one of 'powersave', 'balanced', or 'performance'
        """
        commands = {
            "power-saver": "powerprofilesctl set power-saver",
            "balanced": "powerprofilesctl set balanced",
            "performance": "powerprofilesctl set performance",
        }
        if mode in commands:
            try:
                exec_shell_command_async(commands[mode])
                self.current_mode = mode
                self.update_button_styles()
            except Exception as err:
                # Optionally, handle errors or display a notification.
                print(f"Error setting power mode: {err}")

    def update_button_styles(self):
        """
        Optionally updates button styles to reflect the current mode.
        Adjust the styling method based on your toolkit's capabilities.
        """
        if self.current_mode == "power-saver":
            self.bat_save.add_style_class("active")
            self.bat_balanced.remove_style_class("active")
            self.bat_perf.remove_style_class("active")
        elif self.current_mode == "balanced":
            self.bat_save.remove_style_class("active")
            self.bat_balanced.add_style_class("active")
            self.bat_perf.remove_style_class("active")
        elif self.current_mode == "performance":
            self.bat_save.remove_style_class("active")
            self.bat_balanced.remove_style_class("active")
            self.bat_perf.add_style_class("active")
