#!/bin/bash

# Check if XDG_VIDEOS_DIR is not set
if [ -z "$XDG_VIDEOS_DIR" ]; then
  XDG_VIDEOS_DIR="$HOME/Videos"
fi

# Directorio donde se guardarán las grabaciones
SAVE_DIR="$XDG_VIDEOS_DIR/Recordings"
mkdir -p "$SAVE_DIR"

# If gpu-screen-recorder is already running, send SIGINT to stop it properly
if pgrep -f "gpu-screen-recorder" >/dev/null; then
  pkill -SIGINT -f "gpu-screen-recorder"

  # Espera un momento para asegurarse de que la grabación se haya detenido y el archivo esté listo
  sleep 1

  # Obtiene el último archivo grabado
  LAST_VIDEO=$(ls -t "$SAVE_DIR"/*.mp4 2>/dev/null | head -n 1)

  # Notificación con acciones: "View" abre el archivo, "Open folder" abre la carpeta
  ACTION=$(notify-send -a "Hyprfabricated" "⬜ Recording stopped" \
    -A "view=View" -A "open=Open folder")

  if [ "$ACTION" = "view" ] && [ -n "$LAST_VIDEO" ]; then
    xdg-open "$LAST_VIDEO"
  elif [ "$ACTION" = "open" ]; then
    xdg-open "$SAVE_DIR"
  fi
  exit 0
fi

# Output file name for the new recording
OUTPUT_FILE="$SAVE_DIR/$(date +%Y-%m-%d-%H-%M-%S).mp4"

# Start recording
notify-send -a "Hyprfabricated" "🔴 Recording started"
gpu-screen-recorder -w screen -ac opus -cr full -a default_output -f 60  -o "$OUTPUT_FILE"
