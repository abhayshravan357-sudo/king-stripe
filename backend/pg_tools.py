"""Translate SQLAlchemy/libpq URLs into libpq environment variables without argv leaks."""
import os
from urllib.parse import parse_qs, unquote, urlsplit


def libpq_env(database_url: str, base=None):
    parsed = urlsplit(database_url.replace("postgresql+psycopg://", "postgresql://", 1))
    if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname or not parsed.path.strip("/"):
        raise ValueError("A PostgreSQL URL with host and database is required")
    env = dict(os.environ if base is None else base)
    env["PGHOST"] = parsed.hostname
    env["PGPORT"] = str(parsed.port or 5432)
    env["PGDATABASE"] = unquote(parsed.path.lstrip("/"))
    if parsed.username:
        env["PGUSER"] = unquote(parsed.username)
    if parsed.password is not None:
        env["PGPASSWORD"] = unquote(parsed.password)
    query = parse_qs(parsed.query)
    if query.get("sslmode"):
        env["PGSSLMODE"] = query["sslmode"][0]
    return env


def connection_identity(database_url: str):
    parsed = urlsplit(database_url.replace("postgresql+psycopg://", "postgresql://", 1))
    return (parsed.hostname, parsed.port or 5432, unquote(parsed.path.lstrip("/")))
