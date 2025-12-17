#   ===================================================================================================
#   Insumo Model -  Representa os ingredientes de cada receita
#   Descrição: Esse modelo define a estrutura dos insumos que serão utilizados nas receitas.
#   Data: 07/08/2025
#   Autor: Will - Empresa: IOGAR
#   ===================================================================================================

from sqlalchemy import Column, Float, ForeignKey, Integer, Boolean, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Insumo(BaseModel):
    """
    Modelo que representa um insumo (ingrediente/matéria-prima).

    Campos herdados do BaseModel:
    - grupo, subgrupo, codigo, nome
    - quantidade, unidade, preco_compra, fator

    NOTA: O campo 'fator' foi re-implementado para cálculo de preço unitário.
    Quando fator != 1, o preço unitário é dividido pelo fator.
    Fórmula: preco_unitario = (preco_compra_total / quantidade) / fator
    """
    __tablename__ = "insumos"

    # ========================================================================
    # CONSTRAINT DE UNICIDADE: Código único por restaurante
    # ========================================================================
    __table_args__ = (
        UniqueConstraint(
            'restaurante_id',
            'codigo',
            name='uq_insumo_restaurante_codigo'
        ),
    )

    # ========================================================================
    # CAMPO FATOR - Multiplicador para cálculo de preço unitário
    # ========================================================================
    # Campo fator para conversão de unidades e cálculo de preço
    # Valor padrão: 1.0 (sem conversão)
    # Quando fator != 1: preco_unitario = (preco_compra_total / quantidade) / fator
    # Exemplo: Se compra 750ml mas quer preço por litro, fator = 0.75
    fator = Column(
        Float,
        default=1.0,
        nullable=True,
        comment="Fator multiplicador para cálculo de preço unitário (default: 1.0)"
    )

    # ========================================================================
    # CAMPO OPERACAO_FATOR - Define se fator multiplica ou divide
    # ========================================================================
    # Campo para definir a operação do fator no cálculo de quantidade total
    # Valores aceitos: 'MULTIPLICAR' ou 'DIVIDIR'
    # Valor padrão: 'MULTIPLICAR' (comportamento original)
    # 
    # MULTIPLICAR: quantidade_total = quantidade × fator
    # DIVIDIR: quantidade_total = quantidade ÷ fator
    operacao_fator = Column(
        String(15),
        default='MULTIPLICAR',
        nullable=False,
        comment="Operação do fator: MULTIPLICAR ou DIVIDIR (default: MULTIPLICAR)"
    )

    #   ===================================================================================================
    #   VINCULAÇÃO COM RESTAURANTE - CAMPO OBRIGATÓRIO
    #   ===================================================================================================

    # Vinculação com restaurante - campo opcional para suportar insumos globais
    restaurante_id = Column(
        Integer,
        ForeignKey("restaurantes.id", ondelete="CASCADE"),
        nullable=True,  # NULL = insumo global, ID = insumo específico do restaurante
        index=True,
        comment="ID do restaurante proprietário do insumo (NULL = insumo global)"
    )

    #   ===================================================================================================
    #   CHAVE ESTRANGEIRA PARA FORNECEDOR
    #   ===================================================================================================

    fornecedor_insumo_id = Column(
        Integer,
        ForeignKey("fornecedor_insumos.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID do insumo no catálogo do fornecedor (NULL = fornecedor anônimo)"
    )

    # Campo para marcar se é fornecedor anônimo
    eh_fornecedor_anonimo = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="TRUE = sem fornecedor específico, FALSE = vinculado a fornecedor"
    )

    # FK para Taxonomia Master (sistema novo de padronização)
    taxonomia_id = Column(
        Integer,
        ForeignKey("taxonomias.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID da taxonomia hierárquica master (sistema de padronização)"
    )

    # Campo para controle da classificação IA
    aguardando_classificacao = Column(
        Boolean,
        default=False,
        nullable=True,  # ← MUDAR para True temporariamente
        comment="TRUE = aguardando classificação pela IA, FALSE = não precisa ou já classificado"
    )

    # Campo de rastreamento de criação
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID do usuário que criou o insumo"
    )

    #   ===================================================================================================
    #   IMPORTAÇÃO DE DADOS
    #   ===================================================================================================

    # FK para rastreamento de importação via Excel/TOTVS
    importacao_id = Column(
        Integer,
        ForeignKey("importacoes_insumos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID da importação que criou este insumo (NULL = cadastro manual)"
    )

    #   ===================================================================================================
    #   Relacionamentos com outras tabelas
    #   ===================================================================================================

    # Relacionamento com restaurante (N para 1)
    # Cada insumo pertence a um restaurante específico
    restaurante = relationship(
        "Restaurante",
        back_populates="insumos",
        lazy="select",
        doc="Restaurante proprietário deste insumo"
    )

    # Relacionamento com receitas
    receitas = relationship("ReceitaInsumo", back_populates="insumo")

    # Relacionamento com Fornecedor (muitos insumos para um fornecedor)
    fornecedor_insumo = relationship(
        "FornecedorInsumo",
        back_populates="insumos_sistema"
    )

    # Relacionamento com Taxonomia Master (sistema novo de padronização)
    taxonomia = relationship(
        "Taxonomia",
        back_populates="insumos"
    )

    # Relacionamento com ImportacaoInsumo (N para 1)
    # Rastreia se este insumo foi criado via importação ou manualmente
    importacao = relationship(
        "ImportacaoInsumo",
        back_populates="insumos",
        lazy="select",
        doc="Importação que criou este insumo (None = cadastro manual)"
    )

    def __repr__(self):
        """Representação em string do objeto para debug"""
        return f"<Insumo(codigo='{self.codigo}', nome='{self.nome}', restaurante_id={self.restaurante_id})>"

    #   ===================================================================================================
    #   Propriendades calculadas (getters)
    #   ===================================================================================================
    @property
    def preco_compra_real(self):
        """Converte o preço de centavos para reais."""
        if not self.preco_compra:
            return 0.0
        # Garantir que a operação seja feita com tipos compatíveis
        preco_centavos = float(self.preco_compra) if self.preco_compra else 0.0
        return preco_centavos / 100.0

    @preco_compra_real.setter
    def preco_compra_real(self, valor):
        """Converte reais para centavos"""
        if valor is None:
            self.preco_compra = None
        else:
            # Garantir que o valor seja convertido corretamente
            valor_float = float(valor) if valor else 0.0
            self.preco_compra = int(valor_float * 100)


    @property
    def fornecedor_nome(self) -> str:
        """
        Retorna o nome do fornecedor ou 'Fornecedor Anônimo'.

        Returns:
            str: Nome do fornecedor ou texto padrão
        """
        if self.eh_fornecedor_anonimo or not self.fornecedor_insumo:
            return "Fornecedor Anônimo"
        return self.fornecedor_insumo.fornecedor.nome_razao_social


    @property
    def fornecedor_preco_unitario(self) -> float:
        """
        Retorna o preço unitário do fornecedor para comparação.

        Returns:
            float: Preço unitário do fornecedor ou 0.0 se anônimo
        """
        if self.eh_fornecedor_anonimo or not self.fornecedor_insumo:
            return 0.0

        # Garantir conversão segura de Decimal para float
        preco_unitario = self.fornecedor_insumo.preco_unitario
        return float(preco_unitario) if preco_unitario is not None else 0.0
    
    @property
    def preco_unitario_real(self) -> float:
        """
        Calcula o preço unitário real considerando o fator e operação (multiplicar ou dividir).
        
        Fórmulas:
        - MULTIPLICAR: Preço Unitário = (Preço Total) / (Quantidade × Fator)
        - DIVIDIR: Preço Unitário = (Preço Total) / (Quantidade ÷ Fator)
        
        Exemplos:
        
        MULTIPLICAR (padrão):
        - Compra: 3 caixas de Nori por R$ 150,00
        - Cada caixa tem 50 folhas (fator = 50)
        - operacao_fator = 'MULTIPLICAR'
        - Total de unidades: 3 × 50 = 150 folhas
        - Preço unitário: R$ 150,00 / 150 = R$ 1,00 por folha
        
        DIVIDIR:
        - Compra: 10 litros de óleo por R$ 100,00
        - Quer preço por 100ml (fator = 10 para dividir 1L em 10 partes de 100ml)
        - operacao_fator = 'DIVIDIR'
        - Total de unidades: 10 ÷ 10 = 1 unidade base
        - Preço unitário: R$ 100,00 / 1 = R$ 100,00 por unidade base
        
        Returns:
            float: Preço unitário real por unidade base
        """
        if not self.preco_compra or not self.quantidade:
            return 0.0
        
        # Garantir que fator não seja zero ou None
        fator_usado = self.fator if self.fator and self.fator > 0 else 1.0
        
        # Converter preço de centavos para reais
        preco_real = float(self.preco_compra) / 100.0
        
        # ========================================================================
        # CALCULAR QUANTIDADE TOTAL BASEADO NA OPERAÇÃO DO FATOR
        # ========================================================================
        operacao = getattr(self, 'operacao_fator', 'MULTIPLICAR') or 'MULTIPLICAR'
        
        if operacao == 'DIVIDIR':
            # Dividir a quantidade pelo fator
            # Exemplo: 10 litros ÷ fator(10) = 1 unidade base
            quantidade_total = float(self.quantidade) / fator_usado
        else:
            # MULTIPLICAR (comportamento padrão/original)
            # Multiplicar a quantidade pelo fator
            # Exemplo: 3 caixas × fator(50) = 150 unidades
            quantidade_total = float(self.quantidade) * fator_usado
        
        if quantidade_total <= 0:
            return 0.0
            
        preco_unitario = preco_real / quantidade_total
        
        return round(preco_unitario, 4)  # 4 casas decimais

    #   ===================================================================================================
    #   Novos campos para valor de compra por Kg e total comprado
    #   ===================================================================================================

    @property
    def valor_compra_por_kg(self):
        """Valor de compra por Kg em reais."""
        return getattr(self, '_valor_compra_por_kg', 0.0)

    @valor_compra_por_kg.setter
    def valor_compra_por_kg(self, valor):
        """Define o valor de compra por Kg"""
        self._valor_compra_por_kg = round(float(valor), 2) if valor else 0.0
        self._atualizar_total_comprado()

    @property
    def total_comprado(self):
        """Total comprado (quantidade × valor_compra_por_kg)"""
        return getattr(self, '_total_comprado', 0.0)

    @total_comprado.setter
    def total_comprado(self, valor):
        """Define o total comprado"""
        self._total_comprado = round(float(valor), 2) if valor else 0.0

    def _atualizar_total_comprado(self):
        """Calcula automaticamente: quantidade × valor_compra_por_kg"""
        if hasattr(self, '_valor_compra_por_kg') and self.quantidade:
            self._total_comprado = round(self.quantidade * self._valor_compra_por_kg, 2)
        else:
            self._total_comprado = 0.0

    def calcular_total(self):
        """Método público para recalcular o total comprado"""
        self._atualizar_total_comprado()
        return self.total_comprado