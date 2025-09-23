"""Database configuration and setup."""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator, Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, delete, and_

from ..models.session import Base, Session, SessionState, CurrentStep
from ..utils.logging_config import get_logger
from .config import settings


logger = get_logger("database")


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, database_url: str = None):
        """Initialize database manager.

        Args:
            database_url: Override default database URL from settings
        """
        self.database_url = database_url or settings.database_url
        self.engine = None
        self.SessionLocal = None

    async def initialize(self):
        """Initialize database engine and create tables."""
        try:
            # Create async engine
            self.engine = create_async_engine(
                self.database_url,
                echo=settings.debug,
                future=True,
                pool_pre_ping=True,
            )

            # Create session factory
            self.SessionLocal = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with proper cleanup."""
        if not self.SessionLocal:
            await self.initialize()

        async with self.SessionLocal() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Database session error: {str(e)}")
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async for session in db_manager.get_session():
        yield session


class SessionRepository:
    """Repository for session database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        user_id: Optional[str] = None,
        initial_data: dict = None
    ) -> Session:
        """Create a new session.

        Args:
            user_id: Optional user identifier
            initial_data: Initial session data

        Returns:
            Created session object
        """
        session_id = uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.session_timeout_minutes)

        session = Session(
            session_id=str(session_id),  # Convert to string for SQLite compatibility
            user_id=user_id,
            state=SessionState.INITIALIZED,
            current_step=CurrentStep.START,
            master_career_database=json.dumps(initial_data or {}),
            command_history=json.dumps([]),
            metadata=json.dumps({}),
            expires_at=expires_at
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Created session {session_id} for user {user_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session object or None if not found
        """
        query = select(Session).where(Session.session_id == session_id)
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if session and session.is_expired:
            logger.warning(f"Session {session_id} has expired")
            return None

        return session

    async def update_session(
        self,
        session_id: str,
        **updates
    ) -> Optional[Session]:
        """Update session data.

        Args:
            session_id: Session identifier
            **updates: Fields to update

        Returns:
            Updated session or None if not found
        """
        # Convert dict fields to JSON strings if provided
        json_fields = ['master_career_database', 'command_history', 'metadata']
        for field in json_fields:
            if field in updates and isinstance(updates[field], dict):
                updates[field] = json.dumps(updates[field])
            elif field in updates and isinstance(updates[field], list):
                updates[field] = json.dumps(updates[field])

        # Add updated_at timestamp
        updates['updated_at'] = datetime.now(timezone.utc)

        query = (
            update(Session)
            .where(Session.session_id == session_id)
            .values(**updates)
        )

        result = await self.db.execute(query)
        await self.db.commit()

        if result.rowcount > 0:
            # Return updated session
            return await self.get_session(session_id)

        return None

    async def delete_session(self, session_id: str) -> bool:
        """Delete session by ID.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted, False if not found
        """
        query = delete(Session).where(Session.session_id == session_id)
        result = await self.db.execute(query)
        await self.db.commit()

        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted session {session_id}")

        return deleted

    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        state: Optional[SessionState] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[Session]:
        """List sessions with optional filtering.

        Args:
            user_id: Filter by user ID
            state: Filter by session state
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of session objects
        """
        query = select(Session)

        # Apply filters
        conditions = []
        if user_id:
            conditions.append(Session.user_id == user_id)
        if state:
            conditions.append(Session.state == state)

        if conditions:
            query = query.where(and_(*conditions))

        # Add ordering and pagination
        query = (
            query
            .order_by(Session.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        current_time = datetime.now(timezone.utc)
        query = delete(Session).where(Session.expires_at < current_time)

        result = await self.db.execute(query)
        await self.db.commit()

        count = result.rowcount
        if count > 0:
            logger.info(f"Cleaned up {count} expired sessions")

        return count

    async def extend_session(self, session_id: str, minutes: int = None) -> Optional[Session]:
        """Extend session expiration time.

        Args:
            session_id: Session identifier
            minutes: Minutes to extend (default: session_timeout_minutes)

        Returns:
            Updated session or None if not found
        """
        extension_minutes = minutes or settings.session_timeout_minutes
        new_expiry = datetime.now(timezone.utc) + timedelta(minutes=extension_minutes)

        return await self.update_session(session_id, expires_at=new_expiry)
