import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, Integer, Enum as SQLEnum, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from typing import TYPE_CHECKING, Optional
from app.core.enums import PropertyType

if TYPE_CHECKING:
    from app.leads.models import Lead
    from app.auth.models import User

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
    
    property_type: Mapped[PropertyType] = mapped_column(SQLEnum(PropertyType), nullable=False, default=PropertyType.HOME)
    
    # agent_id is now a UUID matching users.id
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    
    status: Mapped[PropertyStatus] = mapped_column(SQLEnum(PropertyStatus), default=PropertyStatus.available, index=True)
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    agent: Mapped["User"] = relationship("User", foreign_keys=[agent_id])
    leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="property", passive_deletes="all")