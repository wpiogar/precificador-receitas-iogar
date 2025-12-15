"""fix receitas codigo unique per restaurant

Revision ID: fix_receitas_codigo_001
Revises: add_ultimo_login_001
Create Date: 2025-12-12 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'fix_receitas_codigo_001'
down_revision: Union[str, None] = 'add_ultimo_login_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Remove constraint UNIQUE global do codigo e cria constraint
    UNIQUE composta (codigo + restaurante_id).
    """
    op.drop_constraint('receitas_codigo_key', 'receitas', type_='unique')
    op.create_unique_constraint(
        'receitas_codigo_restaurante_key',
        'receitas',
        ['codigo', 'restaurante_id']
    )
    print("✅ Constraint alterada: código único por restaurante")


def downgrade() -> None:
    """Reverte para constraint única global."""
    op.drop_constraint('receitas_codigo_restaurante_key', 'receitas', type_='unique')
    op.create_unique_constraint('receitas_codigo_key', 'receitas', ['codigo'])
    print("✅ Constraint revertida")