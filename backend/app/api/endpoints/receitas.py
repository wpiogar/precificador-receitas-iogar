#   ===================================================================================================
#   API REST para receitas - Endpoints HTTP
#   Descrição: Este arquivo define todas as rotas HTTP para operações com receitas,
#   restaurantes e cálculos de preços
#   Data: 15/08/2025
#   Autor: Will - Empresa: IOGAR
#   ===================================================================================================

import time
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.deps import get_db, get_current_user
from app.models.receita import Receita, ReceitaInsumo
from app.models.insumo import Insumo
from app.models.user import User, UserRole
from app.models.permission import ResourceType, ActionType, DataScope
from app.utils.permissions import PermissionChecker, apply_data_scope_filter, can_access_resource

from app.schemas.receita import (
    # Schemas de receitas
    ReceitaCreate, ReceitaUpdate, ReceitaResponse, ReceitaListResponse,
    # Schemas de receita-insumos
    ReceitaInsumoCreate, ReceitaInsumoUpdate, ReceitaInsumoResponse,
    # Schemas de cálculos (CORRIGIDOS)
    CalculoPrecosResponse, AtualizarCMVResponse,
    # Schemas de exportacao PDF
    PDFLoteRequest, PDFLoteResponse
)
from app.crud import receita as crud_receita

router = APIRouter()

# ===================================================================
# ENDPOINTS RECEITAS (FUNCIONALIDADE PRINCIPAL)
# ===================================================================

# Endpoint de teste temporario para diagnostico
@router.get("/test", summary="Teste de conectividade")
def test_endpoint():
    """
    Endpoint de teste sem autenticacao
    """
    return {"status": "ok", "message": "Endpoint de receitas funcionando"}

