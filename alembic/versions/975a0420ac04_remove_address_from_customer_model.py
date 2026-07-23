"""remove address from customer model

Revision ID: 975a0420ac04
Revises: 107e66e8ace8
Create Date: 2026-07-23 15:20:29.303585

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '975a0420ac04'
down_revision: Union[str, Sequence[str], None] = '107e66e8ace8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Explicitly drop the address column from the customers table
    op.drop_column('customers', 'address')


def downgrade() -> None:
    pass  # Do nothing on downgrade to avoid duplicate column crashes