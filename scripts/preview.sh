#!/usr/bin/env bash
# No database setup or public bind. Stop with Ctrl+C.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
if (( $# > 0 )); then
  echo 'Usage: bash scripts/preview.sh (fixed local address 127.0.0.1:8000)' >&2
  exit 2
fi
export DJANGO_SETTINGS_MODULE=config.settings.preview
exec uv run --locked gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 --workers 1 --threads 2 --timeout 30 --access-logfile /dev/null
