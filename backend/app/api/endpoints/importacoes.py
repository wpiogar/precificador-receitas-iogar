# ============================================================================
# ENDPOINTS - IMPORTAÇÃO DE INSUMOS VIA EXCEL
# ============================================================================
# Descrição: Endpoints para upload e processamento de arquivos Excel/TOTVS
# Data: 30/10/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import shutil
import uuid
from datetime import datetime

from app.database import get_db
from app.models.importacao_insumo import ImportacaoInsumo, StatusImportacao
from app.models.user import User
from app.schemas.importacao_insumo import (
    ImportacaoInsumoResponse,
    ImportacaoInsumoListResponse,
    PreviewImportacao,
    ConfirmacaoImportacao,
    EstatisticasImportacao
)
from app.services.importacao_service import ImportacaoService
from app.api.deps import get_current_user

# Criar roteador
router = APIRouter()

# Diretório para armazenar arquivos
UPLOAD_DIR = Path("uploads/importacoes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def salvar_arquivo_upload(file: UploadFile) -> tuple[str, str, int]:
    """
    Salva o arquivo enviado e retorna informações.
    
    Args:
        file: Arquivo enviado pelo usuário
        
    Returns:
        tuple: (caminho_arquivo, nome_arquivo, tamanho_bytes)
    """
    # Gerar nome único
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Salvar arquivo
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Obter tamanho
    file_size = file_path.stat().st_size
    
    return str(file_path), file.filename, file_size


def calcular_estatisticas(importacao: ImportacaoInsumo) -> EstatisticasImportacao:
    """
    Calcula estatísticas da importação.
    
    Args:
        importacao: Objeto ImportacaoInsumo
        
    Returns:
        EstatisticasImportacao: Estatísticas calculadas
    """
    taxa_sucesso = importacao.calcular_taxa_sucesso()
    taxa_erro = (
        (importacao.linhas_com_erro / importacao.total_linhas * 100)
        if importacao.total_linhas > 0 else 0.0
    )
    
    # Calcular tempo de processamento
    tempo_processamento = None
    if importacao.data_inicio_processamento and importacao.data_fim_processamento:
        delta = importacao.data_fim_processamento - importacao.data_inicio_processamento
        tempo_processamento = delta.total_seconds()
    
    return EstatisticasImportacao(
        taxa_sucesso=round(taxa_sucesso, 2),
        taxa_erro=round(taxa_erro, 2),
        tempo_processamento=tempo_processamento,
        eh_sucesso_total=importacao.eh_sucesso_total()
    )


# ============================================================================
# ENDPOINT: UPLOAD E PREVIEW
# ============================================================================

@router.post(
    "/upload",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Upload de arquivo Excel para preview",
    description="Faz upload do arquivo Excel e retorna preview dos dados que serão importados"
)
async def upload_arquivo_preview(
    file: UploadFile = File(..., description="Arquivo Excel (.xlsx)"),
    restaurante_id: int = Form(..., description="ID do restaurante"),
    db: Session = Depends(get_db),
    #current_user: User = Depends(get_current_user)
):
    """
    Endpoint para upload de arquivo Excel e geração de preview.
    
    Fluxo:
    1. Recebe arquivo Excel
    2. Salva temporariamente
    3. Gera preview dos dados
    4. Cria registro pendente no banco
    5. Retorna preview + importacao_id
    """
    from app.models.receita import Restaurante
    
    restaurante = db.query(Restaurante).filter(
        Restaurante.id == restaurante_id
    ).first()
    
    if not restaurante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurante com ID {restaurante_id} não encontrado"
        )
    
    print("=" * 80)
    print("📤 UPLOAD DE IMPORTAÇÃO DE INSUMOS")
    print(f"   Restaurante ID: {restaurante_id}")
    print(f"   Restaurante Nome: {restaurante.nome}")
    print(f"   Arquivo: {file.filename}")
    print("=" * 80)

    # Validar tipo de arquivo
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas arquivos .xlsx são aceitos"
        )
    
    try:
        # Salvar arquivo
        caminho_arquivo, nome_arquivo, tamanho = salvar_arquivo_upload(file)
        
        # Criar registro de importação (status PENDENTE)
        importacao = ImportacaoInsumo(
            restaurante_id=restaurante_id,
           # usuario_id=None,  #current_user.id,
            nome_arquivo=nome_arquivo,
            caminho_arquivo=caminho_arquivo,
            tamanho_arquivo=tamanho,
            tipo_mime=file.content_type or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            status=StatusImportacao.PENDENTE
        )
        
        db.add(importacao)
        db.commit()
        db.refresh(importacao)
        
        # Gerar preview
        service = ImportacaoService(db)
        preview = service.gerar_preview(caminho_arquivo, nome_arquivo)
        
        return {
            "importacao_id": importacao.id,
            "preview": preview.model_dump()
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )


# ============================================================================
# ENDPOINT: CONFIRMAR E PROCESSAR IMPORTAÇÃO
# ============================================================================

