import psutil
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.label import Label
from fabric.widgets.overlay import Overlay
from fabric.utils import invoke_repeater, exec_shell_command_async
from fabric.widgets.circularprogressbar import CircularProgressBar


import modules.icons as icons

class BatteryBox(Box):
    def __init__(self, **kwargs):
        super().__init__(name="button-bar-vol", **kwargs)

        self.icon_label = Label(
            name="button-bar-label",
            markup = icons.battery
        )

        self.battery_percentage_label = Label(
            name="battery-percentage-label",
            markup = ""
        )
        #self.pack_end(self.battery_percentage_label, True, True, 0)


        self.progress_bar = CircularProgressBar(
            name="button-volume", pie=False, size=30, line_width=3,
        )

        self.overlay = Overlay()
        self.overlay.add_overlay(self.icon_label)
        self.overlay.add(self.progress_bar)
        self.pack_end(self.overlay, True, True, 0)

        self.battery_lowest_percentage = 4
        invoke_repeater(500, self.update_label)

    def update_label(self):
        battery = psutil.sensors_battery()
        percentage = int(battery.percent)
        plugged = battery.power_plugged
        secsleft = battery.secsleft
        self.progress_bar.value = percentage / 100



        if plugged or plugged is None:
            self.icon_label.set_markup(icons.battery_charging)
            self.battery_percentage_label.set_markup(f"{percentage}%")

        else:
            if percentage > 75:
                self.icon_label.set_markup(icons.battery_100)
            elif percentage > 50:
                self.icon_label.set_markup(icons.battery_75)
            elif percentage > 25:
                self.icon_label.set_markup(icons.battery_50)
            else:
                self.icon_label.set_markup(icons.battery_25)
            self.battery_percentage_label.set_markup(f"{percentage}%")

            if percentage <= 10:
                percentage -= self.battery_lowest_percentage - 1
                self.notify(percentage, secsleft)

        return True
    
    def notify(self, percentage, secsleft):
        exec_shell_command_async(f"notify-send '{percentage}% útil' '{secsleft} segundos restantes' -u critical -a 'Batería crítica'")
  
class VitalsBox(Box):
    def __init__(self, **kwargs):
        super().__init__(name="button-bar", **kwargs)

        self.cpu_label = Label(
            name="battery-icon-label",
            markup = icons.cpu
        )

        self.cpu = psutil.cpu_percent()
        #self.pack_end(self.cpu_label, True, True, 0)
        self.set_size_request(40, 20)

        self.circular_progress_bar = AnimatedCircularProgressBar(min_value=0, max_value=100)
        self.circular_progress_bar.animate_value(self.cpu)
        self.pack_end(self.circular_progress_bar, True, True, 0)
        invoke_repeater(500, self.update_label)

    def update_label(self):
        self.circular_progress_bar.animate_value(2.04)
        return True