@router.get("/list", summary="Listar receitas")
def list_receitas(
    skip: int = Query(0, ge=0, description="Pular N registros"),
    limit: int = Query(1000, ge=1, le=5000, description="Limite de registros"),  # Aumentado de 100 para 1000, máximo 5000
    restaurante_id: Optional[int] = Query(None, description="Filtrar por restaurante"),
    grupo: Optional[str] = Query(None, description="Filtrar por grupo"),
    ativo: Optional[bool] = Query(None, description="Filtrar por status ativo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    data_scope = Depends(PermissionChecker(ResourceType.RECEITAS, ActionType.VISUALIZAR))
):
    """
    Lista receitas com CMVs calculados automaticamente baseado nos insumos.
    
    Permissões:
    - Requer permissão de VISUALIZAR RECEITAS
    - Filtra automaticamente por escopo de dados do usuário:
      * ADMIN/CONSULTANT: vê todas as receitas
      * OWNER: vê receitas de toda a rede
      * MANAGER/OPERATOR: vê receitas apenas da sua loja
    """
    
    # Buscar receitas básicas com filtro de escopo
    query = db.query(Receita)
    
    # Aplicar filtro de escopo de dados do usuário PRIMEIRO
    query = apply_data_scope_filter(
        query, 
        current_user, 
        data_scope, 
        Receita.restaurante_id,
        db=db
    )
    
    # CRÍTICO: Garantir que SEMPRE filtra pelo restaurante correto
    # Se restaurante_id foi fornecido na query, usar ele
    # Se não, usar o restaurante do usuário logado
    filtro_restaurante_id = restaurante_id if restaurante_id else current_user.restaurante_id
    
    if filtro_restaurante_id:
        query = query.filter(Receita.restaurante_id == filtro_restaurante_id)
        print(f"🔍 Filtrando receitas por restaurante_id: {filtro_restaurante_id}")
    
    if grupo:
        query = query.filter(Receita.grupo == grupo)
    
    if ativo is not None:
        query = query.filter(Receita.ativo == ativo)
    
    # DEBUG: Contar antes de aplicar paginação
    total_antes_paginacao = query.count()
    print("=" * 80)
    print("📊 DEBUG LISTAGEM DE RECEITAS")
    print(f"   Restaurante ID solicitado: {restaurante_id}")
    print(f"   Restaurante ID do usuário: {current_user.restaurante_id}")
    print(f"   Filtro restaurante_id final: {filtro_restaurante_id}")
    print(f"   Total de receitas ANTES da paginação: {total_antes_paginacao}")
    print(f"   Skip: {skip}, Limit: {limit}")
    print("=" * 80)
    
    # Aplicar paginação
    print(f"⚙️  Aplicando paginacao: offset={skip}, limit={limit}")
    
    # OTIMIZACAO: Buscar com eager loading para evitar N+1 queries  
    from sqlalchemy.orm import joinedload
    from app.models.receita import ReceitaInsumo
    query = query.options(
        joinedload(Receita.receita_insumos).joinedload(ReceitaInsumo.insumo),
        joinedload(Receita.receita_insumos).joinedload(ReceitaInsumo.receita_processada)
    )
    
    try:
        receitas = query.offset(skip).limit(limit).all()
        print(f"✅ Query executada com sucesso: {len(receitas)} receitas")
    except Exception as e:
        print(f"❌ Erro na query: {e}")
        import traceback
        traceback.print_exc()
        receitas = []

    # Retornar formato simplificado SEM processamento pesado
    receitas_response = []
    for receita in receitas:
        # Usar CMV ja salvo no banco
        preco_compra = (receita.cmv / 100) if receita.cmv else 0

        receitas_response.append({
            'id': receita.id,
            'nome': receita.nome,
            'codigo': receita.codigo,
            'grupo': receita.grupo,
            'subgrupo': receita.subgrupo,
            'responsavel': getattr(receita, 'responsavel', None),
            'preco_compra': preco_compra,
            'cmv_real': preco_compra,
            'cmv_20_porcento': preco_compra / 0.20 if preco_compra > 0 else 0,
            'cmv_25_porcento': preco_compra / 0.25 if preco_compra > 0 else 0,
            'cmv_30_porcento': preco_compra / 0.30 if preco_compra > 0 else 0,
            'restaurante_id': receita.restaurante_id,
            'ativo': receita.ativo,
            'created_at': receita.created_at,
            'updated_at': receita.updated_at,
            'tempo_preparo_minutos': getattr(receita, 'tempo_preparo_minutos', 30),
            'rendimento_porcoes': getattr(receita, 'rendimento_porcoes', 1),
            'sugestao_valor': receita.sugestao_valor / 100 if receita.sugestao_valor else 0,
            'unidade': getattr(receita, 'unidade', 'un'),
            'quantidade': getattr(receita, 'quantidade', 1),
            'fator': getattr(receita, 'fator', 1.0),
            'processada': getattr(receita, 'processada', False),
            'rendimento': float(receita.rendimento) if receita.rendimento else 0,
            'total_insumos': len(receita.receita_insumos),
            'insumos_processados': 0,
            'tem_insumos_sem_preco': receita.tem_insumos_sem_preco,
            'insumos_pendentes': receita.insumos_pendentes,
            'receita_insumos': [
                {
                    'id': ri.id,
                    'insumo_id': ri.insumo_id,
                    'quantidade_necessaria': ri.quantidade_necessaria,
                    'unidade_medida': ri.unidade_medida,
                    'custo_calculado': ri.custo_calculado,
                    'receita_processada_id': ri.receita_processada_id,
                    'insumo': {
                        'id': ri.insumo.id,
                        'nome': ri.insumo.nome,
                        'unidade': ri.insumo.unidade,
                        'preco_compra_real': ri.insumo.preco_compra_real
                    } if ri.insumo else None,
                    'receita_processada': {
                        'id': ri.receita_processada.id,
                        'nome': ri.receita_processada.nome,
                        'unidade': ri.receita_processada.unidade
                    } if ri.receita_processada else None
                }
                for ri in (receita.receita_insumos or [])
            ]
        })
       
    print(f"📊 Retornando {len(receitas_response)} receitas")
    return receitas_response

# ===================================================================================================
# FUNÇÃO AUXILIAR PARA CALCULAR CUSTO DA RECEITA
# ===================================================================================================

def calcular_custo_receita(db: Session, receita_id: int) -> dict:
    """
    Calcula o custo total de uma receita baseado nos seus insumos.
    NOVO: Suporta cálculo parcial quando há insumos sem preço.
    
    Returns:
        dict: {
            'custo_total': float,
            'tem_insumos_sem_preco': bool,
            'insumos_pendentes': list[int],
            'total_insumos': int,
            'insumos_com_preco': int
        }
    """
    try:
        # CRÍTICO: Buscar receita primeiro para validar restaurante
        receita = db.query(Receita).filter(Receita.id == receita_id).first()
        if not receita:
            print(f"⚠️ Receita ID {receita_id} não encontrada")
            return {
                'custo_total': 0.0,
                'tem_insumos_sem_preco': False,
                'insumos_pendentes': [],
                'total_insumos': 0,
                'insumos_com_preco': 0
            }
        
        # Buscar insumos da receita COM FILTRO DE RESTAURANTE
        query = """
        SELECT 
            ri.insumo_id,
            ri.quantidade_necessaria,
            i.preco_compra,
            i.nome,
            i.restaurante_id
        FROM receita_insumos ri
        JOIN insumos i ON ri.insumo_id = i.id  
        WHERE ri.receita_id = :receita_id
        AND (i.restaurante_id = :restaurante_id OR i.restaurante_id IS NULL)
        """
        
        result = db.execute(text(query), {
            'receita_id': receita_id,
            'restaurante_id': receita.restaurante_id
        })
        insumos_receita = result.fetchall()
        
        if not insumos_receita:
            print(f"⚠️ Receita ID {receita_id} não tem insumos cadastrados")
            return {
                'custo_total': 0.0,
                'tem_insumos_sem_preco': False,
                'insumos_pendentes': [],
                'total_insumos': 0,
                'insumos_com_preco': 0
            }
        
        custo_total = 0.0
        insumos_sem_preco = []
        insumos_com_preco_count = 0
        
        for insumo in insumos_receita:
            quantidade = float(insumo.quantidade_necessaria)
            preco_compra = insumo.preco_compra
            
            # Verificar se insumo tem preço
            if preco_compra is None or preco_compra == 0:
                # Insumo SEM preço - adicionar à lista de pendentes
                insumos_sem_preco.append(int(insumo.insumo_id))
                print(f"  ⚠️ {insumo.nome}: SEM PREÇO (pendente)")
            else:
                # Insumo COM preço - calcular custo
                preco_unitario = float(preco_compra) / 100  # Converter centavos para reais
                custo_insumo = quantidade * preco_unitario
                custo_total += custo_insumo
                insumos_com_preco_count += 1
                print(f"  ✅ {insumo.nome}: {quantidade} x R${preco_unitario:.2f} = R${custo_insumo:.2f}")
        
        tem_pendentes = len(insumos_sem_preco) > 0
        
        if tem_pendentes:
            print(f"⚠️ Receita ID {receita_id}: {len(insumos_sem_preco)} insumo(s) sem preço")
            print(f"💰 Custo PARCIAL (apenas {insumos_com_preco_count}/{len(insumos_receita)} insumos): R${custo_total:.2f}")
        else:
            print(f"✅ Custo TOTAL da receita ID {receita_id}: R${custo_total:.2f}")
        
        return {
            'custo_total': custo_total,
            'tem_insumos_sem_preco': tem_pendentes,
            'insumos_pendentes': insumos_sem_preco,
            'total_insumos': len(insumos_receita),
            'insumos_com_preco': insumos_com_preco_count
        }
        
    except Exception as e:
        print(f"❌ Erro ao calcular custo da receita {receita_id}: {e}")
        return {
            'custo_total': 0.0,
            'tem_insumos_sem_preco': False,
            'insumos_pendentes': [],
            'total_insumos': 0,
            'insumos_com_preco': 0
        }

@router.post("/", summary="Criar ou atualizar receita")
def create_receita_endpoint(
    receita_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    data_scope = Depends(PermissionChecker(ResourceType.RECEITAS, ActionType.CRIAR))
):
    """
    Cria ou atualiza uma receita.
    Permissoes:
    - Requer permissao de CRIAR RECEITAS
    - Validacoes por escopo:
      * LOJA: so pode criar para seu restaurante
      * REDE: pode criar para qualquer restaurante da rede
      * TODOS: pode criar para qualquer restaurante
    """
    # Rollback de qualquer transacao travada
    try:
        db.rollback()
    except:
        pass
    from app.utils.permissions import can_access_resource
    from fastapi import HTTPException, status
    from app.models.permission import DataScope
    
    # Extrair restaurante_id da receita
    restaurante_id = receita_data.get('restaurante_id')
    
    if not restaurante_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="restaurante_id é obrigatório"
        )
    
    # Validar se usuário pode criar receita para o restaurante especificado
    if data_scope == DataScope.LOJA:
        if restaurante_id != current_user.restaurante_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode criar receitas para o seu restaurante"
            )
    
    elif data_scope == DataScope.REDE:
        # Verificar se restaurante está na mesma rede
        from app.models.receita import Restaurante
        
        restaurante_target = db.query(Restaurante).filter(
            Restaurante.id == restaurante_id
        ).first()
        
        if not restaurante_target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurante não encontrado"
            )
        
        restaurante_user = db.query(Restaurante).filter(
            Restaurante.id == current_user.restaurante_id
        ).first()
        
        # Verificar se estão na mesma rede
        mesma_rede = False
        
        if restaurante_user and restaurante_target:
            # Mesmo pai ou um é pai do outro
            if (restaurante_user.restaurante_pai_id and 
                restaurante_user.restaurante_pai_id == restaurante_target.restaurante_pai_id):
                mesma_rede = True
            elif (restaurante_user.eh_matriz and 
                  restaurante_target.restaurante_pai_id == restaurante_user.id):
                mesma_rede = True
            elif (restaurante_user.restaurante_pai_id == restaurante_target.id and
                  restaurante_target.eh_matriz):
                mesma_rede = True
            elif restaurante_user.id == restaurante_target.id:
                mesma_rede = True
        
        if not mesma_rede:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode criar receitas para restaurantes da sua rede"
            )
        
    # Caça ao dados de porções
    print("=" * 50)
    print("FUNÇÃO POST CHAMADA!")
    print("=" * 50)
    """Cria uma nova receita com insumos OU atualiza uma existente se ID fornecido"""
    try:
        # IMPORTAR MODELO NECESSÁRIO NO INÍCIO
        from app.models.receita import ReceitaInsumo

        print(f"📥 Dados recebidos para receita: {receita_data}")
        
        # ============================================================================
        # VERIFICAR SE É CRIAÇÃO OU EDIÇÃO
        # ============================================================================
        receita_id = receita_data.get('id')
        is_edicao = receita_id is not None
        
        if is_edicao:
            print(f"✏️ MODO EDIÇÃO - Atualizando receita ID: {receita_id}")
            # ============================================================================
            # DEBUG: VERIFICAR O QUE CHEGOU NO BACKEND
            # ============================================================================
            print(f"🔍 receita_data.get('unidade'): {receita_data.get('unidade')}")
            print(f"🔍 'unidade' in receita_data: {'unidade' in receita_data}")
            print(f"🔍 receita_data completo: {receita_data}")
            
            # Buscar receita existente
            receita_existente = db.query(Receita).filter(Receita.id == receita_id).first()
            if not receita_existente:
                raise HTTPException(status_code=404, detail="Receita não encontrada para atualização")
            
            # ============================================================================
            # ATUALIZAR RECEITA EXISTENTE
            # ============================================================================
            
            # Atualizar apenas campos fornecidos
            if receita_data.get('nome'):
                receita_existente.nome = receita_data['nome'].strip()
            if receita_data.get('codigo'):
                receita_existente.codigo = receita_data['codigo'].strip()
            if receita_data.get('descricao') is not None:
                receita_existente.descricao = receita_data['descricao']
            if receita_data.get('grupo'):
                receita_existente.grupo = receita_data['grupo']
            if receita_data.get('subgrupo'):
                receita_existente.subgrupo = receita_data['subgrupo']
            # Mapear rendimento_porcoes (aceita tanto 'rendimento' quanto 'rendimento_porcoes')
            if receita_data.get('rendimento_porcoes'):
                receita_existente.rendimento_porcoes = receita_data['rendimento_porcoes']
            elif receita_data.get('rendimento'):
                receita_existente.rendimento_porcoes = receita_data['rendimento']
            
            print(f"⏱️ DEBUG - tempo_preparo recebido: {receita_data.get('tempo_preparo')}")
            # Atualizar campos de receita processada
            if 'processada' in receita_data:
                receita_existente.processada = receita_data['processada']
            if 'rendimento' in receita_data and receita_data.get('processada'):
                receita_existente.rendimento = receita_data['rendimento']
            print(f"⏱️ DEBUG - tempo_preparo_minutos recebido: {receita_data.get('tempo_preparo_minutos')}")

            if receita_data.get('tempo_preparo_minutos'):
                receita_existente.tempo_preparo_minutos = receita_data['tempo_preparo_minutos']
                print(f"⏱️ SALVO no banco: {receita_existente.tempo_preparo_minutos}")
            elif receita_data.get('tempo_preparo'):
                receita_existente.tempo_preparo_minutos = receita_data['tempo_preparo']
                print(f"⏱️ SALVO no banco (via tempo_preparo): {receita_existente.tempo_preparo_minutos}")
            if receita_data.get('sugestao_valor'):
                # Converter de reais para centavos se necessário
                valor = receita_data['sugestao_valor']
                receita_existente.sugestao_valor = int(float(valor) * 100) if valor < 1000 else int(valor)
            if 'unidade' in receita_data:
                receita_existente.unidade = receita_data['unidade']
                print(f"✅ UNIDADE ATUALIZADA: {receita_data['unidade']}")
            if receita_data.get('quantidade'):
                receita_existente.quantidade = receita_data['quantidade']
            if receita_data.get('fator'):
                receita_existente.fator = receita_data['fator']
            if 'ativo' in receita_data:
                receita_existente.ativo = bool(receita_data['ativo'])
            
            # Atualizar campos de receita processada
            if 'processada' in receita_data:
                receita_existente.processada = bool(receita_data['processada'])
            if 'rendimento' in receita_data:
                receita_existente.rendimento = receita_data['rendimento']
            # Salvar alterações
            db.commit()
            db.refresh(receita_existente)
            print(f"🔍 APÓS COMMIT - receita_existente.unidade: {receita_existente.unidade}")
            print(f"🔍 APÓS COMMIT - receita_existente.nome: {receita_existente.nome}")
            print(f"🔍 APÓS COMMIT - receita_existente.id: {receita_existente.id}")
            print(f"✅ Receita ID {receita_id} atualizada com sucesso!")
            
            # ============================================================================
            # PROCESSAR INSUMOS DA RECEITA (se fornecidos)
            # ============================================================================
            insumos_data = receita_data.get('insumos', [])
            if insumos_data:
                print(f"🔄 Atualizando {len(insumos_data)} insumos...")
                
                # Remover insumos existentes da receita
                db.query(ReceitaInsumo).filter(ReceitaInsumo.receita_id == receita_id).delete()
                
                # Adicionar novos insumos
                for insumo_data in insumos_data:
                    insumo_id = insumo_data.get('insumo_id')
                    quantidade = insumo_data.get('quantidade', 0)
                    unidade_medida = insumo_data.get('unidade_medida', 'unidade')
                    
                    if insumo_id and quantidade > 0:
                        # ===================================================================================================
                        # VERIFICAR SE É RECEITA PROCESSADA OU INSUMO NORMAL
                        # ===================================================================================================
                        receita_processada = db.query(Receita).filter(
                            Receita.id == insumo_id,
                            Receita.processada == True
                        ).first()
                        
                        if receita_processada:
                            # É uma receita processada
                            print(f"  - Salvando Receita Processada {insumo_id}: {quantidade} {unidade_medida}")
                            
                            receita_insumo = ReceitaInsumo(
                                receita_id=receita_id,  # ← Usar receita_id no modo edição
                                receita_processada_id=int(insumo_id),
                                insumo_id=None,
                                quantidade_necessaria=float(quantidade),
                                unidade_medida=unidade_medida
                            )
                            print(f"  🔍 DEBUG - Objeto ReceitaInsumo criado:")
                            print(f"    - receita_id: {receita_insumo.receita_id}")
                            print(f"    - receita_processada_id: {receita_insumo.receita_processada_id}")
                            print(f"    - insumo_id: {receita_insumo.insumo_id}")
                            print(f"    - quantidade: {receita_insumo.quantidade_necessaria}")
                        else:
                            # É um insumo normal
                            print(f"  - Salvando Insumo {insumo_id}: {quantidade} {unidade_medida}")
                            
                            receita_insumo = ReceitaInsumo(
                                receita_id=receita_id,  # ← Usar receita_id no modo edição
                                insumo_id=int(insumo_id),
                                receita_processada_id=None,
                                quantidade_necessaria=float(quantidade),
                                unidade_medida=unidade_medida
                            )
                        
                        db.add(receita_insumo)
                        print(f"  ✅ ReceitaInsumo adicionado ao db.session")
                
                # Commit das alterações de insumos
                db.commit()
                print(f"  ✅ Commit realizado! Verificando se salvou...")

                # Verificar se salvou
                insumo_salvo = db.query(ReceitaInsumo).filter(
                    ReceitaInsumo.receita_id == receita_id  
                ).all()
                print(f"  📊 Total de insumos salvos para esta receita: {len(insumo_salvo)}")
                for ri in insumo_salvo:
                    print(f"    - ID: {ri.id}, insumo_id: {ri.insumo_id}, receita_processada_id: {ri.receita_processada_id}")
            
            # Retornar receita atualizada
            resposta = {
                "id": receita_existente.id,
                "nome": receita_existente.nome,
                "codigo": receita_existente.codigo,
                "restaurante_id": receita_existente.restaurante_id,
                "ativo": receita_existente.ativo,
                "unidade": receita_existente.unidade,  # ← ADICIONAR UNIDADE
                "processada": receita_existente.processada,  # ← ADICIONAR PROCESSADA
                "total_insumos": len(insumos_data),
                "message": "Receita atualizada com sucesso"
            }

            print(f"📤 RESPOSTA sendo enviada: {resposta}")
            return resposta
            
        else:
            print("➕ MODO CRIAÇÃO - Nova receita")

            # ===================================================================================================
            # DEBUG TEMPORÁRIO: Verificar se campo codigo está chegando do frontend
            # ===================================================================================================
            print(f"🔍 DEBUG - Campo 'codigo' em receita_data: {receita_data.get('codigo')}")
            print(f"🔍 DEBUG - 'codigo' in receita_data: {'codigo' in receita_data}")
            print(f"🔍 DEBUG - receita_data keys: {list(receita_data.keys())}")
            # ===================================================================================================
            
            # ============================================================================
            # CRIAR NOVA RECEITA COM CODIGO AUTOMATICO
            # ============================================================================
            
            # Importar service de codigo
            from app.services.codigo_service import gerar_proximo_codigo
            from app.config.codigo_config import TipoCodigo
            
            # Obter restaurante_id
            restaurante_id = int(receita_data.get('restaurante_id', 0))
            if not restaurante_id:
                raise HTTPException(status_code=400, detail="Restaurante é obrigatório para gerar código")
            
            # Determinar tipo de receita para geracao de codigo
            is_processada = receita_data.get('is_processada', False) or receita_data.get('processada', False)
            tipo_codigo = (
                TipoCodigo.RECEITA_PROCESSADA 
                if is_processada 
                else TipoCodigo.RECEITA_NORMAL
            )
            
            # Gerar codigo automaticamente PARA O RESTAURANTE ESPECÍFICO
            try:
                codigo_gerado = gerar_proximo_codigo(db, tipo_codigo, restaurante_id)
                print(f"✅ Código gerado automaticamente para restaurante {restaurante_id}: {codigo_gerado}")
            except ValueError as e:
                # Faixa esgotada
                raise HTTPException(
                    status_code=400,
                    detail=f"Erro ao gerar código: {str(e)}"
                )
            
            # Campos obrigatórios básicos (com codigo gerado)
            campos_obrigatorios = {
                'codigo': codigo_gerado,  # Usar codigo gerado automaticamente
                'nome': receita_data.get('nome', '').strip(),
                'restaurante_id': int(receita_data.get('restaurante_id', 0)),
                'ativo': bool(receita_data.get('ativo', True))
            }
            
            # Validação básica
            if not campos_obrigatorios['nome']:
                raise HTTPException(status_code=400, detail="Nome da receita é obrigatório")
            if not campos_obrigatorios['restaurante_id']:
                raise HTTPException(status_code=400, detail="Restaurante é obrigatório")
                
            # Criar a receita base
            nova_receita = Receita(**campos_obrigatorios)
            
            # Campos opcionais seguros
            campos_opcionais = {
                'descricao': receita_data.get('descricao', ''),
                'responsavel': receita_data.get('responsavel'),
                'grupo': receita_data.get('grupo', 'Geral'),
                'subgrupo': receita_data.get('subgrupo', 'Geral'),
                'rendimento_porcoes': receita_data.get('rendimento_porcoes') or receita_data.get('rendimento', 1),
                'tempo_preparo_minutos': receita_data.get('tempo_preparo_minutos') or receita_data.get('tempo_preparo', 15),
                'unidade': receita_data.get('unidade', 'porção'),
                'quantidade': receita_data.get('quantidade', 1),
                'fator': receita_data.get('fator', 1.0),
                'preco_compra': 0,  # Será calculado automaticamente
                'sugestao_valor': int(float(receita_data.get('sugestao_valor', 0)) * 100) if receita_data.get('sugestao_valor') else None,
                'processada': receita_data.get('processada', False),
                'rendimento': receita_data.get('rendimento'),
            }
            
            # Adicionar campos opcionais apenas se existirem no modelo
            for campo, valor in campos_opcionais.items():
                if hasattr(nova_receita, campo):
                    setattr(nova_receita, campo, valor)
            
            # Salvar receita no banco
            db.add(nova_receita)
            db.commit()
            db.refresh(nova_receita)
            
            print(f"✅ Receita criada com ID: {nova_receita.id}")
            
            # PROCESSAR INSUMOS (código original)
            insumos_data = receita_data.get('insumos', [])
            if insumos_data:
                print(f"📦 Processando {len(insumos_data)} insumos...")
                try:
                    for insumo_data in insumos_data:
                        insumo_id = insumo_data.get('insumo_id')
                        quantidade = insumo_data.get('quantidade', 0)
                        unidade_medida = insumo_data.get('unidade_medida', 'unidade')
                        
                        if insumo_id and quantidade > 0:
                            # ===================================================================================================
                            # VERIFICAR SE É RECEITA PROCESSADA OU INSUMO NORMAL
                            # ===================================================================================================
                            receita_processada = db.query(Receita).filter(
                                Receita.id == insumo_id,
                                Receita.processada == True
                            ).first()
                            
                            if receita_processada:
                                # É uma receita processada
                                print(f"  - Salvando Receita Processada {insumo_id}: {quantidade} {unidade_medida}")
                                
                                receita_insumo = ReceitaInsumo(
                                    receita_id=nova_receita.id,  # ← Usar nova_receita.id no modo criação
                                    receita_processada_id=int(insumo_id),
                                    insumo_id=None,
                                    quantidade_necessaria=float(quantidade),
                                    unidade_medida=unidade_medida
                                )
                            else:
                                # É um insumo normal
                                print(f"  - Salvando Insumo {insumo_id}: {quantidade} {unidade_medida}")
                                
                                receita_insumo = ReceitaInsumo(
                                    receita_id=nova_receita.id,  # ← Usar nova_receita.id no modo criação
                                    insumo_id=int(insumo_id),
                                    receita_processada_id=None,
                                    quantidade_necessaria=float(quantidade),
                                    unidade_medida=unidade_medida
                                )
                            
                            db.add(receita_insumo)
                            
                    # COMMIT das alterações
                    db.commit()
                    print(f"✅ {len(insumos_data)} insumos salvos com sucesso!")
                    
                except Exception as e:
                    print(f"❌ Erro ao salvar insumos: {e}")
                    db.rollback()
                    raise HTTPException(status_code=500, detail=f"Erro ao salvar insumos: {str(e)}")
            
            # Retornar resposta
            return {
                "id": nova_receita.id,
                "nome": nova_receita.nome,
                "codigo": nova_receita.codigo,
                "restaurante_id": nova_receita.restaurante_id,
                "ativo": nova_receita.ativo,
                "total_insumos": len(insumos_data),
                "message": "Receita criada com sucesso"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro interno ao processar receita: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar receita: {str(e)}")


@router.get("/search", response_model=List[ReceitaListResponse],
            summary="Buscar receitas")
def search_receitas(
    q: str = Query(..., min_length=2, description="Termo de busca (nome ou código)"),
    restaurante_id: Optional[int] = Query(None, description="Filtrar por restaurante"),
    db: Session = Depends(get_db)
):
    """Busca receitas por nome ou código"""
    return crud_receita.search_receitas(db, termo=q, restaurante_id=restaurante_id)

@router.get("/{receita_id}", response_model=ReceitaResponse,
            summary="Buscar receita por ID")
def get_receita(receita_id: int, db: Session = Depends(get_db)):
    """Busca uma receita específica por ID com todos os relacionamentos"""
    receita = crud_receita.get_receita_by_id(db, receita_id)
    if receita is None:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    return receita

@router.put("/{receita_id}", response_model=ReceitaResponse,
            summary="Atualizar receita")
def update_receita(
    receita_id: int,
    receita_update: ReceitaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    data_scope = Depends(PermissionChecker(ResourceType.RECEITAS, ActionType.EDITAR))
):
    """
    Atualiza uma receita existente.
    
    Permissões:
    - Requer permissão de EDITAR RECEITAS
    - Validações por escopo:
      * PROPRIOS: só pode editar receitas que criou
      * LOJA: só pode editar receitas do seu restaurante
      * REDE: só pode editar receitas da sua rede
      * TODOS: pode editar qualquer receita
    """
    # Buscar receita antes de atualizar para validar permissões
    db_receita = db.query(Receita).filter(Receita.id == receita_id).first()
    
    if db_receita is None:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    
    # Verificar se usuário tem acesso a esta receita
    created_by_id = getattr(db_receita, 'created_by', None)

    # Se receita não tem created_by (receitas antigas), permitir com escopo TODOS
    if created_by_id is None:
        if data_scope != DataScope.TODOS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Receitas sem proprietário só podem ser deletadas com escopo TODOS"
            )
    else:
        # Receita tem proprietário, verificar permissão normal
        if not can_access_resource(
            user=current_user,
            resource_owner_id=created_by_id,
            resource_restaurante_id=db_receita.restaurante_id,
            data_scope=data_scope,
            db=db
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para deletar esta receita"
            )
    
    # Atualizar receita
    receita = crud_receita.update_receita(db, receita_id, receita_update)
    
    if receita is None:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    
    return receita

