from gi.repository import GLib, Gdk

from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.circularprogressbar import CircularProgressBar
from fabric.widgets.eventbox import EventBox
from fabric.widgets.label import Label
from fabric.widgets.overlay import Overlay

import modules.icons as icons
import config.data as data

from fabric.audio.service import Audio
from fabric.widgets.scale import Scale
from services.brightness import Brightness

class VolumeSlider(Scale):
    def __init__(self, **kwargs):
        super().__init__(
            name="control-slider",
            orientation="h",
            h_expand=True,
            h_align="fill",
            has_origin=True,
            increments=(0.01, 0.1),
            **kwargs,
        )
        self.audio = Audio()
        self.audio.connect("notify::speaker", self.on_new_speaker)
        if self.audio.speaker:
            self.audio.speaker.connect("changed", self.on_speaker_changed)
        self.connect("value-changed", self.on_value_changed)
        self.add_style_class("vol")
        self.on_speaker_changed()

    def on_new_speaker(self, *args):
        if self.audio.speaker:
            self.audio.speaker.connect("changed", self.on_speaker_changed)
            self.on_speaker_changed()

    def on_value_changed(self, _):
        if self.audio.speaker:
            self.audio.speaker.volume = self.value * 100

    def on_speaker_changed(self, *_):
        if not self.audio.speaker:
            return
        self.value = self.audio.speaker.volume / 100
        
        # Apply muted class when speaker is muted
        if self.audio.speaker.muted:
            self.add_style_class("muted")
        else:
            self.remove_style_class("muted")

class MicSlider(Scale):
    def __init__(self, **kwargs):
        super().__init__(
            name="control-slider",
            orientation="h",
            h_expand=True,
            has_origin=True,
            increments=(0.01, 0.1),
            **kwargs,
        )
        self.audio = Audio()
        self.audio.connect("notify::microphone", self.on_new_microphone)
        if self.audio.microphone:
            self.audio.microphone.connect("changed", self.on_microphone_changed)
        self.connect("value-changed", self.on_value_changed)
        self.add_style_class("mic")
        self.on_microphone_changed()

    def on_new_microphone(self, *args):
        if self.audio.microphone:
            self.audio.microphone.connect("changed", self.on_microphone_changed)
            self.on_microphone_changed()

    def on_value_changed(self, _):
        if self.audio.microphone:
            self.audio.microphone.volume = self.value * 100

    def on_microphone_changed(self, *_):
        if not self.audio.microphone:
            return
        self.value = self.audio.microphone.volume / 100
        
        # Apply muted class when microphone is muted
        if self.audio.microphone.muted:
            self.add_style_class("muted")
        else:
            self.remove_style_class("muted")

class BrightnessSlider(Scale):
    def __init__(self, **kwargs):
        super().__init__(
            name="control-slider",
            orientation="h",
            h_expand=True,
            has_origin=True,
            increments=(5, 10),
            **kwargs,
        )
        self.client = Brightness.get_initial()
        if self.client.screen_brightness == -1:
            self.destroy()
            return

        self.set_range(0, self.client.max_screen)
        self.set_value(self.client.screen_brightness)
        self.add_style_class("brightness")

        self._pending_value = None
        self._update_source_id = None
        self._updating_from_brightness = False

        self.connect("change-value", self.on_scale_move)
        self.connect("scroll-event", self.on_scroll)
        self.client.connect("screen", self.on_brightness_changed)

    def on_scale_move(self, widget, scroll, moved_pos):
        if self._updating_from_brightness:
            return False
        self._pending_value = moved_pos
        if self._update_source_id is None:
            self._update_source_id = GLib.idle_add(self._update_brightness_callback)
        return False

    def _update_brightness_callback(self):
        if self._pending_value is not None:
            value_to_set = self._pending_value
            self._pending_value = None
            if value_to_set != self.client.screen_brightness:
                self.client.screen_brightness = value_to_set
            return True
        else:
            self._update_source_id = None
            return False

    def on_scroll(self, widget, event):
        current_value = self.get_value()
        step_size = 1
        if event.direction == Gdk.ScrollDirection.SMOOTH:
            if event.delta_y < 0:
                new_value = min(current_value + step_size, self.client.max_screen)
            elif event.delta_y > 0:
                new_value = max(current_value - step_size, 0)
            else:
                return False
        else:
            if event.direction == Gdk.ScrollDirection.UP:
                new_value = min(current_value + step_size, self.client.max_screen)
            elif event.direction == Gdk.ScrollDirection.DOWN:
                new_value = max(current_value - step_size, 0)
            else:
                return False
        self.set_value(new_value)
        return True

    def on_brightness_changed(self, client, _):
        self._updating_from_brightness = True
        self.set_value(self.client.screen_brightness)
        self._updating_from_brightness = False
        percentage = int((self.client.screen_brightness / self.client.max_screen) * 100)
        self.set_tooltip_text(f"{percentage}%")

    def destroy(self):
        if self._update_source_id is not None:
            GLib.source_remove(self._update_source_id)
        super().destroy()


