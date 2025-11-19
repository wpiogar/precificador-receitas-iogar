# ============================================================================
# ENDPOINTS DE LIMPEZA DE DADOS - PAINEL ADMINISTRATIVO
# ============================================================================
# Descrição: Endpoints para limpeza seletiva de dados do sistema (apenas ADMIN)
# Acesso via tela de Configurações > Limpeza de Dados
# Data: 24/10/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional, Literal
from datetime import datetime, date
from pydantic import BaseModel, Field

# Importar dependências
from app.api.deps import get_db, get_admin_user
from app.models.user import User
from app.models.receita import Receita, ReceitaInsumo, Restaurante
from app.models.insumo import Insumo
from app.models.fornecedor import Fornecedor
from app.models.fornecedor_insumo import FornecedorInsumo
from app.models.taxonomia import Taxonomia

# Criar router (apenas ADMIN tem acesso)
router = APIRouter()

# ============================================================================
# SCHEMAS
# ============================================================================

class EstatisticasLimpeza(BaseModel):
    """Schema para estatísticas de dados"""
    total_receitas: int
    total_insumos: int
    total_fornecedores: int
    total_fornecedor_insumos: int
    total_restaurantes: int
    total_taxonomias: int
    total_usuarios: int

class FiltroLimpeza(BaseModel):
    """Schema para filtros de limpeza"""
    data_inicio: Optional[date] = Field(None, description="Data inicial (created_at)")
    data_fim: Optional[date] = Field(None, description="Data final (created_at)")
    restaurante_id: Optional[int] = Field(None, description="Filtrar por restaurante")

class ResultadoLimpeza(BaseModel):
    """Schema para resultado da limpeza"""
    secao: str
    registros_removidos: int
    sucesso: bool
    mensagem: str

# ============================================================================
# ENDPOINT: ESTATÍSTICAS GERAIS
# ============================================================================

@router.get("/estatisticas", response_model=EstatisticasLimpeza)
def obter_estatisticas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Retorna estatísticas gerais de dados no sistema.
    
    Acesso: Apenas ADMIN
    
    Obs: Mostra TODOS os registros, mas ao limpar:
    - Restaurantes: mantém ID 1
    - Usuários: mantém o admin atual
    """
    # Contar registros em cada tabela
    stats = EstatisticasLimpeza(
        total_receitas=db.query(func.count(Receita.id)).scalar(),
        total_insumos=db.query(func.count(Insumo.id)).scalar(),
        total_fornecedores=db.query(func.count(Fornecedor.id)).scalar(),
        total_fornecedor_insumos=db.query(func.count(FornecedorInsumo.id)).scalar(),
        total_restaurantes=db.query(func.count(Restaurante.id)).scalar(),
        total_taxonomias=db.query(func.count(Taxonomia.id)).scalar(),
        total_usuarios=db.query(func.count(User.id)).scalar()  # Mostra todos
    )
    
    return stats

# ============================================================================
# ENDPOINT: LIMPAR RECEITAS
# ============================================================================

@router.delete("/receitas", response_model=ResultadoLimpeza)
def limpar_receitas(
    filtros: Optional[FiltroLimpeza] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Remove receitas do sistema com filtros opcionais.
    
    Acesso: Apenas ADMIN
    
    Filtros disponíveis:
    - data_inicio/data_fim: Remove receitas criadas no período
    - restaurante_id: Remove apenas receitas de um restaurante
    
    IMPORTANTE: Remove primeiro os vínculos em receita_insumos,
    depois as receitas, respeitando a ordem de dependência.
    """
    try:
        # Query base para receitas
        query_receitas = db.query(Receita)
        
        # Aplicar filtros
        if filtros:
            if filtros.data_inicio:
                query_receitas = query_receitas.filter(Receita.created_at >= filtros.data_inicio)
            if filtros.data_fim:
                query_receitas = query_receitas.filter(Receita.created_at <= filtros.data_fim)
            if filtros.restaurante_id:
                query_receitas = query_receitas.filter(Receita.restaurante_id == filtros.restaurante_id)
        
        # Obter IDs das receitas que serão deletadas
        receita_ids = [r.id for r in query_receitas.all()]
        total = len(receita_ids)
        
        if total == 0:
            return ResultadoLimpeza(
                secao="receitas",
                registros_removidos=0,
                sucesso=True,
                mensagem="Nenhuma receita encontrada com os filtros aplicados"
            )
        
        # PASSO 1: Deletar vínculos em receita_insumos PRIMEIRO
        db.query(ReceitaInsumo).filter(ReceitaInsumo.receita_id.in_(receita_ids)).delete(synchronize_session=False)
        
        # PASSO 2: Deletar as receitas
        db.query(Receita).filter(Receita.id.in_(receita_ids)).delete(synchronize_session=False)
        
        # Commit das alterações
        db.commit()
        
        return ResultadoLimpeza(
            secao="receitas",
            registros_removidos=total,
            sucesso=True,
            mensagem=f"{total} receita(s) removida(s) com sucesso"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao limpar receitas: {str(e)}"
        )

