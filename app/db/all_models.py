from app.db.base import Base

# Import all ORM models so SQLAlchemy registers them with the shared Base
# metadata. This ensures tools like Alembic can discover every table.
from app.customers.models import Customer
from app.properties.models import Property
from app.leads.models import Lead
from app.auth.models import User