class BrightnessSmall(Box):
    def __init__(self, **kwargs):
        super().__init__(name="button-bar-brightness", **kwargs)
        self.brightness = Brightness.get_initial()
        if self.brightness.screen_brightness == -1:
            self.destroy()
            return

        self.progress_bar = CircularProgressBar(
            name="button-brightness", size=28, line_width=2,
            start_angle=150, end_angle=390,
        )
        self.brightness_label = Label(name="brightness-label", markup=icons.brightness_high)
        self.brightness_button = Button(child=self.brightness_label)
        self.event_box = EventBox(
            events=["scroll", "smooth-scroll"],
            child=Overlay(
                child=self.progress_bar,
                overlays=self.brightness_button
            ),
        )
        self.event_box.connect("scroll-event", self.on_scroll)
        self.add(self.event_box)
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)

        self._updating_from_brightness = False
        self._pending_value = None
        self._update_source_id = None

        self.progress_bar.connect("notify::value", self.on_progress_value_changed)
        self.brightness.connect("screen", self.on_brightness_changed)
        self.on_brightness_changed()

    def on_scroll(self, widget, event):
        if self.brightness.max_screen == -1:
            return

        step_size = 5
        current_norm = self.progress_bar.value
        if event.delta_y < 0:
            new_norm = min(current_norm + (step_size / self.brightness.max_screen), 1)
        elif event.delta_y > 0:
            new_norm = max(current_norm - (step_size / self.brightness.max_screen), 0)
        else:
            return
        self.progress_bar.value = new_norm

    def on_progress_value_changed(self, widget, pspec):
        if self._updating_from_brightness:
            return
        new_norm = widget.value
        new_brightness = int(new_norm * self.brightness.max_screen)
        self._pending_value = new_brightness
        if self._update_source_id is None:
            self._update_source_id = GLib.timeout_add(50, self._update_brightness_callback)

    def _update_brightness_callback(self):
        if self._pending_value is not None and self._pending_value != self.brightness.screen_brightness:
            self.brightness.screen_brightness = self._pending_value
            self._pending_value = None
            return True
        else:
            self._update_source_id = None
            return False

    def on_brightness_changed(self, *args):
        if self.brightness.max_screen == -1:
            return
        normalized = self.brightness.screen_brightness / self.brightness.max_screen
        self._updating_from_brightness = True
        self.progress_bar.value = normalized
        self._updating_from_brightness = False

        brightness_percentage = int(normalized * 100)
        if brightness_percentage >= 75:
            self.brightness_label.set_markup(icons.brightness_high)
        elif brightness_percentage >= 24:
            self.brightness_label.set_markup(icons.brightness_medium)
        else:
            self.brightness_label.set_markup(icons.brightness_low)
        self.set_tooltip_text(f"{brightness_percentage}%")

    def destroy(self):
        if self._update_source_id is not None:
            GLib.source_remove(self._update_source_id)
        super().destroy()

