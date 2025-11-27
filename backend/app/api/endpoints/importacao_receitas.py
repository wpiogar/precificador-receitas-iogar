# ============================================================================
# ENDPOINTS - IMPORTAÇÃO DE RECEITAS VIA EXCEL
# ============================================================================
# Descrição: Endpoints para upload e processamento de arquivos Excel de receitas
# Data: 25/11/2025
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
from app.models.user import User
from app.schemas.importacao_receita import (
    PreviewImportacaoReceita,
    ConfirmacaoImportacaoReceita,
    ResultadoImportacaoReceita,
    UploadReceitaResponse,
    ReceitaPreview,
    InsumoReceitaPreview
)
from app.services.receita_import_service import ReceitaImportService
from app.api.deps import get_current_user

# Criar roteador
router = APIRouter()

# Diretório para armazenar arquivos
UPLOAD_DIR = Path("uploads/receitas")
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


# ============================================================================
# ENDPOINT: UPLOAD E PREVIEW DE RECEITAS
# ============================================================================

@router.post(
    "/upload",
    response_model=UploadReceitaResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload de arquivo Excel de receitas",
    description="Faz upload do arquivo Excel e retorna preview das receitas que serão importadas"
)
async def upload_arquivo_receitas(
    file: UploadFile = File(..., description="Arquivo Excel (.xlsx)"),
    restaurante_id: int = Form(..., description="ID do restaurante"),
    db: Session = Depends(get_db),
):
    """
    Endpoint para upload de arquivo Excel de receitas e geração de preview.
    
    Fluxo:
    1. Recebe arquivo Excel
    2. Valida formato
    3. Processa e identifica receitas
    4. Faz matching de insumos
    5. Retorna preview com receitas prontas e com problemas
    """

    # ADICIONAR ESTAS LINHAS:
    print(f"=" * 80)
    print(f"UPLOAD RECEITAS CHAMADO")
    print(f"Arquivo: {file.filename}")
    print(f"Content-Type: {file.content_type}")
    print(f"Restaurante ID: {restaurante_id}")
    print(f"=" * 80)
    # Validar tipo de arquivo
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas arquivos .xlsx são aceitos"
        )
    
    try:
        # Salvar arquivo
        caminho_arquivo, nome_arquivo, tamanho = salvar_arquivo_upload(file)
        
        # Processar arquivo
        service = ReceitaImportService(db, restaurante_id)
        resultado = service.processar_arquivo(caminho_arquivo)
        
        # Buscar nomes dos insumos no sistema para exibir no preview
        resultado_enriquecido = _enriquecer_preview_com_nomes_insumos(
            db, resultado
        )
        
        # Montar preview
        preview = PreviewImportacaoReceita(
            nome_arquivo=nome_arquivo,
            total_receitas=resultado_enriquecido["total_receitas"],
            estatisticas=resultado_enriquecido["estatisticas"],
            receitas_prontas=_converter_receitas_para_preview(
                resultado_enriquecido["receitas_prontas"], True
            ),
            receitas_com_insumos_faltando=_converter_receitas_para_preview(
                resultado_enriquecido["receitas_com_insumos_faltando"], False
            ),
            avisos=_gerar_avisos(resultado_enriquecido)
        )
        
        # Retornar preview (importacao_id será 0 por enquanto, 
        # pois não estamos salvando no banco ainda)
        return UploadReceitaResponse(
            importacao_id=0,  # Temporário
            preview=preview
        )
        
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
    response_model=ResultadoImportacaoReceita,
    status_code=status.HTTP_200_OK,
    summary="Confirmar e processar importação de receitas",
    description="Confirma a importação e cria as receitas no banco de dados"
)
async def processar_importacao_receitas(
    arquivo: UploadFile = File(..., description="Arquivo Excel (.xlsx)"),
    restaurante_id: int = Form(..., description="ID do restaurante"),
    receitas_selecionadas: str = Form(..., description="Lista de códigos de receitas (JSON string)"),
    db: Session = Depends(get_db),
):
    """
    Endpoint para confirmar e processar a importação de receitas.
    ...
    """
    # ============================================================================
    # DEBUG: Log dos dados recebidos
    # ============================================================================
    print("=" * 80)
    print("PROCESSAR IMPORTAÇÃO CHAMADO")
    print(f"Receitas selecionadas (raw): {receitas_selecionadas}")
    print(f"Restaurante ID: {restaurante_id}")
    print(f"Arquivo: {arquivo.filename}")
    print("=" * 80)
    
    # Converter string JSON para lista de inteiros
    import json
    try:
        receitas_selecionadas_list = json.loads(receitas_selecionadas)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lista de receitas inválida"
        )
    
    print(f"Receitas selecionadas (parsed): {receitas_selecionadas_list}")
    
    from app.models.receita import Receita, ReceitaInsumo

    try:
        data_inicio = datetime.now()

        # Salvar arquivo temporariamente
        caminho_arquivo, _, _ = salvar_arquivo_upload(arquivo)

        # Processar arquivo para obter dados completos
        service = ReceitaImportService(db, restaurante_id)
        resultado_processamento = service.processar_arquivo(caminho_arquivo)

        # Filtrar apenas receitas selecionadas pelo usuário
        receitas_para_importar = [
            r for r in resultado_processamento.get("receitas_prontas", [])
            if r["codigo"] in receitas_selecionadas_list  # ← MUDOU AQUI
        ]
        
        receitas_sucesso = []
        receitas_erro = []
        
        # Criar cada receita no banco
        for receita_data in receitas_para_importar:
            try:
                print("=" * 80)
                print(f"🔧 TENTANDO CRIAR RECEITA: {receita_data['nome']}")
                print(f"   Código: {receita_data['codigo']}")
                print(f"   Tipo: {receita_data['tipo']}")
                print("=" * 80)
                # Criar receita
                nova_receita = Receita(
                    codigo=str(receita_data["codigo"]),
                    nome=receita_data["nome"],
                    grupo=receita_data["tipo"],  # COMPOSTO ou PROCESSADO
                    subgrupo="IMPORTADO",  # Valor padrao para receitas importadas
                    restaurante_id=restaurante_id,
                    quantidade=1.0,
                    fator=1.0,
                    unidade="un",
                    ativo=True
                )
                
                db.add(nova_receita)
                db.flush()  # Flush para obter o ID

                print(f"✅ Receita criada com ID: {nova_receita.id}")

                # Vincular insumos à receita
                insumos_vinculados = 0
                if "insumos" in receita_data and receita_data["insumos"]:
                    from app.models.receita import ReceitaInsumo
                    
                    for insumo_data in receita_data["insumos"]:
                        receita_insumo = ReceitaInsumo(
                            receita_id=nova_receita.id,
                            insumo_id=insumo_data["insumo_id"],
                            quantidade_necessaria=insumo_data["quantidade"],
                            unidade_medida=insumo_data["unidade"]
                        )
                        db.add(receita_insumo)
                        insumos_vinculados += 1
                    
                    print(f"✅ {insumos_vinculados} insumos vinculados")

                db.commit()
                
                receitas_sucesso.append({
                    "codigo": receita_data["codigo"],
                    "nome": receita_data["nome"],
                    "mensagem": "Importada com sucesso"
                })

                print(f"✅ SUCESSO: {receita_data['nome']}")
                print("=" * 80)
                
            except Exception as e:
                print(f"❌ ERRO ao criar receita {receita_data['nome']}: {str(e)}")
                print(f"   Tipo de erro: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                print("=" * 80)
                db.rollback()
                receitas_erro.append({
                    "codigo": receita_data["codigo"],
                    "nome": receita_data["nome"],
                    "mensagem": f"Erro: {str(e)}"
                })
        
        # Preparar resultado
        status_final = "SUCESSO" if len(receitas_erro) == 0 else "PARCIAL"
        if len(receitas_sucesso) == 0:
            status_final = "ERRO"
        
        resultado = ResultadoImportacaoReceita(
            importacao_id=0,
            status=status_final,
            total_receitas_processadas=len(receitas_para_importar),
            receitas_importadas_sucesso=len(receitas_sucesso),
            receitas_com_erro=len(receitas_erro),
            receitas_sucesso=receitas_sucesso,
            receitas_erro=receitas_erro,
            mensagem=f"{len(receitas_sucesso)} receitas importadas com sucesso, {len(receitas_erro)} com erro",
            data_inicio=data_inicio,
            data_fim=datetime.now()
        )
        
        return resultado
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar importação: {str(e)}"
        )


