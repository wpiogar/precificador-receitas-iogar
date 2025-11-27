# ============================================================================
# SCHEMAS - IMPORTAÇÃO DE RECEITAS VIA EXCEL
# ============================================================================
# Descrição: Schemas Pydantic para validação de dados de importação de receitas
# Data: 25/11/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============================================================================
# SCHEMAS PARA INSUMOS DENTRO DA RECEITA
# ============================================================================

class InsumoReceitaPreview(BaseModel):
    """
    Schema para preview de um insumo dentro de uma receita.
    """
    codigo: Optional[int] = Field(description="Código do insumo no Excel")
    nome: str = Field(description="Nome do insumo")
    quantidade: float = Field(description="Quantidade do insumo", ge=0)
    unidade: str = Field(description="Unidade de medida")
    custo: float = Field(description="Custo do insumo", ge=0)
    valor: float = Field(description="Valor do insumo na receita", ge=0)
    
    # Informações de matching
    insumo_id_matched: Optional[int] = Field(
        None,
        description="ID do insumo encontrado no sistema"
    )
    tipo_match: Optional[str] = Field(
        None,
        description="Tipo de match: EXATO, FUZZY, NAO_ENCONTRADO"
    )
    score_similaridade: float = Field(
        0.0,
        description="Score de similaridade (0-100)",
        ge=0,
        le=100
    )
    nome_insumo_sistema: Optional[str] = Field(
        None,
        description="Nome do insumo encontrado no sistema"
    )


# ============================================================================
# SCHEMAS PARA RECEITAS
# ============================================================================

class ReceitaPreview(BaseModel):
    """
    Schema para preview de uma receita a ser importada.
    """
    codigo: int = Field(description="Código da receita", gt=0)
    nome: str = Field(description="Nome da receita")
    tipo: str = Field(description="Tipo: COMPOSTO ou PROCESSADO")
    total_insumos: int = Field(description="Total de insumos", ge=0)
    custo_total: float = Field(description="Custo total da receita", ge=0)
    valor_total: float = Field(description="Valor total da receita", ge=0)
    insumos: List[InsumoReceitaPreview] = Field(
        default_factory=list,
        description="Lista de insumos da receita"
    )
    insumos_nao_encontrados: int = Field(
        0,
        description="Quantidade de insumos não encontrados no sistema",
        ge=0
    )
    pode_importar: bool = Field(
        description="Se True, todos os insumos foram encontrados"
    )


# ============================================================================
# SCHEMA PARA PREVIEW GERAL DA IMPORTAÇÃO
# ============================================================================

class PreviewImportacaoReceita(BaseModel):
    """
    Schema para preview completo da importação de receitas.
    Retornado após upload do arquivo.
    """
    nome_arquivo: str = Field(description="Nome do arquivo")
    total_receitas: int = Field(description="Total de receitas detectadas", ge=0)
    
    # Estatísticas de matching
    estatisticas: Dict[str, int] = Field(
        description="Estatísticas de matching de insumos",
        default_factory=dict
    )
    
    # Receitas prontas para importar (todos os insumos encontrados)
    receitas_prontas: List[ReceitaPreview] = Field(
        default_factory=list,
        description="Receitas que podem ser importadas"
    )
    
    # Receitas com insumos faltando
    receitas_com_insumos_faltando: List[ReceitaPreview] = Field(
        default_factory=list,
        description="Receitas que não podem ser importadas (insumos faltando)"
    )
    
    avisos: List[str] = Field(
        default_factory=list,
        description="Avisos sobre o processamento"
    )


# ============================================================================
# SCHEMA PARA CONFIRMAÇÃO DE IMPORTAÇÃO
# ============================================================================

