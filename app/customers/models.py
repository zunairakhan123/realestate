import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from typing import TYPE_CHECKING

# Import only for type checking to avoid circular imports at runtime.
if TYPE_CHECKING:
    from app.leads.models import Lead


# Represents a customer in the database.
class Customer(Base):
    __tablename__ = "customers"

    # Primary key generated as a UUID to ensure global uniqueness.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Customer's full name.
    name: Mapped[str] = mapped_column(String, nullable=False)

    # Unique email address used to identify a customer.
    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False
    )

    # Optional contact number.
    phone: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    # Timestamp automatically set when the record is created.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Timestamp automatically updated whenever the record is modified.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # One customer can have multiple leads.
    # passive_deletes="all" lets PostgreSQL enforce delete rules directly.
    leads: Mapped[list["Lead"]] = relationship(
        "Lead",
        back_populates="customer",
        passive_deletes="all"
    )