import os
import json
import uuid
from datetime import datetime, timedelta
from gi.repository import GdkPixbuf, GLib, Gtk
from loguru import logger
from widgets.rounded_image import CustomImage
from fabric.notifications.service import (
    Notification,
    NotificationAction,
    Notifications,
)
from fabric.widgets.box import Box
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.image import Image
from fabric.widgets.label import Label
from fabric.widgets.scrolledwindow import ScrolledWindow
import modules.icons as icons

# Persistence directory and file (history)
PERSISTENT_DIR = "/tmp/ax-shell/notifications"
PERSISTENT_HISTORY_FILE = os.path.join(PERSISTENT_DIR, "notification_history.json")

def cache_notification_pixbuf(notification_box):
    """
    Saves a scaled pixbuf (48x48) in the cache directory and returns the cache file path.
    """
    notification = notification_box.notification
    if notification.image_pixbuf:
        os.makedirs(PERSISTENT_DIR, exist_ok=True)
        cache_file = os.path.join(PERSISTENT_DIR, f"notification_{notification_box.uuid}.png")
        logger.debug(f"Caching image for notification {notification.id} to: {cache_file}") # Log before caching
        try:
            scaled = notification.image_pixbuf.scale_simple(48, 48, GdkPixbuf.InterpType.BILINEAR)
            scaled.savev(cache_file, "png", [], [])
            logger.info(f"Successfully cached image for notification {notification.id} to: {cache_file}") # Log on success
            return cache_file # Return the cache file path
        except Exception as e:
            logger.error(f"Error caching image for notification {notification.id}: {e}")
            return None
    else:
        logger.debug(f"Notification {notification.id} has no image_pixbuf to cache.")
        return None

def load_scaled_pixbuf(notification_box, width, height):
    """
    Loads and scales a pixbuf for a notification_box, prioritizing cached images.
    """
    notification = notification_box.notification
    if not hasattr(notification_box, 'notification') or notification is None:
        logger.error("load_scaled_pixbuf: notification_box.notification is None or not set!")
        return None

    pixbuf = None
    if hasattr(notification_box, "cached_image_path") and notification_box.cached_image_path and os.path.exists(notification_box.cached_image_path):
        try:
            logger.debug(f"Attempting to load cached image from: {notification_box.cached_image_path} for notification {notification.id}") # Log cache load attempt
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(notification_box.cached_image_path)
            pixbuf = pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)
            logger.info(f"Successfully loaded cached image from: {notification_box.cached_image_path} for notification {notification.id}") # Log cache load success
            return pixbuf
        except Exception as e:
            logger.error(f"Error loading cached image from {notification_box.cached_image_path} for notification {notification.id}: {e}")
            # Fallback to loading from notification if cached load fails
            logger.warning(f"Falling back to notification.image_pixbuf for notification {notification.id}") # Log fallback

    if notification.image_pixbuf:
        logger.debug(f"Loading image directly from notification.image_pixbuf for notification {notification.id}") # Log direct load attempt
        pixbuf = notification.image_pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)
        return pixbuf

    logger.debug(f"No image_pixbuf or cached image found, trying app icon for notification {notification.id}") # Log app icon fallback
    return get_app_icon_pixbuf(notification.app_icon, width, height)

def get_app_icon_pixbuf(icon_path, width, height):
    """
    Loads and scales a pixbuf from an app icon path.
    """
    if not icon_path:
        return None
    if icon_path.startswith("file://"):
        icon_path = icon_path[7:]
    if not os.path.exists(icon_path):
        logger.warning(f"Icon path does not exist: {icon_path}")
        return None
    try:
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_path)
        return pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)
    except Exception as e:
        logger.error(f"Failed to load or scale icon: {e}")
        return None