class ConfirmacaoImportacaoReceita(BaseModel):
    """
    Schema para confirmação da importação de receitas.
    Enviado pelo frontend após o usuário revisar o preview.
    """
    importacao_id: int = Field(description="ID da importação pendente", gt=0)
    confirmar: bool = Field(description="True para confirmar e processar")
    
    # IDs das receitas que o usuário quer importar
    receitas_selecionadas: List[int] = Field(
        default_factory=list,
        description="Lista de códigos das receitas a importar"
    )
    
    # Decisões sobre insumos com match fuzzy (aceitar sugestão ou ignorar)
    decisoes_matching: Optional[Dict[str, int]] = Field(
        None,
        description="Mapa de decisões: {nome_insumo_excel: insumo_id_sistema}"
    )
    
    observacoes: Optional[str] = Field(
        None,
        description="Observações adicionais",
        max_length=1000
    )


# ============================================================================
# SCHEMA PARA RESULTADO DA IMPORTAÇÃO
# ============================================================================

class ResultadoImportacaoReceita(BaseModel):
    """
    Schema para resultado final da importação.
    """
    importacao_id: int = Field(description="ID da importação")
    status: str = Field(description="Status: SUCESSO, PARCIAL, ERRO")
    
    # Estatísticas
    total_receitas_processadas: int = Field(description="Total de receitas processadas", ge=0)
    receitas_importadas_sucesso: int = Field(description="Receitas importadas com sucesso", ge=0)
    receitas_com_erro: int = Field(description="Receitas com erro", ge=0)
    
    # Detalhes
    receitas_sucesso: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Lista de receitas importadas com sucesso"
    )
    
    receitas_erro: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Lista de receitas que falharam"
    )
    
    mensagem: str = Field(description="Mensagem geral sobre a importação")
    
    # Timestamps
    data_inicio: datetime = Field(description="Data/hora de início")
    data_fim: datetime = Field(description="Data/hora de conclusão")


# ============================================================================
# SCHEMA PARA RESPOSTA DE UPLOAD
# ============================================================================

class UploadReceitaResponse(BaseModel):
    """
    Schema para resposta do endpoint de upload.
    """
    importacao_id: int = Field(description="ID da importação criada")
    preview: PreviewImportacaoReceita = Field(description="Preview dos dados")


# ============================================================================
# SCHEMA BASE PARA IMPORTAÇÃO
# ============================================================================

class ImportacaoReceitaBase(BaseModel):
    """
    Schema base com campos comuns de importação de receitas.
    """
    restaurante_id: int = Field(description="ID do restaurante", gt=0)
    observacoes: Optional[str] = Field(
        None,
        description="Observações sobre a importação",
        max_length=2000
    )


# ============================================================================
# SCHEMA PARA RESPOSTA COMPLETA DE IMPORTAÇÃO
# ============================================================================

class ImportacaoReceitaResponse(ImportacaoReceitaBase):
    """
    Schema completo de resposta com todos os campos da importação.
    """
    id: int = Field(description="ID único da importação")
    usuario_id: Optional[int] = Field(description="ID do usuário")
    
    # Informações do arquivo
    nome_arquivo: str = Field(description="Nome original do arquivo")
    caminho_arquivo: str = Field(description="Caminho do arquivo no servidor")
    tamanho_arquivo: int = Field(description="Tamanho do arquivo em bytes")
    
    # Status
    status: str = Field(description="Status atual da importação")
    
    # Estatísticas
    total_receitas: int = Field(description="Total de receitas no arquivo", ge=0)
    receitas_importadas: int = Field(description="Receitas importadas com sucesso", ge=0)
    receitas_com_erro: int = Field(description="Receitas com erro", ge=0)
    
    # Logs
    log_processamento: Optional[str] = Field(description="Log detalhado")
    mensagem_erro: Optional[str] = Field(description="Mensagem de erro principal")
    
    # Timestamps
    created_at: datetime = Field(description="Data/hora de criação")
    updated_at: Optional[datetime] = Field(description="Data/hora da última atualização")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# ============================================================================
# SCHEMA PARA LISTAGEM DE IMPORTAÇÕES
# ============================================================================

class ImportacaoReceitaListResponse(BaseModel):
    """
    Schema para resposta de listagem de importações.
    """
    total: int = Field(description="Total de registros", ge=0)
    items: List[ImportacaoReceitaResponse] = Field(
        default_factory=list,
        description="Lista de importações"
    )
    page: int = Field(description="Página atual", ge=1)
    size: int = Field(description="Tamanho da página", ge=1)