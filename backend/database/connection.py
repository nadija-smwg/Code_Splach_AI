from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Uses environment variable if set in production, otherwise defaults to your local database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/clearancex")

# Create the core engine that talks to PostgreSQL
engine = create_engine(DATABASE_URL)

# Create a session factory to spawn safe database sessions
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    """Dependency injection to get a database session and safely close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Binds the Python models to the database."""
    from .models import Base
    Base.metadata.create_all(bind=engine)
