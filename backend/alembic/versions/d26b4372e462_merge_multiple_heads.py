"""merge_multiple_heads

Revision ID: d26b4372e462
Revises: create_codigo_sequences, fix_receitas_codigo_001
Create Date: 2025-12-16 15:16:47.626870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd26b4372e462'
down_revision: Union[str, Sequence[str], None] = ('create_codigo_sequences', 'fix_receitas_codigo_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
