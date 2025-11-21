# ============================================================================
# MODELO CODIGO_SEQUENCE - Controle de sequências de códigos
# ============================================================================
# Descrição: Garante que códigos nunca sejam reusados após exclusão
# Data: 21/11/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.models.base import Base


class CodigoSequence(Base):
    """
    Modelo para controlar sequências de códigos por restaurante.
    
    Cada restaurante tem sua própria sequência para cada tipo de código.
    Quando um código é gerado, incrementamos o ultimo_numero.
    Mesmo que o registro seja deletado, o número nunca é reusado.
    """
    __tablename__ = "codigo_sequences"
    
    # ========================================================================
    # COLUNAS
    # ========================================================================
    
    id = Column(Integer, primary_key=True, index=True)
    
    restaurante_id = Column(
        Integer,
        nullable=False,
        index=True,
        comment="ID do restaurante (-1 para global)"
    )
    
    tipo_codigo = Column(
        String(50),
        nullable=False,
        index=True,
        comment="INSUMO, RECEITA_NORMAL, RECEITA_PROCESSADA"
    )
    
    ultimo_numero = Column(
        Integer,
        nullable=False,
        comment="Último número gerado (nunca decresce)"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now()
    )
    
    # ========================================================================
    # CONSTRAINTS
    # ========================================================================
    
    __table_args__ = (
        UniqueConstraint(
            'restaurante_id',
            'tipo_codigo',
            name='uq_codigo_sequence_restaurante_tipo'
        ),
    )
    
    def __repr__(self):
        return f"<CodigoSequence(restaurante={self.restaurante_id}, tipo={self.tipo_codigo}, ultimo={self.ultimo_numero})>"