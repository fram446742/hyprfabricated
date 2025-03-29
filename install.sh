#!/bin/bash

set -e  # Exit immediately if a command fails
set -u  # Treat unset variables as errors
set -o pipefail  # Prevent errors in a pipeline from being masked

REPO_URL="https://github.com/fram446742/hyprfabricated.git"
INSTALL_DIR="$HOME/.config/hyprfabricated"
PACKAGES=(
    brightnessctl
    cava
    fabric-cli-git
    gnome-bluetooth-3.0
    gobject-introspection
    gpu-screen-recorder
    grimblast
    hypridle-git
    hyprlock-git
    hyprpicker-git
    hyprsunset-git
    imagemagick
    libnotify
    matugen-bin
    noto-fonts-emoji
    playerctl
    python-fabric-git
    python-ijson
    python-pillow
    python-psutil
    python-requests
    python-setproctitle
    python-toml
    python-watchdog
    python-numpy
    swappy
    swww-git
    uwsm
    wl-clipboard
    wlinhibit
    tesseract
    plasma-browser-integration
    cantarell-fonts
    ttf-jost
    unzip
    tmux
)

PYTHON_PACKAGES=(
    ijson 
    pillow 
    psutil
    requests 
    setproctitle 
    toml 
    watchdog
    numpy
)

# Prevent running as root
if [ "$(id -u)" -eq 0 ]; then
    echo "Please do not run this script as root."
    exit 1
fi

aur_helper="yay"

PARU_EXISTS_INITIALLY=1

# Check if yay exists, otherwise use paru
if command -v yay &>/dev/null; then
    aur_helper="yay"
elif ! command -v paru &>/dev/null; then
    PARU_EXISTS_INITIALLY=0
    echo "Installing paru-bin..."
    tmpdir=$(mktemp -d)
    git clone --depth=1 https://aur.archlinux.org/paru-bin.git "$tmpdir/paru-bin"
    sudo pacman -S --needed --noconfirm base-devel
    (cd "$tmpdir/paru-bin" && makepkg -si --noconfirm)
    rm -rf "$tmpdir"
fi

# Clone or update the repository
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating hyprfabricated..."
    git -C "$INSTALL_DIR" pull
else
    echo "Cloning hyprfabricated..."
    git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
fi

# Install required packages using the detected AUR helper (only if missing)
echo "Installing required packages..."
$aur_helper -Syy --needed --devel --noconfirm "${PACKAGES[@]}" || true

echo "Installing gray-git..."
yes | $aur_helper -Syy --needed --devel --noconfirm gray-git || true

echo "Installing required fonts..."

FONT_URL="https://github.com/zed-industries/zed-fonts/releases/download/1.2.0/zed-sans-1.2.0.zip"
FONT_DIR="$HOME/.fonts/zed-sans"
TEMP_ZIP="/tmp/zed-sans-1.2.0.zip"

# Check if fonts are already installed
if [ ! -d "$FONT_DIR" ]; then
    echo "Downloading fonts from $FONT_URL..."
    curl -L -o "$TEMP_ZIP" "$FONT_URL"

    echo "Extracting fonts to $FONT_DIR..."
    mkdir -p "$FONT_DIR"
    unzip -o "$TEMP_ZIP" -d "$FONT_DIR"

    echo "Cleaning up..."
    rm "$TEMP_ZIP"
else
    echo "Fonts are already installed. Skipping download and extraction."
fi

# Copy local fonts if not already present
if [ ! -d "$HOME/.fonts/tabler-icons" ]; then
    echo "Copying local fonts to $HOME/.fonts/tabler-icons..."
    mkdir -p "$HOME/.fonts/tabler-icons"
    cp -r "$INSTALL_DIR/assets/fonts/"* "$HOME/.fonts/tabler-icons"
else
    echo "Local fonts are already installed. Skipping copy."
fi

# # Create a .venv directory if it doesn't exist
# if [ ! -d "$INSTALL_DIR/.venv" ]; then
#     echo "Creating virtual environment..."
#     python3 -m venv "$INSTALL_DIR/.venv"
# fi

# # Activate the virtual environment
# source "$INSTALL_DIR/.venv/bin/activate"

# # Upgrade pip and install required Python packages
# pip install --upgrade pip
# # Install Python packages
# pip install --upgrade "${PYTHON_PACKAGES[@]}"
# Install fabric from GitHub

# This is a workaround for the issue with the latest version of fabric
# pip install git+https://github.com/Fabric-Development/fabric.git --break-system-packages

# Check installed Python packages
for package in "${PYTHON_PACKAGES[@]}"; do
    if ! pip show "$package" &>/dev/null; then
        echo "Failed to install $package. Exiting."
        exit 1
    fi
done

python "$INSTALL_DIR/config/config.py"


# echo "Starting hyprfabricated..."
# killall hyprfabricated 2>/dev/null || true
# uwsm app -- python "$INSTALL_DIR/main.py" > "$INSTALL_DIR/stdout.log" 2> "$INSTALL_DIR/stderr.log" & disown

echo "Starting hyprfabricated..."

# Asegúrate de activar el entorno virtual antes de ejecutar main.py
killall hyprfabricated 2>/dev/null || true
# app2unit -t service -a hyprfabricated -d "Hyprfabricated Service" -- bash -c "source $INSTALL_DIR/.venv/bin/activate && python $INSTALL_DIR/main.py > $INSTALL_DIR/stdout.log 2> $INSTALL_DIR/stderr.log & disown"
app2unit -t service -a hyprfabricated -d "Hyprfabricated Service" -- bash -c "python $INSTALL_DIR/main.py > $INSTALL_DIR/stdout.log 2> $INSTALL_DIR/stderr.log & disown"

# echo "Enabling and starting the hyprfabricated service..."
# systemctl --user enable hyprfabricated.service
# systemctl --user start hyprfabricated.service


echo "Doing Fallback Image..."
cp "$INSTALL_DIR/assets/wallpapers_example/example-1.jpg" ~/.current.wall

if [ $PARU_EXISTS_INITIALLY -eq 0 ]; then
    echo "The script installed paru-bin. Do you want to keep it? (y/n)"
    read -r choice
    if [[ "$choice" =~ ^[Nn]$ ]]; then
        echo "Uninstalling paru-bin..."
        sudo pacman -Rns --noconfirm paru-bin
    else
        echo "Keeping paru-bin."
    fi
fi

echo "If you see a transparent bar change the wallpaper from the notch"
echo "Backup your hypridle and hyprlock config before accepting in config"

echo "Installation complete."
