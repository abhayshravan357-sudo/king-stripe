import os
import subprocess
import sys
from pathlib import Path

from pg_tools import connection_identity, libpq_env

if len(sys.argv) != 2:
    raise SystemExit("Backup path is required")
backup = Path(sys.argv[1]).resolve()
target_url = os.environ.get("RESTORE_TARGET_DATABASE_URL", "")
source_url = os.environ.get("DATABASE_URL", "")
try:
    env = libpq_env(target_url)
    target_identity = connection_identity(target_url)
    if source_url and target_identity == connection_identity(source_url):
        raise SystemExit("Restore target matches DATABASE_URL; choose a separate recovery database")
except ValueError:
    raise SystemExit("RESTORE_TARGET_DATABASE_URL must be a PostgreSQL connection URL")

def run(args, *, capture=False):
    try:
        return subprocess.run(args, env=env, stdout=subprocess.PIPE if capture else None, stderr=subprocess.PIPE, check=False)
    except FileNotFoundError:
        raise SystemExit(f"Required PostgreSQL client command is missing: {args[0]}")

archive = run(["pg_restore", "--list", str(backup)], capture=True)
if archive.returncode:
    raise SystemExit("Backup is not a readable PostgreSQL custom-format archive")
probe = run(["psql", "--no-password", "-X", "-A", "-t", "-c", "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname NOT IN ('pg_catalog','information_schema') AND c.relkind IN ('r','p','v','m','f')"], capture=True)
if probe.returncode:
    raise SystemExit("Could not verify restore target; no restore was performed")
try:
    object_count = int(probe.stdout.decode().strip())
except ValueError:
    raise SystemExit("Could not verify restore target; no restore was performed")
if object_count:
    raise SystemExit("Restore refused: target database is not empty")
restored = run(["pg_restore", "--no-password", "--no-owner", "--no-privileges", "--dbname", env["PGDATABASE"], str(backup)])
if restored.returncode:
    raise SystemExit("Restore failed; inspect PostgreSQL logs without exposing connection details")
print("Restore complete; verify the restored database before switching application configuration.")
