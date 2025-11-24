# ============================================================================
# API ENDPOINTS RESTAURANTES - Rotas REST para gestão de restaurantes
# ============================================================================
# Descrição: Define todas as rotas da API REST para operações com restaurantes
# Inclui CRUD completo + gestão de unidades/filiais + estatísticas
# Data: 12/09/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.receita import Restaurante 

# Importações internas do projeto
from app.api.deps import get_db
from app.crud import receita as crud_receita
from app.schemas.receita import (
    RestauranteCreate,
    UnidadeCreate,
    RestauranteUpdate,
    RestauranteResponse,
    RestauranteGrid,
    RestauranteSimplificado
)

# ============================================================================
# CONFIGURAÇÃO DO ROTEADOR
# ============================================================================

# Cria o roteador para agrupar todas as rotas de restaurantes
router = APIRouter()

# ============================================================================
# ENDPOINTS DE CONSULTA (GET)
# ============================================================================

@router.get("/grid", response_model=List[RestauranteGrid])
def listar_restaurantes_grid(
    db: Session = Depends(get_db)
):
    """
    Lista restaurantes em formato otimizado para grid.
    
    **Funcionalidades:**
    - Retorna apenas restaurantes matriz
    - Inclui quantidade de unidades calculada
    - Ordenação por nome
    - Dados otimizados para exibição
    
    **Retorna:**
    - Lista de restaurantes com campos essenciais para grid
    - Campo quantidade_unidades calculado automaticamente
    """
    try:
        restaurantes = crud_receita.get_restaurantes_grid(db)
        
        # Converter para formato grid
        resultado = []
        for restaurante in restaurantes:
            resultado.append({
                "id": restaurante.id,
                "nome": restaurante.nome,
                "cidade": restaurante.cidade,
                "estado": restaurante.estado,
                "tipo": restaurante.tipo,
                "tem_delivery": restaurante.tem_delivery,
                "eh_matriz": restaurante.eh_matriz,
                "quantidade_unidades": restaurante.quantidade_unidades,
                "ativo": restaurante.ativo
            })
        
        return resultado
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar restaurantes: {str(e)}"
        )

@router.get("/com-unidades", response_model=List[dict])
def listar_restaurantes_com_unidades(
    db: Session = Depends(get_db)
):
    """
    Lista restaurantes com suas unidades/filiais aninhadas.
    
    **Funcionalidades:**
    - Retorna matrizes com lista de unidades
    - Estrutura hierárquica para grid expandida
    - Dados completos de localização
    
    **Retorna:**
    - Restaurantes matriz com array 'unidades' contendo filiais
    - Ideal para grids que permitem expansão/colapso
    """
    try:
        return crud_receita.get_restaurantes_com_unidades(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar restaurantes com unidades: {str(e)}"
        )

@router.get("/tipos", response_model=List[str])
def listar_tipos_restaurante():
    """
    Lista todos os tipos de estabelecimento disponíveis.
    
    **Tipos disponíveis:**
    - restaurante, bar, pub, quiosque
    - lanchonete, cafeteria, pizzaria
    - hamburgueria, churrascaria, bistrô
    - fast_food, food_truck
    
    **Uso:**
    - Popular dropdown de tipos no frontend
    - Validação de tipos válidos
    """
    return crud_receita.get_tipos_restaurante()

@router.get("/{restaurante_id}", response_model=RestauranteResponse)
def buscar_restaurante(
    restaurante_id: int,
    db: Session = Depends(get_db)
):
    """
    Busca um restaurante específico por ID.
    
    **Retorna:**
    - Dados completos do restaurante
    - Informações de unidade (matriz/filial)
    - Metadados de criação/atualização
    """
    restaurante = crud_receita.get_restaurante_by_id(db, restaurante_id)
    if not restaurante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurante não encontrado"
        )
    
    # Calcular quantidade de unidades dinamicamente
    quantidade_unidades = 1
    if restaurante.eh_matriz and restaurante.unidades:
        quantidade_unidades = 1 + len(restaurante.unidades)
    elif not restaurante.eh_matriz and restaurante.restaurante_pai:
        quantidade_unidades = restaurante.restaurante_pai.quantidade_unidades
    
    # Preparar resposta
    response_data = {
        **restaurante.__dict__,
        "quantidade_unidades": quantidade_unidades
    }
    
    return response_data