# ===================================================================
# ENDPOINTS RECEITA-INSUMOS (COM AUTOMAÇÃO COMPLETA)
# ===================================================================

@router.post("/{receita_id}/insumos/", response_model=ReceitaInsumoResponse,
             summary="Adicionar insumo à receita")
def add_insumo_to_receita(
    receita_id: int,
    receita_insumo: ReceitaInsumoCreate,
    db: Session = Depends(get_db)
):
    # Caça ao dados de porções
    print("=" * 50)
    print("FUNÇÃO POST CHAMADA!")
    print("=" * 50)
    """
    Adiciona insumo à receita com cálculo automático de custos.
    
    **Automação implementada:**
    1. Calcula custo do insumo automaticamente baseado no fator
    2. Adiciona insumo à receita
    3. Recalcula CMV total da receita automaticamente
    4. Atualiza preços sugeridos automaticamente
    
    **Sistema de conversão:**
    - Bacon 1kg (fator=1.0): 15g → custo = (R$50,99 ÷ 1.0) × 0.015kg = R$0,765
    - Pão caixa 20un (fator=20.0): 1un → custo = (R$12,50 ÷ 20.0) × 1 = R$0,625
    """
    try:
        return crud_receita.add_insumo_to_receita(db, receita_id, receita_insumo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{receita_id}/insumos/", response_model=List[ReceitaInsumoResponse],
            summary="Listar insumos da receita")
