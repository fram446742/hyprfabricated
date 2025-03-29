<h1 align="center"><b>HYPRFABRICATED</b></h1>

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/tr1xem/hyprfabricated?style=for-the-badge&logo=github&color=FFB686&logoColor=D9E0EE&labelColor=292324)](https://github.com/tr1xem/hyprfabricated/stargazers)
[![Hyprland](https://img.shields.io/badge/Made%20for-Hyprland-pink?style=for-the-badge&logo=linux&logoColor=D9E0EE&labelColor=292324&color=C6A0F6)](https://hyprland.org/)
[![Maintained](https://img.shields.io/badge/Maintained-Yes-blue?style=for-the-badge&logo=linux&logoColor=D9E0EE&labelColor=292324&color=3362E1)]()
[![Discord](https://dcbadge.limes.pink/api/server/https://discord.gg/EMWUTgegDm)](https://discord.gg/EMWUTgegDm)

</div>
<p align="center"><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Telegram-Animated-Emojis/main/Activity/Sparkles.webp" alt="Sparkles" width="25" height="25" /> <sup>A ʜᴀᴄᴋᴀʙʟᴇ sʜᴇʟʟ ꜰᴏʀ Hʏᴘʀʟᴀɴᴅ, ᴘᴏᴡᴇʀᴇᴅ ʙʏ <a href="https://github.com/Fabric-Development/fabric/">Fᴀʙʀɪᴄ</a>. </sup><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Telegram-Animated-Emojis/main/Activity/Sparkles.webp" alt="Sparkles" width="25" height="25" /></p>

<h2><sub><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Camera%20with%20Flash.png" alt="Camera with Flash" width="25" height="25" /></sub> Screenshots</h2>
<table align="center">
  <tr>
    <td colspan="4"><img src="assets/screenshots/1.png"></td>
  </tr>
  <tr>
    <td colspan="1"><img src="assets/screenshots/2.png"></td>
    <td colspan="1"><img src="assets/screenshots/3.png"></td>
    <td colspan="1" align="center"><img src="assets/screenshots/4.png"></td>
    <td colspan="1" align="center"><img src="assets/screenshots/5.png"></td>
  </tr>
</table>

<h2><sub><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Package.png" alt="Package" width="25" height="25" /></sub> Installation</h2>

> [!NOTE]
>
> - You need a functioning Hyprland installation. <br>
> - You need to install plasma-browser-integration for mpris and cava to work as it is intended <br>
> - Join the discord server for better support

### Arch Linux

> [!TIP]
>
> - This command also works for updating an existing installation!!! <br>
> - If you see a transparent bar just change the wallpaper from notch > wallpaper as then it would gen color configs

```bash
curl -fsSL https://raw.githubusercontent.com/tr1xem/hyprfabricated/main/install.sh | bash
```

### Manual Installation
1. Install dependencies:

- Aur/Pacman:
  - [`Fabric`](https://github.com/Fabric-Development/fabric)
  - [`fabric-cli`](https://github.com/Fabric-Development/fabric-cli)
  - [`Gray`](https://github.com/Fabric-Development/gray)
  - [`Matugen`](https://github.com/InioX/matugen)
  - [`acpi`](https://github.com/acpica/acpica)
  - [`brightnessctl`](https://github.com/Hummer12007/brightnessctl)
  - [`cava`](https://github.com/karlstav/cava)
  - [`gnome-bluetooth-3.0`](https://github.com/GNOME/gnome-bluetooth)
  - [`gpu-screen-recorder`](https://git.dec05eba.com/gpu-screen-recorder/)
  - [`grimblast`](https://github.com/hyprwm/contrib/tree/main/grimblast)
  - [`hypridle`](https://github.com/hyprwm/hypridle)
  - [`hyprlock`](https://github.com/hyprwm/hyprlock)
  - [`hyprpicker`](https://github.com/hyprwm/hyprpicker)
  - [`hyprsunset`](https://github.com/hyprwm/hyprsunset)
  - [`imagemagick`](https://github.com/ImageMagick/ImageMagick)
  - [`libnotify`](https://github.com/GNOME/libnotify)
  - [`noto-fonts-emoji`](https://github.com/androlabs/emoji-archlinux)
  - [`playerctl`](https://github.com/altdesktop/playerctl)
  - [`swappy`](https://github.com/jtheoof/swappy)
  - [`swww`](https://github.com/LGFae/swww)
  - [`tesseract`](https://github.com/tesseract-ocr/tesseract)
  - [`uwsm`](https://github.com/Vladimir-csp/uwsm)
  - [`cantarell-fonts-0.100`](https://fonts.google.com/specimen/Cantarell)
  - [`wl-clipboard`](https://github.com/bugaevc/wl-clipboard)
  - [`wlinhibit`](https://github.com/0x5a4/wlinhibit)
  - [`grimblast-git`](https://github.com/hyprwm/contrib/blob/main/grimblast/grimblast)
  - [`tmux`](https://github.com/tmux/tmux/wiki)
- Python dependencies:
  - [ijson](https://pypi.org/project/ijson/)
  - [pillow](https://pypi.org/project/pillow/)
  - [psutil](https://pypi.org/project/psutil/)
  - [requests](https://pypi.org/project/requests/)
  - [setproctitle](https://pypi.org/project/setproctitle/)
  - [toml](https://pypi.org/project/toml/)
  - [watchdog](https://pypi.org/project/watchdog/)
- Fonts (automated on first run):
  - [Zed Sans](https://github.com/zed-industries/zed-fonts)
  - [Tabler Icons](https://tabler.io/icons)

3. Download and run Ax-Shell:
   ```bash
   git clone https://github.com/tr1xem/hyprfabricated.git ~/.config/hyprfabricated
   uwsm -- app python ~/.config/hyprfabricated/main.py > /dev/null 2>&1 & disown
   ```

<h2><sub><img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Travel%20and%20places/Rocket.png" alt="Rocket" width="25" height="25" /></sub> Roadmap</h2>

- [x] App Launcher
- [x] Bluetooth Manager
- [x] Calculator
- [x] Calendar
- [x] Color Picker
- [x] Customizable UI
- [x] Dashboard
- [x] Dock
- [x] Emoji Picker
- [x] Kanban Board
- [x] Notifications
- [x] OCR
- [x] Full Gui Config
- [x] Better Desktop Widgets
- [x] Customizable Widgets and Bar
- [x] Gui Updater and update notifier
- [x] Pins
- [x] Power Manager
- [x] Power Menu
- [x] Screen Recorder
- [x] Screenshot
- [x] Settings
- [x] System Tray
- [x] Terminal
- [x] Tmux Session Manager
- [x] Vertical Layout
- [x] Wallpaper Selector
- [x] Workspaces Overview
- [ ] Clipboard Manager
- [ ] Multi-monitor support
- [ ] Multimodal AI Assistant
- [ ] Network Manager
- [ ] OTP Manager

# Contibutors
<a href="https://github.com/tr1xem/hyprfabricated/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=tr1xem/hyprfabricated" />
</a>

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=tr1xem/hyprfabricated&type=Date)](https://star-history.com/#tr1xem/hyprfabricated&Date)



