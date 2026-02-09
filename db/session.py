from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLite engine (change the connection string if needed)
engine = create_engine("sqlite:///clinic.db", echo=False)

# Session factory
SessionLocal = sessionmaker(bind=engine)

# Helper function to create a session
def get_session():
    return SessionLocal()