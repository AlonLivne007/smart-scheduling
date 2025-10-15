"""
Database engine and session configuration.

This module sets up the connection to the PostgreSQL database using SQLAlchemy.
It defines the core components required to interact with the database:
    - Engine: manages the actual connection pool.
    - SessionLocal: creates session objects for performing queries and transactions.
    - Base: declarative base class for all ORM models.

"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os


# -------------------------------------------------------------
# 1. Load environment variables
# -------------------------------------------------------------
# The .env file stores sensitive configuration values such as
# database credentials and connection URLs.
load_dotenv()


# -------------------------------------------------------------
# 2. Define the database connection URL
# -------------------------------------------------------------
# The DATABASE_URL environment variable must follow this format:
# postgresql://<username>:<password>@<host>:<port>/<database>
# The default value below is used if the environment variable is missing.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/scheduler_db"
)


# -------------------------------------------------------------
# 3. Create the SQLAlchemy engine
# -------------------------------------------------------------
# The engine is responsible for managing the connection pool and
# executing SQL commands behind the scenes.
engine = create_engine(DATABASE_URL)


# -------------------------------------------------------------
# 4. Configure a Session class factory
# -------------------------------------------------------------
# Each database interaction in the app uses a session created from
# this factory. It handles transactions and persistence.
#
# - autocommit=False ensures explicit commits.
# - autoflush=False prevents automatic flush before queries.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# -------------------------------------------------------------
# 5. Define the base class for ORM models
# -------------------------------------------------------------
# All ORM models (User, Rank, Role, etc.) will inherit from this Base class.
Base = declarative_base()


# -------------------------------------------------------------
# 6. Database session dependency for FastAPI
# -------------------------------------------------------------
def get_db():
    """
    Provides a database session for FastAPI routes.

    This function is used as a dependency in API routes.
    It ensures that the session is created for the request
    and properly closed after the request completes.

    Yields:
        db (Session): A SQLAlchemy session connected to the database.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