@router.post(
    "/processar",
    response_model=ImportacaoInsumoResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirmar e processar importação",
    description="Confirma a importação e processa o arquivo Excel"
)
async def processar_importacao(
    confirmacao: ConfirmacaoImportacao,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """
    Endpoint para confirmar e processar a importação.
    
    Fluxo:
    1. Busca importação pendente
    2. Valida status
    3. Processa arquivo Excel
    4. Cria insumos no banco
    5. Atualiza estatísticas
    6. Retorna resultado
    """
    # Buscar importação
    importacao = db.query(ImportacaoInsumo).filter(
        ImportacaoInsumo.id == confirmacao.importacao_id
    ).first()
    
    if not importacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Importação não encontrada"
        )
    
    # Validar status
    if importacao.status != StatusImportacao.PENDENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Importação já foi processada (status: {importacao.status})"
        )
    
    # Validar confirmação
    if not confirmacao.confirmar:
        # Cancelar importação
        importacao.status = StatusImportacao.ERRO
        importacao.mensagem_erro = "Importação cancelada pelo usuário"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Importação cancelada"
        )
    
    # Atualizar observações se fornecidas
    if confirmacao.observacoes:
        importacao.observacoes = confirmacao.observacoes
        db.commit()
    
    # Processar importação
    service = ImportacaoService(db)
    sucesso, mensagem = service.processar_importacao(
        importacao.id,
        importacao.restaurante_id,
        mapeamento_customizado=confirmacao.mapeamento_colunas
    )
    
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=mensagem
        )
    
    # Retornar importação atualizada
    db.refresh(importacao)
    return importacao


# ============================================================================
# ENDPOINT: LISTAR IMPORTAÇÕES
# ============================================================================

@router.get(
    "/",
    response_model=ImportacaoInsumoListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar importações",
    description="Lista todas as importações com paginação e filtros"
)
async def listar_importacoes(
    restaurante_id: Optional[int] = None,
    status: Optional[StatusImportacao] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista importações com filtros opcionais.
    
    Filtros disponíveis:
    - restaurante_id: Filtrar por restaurante
    - status: Filtrar por status (pendente, processando, sucesso, etc.)
    - skip/limit: Paginação
    """
    # Construir query
    query = db.query(ImportacaoInsumo)
    
    # Aplicar filtros
    if restaurante_id:
        query = query.filter(ImportacaoInsumo.restaurante_id == restaurante_id)
    
    if status:
        query = query.filter(ImportacaoInsumo.status == status)
    
    # Contar total
    total = query.count()
    
    # Aplicar paginação e ordenação
    importacoes = query.order_by(
        ImportacaoInsumo.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return ImportacaoInsumoListResponse(
        importacoes=importacoes,
        total=total,
        skip=skip,
        limit=limit
    )


# ============================================================================
# ENDPOINT: BUSCAR IMPORTAÇÃO POR ID
# ============================================================================

@router.get(
    "/{importacao_id}",
    response_model=ImportacaoInsumoResponse,
    status_code=status.HTTP_200_OK,
    summary="Buscar importação por ID",
    description="Retorna detalhes de uma importação específica"
)
async def buscar_importacao(
    importacao_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Busca uma importação específica por ID.
    """
    importacao = db.query(ImportacaoInsumo).filter(
        ImportacaoInsumo.id == importacao_id
    ).first()
    
    if not importacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Importação não encontrada"
        )
    
    return importacao


# ============================================================================
# ENDPOINT: ESTATÍSTICAS DA IMPORTAÇÃO
# ============================================================================

@router.get(
    "/{importacao_id}/estatisticas",
    response_model=EstatisticasImportacao,
    status_code=status.HTTP_200_OK,
    summary="Estatísticas da importação",
    description="Retorna estatísticas detalhadas de uma importação"
)
async def estatisticas_importacao(
    importacao_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna estatísticas calculadas de uma importação.
    """
    importacao = db.query(ImportacaoInsumo).filter(
        ImportacaoInsumo.id == importacao_id
    ).first()
    
    if not importacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Importação não encontrada"
        )
    
    return calcular_estatisticas(importacao)


# ============================================================================
# ENDPOINT: DELETAR IMPORTAÇÃO
# ============================================================================

@router.delete(
    "/{importacao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar importação",
    description="Deleta uma importação e seus registros relacionados"
)
async def deletar_importacao(
    importacao_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deleta uma importação.
    
    Nota: Os insumos criados por esta importação NÃO serão deletados
    (CASCADE com ON DELETE SET NULL).
    """
    importacao = db.query(ImportacaoInsumo).filter(
        ImportacaoInsumo.id == importacao_id
    ).first()
    
    if not importacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Importação não encontrada"
        )
    
    # Deletar arquivo físico
    try:
        arquivo_path = Path(importacao.caminho_arquivo)
        if arquivo_path.exists():
            arquivo_path.unlink()
    except Exception as e:
        # Log do erro mas não falha a operação
        print(f"Aviso: Não foi possível deletar arquivo: {e}")
    
    # Deletar registro
    db.delete(importacao)
    db.commit()
    
    return None