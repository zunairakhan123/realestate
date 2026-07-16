import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, Integer, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.leads.models import Lead

class PropertyStatus(str, enum.Enum):
    available = "available"
    under_contract = "under_contract"
    sold = "sold"
    off_market = "off_market"

class Property(Base):
    __tablename__ = "properties"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    address: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False, index=True)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    bedrooms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[PropertyStatus] = mapped_column(Enum(PropertyStatus), default=PropertyStatus.available, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="property", passive_deletes="all")