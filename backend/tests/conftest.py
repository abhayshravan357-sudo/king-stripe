import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///./test-unused.db"
os.environ["ENVIRONMENT"] = "test"
os.environ["PAYMENT_PROVIDER"] = "disabled"
os.environ["PAYMENT_MODE"] = "test"
os.environ["ALLOW_LIVE_PAYMENTS"] = "false"
os.environ["RAZORPAY_KEY_ID"] = ""
os.environ["RAZORPAY_KEY_SECRET"] = ""
os.environ["RAZORPAY_WEBHOOK_SECRET"] = ""
os.environ["INVENTORY_MODE"] = "unlimited"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.db import Base
from app.main import seed_catalog


@pytest.fixture
def db():
    database_url = os.environ.get("TEST_DATABASE_URL")
    if database_url:
        test_database = make_url(database_url)
        if "test" not in (test_database.database or "").lower():
            raise ValueError("TEST_DATABASE_URL database name must contain 'test'; refusing to run destructive fixture against an unlabelled database")
        engine = create_engine(database_url, pool_pre_ping=True)
    else:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        seed_catalog(session)
        yield session
    Base.metadata.drop_all(engine)
