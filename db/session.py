from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def sqlite_url(filename: str) -> str:
    return f"sqlite:///{(PROJECT_ROOT / filename).as_posix()}"


DEV = sqlite_url("clinic.db")
TEST = sqlite_url("clinic_stress.db")
PROD = sqlite_url("clinic_prod.db")

# SQLite engine (change the connection string if needed)
engine = create_engine(PROD, echo=False)

# Session factory
SessionLocal = sessionmaker(bind=engine)

# Helper function to create a session
def get_session():
    return SessionLocal()
