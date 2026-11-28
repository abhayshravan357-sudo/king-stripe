import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESTORE = ROOT / "backend" / "restore.sh"


def setup_tools(tmp_path, monkeypatch):
    bindir = tmp_path / "bin"; bindir.mkdir()
    log = tmp_path / "calls.log"
    (bindir / "pg_restore").write_text("""#!/bin/sh
printf 'pg_restore %s\\n' "$*" >> "$MOCK_LOG"
        if [ "$PGPASSWORD" = "testpw" ]; then echo target_credentials_in_environment >> "$MOCK_LOG"; fi
case "$*" in *--list*) echo archive; exit 0;; esac
exit 0
""")
    (bindir / "psql").write_text("""#!/bin/sh
printf 'psql %s\\n' "$*" >> "$MOCK_LOG"
        if [ "$PGPASSWORD" = "testpw" ]; then echo target_credentials_in_environment >> "$MOCK_LOG"; fi
echo "${MOCK_TABLE_COUNT:-0}"
""")
    for tool in bindir.iterdir(): tool.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    monkeypatch.setenv("MOCK_LOG", str(log))
    return log


def run_restore(tmp_path, monkeypatch, table_count="0", target="postgresql://restore:testpw@mock-host:5432/recovery"):
    log = setup_tools(tmp_path, monkeypatch)
    backup = tmp_path / "backup.dump"; backup.write_bytes(b"synthetic archive")
    monkeypatch.setenv("MOCK_TABLE_COUNT", table_count)
    monkeypatch.delenv("RESTORE_TARGET_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://app:srcpw@source-host:5432/production")
    return subprocess.run(["bash", str(RESTORE), str(backup)], input=f"{target}\nRESTORE\n", text=True, capture_output=True), log


def test_restore_redacts_url_and_keeps_credentials_out_of_process_arguments(tmp_path, monkeypatch):
    result, log = run_restore(tmp_path, monkeypatch)
    assert result.returncode == 0
    assert "testpw" not in result.stdout + result.stderr
    assert "target_credentials_in_environment" in log.read_text()
    assert "testpw" not in log.read_text()
    assert "[redacted]" in result.stdout
    assert "Restore complete" in result.stdout


def test_restore_refuses_nonempty_target_without_running_restore(tmp_path, monkeypatch):
    result, log = run_restore(tmp_path, monkeypatch, table_count="2")
    assert result.returncode != 0
    assert "Restore refused: target database is not empty" in result.stderr
    assert "pg_restore --list" in log.read_text()
    assert "--dbname" not in log.read_text()
    assert "testpw" not in result.stdout + result.stderr


def test_restore_refuses_active_database_target_before_inspecting_backup(tmp_path, monkeypatch):
    log = setup_tools(tmp_path, monkeypatch)
    backup = tmp_path / "backup.dump"; backup.write_bytes(b"synthetic archive")
    active = "postgresql://app:srcpw@source-host:5432/production"
    monkeypatch.delenv("RESTORE_TARGET_DATABASE_URL", raising=False)
    monkeypatch.setenv("DATABASE_URL", active)
    result = subprocess.run(["bash", str(RESTORE), str(backup)], input=f"{active}\nRESTORE\n", text=True, capture_output=True)
    assert result.returncode != 0
    assert "Restore target matches DATABASE_URL" in result.stderr
    assert not log.exists()
    assert "srcpw" not in result.stdout + result.stderr
