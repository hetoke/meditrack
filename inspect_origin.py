from sqlalchemy import text, create_engine

from db.session import get_session
from db.models import HoSo

engine = create_engine("sqlite:///clinic.db")
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE HoSo ADD COLUMN GivenName TEXT"))
    conn.commit()

print("GivenName column added.")