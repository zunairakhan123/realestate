import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLEnum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.customers.models import Customer
    from app.properties.models import Property

class LeadStatus(str, enum.Enum):
    new = "new"
    qualified = "qualified"
    viewing = "viewing"
    closed = "closed"

class Lead(Base):
    __tablename__ = "leads"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    property_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("properties.id", ondelete="RESTRICT"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    
    status: Mapped[LeadStatus] = mapped_column(SQLEnum(LeadStatus), default=LeadStatus.new, index=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    customer: Mapped["Customer"] = relationship("Customer", back_populates="leads")
    property: Mapped["Property"] = relationship("Property", back_populates="leads")