# ============================================================================
# FUNÇÕES AUXILIARES INTERNAS
# ============================================================================

def _enriquecer_preview_com_nomes_insumos(db: Session, resultado: dict) -> dict:
    """
    Enriquece o resultado com os nomes dos insumos encontrados no sistema.
    
    Args:
        db: Sessão do banco
        resultado: Resultado do processamento
        
    Returns:
        Resultado enriquecido com nomes dos insumos
    """
    from app.models.insumo import Insumo
    
    # Processar receitas prontas
    for receita in resultado.get("receitas_prontas", []):
        # TODO: Buscar insumos no banco e adicionar nomes
        pass
    
    # Processar receitas com insumos faltando
    for receita in resultado.get("receitas_com_insumos_faltando", []):
        # TODO: Buscar insumos no banco e adicionar nomes
        pass
    
    return resultado


def _converter_receitas_para_preview(
    receitas: List[dict], 
    pode_importar: bool
) -> List[ReceitaPreview]:
    """
    Converte lista de receitas dict para ReceitaPreview.
    
    Args:
        receitas: Lista de dicts com dados das receitas
        pode_importar: Se as receitas podem ser importadas
        
    Returns:
        Lista de ReceitaPreview
    """
    preview_list = []
    
    for receita in receitas:
        # Contar insumos não encontrados
        insumos_nao_encontrados = len(
            receita.get("insumos_faltando", [])
        )
        
        # Criar preview de insumos
        insumos_preview = []
        for insumo in receita.get("insumos_faltando", []):
            insumos_preview.append(
                InsumoReceitaPreview(
                    codigo=None,
                    nome=insumo["nome"],
                    quantidade=insumo["quantidade"],
                    unidade=insumo["unidade"],
                    custo=0.0,
                    valor=0.0,
                    tipo_match="NAO_ENCONTRADO",
                    score_similaridade=0.0
                )
            )
        
        preview = ReceitaPreview(
            codigo=receita["codigo"],
            nome=receita["nome"],
            tipo=receita["tipo"],
            total_insumos=receita.get("total_insumos", 0),
            custo_total=receita.get("custo_total", 0.0),
            valor_total=receita.get("valor_total", 0.0),
            insumos=insumos_preview,
            insumos_nao_encontrados=insumos_nao_encontrados,
            pode_importar=pode_importar
        )
        
        preview_list.append(preview)
    
    return preview_list


