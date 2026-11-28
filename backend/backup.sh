#!/bin/sh
set -eu
exec python "$(dirname "$0")/backup_database.py"
