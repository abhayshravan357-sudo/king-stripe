# Backup and recovery

`backend/backup.sh` creates a PostgreSQL custom-format dump under `backend/backups/`. Set `DATABASE_URL` in the process environment and keep database credentials out of command-line arguments. Copy backup files to encrypted off-machine storage on an operator-defined schedule.

Restore with `backend/restore.sh BACKUP.dump`. The script prompts for the target database URL without echoing it, refuses the active database and non-empty targets, and requires typing `RESTORE`. Confirm application behavior before switching the live connection. Mocked safety tests pass; a PostgreSQL restore drill has not been run. Backup retention and recovery objectives require operator decisions.
