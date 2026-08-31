import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent


def sqlite_url(filename: str) -> str:
    return f"sqlite:///{(PROJECT_ROOT / filename).as_posix()}"


DEV = sqlite_url("clinic.db")
TEST = sqlite_url("clinic_stress.db")
PROD = sqlite_url("clinic_prod.db")

# SQLite engine (change the connection string if needed)
engine = create_engine(DEV, echo=False)

from db.models import Base
Base.metadata.create_all(engine)

from sqlalchemy import text
with engine.begin() as conn:
    columns = {row[1] for row in conn.execute(text("PRAGMA table_info(chidinh)"))}
    if "SoNgay" not in columns:
        conn.execute(text("ALTER TABLE chidinh ADD COLUMN SoNgay INTEGER NOT NULL DEFAULT 1"))
        if "KhongTinhTien" in columns:
            conn.execute(text("UPDATE chidinh SET SoNgay = 0 WHERE KhongTinhTien = 1"))
            conn.execute(text("ALTER TABLE chidinh DROP COLUMN KhongTinhTien"))

# Session factory
SessionLocal = sessionmaker(bind=engine)

# Helper function to create a session
def get_session():
    return SessionLocal()
