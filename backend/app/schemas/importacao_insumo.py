# ============================================================================
# SCHEMAS PYDANTIC - IMPORTAÇÃO DE INSUMOS
# ============================================================================
# Descrição: Schemas para validação de dados de importação de insumos
# Data: 30/10/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class StatusImportacao(str, Enum):
    """
    Status possíveis de uma importação.
    """
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    SUCESSO = "sucesso"
    SUCESSO_PARCIAL = "sucesso_parcial"
    ERRO = "erro"


# ============================================================================
# SCHEMAS BASE
# ============================================================================

class ImportacaoInsumoBase(BaseModel):
    """
    Schema base para importação de insumos.
    Contém apenas os campos que podem ser enviados na criação.
    """
    restaurante_id: int = Field(
        ..., 
        description="ID do restaurante para o qual os insumos serão importados",
        gt=0
    )
    
    observacoes: Optional[str] = Field(
        None,
        description="Observações sobre a importação",
        max_length=1000
    )


# ============================================================================
# SCHEMA PARA CRIAÇÃO (UPLOAD)
# ============================================================================

class ImportacaoInsumoCreate(ImportacaoInsumoBase):
    """
    Schema para criação de uma nova importação.
    Usado no endpoint de upload do arquivo.
    """
    pass


# ============================================================================
# SCHEMA PARA RESPOSTA COMPLETA
# ============================================================================

class ImportacaoInsumoResponse(ImportacaoInsumoBase):
    """
    Schema completo de resposta com todos os campos da importação.
    Usado nos endpoints que retornam dados de importação.
    """
    id: int = Field(description="ID único da importação")
    usuario_id: Optional[int] = Field(description="ID do usuário que realizou a importação")
    
    # Informações do arquivo
    nome_arquivo: str = Field(description="Nome original do arquivo")
    caminho_arquivo: str = Field(description="Caminho do arquivo no servidor")
    tamanho_arquivo: int = Field(description="Tamanho do arquivo em bytes")
    tipo_mime: str = Field(description="Tipo MIME do arquivo")
    
    # Status e processamento
    status: StatusImportacao = Field(description="Status atual da importação")
    data_inicio_processamento: Optional[datetime] = Field(
        description="Data/hora de início do processamento"
    )
    data_fim_processamento: Optional[datetime] = Field(
        description="Data/hora de conclusão do processamento"
    )
    
    # Estatísticas
    total_linhas: int = Field(description="Total de linhas no arquivo", ge=0)
    linhas_processadas: int = Field(description="Linhas processadas com sucesso", ge=0)
    linhas_com_erro: int = Field(description="Linhas com erro", ge=0)
    linhas_ignoradas: int = Field(description="Linhas ignoradas", ge=0)
    
    # Logs
    log_processamento: Optional[str] = Field(description="Log detalhado do processamento")
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
# SCHEMA PARA ESTATÍSTICAS
# ============================================================================

class EstatisticasImportacao(BaseModel):
    """
    Schema para estatísticas calculadas da importação.
    """
    taxa_sucesso: float = Field(
        description="Percentual de linhas processadas com sucesso (0-100)",
        ge=0,
        le=100
    )
    taxa_erro: float = Field(
        description="Percentual de linhas com erro (0-100)",
        ge=0,
        le=100
    )
    tempo_processamento: Optional[float] = Field(
        description="Tempo de processamento em segundos",
        ge=0
    )
    eh_sucesso_total: bool = Field(
        description="True se todas as linhas foram processadas com sucesso"
    )


# ============================================================================
# SCHEMA PARA ITEM DE LOG
# ============================================================================

class ItemLog(BaseModel):
    """
    Schema para um item individual do log de processamento.
    Linha 0 indica mensagens do sistema (não vinculadas a uma linha específica).
    """
    linha: int = Field(description="Número da linha no arquivo (0 = mensagem do sistema)", ge=0)
    tipo: str = Field(description="Tipo: sucesso, erro, aviso, ignorado, atualizado, info")
    mensagem: str = Field(description="Mensagem descritiva")
    dados: Optional[Dict[str, Any]] = Field(
        None,
        description="Dados adicionais (código, nome, etc.)"
    )

# ============================================================================
# SCHEMA PARA LOG ESTRUTURADO
# ============================================================================

class LogProcessamento(BaseModel):
    """
    Schema para log estruturado de processamento.
    """
    sucessos: List[ItemLog] = Field(
        default_factory=list,
        description="Lista de linhas processadas com sucesso"
    )
    erros: List[ItemLog] = Field(
        default_factory=list,
        description="Lista de linhas com erro"
    )
    avisos: List[ItemLog] = Field(
        default_factory=list,
        description="Lista de avisos durante o processamento"
    )
    ignorados: List[ItemLog] = Field(
        default_factory=list,
        description="Lista de linhas ignoradas"
    )


# ============================================================================
# SCHEMA PARA RESPOSTA DE LISTA PAGINADA
# ============================================================================

class ImportacaoInsumoListResponse(BaseModel):
    """
    Schema para resposta de lista paginada de importações.
    """
    importacoes: List[ImportacaoInsumoResponse] = Field(
        description="Lista de importações"
    )
    total: int = Field(description="Total de registros", ge=0)
    skip: int = Field(description="Número de registros pulados", ge=0)
    limit: int = Field(description="Limite de registros por página", gt=0)
    
    class Config:
        from_attributes = True


# ============================================================================
# SCHEMA PARA PREVIEW DE IMPORTAÇÃO
# ============================================================================

class PreviewImportacao(BaseModel):
    """
    Schema para preview dos dados antes de importar.
    Permite ao usuário visualizar o que será importado.
    """
    nome_arquivo: str = Field(description="Nome do arquivo")
    total_linhas: int = Field(description="Total de linhas detectadas", ge=0)
    colunas_detectadas: List[str] = Field(description="Colunas encontradas no arquivo")
    primeiras_linhas: List[Dict[str, Any]] = Field(
        description="Primeiras 5 linhas para preview",
        max_items=5
    )
    mapeamento_colunas: Dict[str, str] = Field(
        description="Mapeamento de colunas (Excel -> Sistema)"
    )
    avisos: List[str] = Field(
        default_factory=list,
        description="Avisos sobre o arquivo"
    )


# ============================================================================
# SCHEMA PARA CONFIRMAÇÃO DE IMPORTAÇÃO
# ============================================================================

class ConfirmacaoImportacao(BaseModel):
    """
    Schema para confirmação da importação após preview.
    """
    importacao_id: int = Field(description="ID da importação pendente", gt=0)
    confirmar: bool = Field(description="True para confirmar e processar")
    mapeamento_colunas: Optional[Dict[str, str]] = Field(
        None,
        description="Mapeamento de colunas do Excel para campos do sistema"
    )
    observacoes: Optional[str] = Field(
        None,
        description="Observações adicionais",
        max_length=1000
    )