class VolumeSmall(Box):
    def __init__(self, **kwargs):
        super().__init__(name="button-bar-vol", **kwargs)
        self.audio = Audio()
        self.progress_bar = CircularProgressBar(
            name="button-volume", size=28, line_width=2,
            start_angle=150, end_angle=390,
        )
        self.vol_label = Label(name="vol-label", markup=icons.vol_high)
        self.vol_button = Button(on_clicked=self.toggle_mute, child=self.vol_label)
        self.event_box = EventBox(
            events=["scroll", "smooth-scroll"],
            child=Overlay(child=self.progress_bar, overlays=self.vol_button),
        )
        self.audio.connect("notify::speaker", self.on_new_speaker)
        if self.audio.speaker:
            self.audio.speaker.connect("changed", self.on_speaker_changed)
        self.event_box.connect("scroll-event", self.on_scroll)
        self.add(self.event_box)
        self.on_speaker_changed()
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)

    def on_new_speaker(self, *args):
        if self.audio.speaker:
            self.audio.speaker.connect("changed", self.on_speaker_changed)
            self.on_speaker_changed()

    def toggle_mute(self, event):
        current_stream = self.audio.speaker
        if current_stream:
            current_stream.muted = not current_stream.muted
            if current_stream.muted:
                self.vol_button.get_child().set_markup(icons.vol_off)
                self.progress_bar.add_style_class("muted")
                self.vol_label.add_style_class("muted")
            else:
                self.on_speaker_changed()
                self.progress_bar.remove_style_class("muted")
                self.vol_label.remove_style_class("muted")

    def on_scroll(self, _, event):
        if not self.audio.speaker:
            return
        if event.direction == Gdk.ScrollDirection.SMOOTH:
            if abs(event.delta_y) > 0:
                self.audio.speaker.volume -= event.delta_y
            if abs(event.delta_x) > 0:
                self.audio.speaker.volume += event.delta_x

    def on_speaker_changed(self, *_):
        if not self.audio.speaker:
            return

        self.progress_bar.value = self.audio.speaker.volume / 100
        vol_high_icon = icons.vol_high
        vol_medium_icon = icons.vol_medium
        vol_mute_icon = icons.vol_mute
        vol_off_icon = icons.vol_off

        if "bluetooth" in self.audio.speaker.icon_name:
            vol_high_icon = icons.bluetooth_connected
            vol_medium_icon = icons.bluetooth
            vol_mute_icon = icons.bluetooth_disconnected
            vol_off_icon = icons.bluetooth_disconnected

        if self.audio.speaker.muted:
            self.vol_button.get_child().set_markup(vol_off_icon)
            self.progress_bar.remove_style_class("zero")
            self.vol_label.remove_style_class("zero")
            self.progress_bar.add_style_class("muted")
            self.vol_label.add_style_class("muted")
            self.set_tooltip_text("0%")
            return
        else:
            self.vol_label.remove_style_class("zero")
            self.progress_bar.remove_style_class("zero")
            self.progress_bar.remove_style_class("muted")
            self.vol_label.remove_style_class("muted")
        self.set_tooltip_text(f"{round(self.audio.speaker.volume)}%")
        self.progress_bar.value = self.audio.speaker.volume / 100
        if self.audio.speaker.volume > 74:
            self.vol_button.get_child().set_markup(vol_high_icon)
        elif self.audio.speaker.volume > 5:
            self.vol_button.get_child().set_markup(vol_medium_icon)
        else:
            self.vol_button.get_child().set_markup(vol_mute_icon)
            self.vol_label.add_style_class("zero")
            self.progress_bar.add_style_class("zero")

