# Parameters
font_family: str = "tabler-icons"
font_weight: str = "normal"

span: str = f"<span font-family='{font_family}' font-weight='{font_weight}'>"

# Panels
apps: str = "&#xf1fd;"
dashboard: str = "&#xea87;"
chat: str = "&#xf59f;"
wallpapers: str = "&#xeb01;"
windows: str = "&#xefe6;"

video: str = "&#xeafa;"  # video
# Bar
colorpicker: str = "&#xebe6;"
media: str = "&#xf00d;"


# network


download: str = "&#xea96;"
upload: str = "&#xeb47;"
# Toolbox
toolbox: str = "&#xebca;"
ssfull: str = "&#xec3c;"
ssregion: str = "&#xf201;"
screenshots: str = "&#xeb0a;"
screenrecord: str = "&#xed22;"
recordings: str = "&#xeafa;"
ocr: str = "&#xfcc3;"
gamemode: str = "&#xf026;"
gamemode_off: str = "&#xf111;"
close : str = "&#xeb55;"

# Circles
temp: str = "&#xeb38;"
disk: str = "&#xea88;"
battery: str = "&#xea38;"
memory: str = "&#xfa97;"
cpu: str = "&#xef8e;"


# AIchat
reload: str = "&#xf3ae;"
detach: str = "&#xea99;"

# Wallpapers
add: str = "&#xeb0b;"
sort: str = "&#xeb5a;"
circle: str = "&#xf671;"

# Chevrons
chevron_up: str = "&#xea62;"
chevron_down: str = "&#xea5f;"
chevron_left: str = "&#xea60;"
chevron_right: str = "&#xea61;"

# Power
lock: str = "&#xeae2;"
suspend: str = "&#xece7;"
logout: str = "&#xeba8;"
reboot: str = "&#xeb13;"
shutdown: str = "&#xeb0d;"

# Power Manager
power_saving: str = "&#xed4f;"
power_balanced: str = "&#xfa77;"
power_performance: str = "&#xec45;"
charging: str = "&#xefef;"
discharging: str = "&#xefe9;"
alert: str = "&#xea06;"
bat_charging: str = "&#xeeca;"
bat_discharging: str = "&#xf0a1;"
bat_low: str = "&#xff1d;"
bat_full: str = "&#xea38;"


# Sensors
battery_25: str = "&#xea2f;"
battery_50: str = "&#xea30;"
battery_75: str = "&#xea31;"
battery_100: str = "&#xea32;"
battery_charging: str = "&#xea33;"

update: str = "&#xfa0a;"
updated: str = "&#xf704;"

# Applets
wifi: str = "&#xeb52;"
wifi_0: str = "&#xeba3;"
wifi_1: str = "&#xeba4;"
wifi_2: str = "&#xeba5;"
wifi_3: str = "&#xeb52;"
world: str = "&#xeb54;"
world_off: str = "&#xf1ca;"
bluetooth: str = "&#xea37;"
night: str = "&#xeaf8;"
coffee: str = "&#xef0e;"
notifications: str = "&#xea35;"

wifi_off: str = "&#xecfa;"
bluetooth_off: str = "&#xeceb;"
night_off: str = "&#xf162;"
notifications_off: str = "&#xece9;"

# Network
wifi_0: str = "&#xeba3;"
wifi_1: str = "&#xeba4;"
wifi_2: str = "&#xeba5;"
download: str = "&#xea96;"
upload: str = "&#xeb47;"
notifications_clear: str = "&#xf814;"

download: str = "&#xea96;"
upload: str = "&#xeb47;"

# Bluetooth
bluetooth_connected: str = "&#xecea;"
bluetooth_disconnected: str = "&#xf081;"

# Player
pause: str = "&#xf690;"
play: str = "&#xf691;"
stop: str = "&#xf695;"
skip_back: str = "&#xf693;"
skip_forward: str = "&#xf694;"
prev: str = "&#xf697;"
next: str = "&#xf696;"
shuffle: str = "&#xf000;"
repeat: str = "&#xeb72;"
music: str = "&#xeafc;"
rewind_backward_5: str = "&#xfabf;"
rewind_forward_5: str = "&#xfac7;"

# Volume
vol_off: str = "&#xf1c3;"
vol_mute: str = "&#xeb50;"
vol_medium: str = "&#xeb4f;"
vol_high: str = "&#xeb51;"

mic: str = "&#xeaf0;"
mic_mute: str = "&#xed16;"

# Overview
circle_plus: str = "&#xea69;"

# Pins
paperclip: str = "&#xeb02;"

# Clipboard Manager
clipboard: str = "&#xea6f;"
clip_text: str = "&#xf089;"

# Confirm
accept: str = "&#xea5e;"
cancel: str = "&#xeb55;"
trash: str = "&#xeb41;"

