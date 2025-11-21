"""add fator field to insumos

Revision ID: add_fator_to_insumos
Revises: <revision_anterior>
Create Date: 2025-11-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_fator_to_insumos'
down_revision = '62b11535b810'  # merge_all_production_heads
branch_labels = None
depends_on = None


def upgrade():
    """
    Adiciona coluna 'fator' na tabela 'insumos'.
    
    Campo para cálculo de preço unitário real:
    - Valor padrão: 1.0 (sem conversão)
    - NOT NULL: Obrigatório para todos os registros
    - Exemplo: Caixa com 50 unidades = fator 50.0
    """
    # ============================================================================
    # ADICIONAR COLUNA FATOR
    # ============================================================================
    op.add_column(
        'insumos',
        sa.Column(
            'fator',
            sa.Float(),
            nullable=False,
            server_default='1.0',
            comment='Fator de conversão para cálculo de preço unitário real (default: 1.0)'
        )
    )
    
    # ============================================================================
    # ATUALIZAR REGISTROS EXISTENTES (Garantir que todos tenham fator = 1.0)
    # ============================================================================
    # Esta etapa é importante para dados legados que possam ter NULL
    op.execute("UPDATE insumos SET fator = 1.0 WHERE fator IS NULL")


def downgrade():
    """
    Remove coluna 'fator' da tabela 'insumos'.
    
    ATENÇÃO: Esta operação causará perda de dados!
    """
    # ============================================================================
    # REMOVER COLUNA FATOR
    # ============================================================================
    op.drop_column('insumos', 'fator')