class MicSmall(Box):
    def __init__(self, **kwargs):
        super().__init__(name="button-bar-mic", **kwargs)
        self.audio = Audio()
        self.progress_bar = CircularProgressBar(
            name="button-mic", size=28, line_width=2,
            start_angle=150, end_angle=390,
        )
        self.mic_label = Label(name="mic-label", markup=icons.mic)
        self.mic_button = Button(on_clicked=self.toggle_mute, child=self.mic_label)
        self.event_box = EventBox(
            events=["scroll", "smooth-scroll"],
            child=Overlay(child=self.progress_bar, overlays=self.mic_button),
        )
        self.audio.connect("notify::microphone", self.on_new_microphone)
        if self.audio.microphone:
            self.audio.microphone.connect("changed", self.on_microphone_changed)
        self.event_box.connect("scroll-event", self.on_scroll)
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.add(self.event_box)
        self.on_microphone_changed()

    def on_new_microphone(self, *args):
        if self.audio.microphone:
            self.audio.microphone.connect("changed", self.on_microphone_changed)
            self.on_microphone_changed()

    def toggle_mute(self, event):
        current_stream = self.audio.microphone
        if current_stream:
            current_stream.muted = not current_stream.muted
            if current_stream.muted:
                self.mic_button.get_child().set_markup(icons.mic_mute)
                self.progress_bar.add_style_class("muted")
                self.mic_label.add_style_class("muted")
            else:
                self.on_microphone_changed()
                self.progress_bar.remove_style_class("muted")
                self.mic_label.remove_style_class("muted")

    def on_scroll(self, _, event):
        if not self.audio.microphone:
            return
        if event.direction == Gdk.ScrollDirection.SMOOTH:
            if abs(event.delta_y) > 0:
                self.audio.microphone.volume -= event.delta_y
            if abs(event.delta_x) > 0:
                self.audio.microphone.volume += event.delta_x

    def on_microphone_changed(self, *_):
        if not self.audio.microphone:
            return
        if self.audio.microphone.muted:
            self.mic_button.get_child().set_markup(icons.mic_mute)
            self.progress_bar.add_style_class("muted")
            self.mic_label.add_style_class("muted")
            self.set_tooltip_text("0%")
            return
        else:
            self.progress_bar.remove_style_class("muted")
            self.mic_label.remove_style_class("muted")
        self.progress_bar.value = self.audio.microphone.volume / 100
        self.set_tooltip_text(f"{round(self.audio.microphone.volume)}%")
        if self.audio.microphone.volume >= 1:
            self.mic_button.get_child().set_markup(icons.mic)
        else:
            self.mic_button.get_child().set_markup(icons.mic_mute)

class BrightnessIcon(Box):
    def __init__(self, **kwargs):
        super().__init__(name="brightness-icon", **kwargs)
        self.brightness = Brightness.get_initial()
        if self.brightness.screen_brightness == -1:
            self.destroy()
            return
            
        self.brightness_label = Label(name="brightness-label-dash", markup=icons.brightness_high, h_align="center", v_align="center", h_expand=True, v_expand=True)
        self.brightness_button = Button(child=self.brightness_label, h_align="center", v_align="center", h_expand=True, v_expand=True)
        
        # Wrap the button in an EventBox for scroll events - add alignment properties here
        self.event_box = EventBox(
            events=["scroll", "smooth-scroll"],
            child=self.brightness_button,
            h_align="center", 
            v_align="center", 
            h_expand=True, 
            v_expand=True
        )
        self.event_box.connect("scroll-event", self.on_scroll)
        self.add(self.event_box)
        
        self.brightness.connect("screen", self.on_brightness_changed)
        self.on_brightness_changed()
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
    
    def on_scroll(self, _, event):
        if self.brightness.max_screen == -1:
            return
            
        step_size = 5
        current_brightness = self.brightness.screen_brightness
        
        if event.direction == Gdk.ScrollDirection.SMOOTH:
            if event.delta_y < 0:
                new_brightness = min(current_brightness + step_size, self.brightness.max_screen)
            elif event.delta_y > 0:
                new_brightness = max(current_brightness - step_size, 0)
            else:
                return
        else:
            if event.direction == Gdk.ScrollDirection.UP:
                new_brightness = min(current_brightness + step_size, self.brightness.max_screen)
            elif event.direction == Gdk.ScrollDirection.DOWN:
                new_brightness = max(current_brightness - step_size, 0)
            else:
                return
                
        self.brightness.screen_brightness = new_brightness
    
    def on_brightness_changed(self, *args):
        if self.brightness.max_screen == -1:
            return
            
        normalized = self.brightness.screen_brightness / self.brightness.max_screen
        brightness_percentage = int(normalized * 100)
        
        if brightness_percentage >= 75:
            self.brightness_label.set_markup(icons.brightness_high)
        elif brightness_percentage >= 24:
            self.brightness_label.set_markup(icons.brightness_medium)
        else:
            self.brightness_label.set_markup(icons.brightness_low)
        self.set_tooltip_text(f"{brightness_percentage}%")

