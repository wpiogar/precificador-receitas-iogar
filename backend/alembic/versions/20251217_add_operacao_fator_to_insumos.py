"""add operacao_fator to insumos

Revision ID: add_operacao_fator_20251217
Revises: d26b4372e462
Create Date: 2025-12-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_operacao_fator_20251217'
down_revision = 'd26b4372e462'
branch_labels = None
depends_on = None


def upgrade():
    """
    Adiciona coluna 'operacao_fator' na tabela 'insumos'.
    
    Campo para definir se o fator multiplica ou divide no cálculo do valor unitário:
    - Valor padrão: 'MULTIPLICAR' (comportamento original)
    - Valores aceitos: 'MULTIPLICAR' ou 'DIVIDIR'
    - NOT NULL: Obrigatório para todos os registros
    
    Exemplos de uso:
    - MULTIPLICAR: Caixa com 50 unidades (fator = 50)
      quantidade_total = quantidade × 50
    - DIVIDIR: 10 litros vendidos, calcular por 100ml (fator = 10)
      quantidade_total = quantidade ÷ 10
    """
    # ============================================================================
    # ADICIONAR COLUNA OPERACAO_FATOR
    # ============================================================================
    op.add_column(
        'insumos',
        sa.Column(
            'operacao_fator',
            sa.String(15),
            nullable=False,
            server_default='MULTIPLICAR',
            comment='Operação do fator no cálculo: MULTIPLICAR ou DIVIDIR (default: MULTIPLICAR)'
        )
    )
    
    # ============================================================================
    # ATUALIZAR REGISTROS EXISTENTES
    # ============================================================================
    # Garantir que todos os registros existentes tenham 'MULTIPLICAR' (comportamento original)
    op.execute("UPDATE insumos SET operacao_fator = 'MULTIPLICAR' WHERE operacao_fator IS NULL")


def downgrade():
    """
    Remove coluna 'operacao_fator' da tabela 'insumos'.
    
    ATENÇÃO: Esta operação causará perda de dados!
    """
    # ============================================================================
    # REMOVER COLUNA OPERACAO_FATOR
    # ============================================================================
    op.drop_column('insumos', 'operacao_fator')