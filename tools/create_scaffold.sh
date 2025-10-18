#!/usr/bin/env bash
set -e

# This wrapper tries to find the actual scaffold generator script in likely locations
# and executes it. It makes the target executable before running.
SCRIPT_DIR="$(cd "$(dirname ""${BASH_SOURCE[0]}"")" && pwd)"

CANDIDATES=(
  "$SCRIPT_DIR/create_scaffold_Version4.sh"
  "$SCRIPT_DIR/create_scaffold.sh"
  "$SCRIPT_DIR/../create_scaffold.sh"
  "$SCRIPT_DIR/../create_scaffold_Version4.sh"
)

TARGET=""
for c in "${CANDIDATES[@]}"; do
  if [ -f "$c" ]; then
    TARGET="$c"
    break
  fi
done

if [ -z "$TARGET" ]; then
  echo "Error: scaffold script not found in expected locations:"
  for c in "${CANDIDATES[@]}"; do echo "  - $c"; done
  exit 2
fi

chmod +x "$TARGET"
exec "$TARGET" "$@"