class ActionButton(Button):
    def __init__(self, action: NotificationAction, index: int, total: int, notification_box):
        super().__init__(
            name="action-button",
            h_expand=True,
            on_clicked=self.on_clicked,
            child=Label(name="button-label", label=action.label),
        )
        self.action = action
        self.notification_box = notification_box
        style_class = (
            "start-action" if index == 0
            else "end-action" if index == total - 1
            else "middle-action"
        )
        self.add_style_class(style_class)
        self.connect("enter-notify-event", lambda *_: notification_box.hover_button(self))
        self.connect("leave-notify-event", lambda *_: notification_box.unhover_button(self))

    def on_clicked(self, *_):
        self.action.invoke()
        self.action.parent.close("dismissed-by-user")
        # File cleanup should happen in NotificationBox.destroy() called by NotificationContainer

class NotificationBox(Box):
    def __init__(self, notification: Notification, timeout_ms=5000, **kwargs):
        super().__init__(
            name="notification-box",
            orientation="v",
            h_align="fill",
            h_expand=True,
            children=[],
        )
        self.notification = notification
        self.uuid = str(uuid.uuid4())
        self.timeout_ms = timeout_ms
        self._timeout_id = None
        self._container = None
        self.cached_image_path = None
        self.start_timeout()

        # Cache image and get path immediately in constructor
        if self.notification.image_pixbuf:
            cache_path = cache_notification_pixbuf(self)
            if cache_path:
                self.cached_image_path = cache_path
                logger.debug(f"NotificationBox {self.uuid}: Cached image path set to: {self.cached_image_path}")
            else:
                logger.warning(f"NotificationBox {self.uuid}: Caching failed, cached_image_path not set.")
        else:
            logger.debug(f"NotificationBox {self.uuid}: No image to cache.")


        content = self.create_content()
        action_buttons = self.create_action_buttons()
        self.add(content)
        if action_buttons:
            self.add(action_buttons)

        self.connect("enter-notify-event", self.on_hover_enter)
        self.connect("leave-notify-event", self.on_hover_leave)

        self._destroyed = False
        self._is_history = False
        logger.debug(f"NotificationBox {self.uuid} created for notification {notification.id}")


    def set_is_history(self, is_history):
        self._is_history = is_history

    def set_container(self, container):
        self._container = container

    def get_container(self):
        return self._container

    def create_header(self):
        notification = self.notification
        app_icon = (
            Image(
                name="notification-icon",
                image_file=notification.app_icon[7:],
                size=24,
            ) if "file://" in notification.app_icon else
            Image(
                name="notification-icon",
                icon_name="dialog-information-symbolic" or notification.app_icon,
                icon_size=24,
            )
        )

        return CenterBox(
            name="notification-title",
            start_children=[
                Box(
                    spacing=4,
                    children=[
                        app_icon,
                        Label(
                            notification.app_name,
                            name="notification-app-name",
                            h_align="start"
                        )
                    ]
                )
            ],
            end_children=[self.create_close_button()]
        )

    def create_content(self):
        notification = self.notification
        pixbuf = load_scaled_pixbuf(self, 48, 48) # Pass self to load_scaled_pixbuf
        return Box(
            name="notification-content",
            spacing=8,
            children=[
                Box(
                    name="notification-image",
                    children=CustomImage(pixbuf=pixbuf),
                ),
                Box(
                    name="notification-text",
                    orientation="v",
                    v_align="center",
                    children=[
                        Box(
                            name="notification-summary-box",
                            orientation="h",
                            children=[
                                Label(
                                    name="notification-summary",
                                    markup=notification.summary,
                                    h_align="start",
                                    ellipsization="end",
                                ),
                                Label(
                                    name="notification-app-name",
                                    markup=" | " + notification.app_name,
                                    h_align="start",
                                    ellipsization="end",
                                ),
                            ],
                        ),
                        Label(
                            markup=notification.body,
                            h_align="start",
                            ellipsization="end",
                        ) if notification.body else Box(),
                    ],
                ),
                Box(h_expand=True),
                Box(
                    orientation="v",
                    children=[
                        self.create_close_button(),
                        Box(v_expand=True),
                    ],
                ),
            ],
        )


    def create_action_buttons(self):
        notification = self.notification
        if not notification.actions:
            return None

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_column_spacing(4)
        for i, action in enumerate(notification.actions):
            action_button = ActionButton(action, i, len(notification.actions), self)
            grid.attach(action_button, i, 0, 1, 1)
        return grid

    def create_close_button(self):
        close_button = Button(
            name="notif-close-button",
            child=Label(name="notif-close-label", markup=icons.cancel),
            on_clicked=lambda *_: self.notification.close("dismissed-by-user"),
        )
        close_button.connect("enter-notify-event", lambda *_: self.hover_button(close_button))
        close_button.connect("leave-notify-event", lambda *_: self.unhover_button(close_button))
        return close_button

    def on_hover_enter(self, *args):
        if self._container:
            self._container.pause_and_reset_all_timeouts()

    def on_hover_leave(self, *args):
        if self._container:
            self._container.resume_all_timeouts()

    def start_timeout(self):
        self.stop_timeout()
        self._timeout_id = GLib.timeout_add(self.timeout_ms, self.close_notification)

    def stop_timeout(self):
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None

    def close_notification(self):
        if not self._destroyed:
            try:
                logger.debug(f"Notification {self.notification.id} timeout expired, closing notification.") # Log timeout close
                self.notification.close("expired")
                self.stop_timeout()
            except Exception as e:
                logger.error(f"Error in close_notification for notification {self.notification.id}: {e}")
        return False

    def destroy(self, from_history_delete=False):
        logger.debug(f"NotificationBox destroy called for notification: {self.notification.id}, from_history_delete: {from_history_delete}, is_history: {self._is_history}")
        if hasattr(self, "cached_image_path") and self.cached_image_path and os.path.exists(self.cached_image_path) and (not self._is_history or from_history_delete): # Modified condition here
            try:
                os.remove(self.cached_image_path)
                logger.info(f"Deleted cached image: {self.cached_image_path}")
            except Exception as e:
                logger.error(f"Error deleting cached image {self.cached_image_path}: {e}")
        self._destroyed = True
        self.stop_timeout()
        super().destroy()

    def hover_button(self, button):
        if self._container:
            self._container.pause_and_reset_all_timeouts()

    def unhover_button(self, button):
        if self._container:
            self._container.resume_all_timeouts()