@router.get("/{restaurante_id}/estatisticas", response_model=dict)
def buscar_estatisticas_restaurante(
    restaurante_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas de um restaurante específico.
    
    **Estatísticas incluídas:**
    - Quantidade de unidades
    - Total de receitas cadastradas
    - Últimos insumos cadastrados (futuro)
    - Últimas receitas cadastradas (futuro)
    
    **Uso:**
    - Dashboard de estatísticas
    - Widgets informativos
    """
    try:
        return crud_receita.get_restaurante_estatisticas(db, restaurante_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar estatísticas: {str(e)}"
        )

# ============================================================================
# ENDPOINTS DE CRIAÇÃO (POST)
# ============================================================================

@router.post("/", response_model=RestauranteResponse)
def criar_restaurante(
    restaurante: RestauranteCreate,
    db: Session = Depends(get_db)
):
    """
    Cria um novo restaurante matriz.
    
    **Validações:**
    - CNPJ único (obrigatório para matriz)
    - Nome obrigatório
    - Tipo válido conforme lista disponível
    
    **Comportamento:**
    - Sempre cria como matriz (eh_matriz=True)
    - CNPJ deve ser único no sistema
    - Define localização completa
    """
    try:
        # ===========================================================================
        # Normalizar tipo de estabelecimento para maiúsculo antes de salvar
        # ===========================================================================
        restaurante.tipo = restaurante.tipo.upper()
        
        restaurante_criado = crud_receita.create_restaurante(db, restaurante)
        
        # Calcular quantidade de unidades (sempre 1 para novo restaurante)
        response_data = {
            **restaurante_criado.__dict__,
            "quantidade_unidades": 1
        }
        
        return response_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar restaurante: {str(e)}"
        )

@router.post("/{restaurante_id}/unidades", response_model=RestauranteResponse)
def criar_unidade(
    restaurante_id: int,
    unidade: UnidadeCreate,
    db: Session = Depends(get_db)
):
    """
    Cria uma nova unidade/filial para um restaurante matriz.
    
    **Validações:**
    - Restaurante matriz deve existir
    - Apenas matrizes podem ter filiais
    - Dados de localização obrigatórios
    
    **Comportamento:**
    - Herda nome e tipo da matriz
    - Não possui CNPJ próprio
    - Vincula à matriz via restaurante_pai_id
    """
    try:
        unidade_criada = crud_receita.create_unidade(db, restaurante_id, unidade)
        
        # Preparar resposta com quantidade de unidades da matriz
        matriz = crud_receita.get_restaurante_by_id(db, restaurante_id)
        quantidade_total = 1 + len(matriz.unidades) if matriz and matriz.unidades else 2
        
        response_data = {
            **unidade_criada.__dict__,
            "quantidade_unidades": quantidade_total
        }
        
        return response_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar unidade: {str(e)}"
        )

# ============================================================================
# ENDPOINTS DE ATUALIZAÇÃO (PUT)
# ============================================================================

@router.put("/{restaurante_id}", response_model=RestauranteResponse)
def atualizar_restaurante(
    restaurante_id: int,
    restaurante_update: RestauranteUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza dados de um restaurante.
    
    **Validações:**
    - CNPJ único (se sendo alterado)
    - Restaurante deve existir
    - Tipo válido conforme lista
    
    **Comportamento:**
    - Atualização parcial (apenas campos enviados)
    - Mantém estrutura de matriz/filial
    - Valida unicidade de CNPJ
    """
    try:
        restaurante_atualizado = crud_receita.update_restaurante(db, restaurante_id, restaurante_update)
        if not restaurante_atualizado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurante não encontrado"
            )
        
        # Calcular quantidade de unidades
        quantidade_unidades = 1
        if restaurante_atualizado.eh_matriz and restaurante_atualizado.unidades:
            quantidade_unidades = 1 + len(restaurante_atualizado.unidades)
        elif not restaurante_atualizado.eh_matriz and restaurante_atualizado.restaurante_pai:
            quantidade_unidades = restaurante_atualizado.restaurante_pai.quantidade_unidades
        
        response_data = {
            **restaurante_atualizado.__dict__,
            "quantidade_unidades": quantidade_unidades
        }
        
        return response_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar restaurante: {str(e)}"
        )

# ============================================================================
# ENDPOINTS DE EXCLUSÃO (DELETE)
# ============================================================================

@router.delete("/{restaurante_id}")
def excluir_restaurante(
    restaurante_id: int,
    db: Session = Depends(get_db)
):
    """
    Exclui um restaurante (e suas unidades se for matriz).
    
    **Validações:**
    - Verifica se existem receitas vinculadas
    - Não permite exclusão com dados dependentes
    
    **Comportamento:**
    - Se matriz: exclui todas as unidades (cascade)
    - Se filial: exclui apenas a unidade
    - Protege integridade dos dados
    """
    try:
        sucesso = crud_receita.delete_restaurante(db, restaurante_id)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurante não encontrado"
            )
        
        return {"message": "Restaurante excluído com sucesso"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao excluir restaurante: {str(e)}"
        )

# ============================================================================
# ENDPOINTS UTILITÁRIOS
# ============================================================================

@router.get("/", response_model=List[RestauranteSimplificado])
def listar_restaurantes_simples(
    skip: int = Query(0, ge=0, description="Número de registros a pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros por página"),
    incluir_filiais: bool = Query(False, description="Incluir unidades/filiais na listagem"),
    db: Session = Depends(get_db)
):
    """
    Lista restaurantes em formato simplificado com paginação.
    
    **Parâmetros:**
    - incluir_filiais: se True, inclui filiais na listagem
    - skip/limit: paginação padrão
    
    **Uso:**
    - Dropdowns de seleção
    - Listagens simples sem detalhes
    """
    if incluir_filiais:
        restaurantes = crud_receita.get_restaurantes(db, skip=skip, limit=limit)
    else:
        # Apenas matrizes
        restaurantes = crud_receita.get_restaurantes_grid(db)

        # Carregar unidades para cada matriz
        for restaurante in restaurantes:
            if restaurante.eh_matriz:
                # Buscar unidades filhas desta matriz
                unidades_filhas = db.query(Restaurante).filter(
                    Restaurante.restaurante_pai_id == restaurante.id,
                    Restaurante.ativo == True
                ).all()
                
                # Garantir que o atributo existe no objeto
                if hasattr(restaurante, 'unidades'):
                    restaurante.unidades = unidades_filhas
                else:
                    # Adicionar manualmente se não existir
                    restaurante.__dict__['unidades'] = unidades_filhas
                    
                print(f"DEBUG - Restaurante {restaurante.nome}: {len(unidades_filhas)} unidades")
            else:
                if hasattr(restaurante, 'unidades'):
                    restaurante.unidades = []
                else:
                    restaurante.__dict__['unidades'] = []

        # Aplicar paginação manual para matrizes
        restaurantes = restaurantes[skip:skip+limit]
    
    return [
        {
            "id": r.id,
            "nome": r.nome,
            "tipo": r.tipo,
            "cidade": r.cidade,
            "ativo": r.ativo
        }
        for r in restaurantes
    ]