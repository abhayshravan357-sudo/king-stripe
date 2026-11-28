#!/bin/bash
set -eu
if [ "$#" -ne 1 ]; then echo "Usage: $0 BACKUP.dump" >&2; exit 2; fi
if [ -z "${RESTORE_TARGET_DATABASE_URL:-}" ]; then
  read -r -s -p "Recovery target PostgreSQL URL (input hidden): " RESTORE_TARGET_DATABASE_URL
  printf '\n'
fi
export RESTORE_TARGET_DATABASE_URL
backup=$1
[ -f "$backup" ] || { echo "Backup file not found" >&2; exit 2; }
target=$(RESTORE_TARGET_DATABASE_URL="$RESTORE_TARGET_DATABASE_URL" python "$(dirname "$0")/redact_database_url.py")
echo "Restore will target: $target"
echo "The target must be a separate, empty database. Type RESTORE to continue:"
read answer
[ "$answer" = RESTORE ] || { echo "Cancelled"; exit 1; }
exec python "$(dirname "$0")/restore_database.py" "$backup"