class VolumeIcon(Box):
    def __init__(self, **kwargs):
        super().__init__(name="vol-icon", **kwargs)
        self.audio = Audio()
        
        self.vol_label = Label(name="vol-label-dash", markup=icons.vol_high, h_align="center", v_align="center", h_expand=True, v_expand=True)
        self.vol_button = Button(on_clicked=self.toggle_mute, child=self.vol_label, h_align="center", v_align="center", h_expand=True, v_expand=True)
        
        # Wrap the button in an EventBox for scroll events - add alignment properties here
        self.event_box = EventBox(
            events=["scroll", "smooth-scroll"],
            child=self.vol_button,
            h_align="center", 
            v_align="center", 
            h_expand=True, 
            v_expand=True
        )
        self.event_box.connect("scroll-event", self.on_scroll)
        self.add(self.event_box)
        
        self.audio.connect("notify::speaker", self.on_new_speaker)
        if self.audio.speaker:
            self.audio.speaker.connect("changed", self.on_speaker_changed)
        self.on_speaker_changed()
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
        
    def on_scroll(self, _, event):
        if not self.audio.speaker:
            return
            
        if event.direction == Gdk.ScrollDirection.SMOOTH:
            if abs(event.delta_y) > 0:
                self.audio.speaker.volume -= event.delta_y
            if abs(event.delta_x) > 0:
                self.audio.speaker.volume += event.delta_x
        else:
            if event.direction == Gdk.ScrollDirection.UP:
                self.audio.speaker.volume = min(self.audio.speaker.volume + 5, 100)
            elif event.direction == Gdk.ScrollDirection.DOWN:
                self.audio.speaker.volume = max(self.audio.speaker.volume - 5, 0)
            
    def on_new_speaker(self, *args):
        if self.audio.speaker:
            self.audio.speaker.connect("changed", self.on_speaker_changed)
            self.on_speaker_changed()
            
    def toggle_mute(self, event):
        current_stream = self.audio.speaker
        if current_stream:
            current_stream.muted = not current_stream.muted
            if current_stream.muted:
                self.vol_button.get_child().set_markup(icons.vol_off)
                self.vol_label.add_style_class("muted")
                self.vol_button.add_style_class("muted")
            else:
                self.on_speaker_changed()
                self.vol_label.remove_style_class("muted")
                self.vol_button.remove_style_class("muted")
                
    def on_speaker_changed(self, *_):
        if not self.audio.speaker:
            return
        if self.audio.speaker.muted:
            self.vol_button.get_child().set_markup(icons.vol_off)
            self.add_style_class("muted")
            self.vol_label.add_style_class("muted")
            self.set_tooltip_text("Muted")
            return
        else:
            self.remove_style_class("muted")
            self.vol_label.remove_style_class("muted")
            
        self.set_tooltip_text(f"{round(self.audio.speaker.volume)}%")
        if self.audio.speaker.volume > 74:
            self.vol_button.get_child().set_markup(icons.vol_high)
        elif self.audio.speaker.volume > 0:
            self.vol_button.get_child().set_markup(icons.vol_medium)
        else:
            self.vol_button.get_child().set_markup(icons.vol_mute)