class HistoricalNotification:
    """
    Minimal object to create persistent historical notifications.
    """
    def __init__(self, id, app_icon, summary, body, app_name, timestamp, cached_image_path=None):
        self.id = id
        self.app_icon = app_icon
        self.summary = summary
        self.body = body
        self.app_name = app_name
        self.timestamp = timestamp
        self.cached_image_path = cached_image_path
        self.image_pixbuf = None
        self.actions = []
        self.cached_scaled_pixbuf = None


class NotificationHistory(Box):
    def __init__(self, **kwargs):
        super().__init__(
            name="notification-history",
            orientation="v",
            **kwargs
        )
        self.notch = kwargs["notch"]
        self.header_label = Label(
            name="nhh",
            label="Notifications",
            h_align="start",
            h_expand=True,
        )
        self.header_switch = Gtk.Switch(name="dnd-switch")
        self.header_switch.set_vexpand(False)
        self.header_switch.set_valign(Gtk.Align.CENTER)
        self.header_switch.set_active(False)
        self.header_clean = Button(
            name="nhh-button",
            child=Label(name="nhh-button-label", markup=icons.trash),
            on_clicked=self.clear_history,
        )
        self.do_not_disturb_enabled = False
        self.header_switch.connect("notify::active", self.on_do_not_disturb_changed)
        self.dnd_label = Label(name="dnd-label", markup=icons.notifications_off)

        self.history_header = CenterBox(
            name="notification-history-header",
            spacing=8,
            start_children=[self.header_switch, self.dnd_label],
            center_children=[self.header_label],
            end_children=[self.header_clean],
        )
        self.notifications_list = Box(
            name="notifications-list",
            orientation="v",
            spacing=4,
        )
        self.no_notifications_label = Label(
            name="no-notifications-label",
            markup=icons.notifications_clear,
            v_align="fill",
            h_align="fill",
            v_expand=True,
            h_expand=True,
            justification="center",
        )
        self.no_notifications_box = Box(
            name="no-notifications-box",
            v_align="fill",
            h_align="fill",
            v_expand=True,
            h_expand=True,
            children=[self.no_notifications_label],
        )
        self.scrolled_window = ScrolledWindow(
            name="notification-history-scrolled-window",
            h_vexpand=True,
            orientation="v",
            h_expand=True,
            v_expand=True,
            min_content_size=(-1, -1),
            max_content_size=(-1, -1),
        )
        self.scrolled_window.add_with_viewport(Box(orientation="v", children=[self.notifications_list, self.no_notifications_box]))
        self.persistent_notifications = []
        self.add(self.history_header)
        self.add(self.scrolled_window)
        self._load_persistent_history()

    def on_do_not_disturb_changed(self, switch, pspec):
        self.do_not_disturb_enabled = switch.get_active()
        logger.info(f"Do Not Disturb mode {'enabled' if self.do_not_disturb_enabled else 'disabled'}")

    def clear_history(self, *args):
        """Clears the notification history (visual and persistent)."""
        for child in self.notifications_list.get_children()[:]:
            container = child
            notif_box = container.notification_box if hasattr(container, "notification_box") else None
            if notif_box:
                notif_box.destroy(from_history_delete=True)
            self.notifications_list.remove(child)
            child.destroy()

        if os.path.exists(PERSISTENT_HISTORY_FILE):
            try:
                os.remove(PERSISTENT_HISTORY_FILE)
                logger.info("Notification history cleared and persistent file deleted.")
            except Exception as e:
                logger.error(f"Error deleting persistent history file: {e}")
        self.persistent_notifications = []
        self.update_separators()
        self.update_no_notifications_label_visibility()

    def _load_persistent_history(self):
        """Loads the persistent history from the JSON file and restores it."""
        if not os.path.exists(PERSISTENT_DIR):
            os.makedirs(PERSISTENT_DIR, exist_ok=True)
        if os.path.exists(PERSISTENT_HISTORY_FILE):
            try:
                with open(PERSISTENT_HISTORY_FILE, "r") as f:
                    self.persistent_notifications = json.load(f)
                for note in self.persistent_notifications:
                    self._add_historical_notification(note)
            except Exception as e:
                logger.error(f"Error loading persistent history: {e}")
        GLib.idle_add(self.update_no_notifications_label_visibility)

    def _save_persistent_history(self):
        """Saves the list of notifications to the JSON file."""
        try:
            with open(PERSISTENT_HISTORY_FILE, "w") as f:
                json.dump(self.persistent_notifications, f)
        except Exception as e:
            logger.error(f"Error saving persistent history: {e}")

    def delete_historical_notification(self, note_id, container):
        """
        Deletes a historical notification (visual and persistent) and its files.
        """
        if hasattr(container, "notification_box"):
            notif_box = container.notification_box
            notif_box.destroy(from_history_delete=True)

        self.persistent_notifications = [
            note for note in self.persistent_notifications if note.get("id") != note_id
        ]
        self._save_persistent_history()
        container.destroy()
        GLib.idle_add(self.update_separators)
        self.update_no_notifications_label_visibility()

    def _add_historical_notification(self, note):
        """Creates and adds a NotificationBox based on a historical dict."""
        hist_notif = HistoricalNotification(
            id=note.get("id"),
            app_icon=note.get("app_icon"),
            summary=note.get("summary"),
            body=note.get("body"),
            app_name=note.get("app_name"),
            timestamp=note.get("timestamp"),
            cached_image_path=note.get("cached_image_path"),
        )

        hist_box = NotificationBox(hist_notif, timeout_ms=0)
        hist_box.uuid = hist_notif.id
        hist_box.cached_image_path = hist_notif.cached_image_path
        hist_box.set_is_history(True)
        for child in hist_box.get_children():
            if child.get_name() == "notification-action-buttons":
                hist_box.remove(child)
        container = Box(
            name="notification-container",
            orientation="v",
            h_align="fill",
            h_expand=True,
        )
        container.notification_box = hist_box
        try:
            arrival = datetime.fromisoformat(hist_notif.timestamp)
        except Exception:
            arrival = datetime.now()
        container.arrival_time = arrival

        def compute_time_label(arrival_time):
            now = datetime.now()
            if arrival_time.date() != now.date():
                if arrival_time.date() == (now - timedelta(days=1)).date():
                    return " | Yesterday " + arrival_time.strftime("%H:%M")
                else:
                    return arrival_time.strftime("| %d/%m/%Y %H:%M")
            delta = now - arrival_time
            seconds = delta.total_seconds()
            if seconds < 60:
                return " | Now"
            elif seconds < 3600:
                minutes = int(seconds // 60)
                return f" | {minutes} min" if minutes == 1 else f" | {minutes} mins"
            else:
                return arrival_time.strftime(" | %H:%M")

        time_label = Label(name="notification-timestamp", markup=compute_time_label(container.arrival_time))
        content_box = Box(
            name="notification-box-hist",
            spacing=8,
            children=[
                Box(
                    name="notification-image",
                    children=[
                        CustomImage(
                            pixbuf=load_scaled_pixbuf(hist_box, 48, 48) # Pass hist_box to load_scaled_pixbuf
                        )
                    ]
                ),
                Box(
                    name="notification-text",
                    orientation="v",
                    v_align="center",
                    h_expand=True,
                    children=[
                        Box(
                            name="notification-summary-box",
                            orientation="h",
                            children=[
                                Label(
                                    name="notification-summary",
                                    markup=hist_notif.summary,
                                    h_align="start",
                                    ellipsization="end",
                                ),
                                Label(
                                    name="notification-app-name",
                                    markup=f" | {hist_notif.app_name}",
                                    h_align="start",
                                    ellipsization="end",
                                ),
                                time_label,
                            ],
                        ),
                        Label(
                            name="notification-body",
                            markup=hist_notif.body,
                            h_align="start",
                            ellipsization="end",
                        ) if hist_notif.body else Box(),
                    ],
                ),
                Box(
                    orientation="v",
                    children=[
                        Button(
                            name="notif-close-button",
                            child=Label(name="notif-close-label", markup=icons.cancel),
                            on_clicked=lambda *_: self.delete_historical_notification(hist_notif.id, container),
                        ),
                        Box(v_expand=True),
                    ],
                ),
            ],
        )
        container.add(content_box)
        container.add(Box(name="notification-separator"))
        self.notifications_list.pack_start(container, False, False, 0)
        self.update_separators()
        self.show_all()
        self.update_no_notifications_label_visibility()

    def update_last_separator(self):
        children = self.notifications_list.get_children()
        for child in children:
            separator = [c for c in child.get_children() if c.get_name() == "notification-separator"]
            if separator:
                separator[0].set_visible(child != children[-1])


    def add_notification(self, notification_box):
        if len(self.notifications_list.get_children()) >= 50:
            oldest_notification_container = self.notifications_list.get_children()[0]
            self.notifications_list.remove(oldest_notification_container)
            if hasattr(oldest_notification_container, "notification_box") and hasattr(oldest_notification_container.notification_box, "cached_image_path") and oldest_notification_container.notification_box.cached_image_path and os.path.exists(oldest_notification_container.notification_box.cached_image_path):
                try:
                    os.remove(oldest_notification_container.notification_box.cached_image_path)
                    logger.info(f"Deleted cached image of oldest notification due to history limit: {oldest_notification_container.notification_box.cached_image_path}")
                except Exception as e:
                    logger.error(f"Error deleting cached image of oldest notification: {e}")
            oldest_notification_container.destroy()


        def on_container_destroy(container):
            if hasattr(container, "_timestamp_timer_id") and container._timestamp_timer_id:
                GLib.source_remove(container._timestamp_timer_id)
            if hasattr(container, "notification_box"):
                notif_box = container.notification_box
            container.destroy()
            GLib.idle_add(self.update_separators)
            self.update_no_notifications_label_visibility()

        container = Box(
            name="notification-container",
            orientation="v",
            h_align="fill",
            h_expand=True,
        )
        container.arrival_time = datetime.now()
        def compute_time_label(arrival_time):
            now = datetime.now()
            if arrival_time.date() != now.date():
                if arrival_time.date() == (now - timedelta(days=1)).date():
                    return " | Yesterday " + arrival_time.strftime("%H:%M")
                else:
                    return arrival_time.strftime("| %d/%m/%Y %H:%M")
            delta = now - arrival_time
            seconds = delta.total_seconds()
            if seconds < 60:
                return " | Now"
            elif seconds < 3600:
                minutes = int(seconds // 60)
                return f" | {minutes} min" if minutes == 1 else f" | {minutes} mins"
            else:
                return arrival_time.strftime(" | %H:%M")
        time_label = Label(name="notification-timestamp", markup=compute_time_label(container.arrival_time))
        content_box = Box(
            name="notification-content",
            spacing=8,
            children=[
                Box(
                    name="notification-image",
                    children=[
                        CustomImage(
                            pixbuf=load_scaled_pixbuf(notification_box, 48, 48) # Pass notification_box to load_scaled_pixbuf
                        )
                    ]
                ),
                Box(
                    name="notification-text",
                    orientation="v",
                    v_align="center",
                    h_expand=True,
                    children=[
                        Box(
                            name="notification-summary-box",
                            orientation="h",
                            children=[
                                Label(
                                    name="notification-summary",
                                    markup=notification_box.notification.summary,
                                    h_align="start",
                                    ellipsization="end",
                                ),
                                Label(
                                    name="notification-app-name",
                                    markup=f" | {notification_box.notification.app_name}",
                                    h_align="start",
                                    ellipsization="end",
                                ),
                                time_label,
                            ],
                        ),
                        Label(
                            name="notification-body",
                            markup=notification_box.notification.body,
                            h_align="start",
                            ellipsization="end",
                        ) if notification_box.notification.body else Box(),
                    ],
                ),
                Box(
                    orientation="v",
                    children=[
                        Button(
                            name="notif-close-button",
                            child=Label(name="notif-close-label", markup=icons.cancel),
                            on_clicked=lambda *_: on_container_destroy(container),
                        ),
                        Box(v_expand=True),
                    ],
                ),
            ],
        )
        def update_timestamp():
            time_label.set_markup(compute_time_label(container.arrival_time))
            return True
        container._timestamp_timer_id = GLib.timeout_add_seconds(10, update_timestamp)
        container.notification_box = notification_box
        hist_box = Box(
            name="notification-box-hist",
            orientation="v",
            h_align="fill",
            h_expand=True,
        )
        hist_box.add(content_box)
        content_box.get_children()[2].get_children()[0].connect(
            "clicked",
            lambda *_: on_container_destroy(container)
        )
        container.add(hist_box)
        container.add(Box(name="notification-separator"))
        self.notifications_list.pack_start(container, False, False, 0)
        self.update_separators()
        self.show_all()
        self._append_persistent_notification(notification_box, container.arrival_time)
        self.update_no_notifications_label_visibility()

    def _append_persistent_notification(self, notification_box, arrival_time):
        note = {
            "id": notification_box.uuid,
            "app_icon": notification_box.notification.app_icon,
            "summary": notification_box.notification.summary,
            "body": notification_box.notification.body,
            "app_name": notification_box.notification.app_name,
            "timestamp": arrival_time.isoformat(),
            "cached_image_path": notification_box.cached_image_path
        }
        self.persistent_notifications.append(note)
        self.persistent_notifications = self.persistent_notifications[-50:]
        self._save_persistent_history()


    def update_separators(self):
        children = self.notifications_list.get_children()
        for child in children:
            for widget in child.get_children():
                if widget.get_name() == "notification-separator":
                    child.remove(widget)
        for i, child in enumerate(children):
            if i < len(children) - 1:
                separator = Box(name="notification-separator")
                child.add(separator)

    def update_no_notifications_label_visibility(self):
        """Updates the visibility of the 'No notifications!' label based on history."""
        has_notifications = bool(self.notifications_list.get_children())
        self.no_notifications_box.set_visible(not has_notifications)
        self.notifications_list.set_visible(has_notifications)


class NotificationContainer(Box):
    def __init__(self, **kwargs):
        super().__init__(name="notification", orientation="v", spacing=4)
        self.notch = kwargs["notch"]
        self._server = Notifications()
        self._server.connect("notification-added", self.on_new_notification)
        self._pending_removal = False
        self._is_destroying = False

        self.history = NotificationHistory(notch=self.notch)
        self.stack = Gtk.Stack(
            name="notification-stack",
            transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT,
            transition_duration=200,
            visible=True,
        )
        self.stack_box = Box(
            name="notification-stack-box",
            h_align="center",
            h_expand=False,
            children=[self.stack]
        )
        self.navigation = Box(
            name="notification-navigation",
            spacing=4,
            h_align="center"
        )
        self.prev_button = Button(
            name="nav-button",
            child=Label(name="nav-button-label", markup=icons.chevron_left),
            on_clicked=self.show_previous,
        )
        self.close_all_button = Button(
            name="nav-button",
            child=Label(name="nav-button-label", markup=icons.cancel),
            on_clicked=self.close_all_notifications,
        )
        self.close_all_button.get_child().add_style_class("close")
        self.next_button = Button(
            name="nav-button",
            child=Label(name="nav-button-label", markup=icons.chevron_right),
            on_clicked=self.show_next,
        )
        for button in [self.prev_button, self.close_all_button, self.next_button]:
            button.connect("enter-notify-event", lambda *_: self.pause_and_reset_all_timeouts())
            button.connect("leave-notify-event", lambda *_: self.resume_all_timeouts())
        self.navigation.add(self.prev_button)
        self.navigation.add(self.close_all_button)
        self.navigation.add(self.next_button)
        self.notification_box = Box(
            orientation="v",
            spacing=4,
            children=[self.stack_box, self.navigation]
        )
        self.notifications = []
        self.current_index = 0
        self.update_navigation_buttons()
        self._destroyed_notifications = set()

    def show_previous(self, *args):
        if self.current_index > 0:
            self.current_index -= 1
            self.stack.set_visible_child(self.notifications[self.current_index])
            self.update_navigation_buttons()

    def show_next(self, *args):
        if self.current_index < len(self.notifications) - 1:
            self.current_index += 1
            self.stack.set_visible_child(self.notifications[self.current_index])
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.prev_button.set_sensitive(self.current_index > 0)
        self.next_button.set_sensitive(self.current_index < len(self.notifications) - 1)
        self.navigation.set_visible(len(self.notifications) > 1)

    def on_new_notification(self, fabric_notif, id):
        if self.notch.notification_history.do_not_disturb_enabled:
            logger.info("Do Not Disturb mode enabled: adding notification directly to history.")
            notification = fabric_notif.get_notification_from_id(id)
            new_box = NotificationBox(notification)
            if notification.image_pixbuf:
                cache_notification_pixbuf(new_box) # Cache synchronously before history
            self.notch.notification_history.add_notification(new_box)
            return

        notification = fabric_notif.get_notification_from_id(id)
        new_box = NotificationBox(notification) # Caching now happens inside NotificationBox constructor
        # if notification.image_pixbuf: # No need to cache again here, already done in NotificationBox init.
        #     GLib.idle_add(cache_notification_pixbuf, new_box)
        new_box.set_container(self)
        notification.connect("closed", self.on_notification_closed)
        while len(self.notifications) >= 5:
            oldest_notification = self.notifications[0]
            self.notch.notification_history.add_notification(oldest_notification)
            self.stack.remove(oldest_notification)
            self.notifications.pop(0)
            if self.current_index > 0:
                self.current_index -= 1
        self.stack.add_named(new_box, str(id))
        self.notifications.append(new_box)
        self.current_index = len(self.notifications) - 1
        self.stack.set_visible_child(new_box)
        for notification_box in self.notifications:
            notification_box.start_timeout()
        if len(self.notifications) == 1:
            if not self.notification_box.get_parent():
                self.notch.notification_revealer.add(self.notification_box)
        self.notch.notification_revealer.show_all()
        self.notch.notification_revealer.set_reveal_child(True)
        self.update_navigation_buttons()

    def on_notification_closed(self, notification, reason):
        if self._is_destroying:
            return
        if notification.id in self._destroyed_notifications:
            return
        self._destroyed_notifications.add(notification.id)
        try:
            logger.info(f"Notification {notification.id} closing with reason: {reason}")
            notif_to_remove = None
            for i, notif_box in enumerate(self.notifications):
                if notif_box.notification.id == notification.id:
                    notif_to_remove = (i, notif_box)
                    break
            if not notif_to_remove:
                return
            i, notif_box = notif_to_remove
            reason_str = str(reason)
            if reason_str == "NotificationCloseReason.DISMISSED_BY_USER":
                logger.info(f"Cleaning up resources for dismissed notification {notification.id}")
                notif_box.destroy()
            elif (reason_str == "NotificationCloseReason.EXPIRED" or
                  reason_str == "NotificationCloseReason.CLOSED" or
                  reason_str == "NotificationCloseReason.UNDEFINED"):
                logger.info(f"Adding notification {notification.id} to history (reason: {reason_str})")
                notif_box.set_is_history(True)
                self.notch.notification_history.add_notification(notif_box)
                notif_box.stop_timeout()
            else:
                logger.warning(f"Unknown close reason: {reason_str} for notification {notification.id}. Defaulting to destroy.")
                notif_box.destroy()

            if len(self.notifications) == 1:
                self._is_destroying = True
                self.notch.notification_revealer.set_reveal_child(False)
                GLib.timeout_add(
                    self.notch.notification_revealer.get_transition_duration(),
                    self._destroy_container
                )
                return
            new_index = i
            if i == self.current_index:
                new_index = max(0, i - 1)
            elif i < self.current_index:
                new_index = self.current_index - 1
            next_notification = self.notifications[new_index if new_index < i else i]
            self.stack.set_visible_child(next_notification)
            if notif_box.get_parent() == self.stack:
                self.stack.remove(notif_box)
            self.notifications.remove(notif_box)
            self.current_index = new_index
            self.update_navigation_buttons()
        except Exception as e:
            logger.error(f"Error closing notification: {e}")
        logger.info(f"Notification {notification.id} closed with reason: {reason}")

    def _destroy_container(self):
        try:
            self.notifications.clear()
            self._destroyed_notifications.clear()
            for child in self.stack.get_children():
                child.destroy()
                self.stack.remove(child)
            self.current_index = 0
            self.navigation.set_visible(False)
            if self.notification_box.get_parent():
                self.notification_box.get_parent().remove(self.notification_box)
        except Exception as e:
            logger.error(f"Error cleaning up the container: {e}")
        finally:
            self._is_destroying = False
            return False

    def pause_and_reset_all_timeouts(self):
        if self._is_destroying:
            return
        for notification in self.notifications[:]:
            try:
                if not notification._destroyed and notification.get_parent():
                    notification.stop_timeout()
            except Exception as e:
                logger.error(f"Error pausing timeout: {e}")

    def resume_all_timeouts(self):
        if self._is_destroying:
            return
        for notification in self.notifications[:]:
            try:
                if not notification._destroyed and notification.get_parent():
                    notification.start_timeout()
            except Exception as e:
                logger.error(f"Error resuming timeout: {e}")

    def close_all_notifications(self, *args):
        notifications_to_close = self.notifications.copy()
        for notification_box in notifications_to_close:
            notification_box.notification.close("dismissed-by-user")