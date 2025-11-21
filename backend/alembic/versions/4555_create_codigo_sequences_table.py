"""create codigo sequences table

Revision ID: create_codigo_sequences
Revises: add_fator_to_insumos
Create Date: 2025-11-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_codigo_sequences'
down_revision = 'add_fator_to_insumos'
branch_labels = None
depends_on = None


def upgrade():
    """
    Cria tabela para controlar sequências de códigos por restaurante.
    Garante que códigos deletados nunca sejam reusados.
    """
    # ============================================================================
    # CRIAR TABELA CODIGO_SEQUENCES
    # ============================================================================
    op.create_table(
        'codigo_sequences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restaurante_id', sa.Integer(), nullable=False, comment='ID do restaurante (-1 para global)'),
        sa.Column('tipo_codigo', sa.String(50), nullable=False, comment='INSUMO, RECEITA_NORMAL, RECEITA_PROCESSADA'),
        sa.Column('ultimo_numero', sa.Integer(), nullable=False, comment='Último número gerado'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('restaurante_id', 'tipo_codigo', name='uq_codigo_sequence_restaurante_tipo')
    )
    
    # ============================================================================
    # CRIAR ÍNDICES
    # ============================================================================
    op.create_index('idx_codigo_sequences_restaurante_tipo', 'codigo_sequences', ['restaurante_id', 'tipo_codigo'])
    
    # ============================================================================
    # POPULAR COM DADOS EXISTENTES
    # ============================================================================
    # Buscar máximos atuais por restaurante e tipo e inserir na tabela
    op.execute("""
        INSERT INTO codigo_sequences (restaurante_id, tipo_codigo, ultimo_numero, created_at)
        SELECT 
            COALESCE(restaurante_id, -1) as restaurante_id,
            'INSUMO' as tipo_codigo,
            MAX(CAST(codigo AS INTEGER)) as ultimo_numero,
            NOW() as created_at
        FROM insumos
        WHERE codigo ~ '^[0-9]+$'
          AND CAST(codigo AS INTEGER) BETWEEN 5000 AND 5999
        GROUP BY COALESCE(restaurante_id, -1)
    """)


def downgrade():
    """
    Remove tabela de sequências de códigos.
    """
    op.drop_index('idx_codigo_sequences_restaurante_tipo')
    op.drop_table('codigo_sequences')