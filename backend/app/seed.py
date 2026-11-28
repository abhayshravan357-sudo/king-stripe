from sqlalchemy.orm import Session
from app.db import engine
from app.main import seed_catalog

with Session(engine) as db:
    seed_catalog(db)
