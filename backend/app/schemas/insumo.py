#   ===================================================================================================
#   Schemas Pydantic para Insumos - Validação de dados
#   Descrição: Este arquivo define os schemas para validação de entrada e saída
#   das APIs de insumos usando Pydantic
#   Data: 08/08/2025
#   Autor: Will - Empresa: IOGAR
#   ===================================================================================================

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# ===================================================================================================
# Schemas Base - Campos comuns
# ===================================================================================================

class InsumoBase(BaseModel):
    """
    Schema base com campos comuns dos insumos.
    Usado como base para criação e atualização.
    
    CAMPO FATOR: Reativado para cálculo correto de preço unitário.
    Exemplo: Compra 3 caixas com 50 unidades cada = quantidade: 3, fator: 50
    
    CAMPO OPERACAO_FATOR: Define se o fator multiplica ou divide a quantidade.
    Valores: 'MULTIPLICAR' (padrão) ou 'DIVIDIR'
    """
    grupo: Optional[str] = Field(default="", max_length=100, description="Grupo de insumo (legado)")
    subgrupo: Optional[str] = Field(default="", max_length=100, description="Subgrupo do insumo (legado)")
    codigo: Optional[str] = Field(default=None, description="Código único (gerado automaticamente se não fornecido)")
    nome: str = Field(..., min_length=1, max_length=255, description="Nome do produto")
    quantidade: int = Field(default=1, ge=1, description="Quantidade padrão")
    fator: Optional[float] = Field(default=1.0, description="Fator multiplicador para cálculo de preço unitário")
    operacao_fator: Optional[str] = Field(
        default='MULTIPLICAR',
        description="Operação do fator no cálculo: MULTIPLICAR ou DIVIDIR"
    )
    unidade: str = Field(..., description="Unidade de medida")
    preco_compra_real: Optional[float] = Field(None, ge=0, description="Preço de compra em reais")
    valor_compra_por_kg: Optional[float] = Field(None, ge=0, description="Valor de compra por Kg", example=85.0)
    
    # ===================================================================================================
    # Validações customizadas
    # ===================================================================================================

    @field_validator('unidade')
    @classmethod
    def validar_unidade(cls, v):
        """
        Valida se a unidade de medida é permitida.
    
        Unidades aceitas (padrão do sistema):
        - kg: Quilograma para peso
        - g: Grama para peso
        - L: Litro para volume
        - ml: Mililitro para volume
        - unidade: Para produtos contáveis
        - caixa: Para embalagens
        - pacote: Para embalagens menores
        """
        unidades_validas = ['kg', 'g', 'L', 'ml', 'unidade', 'caixa', 'pacote']
        if v not in unidades_validas:
            raise ValueError(f'Unidade deve ser uma das: {", ".join(unidades_validas)}')
        return v

    @field_validator('codigo')
    @classmethod
    def validar_codigo(cls, v):
        """
        Valida o formato do código do produto.
        
        Regras:
        - Aceita None (código será gerado automaticamente)
        - Se fornecido, deve conter apenas letras, números e hífen
        - Converte para maiúsculo
        """
        # Se for None ou string vazia, retornar None (será gerado automaticamente)
        if v is None or (isinstance(v, str) and v.strip() == ''):
            return None
        
        # Se fornecido, validar formato
        codigo_limpo = v.replace('-', '').replace('_', '')
        if not codigo_limpo.isalnum():
            raise ValueError('Código deve conter apenas letras, números, hífen ou underscore')
        
        return v.upper()

    @field_validator('preco_compra_real')
    @classmethod
    def validar_preco(cls, v):
        """
        Valida o preço de compra quando fornecido.
        
        Regras:
        - Aceita None (insumo sem preço definido)
        - Se fornecido, deve ser positivo
        - Máximo 2 casas decimais
        """
        # Permite None para insumos sem preço
        if v is None:
            return None
        
        # Se fornecido, valida que seja positivo
        if v < 0:
            raise ValueError('Preço não pode ser negativo')
        
        # Arredonda para 2 casas decimais
        return round(v, 2)
    
    @field_validator('fator')
    @classmethod
    def validar_fator(cls, v):
        """
        Valida o fator de conversão.
        
        Regras:
        - Deve ser sempre maior que zero
        - Aceita valores decimais com até 4 casas
        - Padrão: 1.0 (sem conversão)
        
        Exemplos:
        - Caixa com 50 unidades: fator = 50.0
        - Embalagem de 500g: fator = 0.5 (para base kg)
        - Garrafa de 750ml: fator = 0.75 (para base L)
        """
        # DEBUG: Log do valor recebido
        print(f"🔍 VALIDADOR FATOR - Valor recebido: {v}, Tipo: {type(v)}")
        
        # Se None ou 0, retornar 1.0 (valor padrão)
        if v is None or v == 0:
            print(f"⚠️ VALIDADOR FATOR - Valor inválido, usando padrão 1.0")
            return 1.0
            
        if v <= 0:
            raise ValueError('Fator deve ser um número positivo maior que zero')
        
        # Arredonda para 4 casas decimais
        fator_arredondado = round(float(v), 4)
        print(f"✅ VALIDADOR FATOR - Valor final: {fator_arredondado}")
        return fator_arredondado
    
    @field_validator('operacao_fator', mode='before')
    @classmethod
    def validar_operacao_fator(cls, v):
        """
        Valida se a operação do fator é válida.
        
        Regras:
        - Deve ser 'MULTIPLICAR' ou 'DIVIDIR'
        - Valor padrão: 'MULTIPLICAR'
        - Case-insensitive (converte para uppercase)
        
        Exemplos:
        - 'multiplicar' -> 'MULTIPLICAR'
        - 'Dividir' -> 'DIVIDIR'
        - None -> 'MULTIPLICAR'
        """
        # Se None ou vazio, retornar padrão
        if v is None or (isinstance(v, str) and v.strip() == ''):
            return 'MULTIPLICAR'
        
        # Converter para uppercase e remover espaços
        v_upper = str(v).strip().upper()
        
        # Validar valores aceitos
        valores_validos = ['MULTIPLICAR', 'DIVIDIR']
        if v_upper not in valores_validos:
            raise ValueError(
                f"Operação do fator inválida: '{v}'. "
                f"Valores aceitos: {', '.join(valores_validos)}"
            )
        
        return v_upper
    
    @field_validator('codigo', mode='before')
    @classmethod
    def validar_codigo_opcional(cls, v):
        """
        Valida código se fornecido, mas permite None ou string vazia
        """
        # Se for None ou string vazia, retornar None
        if v is None or (isinstance(v, str) and v.strip() == ''):
            return None
        
        # Se fornecido, validar formato
        codigo_limpo = v.replace('-', '').replace('_', '')
        if not codigo_limpo.isalnum():
            raise ValueError('Código deve conter apenas letras, números, hífen ou underscore')
        return v.upper()

