"""Apply 3 new filters and add viewing and offered to leadstatus enum

Revision ID: 2a47c19fb4e8
Revises: efb53813e652
Create Date: 2026-07-16 11:43:35.975489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a47c19fb4e8'
down_revision: Union[str, Sequence[str], None] = 'efb53813e652'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adding to an ENUM type in PostgreSQL requires raw DDL execution.
    # We use 'IF NOT EXISTS' if your Postgres version supports it, or standard ADD VALUE.
    # Note: Alembic cannot easily autogenerate Enum additions, hence the manual script.
    
    # Adding 'viewing'
    op.execute("ALTER TYPE leadstatus ADD VALUE 'viewing'")
    
    # Adding 'offered'
    op.execute("ALTER TYPE leadstatus ADD VALUE 'offered'")

def downgrade() -> None:
    # PostgreSQL does not natively support dropping a single value from an ENUM.
    # Doing so safely requires creating a new type, migrating data, and dropping the old type.
    # In CI/CD data pipelines, Enum additions are typically treated as irreversible (forward-only).
    pass