def get_receita_insumos(receita_id: int, db: Session = Depends(get_db)):
    """Lista todos os insumos de uma receita com custos calculados"""
    return crud_receita.get_receita_insumos(db, receita_id)

@router.put("/insumos/{receita_insumo_id}", response_model=ReceitaInsumoResponse,
            summary="Atualizar insumo na receita")
def update_insumo_in_receita(
    receita_insumo_id: int,
    receita_insumo_update: ReceitaInsumoUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza quantidade ou dados de um insumo na receita.
    
    **Automação implementada:**
    1. Atualiza dados do insumo na receita
    2. Recalcula custo se quantidade mudou
    3. Recalcula CMV total da receita automaticamente
    4. Atualiza preços sugeridos automaticamente
    """
    receita_insumo = crud_receita.update_insumo_in_receita(db, receita_insumo_id, receita_insumo_update)
    if receita_insumo is None:
        raise HTTPException(status_code=404, detail="Insumo não encontrado na receita")
    return receita_insumo

@router.delete("/insumos/{receita_insumo_id}", summary="Remover insumo da receita")
def remove_insumo_from_receita(receita_insumo_id: int, db: Session = Depends(get_db)):
    """
    Remove um insumo de uma receita.
    
    **Automação implementada:**
    1. Remove o insumo da receita
    2. Recalcula CMV total da receita automaticamente (sem este insumo)
    3. Atualiza preços sugeridos automaticamente
    
    **Atenção:**
    - Esta ação não pode ser desfeita
    - O custo da receita será reduzido automaticamente
    - Se era o último insumo, custo ficará zerado
    """
    success = crud_receita.remove_insumo_from_receita(db, receita_insumo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Insumo não encontrado na receita")
    return {"message": "Insumo removido da receita com sucesso"}

# ===================================================================
# ENDPOINTS DE CÁLCULOS (CORRIGIDOS COM SISTEMA DE PREÇOS AUTOMÁTICO)
# ===================================================================

@router.post("/{receita_id}/calcular-cmv", response_model=AtualizarCMVResponse,
             summary="Recalcular custo da receita")
def recalcular_cmv_receita(
    receita_id: int,
    db: Session = Depends(get_db)
):
    # Caça ao dados de porções
    print("=" * 50)
    print("FUNÇÃO POST CHAMADA!")
    print("=" * 50)
    """
    Força recálculo do custo de produção de uma receita baseado nos insumos atuais.
    
    **Quando usar:**
    - Preços dos insumos foram atualizados (fatores corrigidos)
    - Suspeita de custo desatualizado
    - Após importação de dados do TOTVS
    - Para verificar cálculos após alterações
    
    **Processo:**
    1. Recalcula custo de todos os insumos da receita
    2. Soma todos os custos para obter custo total de produção
    3. Atualiza o registro da receita
    4. Retorna custo anterior vs atual
    
    **Retorna:**
    - Custo anterior e atual de produção
    - Quantidade de insumos processados
    - ID da receita
    """
    receita = crud_receita.get_receita_by_id(db, receita_id)
    if receita is None:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    
    custo_anterior = receita.cmv_real if receita.cmv_real else 0.0
    custo_atual = crud_receita.calcular_cmv_receita(db, receita_id)
    total_insumos = len(receita.receita_insumos)

    return {
        "receita_id": receita_id,
        "custo_anterior": custo_anterior,
        "custo_atual": custo_atual,
        "total_insumos": total_insumos
    }

@router.get("/{receita_id}/precos-sugeridos", response_model=CalculoPrecosResponse,
            summary="Calcular preços sugeridos")
def calcular_precos_sugeridos(
    receita_id: int,
    db: Session = Depends(get_db)
):
    """
    Calcula preços sugeridos para uma receita baseado no custo de produção atual.
    
    **IMPORTANTE:**
    - custo_producao = quanto custa para fazer a receita
    - precos_sugeridos = quanto cobrar do cliente para ter lucro
    
    **Fórmula usada:**
    Preço = Custo ÷ (1 - Margem)
    
    **Margens calculadas:**
    - 20% de margem: Custo ÷ 0,80
    - 25% de margem: Custo ÷ 0,75
    - 30% de margem: Custo ÷ 0,70
    
    **Exemplo:**
    - Custo = R$ 6,97
    - Margem 25% = 6,97 ÷ (1 - 0,25) = R$ 9,29
    
    **Retorna:**
    - Custo atual de produção
    - Preços sugeridos para as 3 margens
    - ID da receita
    
    **Atenção:**
    - Se custo = 0, todos os preços serão 0
    - Certifique-se de que a receita tem insumos
    """
    resultado = crud_receita.calcular_precos_sugeridos(db, receita_id)

    if "error" in resultado:
        raise HTTPException(status_code=404, detail=resultado["error"])
    
    return resultado

# ===================================================================
# ENDPOINTS UTILITÁRIOS
# ===================================================================

@router.get("/utils/grupos", response_model=List[str],
            summary="Listar grupos únicos")
def listar_grupos_receitas(
    restaurante_id: Optional[int] = Query(None, description="Filtrar por restaurante"),
    db: Session = Depends(get_db)
):
    """Lista todos os grupos únicos de receitas"""
    return crud_receita.get_grupos_receitas(db, restaurante_id=restaurante_id)

@router.get("/utils/subgrupos/{grupo}", response_model=List[str],
            summary="Listar subgrupos de um grupo")
def listar_subgrupos_receitas(
    grupo: str,
    restaurante_id: Optional[int] = Query(None, description="Filtrar por restaurante"),
    db: Session = Depends(get_db)
):
    """Lista subgrupos únicos dentro de um grupo específico"""
    return crud_receita.get_subgrupos_receitas(db, grupo=grupo, restaurante_id=restaurante_id)

@router.get("/utils/stats", summary="Estatísticas das receitas")
def estatisticas_receitas(
    restaurante_id: Optional[int] = Query(None, description="Filtrar por restaurante"),
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas gerais das receitas.
    
    **Inclui:**
    - Total de receitas
    - Receitas ativas vs inativas
    - Receitas com custo calculado vs sem custo
    - Filtro opcional por restaurante
    """
    return crud_receita.get_receitas_stats(db, restaurante_id=restaurante_id)

@router.get("/utils/insumos-disponiveis", summary="Listar insumos disponíveis")
def listar_insumos_disponiveis(
    termo: Optional[str] = Query(None, description="Buscar por nome ou código"),
    db: Session = Depends(get_db)
):
    """
    Lista insumos disponíveis para adicionar em receitas.
    
    **Útil para:**
    - Dropdown de seleção de insumos
    - Autocomplete ao adicionar insumos
    - Busca por nome ou código
    """
    return crud_receita.get_insumos_disponiveis(db, termo=termo)

# ===================================================================
# ENDPOINT RESUMO COMPLETO
# ===================================================================

@router.get("/{receita_id}/resumo", summary="Resumo completo da receita")
def obter_resumo_receita(
    receita_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna um resumo completo da receita com todos os dados importantes.
    
    **Inclui:**
    - Dados básicos da receita
    - Lista completa de insumos com custos
    - Custo total calculado
    - Preços sugeridos
    - Dados do restaurante
    
    **Ideal para:**
    - Tela de visualização completa
    - Relatórios de custos
    - Conferência antes da produção
    - Análise de rentabilidade
    """
    # Buscar receita com todos os relacionamentos
    receita = crud_receita.get_receita_by_id(db, receita_id)
    if receita is None:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    
    # Buscar insumos da receita
    insumos = crud_receita.get_receita_insumos(db, receita_id)
    
    # Calcular preços sugeridos
    precos_sugeridos = crud_receita.calcular_precos_sugeridos(db, receita_id)
    
    return {
        "receita": {
            "id": receita.id,
            "nome": receita.nome,
            "codigo": receita.codigo,
            "grupo": receita.grupo,
            "subgrupo": receita.subgrupo,
            "custo_producao": receita.cmv_real if receita.cmv_real else 0.0,
            "preco_venda_real": receita.preco_venda_real,
            "margem_real": receita.margem_real,
            "ativo": receita.ativo,
            "restaurante": {
                "id": receita.restaurante.id,
                "nome": receita.restaurante.nome
            } if receita.restaurante else None
        },
        "insumos": [
            {
                "id": insumo.id,
                "insumo_nome": insumo.insumo.nome if insumo.insumo else "Insumo não encontrado",
                "insumo_codigo": insumo.insumo.codigo if insumo.insumo else "N/A",
                "quantidade_necessaria": insumo.quantidade_necessaria,
                "unidade_medida": insumo.unidade_medida,
                "custo_calculado": insumo.custo_calculado if insumo.custo_calculado else 0.0,
                "observacoes": insumo.observacoes
            }
            for insumo in insumos
        ],
        "totais": {
            "custo_total": receita.cmv_real if receita.cmv_real else 0.0,
            "total_insumos": len(insumos),
            "precos_sugeridos": precos_sugeridos.get("precos_sugeridos", {}) if "error" not in precos_sugeridos else {}
        }
    }

# ===================================================================
# ENDPOINTS DE EXPORTACAO PDF
# ===================================================================

@router.get("/{receita_id}/pdf", summary="Gerar PDF de uma receita")
def gerar_pdf_receita(
    receita_id: int,
    tipo: str = Query("completo", regex="^(completo|cozinha)$"),
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),
    # permission_check = Depends(PermissionChecker(ResourceType.RECEITAS, ActionType.VISUALIZAR))
):
    """
    Gera PDF profissional de uma receita específica.
    
    Funcionalidades:
    - Exporta receita completa com todas informações
    - Inclui tabela de ingredientes estilizada
    - Mostra cálculo de CMV e precificação
    - Design profissional com identidade IOGAR
    - Download automático no navegador
    
    Permissões necessárias:
    - Visualizar receitas
    - Acesso ao restaurante da receita (data scope aplicado)
    """
    from fastapi.responses import FileResponse
    from app.services.pdf_service import obter_pdf_service
    import tempfile
    import os
    
    try:
        print(f"🎨 === GERANDO PDF DA RECEITA {receita_id} ===")
        
        # Buscar receita com validação de permissões
        print(f"🔍 Buscando receita ID {receita_id}...")
        receita = db.query(Receita).filter(Receita.id == receita_id).first()
        
        if not receita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Receita com ID {receita_id} não encontrada"
            )
        
        # Buscar insumos da receita
        receita_insumos = db.query(ReceitaInsumo).filter(
            ReceitaInsumo.receita_id == receita_id
        ).all()
        
        # Preparar dados dos ingredientes
        ingredientes = []
        for ri in receita_insumos:
            insumo = db.query(Insumo).filter(Insumo.id == ri.insumo_id).first()
            if insumo:
                preco_unitario = insumo.preco_compra_real or 0
                custo_total = ri.quantidade_necessaria * preco_unitario
                
                ingredientes.append({
                    'codigo': insumo.codigo,
                    'nome': insumo.nome,
                    'quantidade': float(ri.quantidade_necessaria),
                    'unidade': insumo.unidade,
                    'preco_unitario': float(preco_unitario),
                    'custo_total': float(custo_total)
                })
        
        # Calcular CMV total
        cmv_total = sum(ing['custo_total'] for ing in ingredientes)
        # Converter para float para evitar erro de tipagem Decimal
        cmv_unitario = float(cmv_total) / float(receita.rendimento_porcoes) if receita.rendimento_porcoes and receita.rendimento_porcoes > 0 else 0.0
        
        # Calcular precificação com margem de 65%
        margem_sugerida = 65.0
        preco_sugerido = cmv_unitario / (1 - margem_sugerida / 100) if margem_sugerida < 100 else 0
        
        # Preparar dados completos da receita
        receita_data = {
            'codigo': receita.codigo,
            'nome': receita.nome,
            'categoria': receita.grupo or 'Sem categoria',
            'status': 'Ativo' if receita.ativo else 'Inativo',
            'rendimento': float(receita.rendimento_porcoes) if receita.rendimento_porcoes else 0,
            'unidade_rendimento': 'porções',
            'tempo_preparo': receita.tempo_preparo_minutos if receita.tempo_preparo_minutos else 0,
            'responsavel': receita.responsavel or 'Não informado',
            'ingredientes': ingredientes,
            'precificacao': {
                'cmv': float(cmv_total),
                'cmv_unitario': float(cmv_unitario),
                'margem_sugerida': margem_sugerida,
                'preco_sugerido': float(preco_sugerido),
                'preco_venda_atual': float(receita.preco_venda) if receita.preco_venda else None
            }
        }
        
        # Gerar PDF usando o serviço
        pdf_service = obter_pdf_service()
        
        # Criar arquivo temporário para o PDF
        temp_dir = tempfile.gettempdir()
        output_filename = f"receita_{receita.codigo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join(temp_dir, output_filename)
        
        # Gerar PDF conforme tipo selecionado
        print(f"📄 Gerando PDF tipo '{tipo}' em: {output_path}")
        
        if tipo == "cozinha":
            pdf_path = pdf_service.gerar_pdf_cozinha(
                receita_data=receita_data,
                output_path=output_path
            )
        else:
            pdf_path = pdf_service.gerar_pdf_receita(
                receita_data=receita_data,
                output_path=output_path
            )
        
        print(f"✅ PDF gerado com sucesso para receita {receita_id}")
        
        # Retornar arquivo PDF com headers corretos para download
        return FileResponse(
            path=pdf_path,
            media_type='application/pdf',
            filename=f"receita_{receita.codigo}.pdf",
            headers={
                'Content-Disposition': f'attachment; filename="receita_{receita.codigo}.pdf"',
                'Cache-Control': 'no-cache'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ ERRO ao gerar PDF da receita {receita_id}:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensagem: {str(e)}")
        print(f"   Traceback completo:")
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar PDF: {str(e)}"
        )
    
@router.post("/pdf/lote", summary="Gerar PDFs de múltiplas receitas")
def gerar_pdf_lote(
    request: PDFLoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    permission_check = Depends(PermissionChecker(ResourceType.RECEITAS, ActionType.VISUALIZAR))
):
    """
    Gera PDFs de múltiplas receitas e retorna arquivo ZIP com todos os PDFs.
    
    Funcionalidades:
    - Gera múltiplos PDFs em uma única requisição
    - Compacta todos em arquivo ZIP
    - Valida permissões para cada receita individualmente
    - Ignora receitas sem permissão (não retorna erro)
    - Útil para exportação em massa
    
    Request Body:
    - receita_ids: Lista de IDs das receitas para gerar PDF
    
    Permissões necessárias:
    - Visualizar receitas
    - Acesso aos restaurantes das receitas (data scope aplicado)
    """
    from fastapi.responses import FileResponse
    from app.services.pdf_service import obter_pdf_service
    import tempfile
    import os
    import zipfile
    
    # Validar que há receitas para processar
    if not request.receita_ids or len(request.receita_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lista de receitas vazia. Forneça ao menos um ID de receita."
        )
    
    # Limitar quantidade máxima para evitar sobrecarga
    MAX_RECEITAS = 50
    if len(request.receita_ids) > MAX_RECEITAS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Máximo de {MAX_RECEITAS} receitas por vez. Você enviou {len(request.receita_ids)}."
        )
    
    # Criar diretório temporário para PDFs
    temp_dir = tempfile.mkdtemp()
    pdf_service = obter_pdf_service()
    pdfs_gerados = []
    receitas_sem_permissao = []
    receitas_nao_encontradas = []
    
    try:
        # Processar cada receita
        for receita_id in request.receita_ids:
            # Buscar receita
            receita = db.query(Receita).filter(Receita.id == receita_id).first()
            
            if not receita:
                receitas_nao_encontradas.append(receita_id)
                continue
            
            # Verificar permissão de acesso
            if not can_access_resource(current_user, receita.restaurante_id, ResourceType.RECEITAS):
                receitas_sem_permissao.append(receita_id)
                continue
            
            # Buscar insumos da receita
            receita_insumos = db.query(ReceitaInsumo).filter(
                ReceitaInsumo.receita_id == receita_id
            ).all()
            
            # Preparar dados dos ingredientes
            ingredientes = []
            for ri in receita_insumos:
                insumo = db.query(Insumo).filter(Insumo.id == ri.insumo_id).first()
                if insumo:
                    preco_unitario = insumo.preco_compra_real or 0
                    custo_total = ri.quantidade * preco_unitario
                    
                    ingredientes.append({
                        'nome': insumo.nome,
                        'quantidade': float(ri.quantidade_necessaria),
                        'unidade': insumo.unidade,
                        'preco_unitario': float(preco_unitario),
                        'custo_total': float(custo_total)
                    })
            
            # Calcular CMV total
            cmv_total = sum(ing['custo_total'] for ing in ingredientes)
            cmv_unitario = cmv_total / receita.rendimento if receita.rendimento > 0 else 0
            
            # Calcular precificação com margem de 65%
            margem_sugerida = 65.0
            preco_sugerido = cmv_unitario / (1 - margem_sugerida / 100) if margem_sugerida < 100 else 0
            
            # Preparar dados completos da receita
            receita_data = {
                'codigo': receita.codigo,
                'nome': receita.nome,
                'categoria': receita.grupo or 'Sem categoria',
                'status': 'Ativo' if receita.ativo else 'Inativo',
                'rendimento': float(receita.rendimento_porcoes) if receita.rendimento_porcoes else 0,
                'unidade_rendimento': 'porções',
                'tempo_preparo': receita.tempo_preparo_minutos if receita.tempo_preparo_minutos else 0,
                'responsavel': receita.responsavel or 'Não informado',
                'ingredientes': ingredientes,
                'precificacao': {
                    'cmv': float(cmv_total),
                    'cmv_unitario': float(cmv_unitario),
                    'margem_sugerida': margem_sugerida,
                    'preco_sugerido': float(preco_sugerido),
                    'preco_venda_atual': float(receita.preco_venda) if receita.preco_venda else None
                }
            }
            
            # Gerar PDF
            try:
                output_filename = f"receita_{receita.codigo}.pdf"
                output_path = os.path.join(temp_dir, output_filename)
                
                pdf_path = pdf_service.gerar_pdf_receita(
                    receita_data=receita_data,
                    output_path=output_path
                )
                
                pdfs_gerados.append({
                    'receita_id': receita_id,
                    'codigo': receita.codigo,
                    'path': pdf_path
                })
                
            except Exception as e:
                print(f"Erro ao gerar PDF da receita {receita_id}: {e}")
                continue
        
        # Verificar se algum PDF foi gerado
        if len(pdfs_gerados) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Nenhum PDF foi gerado",
                    "receitas_nao_encontradas": receitas_nao_encontradas,
                    "receitas_sem_permissao": receitas_sem_permissao
                }
            )
        
        # Criar arquivo ZIP com todos os PDFs
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"receitas_lote_{timestamp}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for pdf_info in pdfs_gerados:
                zipf.write(
                    pdf_info['path'],
                    arcname=f"receita_{pdf_info['codigo']}.pdf"
                )
        
        # Preparar mensagem de resumo
        resumo = {
            "total_solicitado": len(request.receita_ids),
            "total_gerado": len(pdfs_gerados),
            "nao_encontradas": len(receitas_nao_encontradas),
            "sem_permissao": len(receitas_sem_permissao)
        }
        
        # Retornar arquivo ZIP
        return FileResponse(
            path=zip_path,
            media_type='application/zip',
            filename=f"receitas_{timestamp}.zip",
            headers={
                'Content-Disposition': f'attachment; filename="receitas_{timestamp}.zip"',
                'Cache-Control': 'no-cache',
                'X-Total-Generated': str(resumo['total_gerado']),
                'X-Total-Requested': str(resumo['total_solicitado'])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar PDFs em lote: {str(e)}"
        )
    
# ===================================================================
# ENDPOINT DE LIMPEZA COMPLETA - SISTEMA DE RECEITAS
# ===================================================================

@router.delete("/clear", summary="Limpar todas as receitas")
def clear_all_receitas(
    confirm: bool = Query(False, description="Confirmação obrigatória"),
    db: Session = Depends(get_db)
):
    """
    Remove todas as receitas do sistema para limpeza completa.
    
    ATENÇÃO: Esta operação é irreversível!
    
    Processo de limpeza:
    1. Remove todos os vínculos receita-insumos
    2. Remove todas as receitas do banco
    3. Reseta sequências de IDs
    4. Retorna estatísticas da operação
    
    Parâmetro 'confirm' deve ser True para executar a limpeza.
    Exemplo de uso: DELETE /api/v1/receitas/clear?confirm=true
    """
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Para confirmar a limpeza, adicione ?confirm=true na URL"
        )
    
    try:
        estatisticas = crud_receita.clear_all_receitas(db)
        return {
            "message": "Limpeza de receitas concluída com sucesso",
            "estatisticas": estatisticas,
            "timestamp": "2025-09-17",
            "operacao": "clear_receitas"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro durante limpeza das receitas: {str(e)}"
        )
    
@router.delete("/{receita_id}", summary="Deletar receita")
def delete_receita(
    receita_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    data_scope = Depends(PermissionChecker(ResourceType.RECEITAS, ActionType.DELETAR))
):
    """
    Deleta uma receita.
    
    Permissões:
    - Requer permissão de DELETAR RECEITAS
    - Validações por escopo:
      * PROPRIOS: só pode deletar receitas que criou
      * LOJA: só pode deletar receitas do seu restaurante
      * REDE: só pode deletar receitas da sua rede
      * TODOS: pode deletar qualquer receita
    """
    # DEBUG: Logs para entender o erro 403
    print(f"🗑️ === TENTATIVA DE DELETAR RECEITA {receita_id} ===")
    print(f"👤 Usuário: {current_user.username} (ID: {current_user.id})")
    print(f"🎭 Role: {current_user.role}")
    print(f"📊 Data Scope: {data_scope}")

    # Buscar receita antes de deletar para validar permissões
    db_receita = db.query(Receita).filter(Receita.id == receita_id).first()
    
    if db_receita is None:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    
    # Verificar se usuário tem acesso a esta receita
    created_by_id = getattr(db_receita, 'created_by', None)

    print(f"📝 Receita: {db_receita.nome}")
    print(f"🏪 Restaurante da receita: {db_receita.restaurante_id}")
    print(f"👤 Criada por (created_by): {created_by_id}")
    print(f"🏪 Restaurante do usuário: {current_user.restaurante_id}")
    
    if not can_access_resource(
        user=current_user,
        resource_owner_id=created_by_id or 0,
        resource_restaurante_id=db_receita.restaurante_id,
        data_scope=data_scope,
        db=db
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para deletar esta receita"
        )
    
    # Deletar receita
    success = crud_receita.delete_receita(db, receita_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Receita não encontrada")
    
    return {"message": "Receita deletada com sucesso"}