# ===================================================================================================
# Schemas para criação
# ===================================================================================================

class InsumoCreate(InsumoBase):
    """
    Schema para criação de insumo.
    Herda todos os campos do InsumoBase.
    
    IMPORTANTE: restaurante_id é opcional.
    - Se NULL: insumo global (pode ser usado por qualquer restaurante)
    - Se preenchido: insumo específico daquele restaurante
    """
    restaurante_id: Optional[int] = Field(
        None,
        description="ID do restaurante proprietário do insumo (NULL = insumo global)"
    )
    # Campo alternativo para compatibilidade com frontend
    preco_unitario: Optional[float] = Field(None, ge=0, description="Preço unitário (alias para preco_compra_real)")
    
    @field_validator('preco_compra_real', mode='before')
    @classmethod
    def mapear_preco_unitario(cls, v, info):
        """
        Mapeia preco_unitario para preco_compra_real se fornecido.
        Isso garante compatibilidade com o frontend que envia preco_unitario.
        """
        # Se preco_compra_real está None mas preco_unitario foi fornecido, usar preco_unitario
        if v is None and 'preco_unitario' in info.data and info.data['preco_unitario'] is not None:
            print(f"🔄 Mapeando preco_unitario ({info.data['preco_unitario']}) para preco_compra_real")
            return info.data['preco_unitario']
        return v
    
    fornecedor_id: Optional[int] = Field(
        None,
        description="ID do fornecedor deste insumo (opcional)"
    )
    fornecedor_insumo_id: Optional[int] = Field(
        None,
        description="ID do insumo no catálogo do fornecedor (opcional)"
    )
    taxonomia_id: Optional[int] = Field(
        None,
        description="ID da taxonomia hierárquica master (sistema de padronização)"
    )

    class Config:
        """
        Configurações do schema
        """
        json_schema_extra = {
            "example": {
                "grupo": "Verduras",
                "subgrupo": "Tomate",
                "codigo": "VER001",
                "nome": "Tomate maduro",
                "quantidade": 1,
                "unidade": "kg",
                "preco_compra_real": 3.50,
                "restaurante_id": 1
            }
        }

