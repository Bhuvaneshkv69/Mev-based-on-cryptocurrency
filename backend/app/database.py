"""Database Connection and Session Management Module.

Provides the SQLAlchemy 2.x declarative Base, connection engine,
session factory, FastAPI dependency for database sessions, and a
lightweight connectivity readiness check.
"""

import logging
from typing import Generator, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

logger = logging.getLogger("mevshield.database")

# ------------------------------------------------------------------------------
# 1. Declarative Base
# ------------------------------------------------------------------------------
# Base class for all SQLAlchemy ORM models in MEVShield.
Base = declarative_base()

# ------------------------------------------------------------------------------
# 2. Database Engine & Connection Pooling
# ------------------------------------------------------------------------------
# create_engine initializes the pool definition lazily. No actual network
# socket or PostgreSQL connection is opened until a session checks out a connection.
# pool_pre_ping=True emits a lightweight ping before checkout to ensure the
# connection is still alive, preventing stale-connection errors.
_database_url = settings.sqlalchemy_database_url
_engine_options = {"echo": False}
if _database_url.startswith("sqlite"):
    # SQLite is useful for isolated tests and lightweight local demonstrations.
    # PostgreSQL remains the recommended persistent application database.
    from sqlalchemy.pool import StaticPool
    _engine_options["connect_args"] = {"check_same_thread": False}
    if ":memory:" in _database_url or _database_url.rstrip("/") == "sqlite:":
        _engine_options["poolclass"] = StaticPool
else:
    _engine_options.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_pre_ping": True,
    })

engine = create_engine(_database_url, **_engine_options)

# ------------------------------------------------------------------------------
# 3. Session Factory
# ------------------------------------------------------------------------------
# Standard session factory with explicit transaction boundaries (autocommit=False).
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ------------------------------------------------------------------------------
# 4. Dependency Injection for Route Handlers
# ------------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding an isolated SQLAlchemy database session.

    Lifecycle:
    1. A new Session is created for the requesting HTTP thread.
    2. The route handler performs database operations.
    3. If an uncaught exception occurs, the session rolls back pending changes.
    4. The session is reliably closed in the finally block, returning the
       underlying connection back to the connection pool.

    Usage in routes:
        @router.get("/example")
        def route(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception as exc:
        logger.error("Session transaction error, rolling back: %s", exc)
        db.rollback()
        raise
    finally:
        db.close()


# ------------------------------------------------------------------------------
# 5. Database Readiness Verification
# ------------------------------------------------------------------------------
def check_db_connectivity() -> Tuple[bool, str]:
    """Test live connectivity to the PostgreSQL database with a simple ping.

    Returns:
        (True, "Database reachable") if connection succeeds,
        (False, error_description) if database is unreachable or offline.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "Database reachable and operational"
    except SQLAlchemyError as err:
        logger.warning("Database connectivity check failed: %s", err)
        return False, f"Database unreachable: {err.__class__.__name__}"
    except Exception as err:
        logger.warning("Unexpected error during database check: %s", err)
        return False, f"Unexpected database error: {err.__class__.__name__}"
