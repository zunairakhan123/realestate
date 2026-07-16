from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import get_settings

# Load application configuration (cached after the first call).
settings = get_settings()

# Create a single asynchronous database engine shared across the application.
engine = create_async_engine(settings.database_url, echo=settings.debug)

# Factory for creating independent database sessions for each request.
# expire_on_commit=False keeps objects usable after a transaction is committed.
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_db():
    """
    Provide a database session for a request.

    A new session is created for each request and automatically closed
    when the request completes, ensuring proper resource cleanup.
    """
    async with AsyncSessionLocal() as session:
        yield session