# ===================================================================================================
# Schemas para atualização
# ===================================================================================================

class InsumoUpdate(BaseModel):
    """
    Schema para atualização de insumo.
    Todos os campos são opcionais.
    Campo fator removido conforme nova regra de negócio.
    """
    grupo: Optional[str] = Field(None, min_length=1, max_length=100)
    subgrupo: Optional[str] = Field(None, min_length=1, max_length=100)
    codigo: Optional[str] = Field(None, min_length=1, max_length=50)
    nome: Optional[str] = Field(None, min_length=2, max_length=255)
    quantidade: Optional[int] = Field(None, ge=1)
    fator: Optional[float] = Field(default=1.0, description="Fator multiplicador para cálculo de preço unitário")
    unidade: Optional[str] = None
    preco_compra_real: Optional[float] = Field(None, ge=0)
    aguardando_classificacao: Optional[bool] = Field(default=None, description="Se está aguardando classificação")

    # Campos para comparação de preços com fornecedores
    valor_compra_por_kg: Optional[float] = Field(None, ge=0, description="Valor de compra por Kg em reais", example=10.50)
    total_comprado: Optional[float] = Field(None, ge=0, description="Total comprado (quantidade * valor_compra_por_kg)", example=52.50)
    fornecedor_insumo_id: Optional[int] = Field(None, description="ID do insumo no catálogo do fornecedor para comparação de preços")
    eh_fornecedor_anonimo: Optional[bool] = Field(None, description="Se o insumo é de fornecedor anônimo (sem vinculação)")

    # Validador para garantir valores positivos
    @field_validator('valor_compra_por_kg')
    @classmethod
    def validar_valor_compra_por_kg(cls, v):
        """Valida que valor de compra por Kg é positivo"""
        if v is not None and v < 0:
            raise ValueError('Valor de compra por Kg deve ser positivo')
        if v is not None:
            return round(v, 2)  # Máximo 2 casas decimais
        return v

    # Validações customizadas para campos opcionais
    @field_validator('unidade')
    @classmethod
    def validar_unidade(cls, v):
        """Valida unidade se fornecida"""
        if v is None:
            return v
        unidades_validas = ['unidade', 'caixa', 'kg', 'g', 'L', 'ml']
        if v not in unidades_validas:
            raise ValueError(f'Unidade deve ser uma das: {", ".join(unidades_validas)}')
        return v
    
    @field_validator('codigo')
    @classmethod
    def validar_codigo(cls, v):
        """Valida código se fornecido"""
        if v is None:
            return v
        # Remove caracteres especiais para validação
        codigo_limpo = v.replace('-', '').replace('_', '')
        if not codigo_limpo.isalnum():
            raise ValueError('Código deve conter apenas letras, números, hífen ou underscore')
        return v.upper()
    
    @field_validator('preco_compra_real')
    @classmethod
    def validar_preco(cls, v):
        """
        Valida o preço de compra quando fornecido.
        
        Regras:
        - Aceita None (insumo sem preço definido)
        - Aceita 0 (insumo sem preço)
        - Se maior que 0, arredonda para 2 casas decimais
        """
        # Permite None ou 0 para insumos sem preço
        if v is None or v == 0:
            return v
        
        # Se fornecido e maior que zero, valida que seja positivo
        if v < 0:
            raise ValueError('Preço não pode ser negativo')
        
        # Arredonda para 2 casas decimais
        return round(v, 2)
    
    fornecedor_id: Optional[int] = Field(
        None,
        description="ID do fornecedor deste insumo"
    )

    taxonomia_id: Optional[int] = Field(
        None,
        description="ID da taxonomia hierárquica master para atualizar"
    )

# ===================================================================================================
# Schemas para resposta
# ===================================================================================================