# Config
config: str = "&#xeb20;"

# Icons
desktop: str = "&#xea89;"
firefox: str = "&#xecfd;"
chromium: str = "&#xec18;"
spotify: str = "&#xfe86;"
code: str = "&#xf3a0;"
discord: str = "&#xece3;"
obsidian: str = "&#xeff5;"
anytype: str = "&#xf495;"
safari: str = "&#xec23;"
obs: str = "&#xef70;"
ghost: str = "&#xfc13;"
appstore: str = "&#xebb6;"
bottle: str = "&#xfa89;"
theme: str = "&#xeb00;"

writing: str = "&#xef08;"
brush: str = "&#xebb8;"

apple: str = "&#xec17;"
mobile: str = "&#xea8a;"

finder: str = "&#xf218;"
folder: str = "&#xeaad;"
zip: str = "&#xed4e;"

terminal: str = "&#xebef;"


disc: str = "&#x1003e;"
disc_off: str = "&#xf118;"

# Brightness
brightness_low: str = "&#xeb7d;"
brightness_medium: str = "&#xeb7e;"
brightness_high: str = "&#xeb30;"

# Misc
dot: str = "&#xf698;"
palette: str = "&#xeb01;"
cloud_off: str = "&#xed3e;"
loader: str = "&#xeca3;"
radar: str = "&#xf017;"
emoji: str = "&#xeaf7;"
keyboard: str = "&#xebd6;"
terminal: str = "&#xebef;"
timer_off: str = "&#xf146;"
timer_on: str = "&#xf756;"

exceptions: list[str] = ["font_family", "font_weight", "span"]


def apply_span() -> None:
    global_dict = globals()
    for key in global_dict:
        if key not in exceptions and not key.startswith("__"):
            global_dict[key] = f"{span}{global_dict[key]}</span>"


apply_span()


def get_class_icon(win_class):
    icon = ghost  # Default icon if no match is found

    match win_class:
        case "unknown":
            icon = desktop
        case "firefox":
            icon = firefox
        case "org.kde.dolphin":
            icon = finder
        case "chromium" | "google-chrome" | "brave-browser":
            icon = chromium
        case "Spotify":
            icon = spotify
        case "code" | "com.visualstudio.code":
            icon = code
        case "com.discordapp.Discord" | "discord":
            icon = discord
        case "kitty" | "alacritty" | "wezterm" | "gnome-terminal" | "xfce4-terminal":
            icon = terminal
        case "obsidian":
            icon = obsidian
        case "anytype":
            icon = anytype
        case "zen" | "safari":
            icon = safari
        case "com.obsproject.Studio":
            icon = obs
        case "org.kde.kdeconnect.app" | "org.kde.kdeconnect-settings" | "GStreamer":
            icon = mobile
        case "org.kde.discover":
            icon = appstore
        case "org.pulseaudio.pavucontrol" | "pavucontrol":
            icon = vol_high
        case (
            "com.github.flxzt.rnote"
            | "com.github.xournalpp.xournalpp"
            | "org.gnome.gedit"
            | "gedit"
        ):
            icon = writing
        case "krita":
            icon = brush
        case "org.kde.ark":
            icon = zip
        case "com.usebottles.bottles":
            icon = bottle
        case "nwg-look":
            icon = theme
        case "thunderbird":
            icon = "&#xf0e0;"  # mail
        case "vlc" | "mpv" | "org.kde.kdenlive":
            icon = "&#xeafa;"  # video
        case "steam":
            icon = "&#xf1b6;"  # steam
        case "lutris":
            icon = "&#xf11b;"  # lutris
        case "heroic":
            icon = "&#xe3e5;"  # heroic
        case "telegram-desktop":
            icon = "&#xf2c6;"  # telegram
        case "signal":
            icon = "&#xf3f7;"  # signal
        case "whatsapp-for-linux":
            icon = "&#xf232;"  # whatsapp
        case "slack":
            icon = "&#xf198;"  # slack
        case "teams-for-linux" | "Microsoft Teams - Preview":
            icon = "&#xf4c4;"  # teams
        case "element":
            icon = "&#xf3b6;"  # matrix
        case "bitwarden":
            icon = "&#xf2c1;"  # password
        case "qbittorrent":
            icon = "&#xf2e4;"  # torrent
        case "android-studio":
            icon = "&#xf17b;"  # android
        case "inkscape":
            icon = "&#xf5d1;"  # vector
        case "gimp":
            icon = "&#xf1fc;"  # gimp
        case "libreoffice-writer" | "libreoffice":
            icon = "&#xf5c3;"  # libreoffice
        case "blender":
            icon = "&#xf1d1;"  # blender
        case "godot":
            icon = "&#xf313;"  # godot
        case "unityhub":
            icon = "&#xf949;"  # unity
        case _:
            icon = ghost  # Default

    return icon
