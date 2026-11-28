import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pg_tools import libpq_env

url = os.environ.get("DATABASE_URL", "")
try:
    env = libpq_env(url)
except ValueError:
    raise SystemExit("Set DATABASE_URL to a PostgreSQL connection URL")
folder = Path(__file__).resolve().parent / "backups"
folder.mkdir(mode=0o700, exist_ok=True)
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
destination = folder / f"kingstripe-{stamp}.dump"
fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
try:
    with os.fdopen(fd, "wb") as output:
        result = subprocess.run(["pg_dump", "--no-password", "--format=custom"], env=env, stdout=output, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        destination.unlink(missing_ok=True)
        raise SystemExit("pg_dump failed; check PostgreSQL client installation and database access")
except FileNotFoundError:
    destination.unlink(missing_ok=True)
    raise SystemExit("pg_dump is not installed")
print(f"Created {destination.relative_to(Path(__file__).resolve().parent)}")