class InsumoResponse(InsumoBase):
    """
    Schema para resposta da API.
    Inclui campos adicionais como ID e timestamps.
    ADICIONADO: Campos para comparação de preços com fornecedores.
    Campo fator herdado do InsumoBase foi removido.
    """
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    preco_compra_centavos: Optional[int] = Field(None, description="Preço em centavos")
    # Campo calculado - preço unitário real considerando fator
    # preco_unitario_real: Optional[float] = Field(None, description="Preço unitário real calculado com fator (preco_total / (quantidade × fator))")
    # Campos para comparação de preços
    preco_por_unidade: Optional[float] = Field(None, description="Preço por unidade calculado (preco_compra * quantidade)")
    fornecedor_insumo_id: Optional[int] = Field(None, description="ID do insumo no catálogo do fornecedor")
    eh_fornecedor_anonimo: Optional[bool] = Field(None, description="Se o insumo é de fornecedor anônimo")
    fornecedor_preco_unidade: Optional[float] = Field(None, description="Preço por unidade do fornecedor (para comparação)")
    diferenca_percentual: Optional[float] = Field(None, description="Diferença percentual com o fornecedor (+ = mais caro, - = mais barato)")
    eh_mais_barato: Optional[bool] = Field(None, description="Se o insumo do sistema é mais barato que o do fornecedor")
    fornecedor_id: Optional[int] = Field(None, description="ID do fornecedor deste insumo")
    taxonomia_id: Optional[int] = Field(None, description="ID da taxonomia hierárquica master")

    class Config:
        """
        Configuração para trabalhar com objetos SQLAlchemy.
        from_attributes=True permite converter objetos do SQLAlchemy em Pydantic.
        """
        from_attributes = True

        json_schema_extra = {
            "example": {
                "id": 1,
                "grupo": "Verduras",
                "subgrupo": "Tomate", 
                "codigo": "VER001", 
                "nome": "Tomate Maduro",
                "quantidade": 1,
                "unidade": "kg",
                "preco_compra_real": 3.50,
                "preco_compra_centavos": 350,
                
                # ============================================================================
                # EXEMPLO DOS CAMPOS DE COMPARAÇÃO DE PREÇOS
                # ============================================================================
                "preco_por_unidade": 3.50,
                "fornecedor_insumo_id": 15,
                "eh_fornecedor_anonimo": False,
                "fornecedor_preco_unidade": 4.20,
                "diferenca_percentual": -16.67,
                "eh_mais_barato": True,
                
                "created_at": "2024-01-15T10:00:00",
                "updated_at": "2024-01-15T15:30:00"
            }
        }

# ===================================================================================================
# Schemas para listagem
# ===================================================================================================

class InsumoListResponse(BaseModel):
    """
    Schema simplificado para resposta de listagem de insumos.
    Usado no endpoint GET /api/v1/insumos/ para exibir listas.
    Inclui campos essenciais incluindo taxonomia_id, aguardando_classificacao e fator.
    """
    id: int = Field(description="ID único do insumo")
    codigo: str = Field(description="Código do insumo")
    nome: str = Field(description="Nome do insumo")
    grupo: str = Field(description="Grupo do insumo")
    subgrupo: str = Field(description="Subgrupo do insumo")
    unidade: str = Field(description="Unidade de medida")
    preco_compra_real: Optional[float] = Field(description="Preço de compra em reais")
    quantidade: int = Field(description="Quantidade")
    fator: Optional[float] = Field(default=1.0, description="Fator multiplicador para cálculo de preço unitário")
    restaurante_id: Optional[int] = None
    
    # Campo importante para taxonomias
    taxonomia_id: Optional[int] = Field(
        None,
        description="ID da taxonomia hierárquica master"
    )
    
    # Campo para controle da classificação IA
    aguardando_classificacao: Optional[bool] = Field(
        None,
        description="TRUE = aguardando classificação pela IA, FALSE = não precisa ou já classificado"
    )

    class Config:
        from_attributes = True

# ===================================================================================================
# Schemas para busca e filtro
# ===================================================================================================

class InsumoFilter(BaseModel):
    """
    Schema para filtros de busca de insumos.
    """
    grupo: Optional[str] = None
    subgrupo: Optional[str] = None
    codigo: Optional[str] = None
    nome: Optional[str] = None
    unidade: Optional[str] = None

    # Filtros de preço
    preco_min: Optional[float] = Field(None, ge=0)
    preco_max: Optional[float] = Field(None, ge=0)

    # Paginação
    skip: int = Field(0, ge=0, description="Registros para pular")
    limit: int = Field(100, ge=1, le=1000, description="Limite de registros")


# ===================================================================================================
# Schema para resposta paginada
# ===================================================================================================

class InsumoListPaginadaResponse(BaseModel):
    """
    Schema de resposta para listagem paginada de insumos.
    
    Retorna dados paginados com metadados de navegação para implementar
    paginação server-side no frontend.
    """
    data: List[InsumoListResponse] = Field(description="Lista de insumos da página atual")
    total: int = Field(description="Total de registros no banco de dados")
    page: int = Field(description="Página atual")
    pages: int = Field(description="Total de páginas disponíveis")
    per_page: int = Field(description="Registros por página")
    
    class Config:
        from_attributes = True