def _gerar_avisos(resultado: dict) -> List[str]:
    """
    Gera lista de avisos baseado no resultado do processamento.
    
    Args:
        resultado: Resultado do processamento
        
    Returns:
        Lista de avisos
    """
    avisos = []
    
    # Avisos sobre receitas com insumos faltando
    total_com_problema = len(resultado.get("receitas_com_insumos_faltando", []))
    if total_com_problema > 0:
        avisos.append(
            f"{total_com_problema} receita(s) não podem ser importadas "
            f"pois possuem insumos não cadastrados no sistema"
        )
    
    # Avisos sobre matching fuzzy
    insumos_fuzzy = resultado.get("estatisticas", {}).get("insumos_matched_fuzzy", 0)
    if insumos_fuzzy > 0:
        avisos.append(
            f"{insumos_fuzzy} insumo(s) foram identificados por similaridade. "
            f"Revise se os matches estão corretos"
        )
    
    # Avisos sobre insumos não encontrados
    insumos_nao_encontrados = resultado.get("estatisticas", {}).get(
        "insumos_nao_encontrados", 0
    )
    if insumos_nao_encontrados > 0:
        avisos.append(
            f"{insumos_nao_encontrados} insumo(s) não foram encontrados no sistema. "
            f"Cadastre-os antes de importar as receitas"
        )
    
    return avisos