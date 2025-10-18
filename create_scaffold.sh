#!/usr/bin/env bash
set -e
# Wrapper: meghívja a tényleges scaffold scriptet (állítsd be a pontos verziónevet ha kell)
TARGET="./tools/create_scaffold_Version4.sh"

if [ ! -f "$TARGET" ]; then
  echo "Error: target scaffold script not found: $TARGET"
  exit 2
fi

chmod +x "$TARGET"
exec "$TARGET" "$@"
