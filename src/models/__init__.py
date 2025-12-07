"""SQLAlchemy models for Smart Expense Analyzer"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
import os
from typing import Optional, TYPE_CHECKING

# For Google Cloud SQL connection
if TYPE_CHECKING:
    from google.cloud.sql.connector import Connector  # type: ignore[import]

try:
    from google.cloud.sql.connector import Connector
    import pg8000  # required driver for PostgreSQL
    CLOUD_SQL_AVAILABLE = True
except ImportError:
    CLOUD_SQL_AVAILABLE = False
    Connector = None  # Type stub for when not available

Base = declarative_base()

# Global session factory
_session_factory: Optional[sessionmaker] = None
_engine = None
_connector: Optional["Connector"] = None  # Singleton connector - use string for forward reference


def get_cloud_sql_connection():
    """Create connection to Cloud SQL using Python Connector (singleton pattern)"""
    global _connector

    if not CLOUD_SQL_AVAILABLE:
        raise ImportError(
            "cloud-sql-python-connector is not installed. "
            "Install it with: pip install 'cloud-sql-python-connector[pg8000]'"
        )

    # Create connector once and reuse (important for Cloud Run)
    if _connector is None:
        # Connector was already imported in the try block above
        _connector = Connector()

    def getconn():
        conn = _connector.connect(
            os.getenv("CLOUD_SQL_CONNECTION_NAME"),  # e.g., "project:region:instance"
            "pg8000",
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
        )
        return conn

    return getconn


def init_db(connection_string: Optional[str] = None, use_cloud_sql: bool = False):
    """
    Initialize database connection.

    Args:
        connection_string: PostgreSQL connection string (for local/dev)
        use_cloud_sql: If True, use Cloud SQL connector instead of connection string
    """
    global _engine, _session_factory

    if use_cloud_sql:
        if not CLOUD_SQL_AVAILABLE:
            raise ImportError(
                "cloud-sql-python-connector is not installed. Install it with:\n"
                "  pip install 'cloud-sql-python-connector[pg8000]'"
            )
        # Use Cloud SQL Python Connector
        getconn = get_cloud_sql_connection()
        _engine = create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,         # Connection pool for Cloud Run
            max_overflow=10,
            pool_recycle=3600,   # Recycle connections after 1 hour
        )
    elif connection_string:
        # Use standard connection string (local/dev)
        _engine = create_engine(
            connection_string,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,
            max_overflow=10,
        )
    else:
        raise ValueError("Either connection_string or use_cloud_sql must be provided")

    # Create session factory
    _session_factory = sessionmaker(bind=_engine)

    # Create tables
    Base.metadata.create_all(_engine)

    return _engine


def get_session():
    """Get database session"""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _session_factory()


def get_scoped_session():
    """Get scoped session for thread-safe operations"""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return scoped_session(sessionmaker(bind=_engine))


# Import models to register them with Base
from src.models.user import User
from src.models.account import Account
from src.models.transaction import Transaction

__all__ = [
    "Base",
    "User",
    "Account",
    "Transaction",
    "init_db",
    "get_session",
    "get_scoped_session",
    "CLOUD_SQL_AVAILABLE",
]
