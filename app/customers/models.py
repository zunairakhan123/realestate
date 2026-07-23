import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.leads.models import Lead
    from app.auth.models import User

class PaymentMethod(str, enum.Enum):
    CASH = "Cash"
    CHEQUE = "Cheque"

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign key referencing UUID-based user primary key
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    payment: Mapped[PaymentMethod] = mapped_column(SQLEnum(PaymentMethod), nullable=False, default=PaymentMethod.CASH)
    notification_preferences: Mapped[Optional[str]] = mapped_column(String, nullable=True, default="email")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", backref="customer", uselist=False)
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="customer", passive_deletes="all")