# database.py
# This file sets up the SQLAlchemy ORM for SQLite and defines the WaterUsage model.

from sqlalchemy import create_engine, Column, Integer, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Define the SQLite database URL.
# water_usage.db will be created in the same directory as this script.
DATABASE_URL = "sqlite:///./water_usage.db"

# Create the SQLAlchemy engine.
# connect_args={"check_same_thread": False} is needed for SQLite with FastAPI
# because SQLAlchemy expects to access the database from a single thread by default,
# but FastAPI might use different threads for requests.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a declarative base for our models.
Base = declarative_base()

# Define the WaterUsage model.
# This table will store the accumulated water usage readings over time.
class WaterUsage(Base):
    __tablename__ = "water_usage"

    id = Column(Integer, primary_key=True, index=True)
    # Timestamp when the reading was taken.
    timestamp = Column(DateTime, default=datetime.now)
    # The accumulated water usage value from the OPC server.
    accumulated_value = Column(Float)

# Create the database tables.
# This function will be called during application startup to ensure the database
# schema is up-to-date.
def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

# Create a session local class.
# Each instance of SessionLocal will be a database session.
# We will use this to create new sessions for each database operation.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get a database session.
# This function will be used by FastAPI endpoints to get a database session,
# ensuring it's properly closed after the request.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