# ============================================================================
# ENDPOINT: LIMPAR INSUMOS
# ============================================================================

@router.delete("/insumos", response_model=ResultadoLimpeza)
def limpar_insumos(
    filtros: Optional[FiltroLimpeza] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Remove insumos do sistema com filtros opcionais.
    
    Acesso: Apenas ADMIN
    
    IMPORTANTE: Remove primeiro os vínculos em receita_insumos,
    depois os insumos, respeitando a ordem de dependência.
    """
    try:
        # Query base para insumos
        query_insumos = db.query(Insumo)
        
        # Aplicar filtros
        if filtros:
            if filtros.data_inicio:
                query_insumos = query_insumos.filter(Insumo.created_at >= filtros.data_inicio)
            if filtros.data_fim:
                query_insumos = query_insumos.filter(Insumo.created_at <= filtros.data_fim)
            if filtros.restaurante_id:
                query_insumos = query_insumos.filter(Insumo.restaurante_id == filtros.restaurante_id)
        
        # Obter IDs dos insumos que serão deletados
        insumo_ids = [i.id for i in query_insumos.all()]
        total = len(insumo_ids)
        
        if total == 0:
            return ResultadoLimpeza(
                secao="insumos",
                registros_removidos=0,
                sucesso=True,
                mensagem="Nenhum insumo encontrado com os filtros aplicados"
            )
        
        # PASSO 1: Deletar vínculos em receita_insumos PRIMEIRO
        db.query(ReceitaInsumo).filter(ReceitaInsumo.insumo_id.in_(insumo_ids)).delete(synchronize_session=False)
        
        # PASSO 2: Deletar os insumos
        db.query(Insumo).filter(Insumo.id.in_(insumo_ids)).delete(synchronize_session=False)
        
        # Commit das alterações
        db.commit()
        
        return ResultadoLimpeza(
            secao="insumos",
            registros_removidos=total,
            sucesso=True,
            mensagem=f"{total} insumo(s) removido(s) com sucesso"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao limpar insumos: {str(e)}"
        )

# ============================================================================
# ENDPOINT: LIMPAR FORNECEDORES
# ============================================================================

@router.delete("/fornecedores", response_model=ResultadoLimpeza)
def limpar_fornecedores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Remove todos os fornecedores do sistema.
    
    Acesso: Apenas ADMIN
    
    ATENÇÃO: Remove também os insumos do catálogo dos fornecedores.
    """
    try:
        # Contar antes de deletar
        total = db.query(Fornecedor).count()
        
        # Deletar todos
        db.query(Fornecedor).delete()
        db.commit()
        
        return ResultadoLimpeza(
            secao="fornecedores",
            registros_removidos=total,
            sucesso=True,
            mensagem=f"{total} fornecedor(es) removido(s) com sucesso"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao limpar fornecedores: {str(e)}"
        )

# ============================================================================
# ENDPOINT: LIMPAR RESTAURANTES
# ============================================================================

@router.delete("/restaurantes", response_model=ResultadoLimpeza)
def limpar_restaurantes(
    manter_primeiro: bool = Query(
        True, 
        description="Manter o primeiro restaurante (ID 1) para testes"
    ),
    restaurante_id: Optional[int] = Query(
        None,
        description="ID específico do restaurante a ser removido"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Remove restaurantes do sistema.
    
    Acesso: Apenas ADMIN
    
    IMPORTANTE: Remove em cascata respeitando a ordem de dependência:
    1. Vínculos receita_insumos das receitas do restaurante
    2. Receitas do restaurante
    3. Insumos do restaurante
    4. Restaurante
    """
    try:
        # Query base para restaurantes
        query_restaurantes = db.query(Restaurante)
        
        # Se foi especificado um restaurante_id, remover apenas ele
        if restaurante_id:
            query_restaurantes = query_restaurantes.filter(Restaurante.id == restaurante_id)
        # Senão, opção de manter o primeiro restaurante
        elif manter_primeiro:
            query_restaurantes = query_restaurantes.filter(Restaurante.id != 1)
        
        # Obter IDs dos restaurantes que serão deletados
        restaurante_ids = [r.id for r in query_restaurantes.all()]
        total = len(restaurante_ids)
        
        if total == 0:
            return ResultadoLimpeza(
                secao="restaurantes",
                registros_removidos=0,
                sucesso=True,
                mensagem="Nenhum restaurante encontrado para remover (ID 1 mantido)"
            )
        
        # PASSO 1: Buscar IDs das receitas dos restaurantes
        receita_ids = [r.id for r in db.query(Receita).filter(Receita.restaurante_id.in_(restaurante_ids)).all()]
        
        # PASSO 2: Deletar vínculos receita_insumos das receitas PRIMEIRO
        if receita_ids:
            db.query(ReceitaInsumo).filter(ReceitaInsumo.receita_id.in_(receita_ids)).delete(synchronize_session=False)
        
        # PASSO 3: Deletar receitas dos restaurantes
        db.query(Receita).filter(Receita.restaurante_id.in_(restaurante_ids)).delete(synchronize_session=False)
        
        # PASSO 4: Deletar insumos dos restaurantes
        db.query(Insumo).filter(Insumo.restaurante_id.in_(restaurante_ids)).delete(synchronize_session=False)
        
        # PASSO 5: Deletar os restaurantes
        db.query(Restaurante).filter(Restaurante.id.in_(restaurante_ids)).delete(synchronize_session=False)
        
        # Commit das alterações
        db.commit()
        
        mensagem_extra = " (ID 1 mantido)" if manter_primeiro else ""
        
        return ResultadoLimpeza(
            secao="restaurantes",
            registros_removidos=total,
            sucesso=True,
            mensagem=f"{total} restaurante(s) removido(s) com sucesso{mensagem_extra}"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao limpar restaurantes: {str(e)}"
        )

# ============================================================================
# ENDPOINT: LIMPAR TUDO (RESET COMPLETO)
# ============================================================================

@router.delete("/limpar-tudo", response_model=List[ResultadoLimpeza])
def limpar_tudo(
    confirmacao: str = Query(
        ..., 
        description="Digite 'CONFIRMAR LIMPEZA TOTAL' para prosseguir"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Remove TODOS os dados do sistema (exceto o usuário ADMIN atual).
    
    Acesso: Apenas ADMIN
    
    ATENÇÃO: Esta ação é IRREVERSÍVEL!
    
    Ordem de limpeza:
    1. Receitas e seus vínculos
    2. Insumos
    3. Fornecedores e catálogo
    4. Restaurantes (mantém ID 1)
    5. Taxonomias
    6. Usuários (exceto o ADMIN atual)
    """
    # Validar confirmação
    if confirmacao != "CONFIRMAR LIMPEZA TOTAL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmação incorreta. Digite exatamente: CONFIRMAR LIMPEZA TOTAL"
        )
    
    resultados = []
    
    try:
        # 1. Limpar receitas
        total_receitas = db.query(Receita).count()
        db.query(ReceitaInsumo).delete()
        db.query(Receita).delete()
        resultados.append(ResultadoLimpeza(
            secao="receitas",
            registros_removidos=total_receitas,
            sucesso=True,
            mensagem=f"{total_receitas} receita(s) removida(s)"
        ))
        
        # 2. Limpar insumos
        total_insumos = db.query(Insumo).count()
        db.query(Insumo).delete()
        resultados.append(ResultadoLimpeza(
            secao="insumos",
            registros_removidos=total_insumos,
            sucesso=True,
            mensagem=f"{total_insumos} insumo(s) removido(s)"
        ))
        
        # 3. Limpar fornecedores
        total_fornecedores = db.query(Fornecedor).count()
        db.query(FornecedorInsumo).delete()
        db.query(Fornecedor).delete()
        resultados.append(ResultadoLimpeza(
            secao="fornecedores",
            registros_removidos=total_fornecedores,
            sucesso=True,
            mensagem=f"{total_fornecedores} fornecedor(es) removido(s)"
        ))
        
        # 4. Limpar restaurantes (mantém ID 1)
        total_restaurantes = db.query(Restaurante).filter(Restaurante.id != 1).count()
        db.query(Restaurante).filter(Restaurante.id != 1).delete()
        resultados.append(ResultadoLimpeza(
            secao="restaurantes",
            registros_removidos=total_restaurantes,
            sucesso=True,
            mensagem=f"{total_restaurantes} restaurante(s) removido(s) (mantido ID 1)"
        ))
        
        # 5. Limpar taxonomias
        total_taxonomias = db.query(Taxonomia).count()
        db.query(Taxonomia).delete()
        resultados.append(ResultadoLimpeza(
            secao="taxonomias",
            registros_removidos=total_taxonomias,
            sucesso=True,
            mensagem=f"{total_taxonomias} taxonomia(s) removida(s)"
        ))
        
        # 6. Limpar usuários (exceto o admin atual)
        total_usuarios = db.query(User).filter(User.id != current_user.id).count()
        db.query(User).filter(User.id != current_user.id).delete()
        resultados.append(ResultadoLimpeza(
            secao="usuarios",
            registros_removidos=total_usuarios,
            sucesso=True,
            mensagem=f"{total_usuarios} usuário(s) removido(s) (mantido admin atual)"
        ))
        
        # Commit de tudo
        db.commit()
        
        return resultados
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao limpar sistema: {str(e)}"
        )

# ============================================================================
# EXPORTAR ROUTER
# ============================================================================

__all__ = ["router"]