class MicIcon(Box):
    def __init__(self, **kwargs):
        super().__init__(name="mic-icon", **kwargs)
        self.audio = Audio()
        
        self.mic_label = Label(name="mic-label-dash", markup=icons.mic, h_align="center", v_align="center", h_expand=True, v_expand=True)
        self.mic_button = Button(on_clicked=self.toggle_mute, child=self.mic_label, h_align="center", v_align="center", h_expand=True, v_expand=True)
        
        # Wrap the button in an EventBox for scroll events - add alignment properties here
        self.event_box = EventBox(
            events=["scroll", "smooth-scroll"],
            child=self.mic_button,
            h_align="center", 
            v_align="center", 
            h_expand=True, 
            v_expand=True
        )
        self.event_box.connect("scroll-event", self.on_scroll)
        self.add(self.event_box)
        
        self.audio.connect("notify::microphone", self.on_new_microphone)
        if self.audio.microphone:
            self.audio.microphone.connect("changed", self.on_microphone_changed)
        self.on_microphone_changed()
        self.add_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
        
    def on_scroll(self, _, event):
        if not self.audio.microphone:
            return
            
        if event.direction == Gdk.ScrollDirection.SMOOTH:
            if abs(event.delta_y) > 0:
                self.audio.microphone.volume -= event.delta_y
            if abs(event.delta_x) > 0:
                self.audio.microphone.volume += event.delta_x
        else:
            if event.direction == Gdk.ScrollDirection.UP:
                self.audio.microphone.volume = min(self.audio.microphone.volume + 5, 100)
            elif event.direction == Gdk.ScrollDirection.DOWN:
                self.audio.microphone.volume = max(self.audio.microphone.volume - 5, 0)
            
    def on_new_microphone(self, *args):
        if self.audio.microphone:
            self.audio.microphone.connect("changed", self.on_microphone_changed)
            self.on_microphone_changed()
            
    def toggle_mute(self, event):
        current_stream = self.audio.microphone
        if current_stream:
            current_stream.muted = not current_stream.muted
            if current_stream.muted:
                self.mic_button.get_child().set_markup(icons.mic_mute)
                self.mic_label.add_style_class("muted")
                self.mic_button.add_style_class("muted")
            else:
                self.on_microphone_changed()
                self.mic_label.remove_style_class("muted")
                self.mic_button.remove_style_class("muted")
                
    def on_microphone_changed(self, *_):
        if not self.audio.microphone:
            return
        if self.audio.microphone.muted:
            self.mic_button.get_child().set_markup(icons.mic_mute)
            self.add_style_class("muted")
            self.mic_label.add_style_class("muted")
            self.set_tooltip_text("Muted")
            return
        else:
            self.remove_style_class("muted")
            self.mic_label.remove_style_class("muted")
            
        self.set_tooltip_text(f"{round(self.audio.microphone.volume)}%")
        if self.audio.microphone.volume >= 1:
            self.mic_button.get_child().set_markup(icons.mic)
        else:
            self.mic_button.get_child().set_markup(icons.mic_mute)

class ControlSliders(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="control-sliders",
            orientation="h",
            spacing=8,
            **kwargs,
        )
        
        brightness = Brightness.get_initial()
        
        # Create all slider containers with icons
        if (brightness.screen_brightness != -1):
            brightness_row = Box(orientation="h", spacing=4, h_expand=True, h_align="fill")
            brightness_row.add(BrightnessIcon())
            brightness_row.add(BrightnessSlider())  # Removed h_expand=True
            self.add(brightness_row)
            
        volume_row = Box(orientation="h", spacing=4, h_expand=True, h_align="fill")
        volume_row.add(VolumeIcon())
        volume_row.add(VolumeSlider())  # Removed h_expand=True
        self.add(volume_row)
        
        mic_row = Box(orientation="h", spacing=4, h_expand=True, h_align="fill")
        mic_row.add(MicIcon())
        mic_row.add(MicSlider())  # Removed h_expand=True
        self.add(mic_row)
        
        self.show_all()

class ControlSmall(Box):
    def __init__(self, **kwargs):
        brightness = Brightness.get_initial()
        children = []
        if (brightness.screen_brightness != -1):
            children.append(BrightnessSmall())
        children.extend([VolumeSmall(), MicSmall()])
        super().__init__(
            name="control-small",
            orientation="h" if not data.VERTICAL else "v",
            spacing=4,
            children=children,
            **kwargs,
        )
        self.show_all()
