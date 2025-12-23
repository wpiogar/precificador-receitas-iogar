#   ===================================================================================================
#   CRUD RECEITAS - Operações de banco de dados para receitas
#   Descrição: Este arquivo contém todas as operações de banco de dados para receitas,
#   restaurantes e relacionamentos receita-insumo
#   Data: 14/08/2025
#   Autor: Will - Empresa: IOGAR
#   ===================================================================================================

from typing import List, Optional, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, text

from app.models.receita import Receita, Restaurante, ReceitaInsumo
from app.models.insumo import Insumo
from app.schemas.receita import (
    ReceitaCreate, ReceitaUpdate, UnidadeCreate, ReceitaInsumoCreate, ReceitaInsumoUpdate,
    RestauranteCreate, RestauranteUpdate
)

# ===================================================================================================
# FUNÇÃO DE CONVERSÃO DE UNIDADES (CORRIGIDA COM SISTEMA DE FATOR)
# ===================================================================================================

def converter_para_unidade_base(quantidade: float, unidade: str) -> float:
    """
    Converte quantidade para unidade base compatível com o fator do insumo.
    
    Regras de conversão:
    - Para peso: converte tudo para kg (unidade base)
    - Para volume: converte tudo para L (unidade base)  
    - Para unidades: mantém como está
    
    Args:
        quantidade: Quantidade na unidade original
        unidade: Unidade original (g, kg, ml, L, unidade)
        
    Returns:
        float: Quantidade convertida para unidade base
        
    Exemplos:
        - 15g → 0.015kg
        - 10ml → 0.01L
        - 1 unidade → 1 unidade
    """
    conversoes = {
        'g': 0.001,    # g → kg (15g = 0.015kg)
        'kg': 1.0,     # kg → kg (1kg = 1kg)
        'ml': 0.001,   # ml → L (10ml = 0.01L)
        'L': 1.0,      # L → L (1L = 1L)
        'unidade': 1.0 # unidade → unidade (1un = 1un)
    }
    
    fator_conversao = conversoes.get(unidade, 1.0)
    quantidade_convertida = quantidade * fator_conversao
    
    # Arredondar para 6 casas decimais para evitar problemas de precisão
    return round(quantidade_convertida, 6)

def calcular_custo_insumo(insumo: Insumo, quantidade_necessaria: float, unidade_medida: str) -> float:
    """
    Calcula o custo de um insumo na receita (SEM FATOR).
    
    HISTÓRICO: Sistema de fator desabilitado em 17/11/2025
    NOVO CÁLCULO: Custo = Preço × Quantidade convertida (sem divisão por fator)
    
    Fórmula: Custo = Preço × Quantidade convertida
    
    Args:
        insumo: Objeto do insumo
        quantidade_necessaria: Quantidade necessária na receita
        unidade_medida: Unidade da quantidade (g, kg, ml, L, unidade)
        
    Returns:
        float: Custo calculado em reais
        
    Exemplos (sem fator):
        - Bacon 1kg (R$50,99): 15g = 50,99 × 0.015kg = R$0,765
        - Maionese 750ml (R$7,50): 10ml = 7,50 × 0.01L = R$0,075
        - Pão caixa 20un (R$12,50): 1un = 12,50 × 1 = R$12,50
    """
    # ========================================================================
    # VALIDAÇÃO COM FATOR - DESABILITADA (MANTIDA POR PRECAUÇÃO)
    # ========================================================================
    # CÓDIGO ORIGINAL COMENTADO:
    # if not insumo or not insumo.preco_compra or insumo.fator <= 0:
    #     return 0.0
    
    # NOVA VALIDAÇÃO (sem fator)
    if not insumo or not insumo.preco_compra:
        return 0.0
    
    # Converter quantidade para unidade base
    quantidade_convertida = converter_para_unidade_base(quantidade_necessaria, unidade_medida)
    
    # Preço em reais
    preco_reais = insumo.preco_compra / 100.0
    
    # ========================================================================
    # CÁLCULO COM FATOR - DESABILITADO (MANTIDO POR PRECAUÇÃO)
    # ========================================================================
    # CÓDIGO ORIGINAL COMENTADO:
    # # Cálculo: (Preço ÷ Fator) × Quantidade convertida
    # custo_calculado = (preco_reais / insumo.fator) * quantidade_convertida
    
    # NOVO CÁLCULO SIMPLIFICADO (sem fator)
    custo_calculado = preco_reais * quantidade_convertida
    
    # Arredondar para 6 casas decimais para precisão
    return round(custo_calculado, 6)

# ===================================================================================================
# CRUD Restaurantes
# ===================================================================================================

def create_restaurante(db: Session, restaurante: RestauranteCreate) -> Restaurante:
    """Cria um novo restaurante matriz"""
    # Validar CNPJ único
    if restaurante.cnpj:
        existing = db.query(Restaurante).filter(Restaurante.cnpj == restaurante.cnpj).first()
        if existing:
            raise ValueError(f"CNPJ {restaurante.cnpj} já está cadastrado")
    
    # Criar restaurante matriz
    db_restaurante = Restaurante(
        **restaurante.model_dump(),
        eh_matriz=True,
        restaurante_pai_id=None
    )
    db.add(db_restaurante)
    db.commit()
    db.refresh(db_restaurante)
    return db_restaurante

def create_unidade(db: Session, restaurante_matriz_id: int, unidade: UnidadeCreate) -> Restaurante:
    """Cria uma nova unidade/filial para um restaurante matriz"""
    # Verificar se matriz existe
    matriz = get_restaurante_by_id(db, restaurante_matriz_id)
    if not matriz:
        raise ValueError("Restaurante matriz não encontrado")
    
    if not matriz.eh_matriz:
        raise ValueError("Só é possível criar unidades para restaurantes matriz")
    
    # Criar filial com mesmo nome da matriz
    db_unidade = Restaurante(
        nome=matriz.nome,
        cnpj=None,  # Filiais não tem CNPJ próprio
        tipo=matriz.tipo,
        tem_delivery=unidade.tem_delivery if hasattr(unidade, 'tem_delivery') and unidade.tem_delivery is not None else matriz.tem_delivery,
        endereco=unidade.endereco,
        bairro=unidade.bairro,
        cidade=unidade.cidade,
        estado=unidade.estado,
        telefone=unidade.telefone,
        ativo=True,
        eh_matriz=False,
        restaurante_pai_id=restaurante_matriz_id
    )
    
    db.add(db_unidade)
    db.commit()
    db.refresh(db_unidade)
    return db_unidade

def get_restaurante_by_id(db: Session, restaurante_id: int) -> Optional[Restaurante]:
    """Busca restaurante por ID"""
    return db.query(Restaurante).filter(Restaurante.id == restaurante_id).first()

def get_restaurantes_grid(db: Session) -> List[Restaurante]:
    """Lista apenas restaurantes matriz para exibição em grid"""
    return db.query(Restaurante).filter(
        Restaurante.eh_matriz == True
    ).order_by(Restaurante.nome).all()

def get_restaurantes_com_unidades(db: Session) -> List[dict]:
    """Lista restaurantes com suas unidades para grid expandida"""
    matrizes = db.query(Restaurante).filter(
        Restaurante.eh_matriz == True
    ).order_by(Restaurante.nome).all()
    
    resultado = []
    for matriz in matrizes:
        # Buscar unidades da matriz
        unidades = db.query(Restaurante).filter(
            Restaurante.restaurante_pai_id == matriz.id
        ).order_by(Restaurante.cidade, Restaurante.bairro).all()
        
        # Dados da matriz
        matriz_data = {
            "id": matriz.id,
            "nome": matriz.nome,
            "cidade": matriz.cidade,
            "estado": matriz.estado,
            "tipo": matriz.tipo,
            "tem_delivery": matriz.tem_delivery,
            "eh_matriz": True,
            "quantidade_unidades": 1 + len(unidades),
            "ativo": matriz.ativo,
            "unidades": []
        }
        
        # Adicionar unidades/filiais
        for unidade in unidades:
            unidade_data = {
                "id": unidade.id,
                "nome": unidade.nome,
                "cidade": unidade.cidade,
                "estado": unidade.estado,
                "tipo": unidade.tipo,
                "tem_delivery": unidade.tem_delivery,
                "eh_matriz": False,
                "quantidade_unidades": 1,
                "ativo": unidade.ativo
            }
            matriz_data["unidades"].append(unidade_data)
        
        resultado.append(matriz_data)
    
    return resultado

def get_restaurantes(db: Session, skip: int = 0, limit: int = 100) -> List[Restaurante]:
    """Lista todos os restaurantes (matrizes e filiais) com paginação"""
    return db.query(Restaurante).offset(skip).limit(limit).all()

def get_tipos_restaurante() -> List[str]:
    """Retorna lista dos tipos de estabelecimento disponíveis"""
    return [
        "restaurante",
        "bar", 
        "pub",
        "quiosque",
        "lanchonete",
        "cafeteria",
        "pizzaria",
        "hamburgueria",
        "churrascaria",
        "bistrô",
        "fast_food",
        "food_truck"
    ]

def update_restaurante(db: Session, restaurante_id: int, restaurante_update: RestauranteUpdate) -> Optional[Restaurante]:
    """Atualiza um restaurante"""
    db_restaurante = get_restaurante_by_id(db, restaurante_id)
    if not db_restaurante:
        return None
    
    # Preparar dados para atualização
    update_data = restaurante_update.model_dump(exclude_unset=True)
    
    # ============================================================================
    # LÓGICA ESPECIAL PARA CNPJ EM FILIAIS
    # ============================================================================
    if 'cnpj' in update_data:
        # Se é filial, CNPJ deve ser NULL, não string vazia
        if not db_restaurante.eh_matriz:
            update_data['cnpj'] = None  # Filial não tem CNPJ
        else:
            # Para matriz, validar CNPJ único se está sendo alterado
            cnpj_novo = update_data['cnpj']
            if cnpj_novo and cnpj_novo.strip() != '':
                # Verificar se CNPJ não é duplicado
                existing = db.query(Restaurante).filter(
                    Restaurante.cnpj == cnpj_novo,
                    Restaurante.id != restaurante_id
                ).first()
                if existing:
                    raise ValueError(f"CNPJ {cnpj_novo} já está cadastrado")
            else:
                # Se CNPJ vazio para matriz, definir como NULL
                update_data['cnpj'] = None
    
    # Aplicar atualizações
    for field, value in update_data.items():
        setattr(db_restaurante, field, value)
    
    db.commit()
    db.refresh(db_restaurante)
    return db_restaurante

def delete_restaurante(db: Session, restaurante_id: int) -> bool:
    """Deleta um restaurante (e suas unidades se for matriz)"""
    db_restaurante = get_restaurante_by_id(db, restaurante_id)
    if not db_restaurante:
        return False
    
    # Se for matriz, verificar se tem receitas em qualquer unidade
    if db_restaurante.eh_matriz:
        # Buscar todas as unidades
        unidades_ids = [db_restaurante.id]  # Incluir a própria matriz
        unidades = db.query(Restaurante).filter(
            Restaurante.restaurante_pai_id == db_restaurante.id
        ).all()
        unidades_ids.extend([u.id for u in unidades])
        
        # Verificar se alguma unidade tem receitas
        receitas_count = db.query(Receita).filter(
            Receita.restaurante_id.in_(unidades_ids)
        ).count()
        
        if receitas_count > 0:
            raise ValueError("Não é possível excluir: existem receitas vinculadas")
    
    # Deletar (cascade irá remover unidades automaticamente)
    db.delete(db_restaurante)
    db.commit()
    return True

def get_restaurante_estatisticas(db: Session, restaurante_id: int) -> dict:
    """Retorna estatísticas de um restaurante específico"""
    restaurante = get_restaurante_by_id(db, restaurante_id)
    if not restaurante:
        return {}
    
    # Se for matriz, incluir estatísticas de todas as unidades
    if restaurante.eh_matriz:
        unidades_ids = [restaurante.id]
        unidades = db.query(Restaurante).filter(
            Restaurante.restaurante_pai_id == restaurante.id
        ).all()
        unidades_ids.extend([u.id for u in unidades])
    else:
        unidades_ids = [restaurante.id]
    
    # Contar receitas por unidade
    total_receitas = db.query(Receita).filter(
        Receita.restaurante_id.in_(unidades_ids)
    ).count()
    
    total_receitas = db.query(Receita).filter(
        Receita.restaurante_id.in_(unidades_ids)
    ).count()
    
    # Para implementação futura: últimos insumos cadastrados
    return {
        "restaurante_id": restaurante_id,
        "nome": restaurante.nome,
        "quantidade_unidades": len(unidades_ids),
        "total_receitas": total_receitas,
        "ultimos_insumos": [],  # Implementar futuramente
        "ultimas_receitas": []  # Implementar futuramente
    }

# ===================================================================================================
# CRUD Receitas
# ===================================================================================================

def create_receita(db: Session, receita: ReceitaCreate) -> Receita:
    """Cria uma nova receita"""
    # Converter preço de reais para centavos se fornecido
    preco_venda_centavos = None
    if receita.preco_venda_real is not None:
        preco_venda_centavos = int(receita.preco_venda_real * 100)
    
    # Converter margem para centavos se fornecida
    margem_centavos = None
    if receita.margem_percentual_real is not None:
        margem_centavos = int(receita.margem_percentual_real * 100)
    
    db_receita = Receita(
        grupo=receita.grupo,
        subgrupo=receita.subgrupo,
        codigo=receita.codigo.upper(),
        nome=receita.nome,
        quantidade=receita.quantidade,
        fator=receita.fator,
        unidade=receita.unidade,
        restaurante_id=receita.restaurante_id,
        preco_venda=preco_venda_centavos,
        cmv=0,  # Será calculado automaticamente
        margem_percentual=margem_centavos,
        receita_pai_id=receita.receita_pai_id,
        variacao_nome=receita.variacao_nome,
        descricao=receita.descricao,
        modo_preparo=receita.modo_preparo,
        tempo_preparo_minutos=receita.tempo_preparo_minutos,
        rendimento_porcoes=receita.rendimento_porcoes,
        ativo=receita.ativo
    )

    db.add(db_receita)
    db.commit()
    db.refresh(db_receita)
    return db_receita

def get_receita_by_id(db: Session, receita_id: int) -> Optional[Receita]:
    # ===================================================================================================
    # CORREÇÃO: Adicionar joinedload para receitas processadas usadas como insumos
    # ===================================================================================================
    """Busca receita por ID com relacionamentos"""
    return db.query(Receita).options(
        joinedload(Receita.restaurante),
        joinedload(Receita.receita_insumos).joinedload(ReceitaInsumo.insumo),
        joinedload(Receita.receita_insumos).joinedload(ReceitaInsumo.receita_processada),
        joinedload(Receita.receita_pai),
        joinedload(Receita.variacoes)
    ).filter(Receita.id == receita_id).first()

def get_receitas(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    restaurante_id: Optional[int] = None,
    grupo: Optional[str] = None,
    ativo: Optional[bool] = None
) -> List[Receita]:
    # ===================================================================================================
    # CORREÇÃO: Adicionar joinedload para carregar receita_insumos com relacionamentos
    # ===================================================================================================
    """
    Lista receitas com filtros opcionais.
    
    IMPORTANTE: Filtra apenas receitas com restaurante_id válido
    para evitar erros com registros órfãos em produção.
    """
    # ============================================================================
    # Filtro base: apenas receitas com restaurante_id válido
    # ============================================================================
    query = db.query(Receita).filter(
        Receita.restaurante_id.isnot(None)
    ).options(
        joinedload(Receita.restaurante),
        joinedload(Receita.receita_insumos).joinedload(ReceitaInsumo.insumo),
        joinedload(Receita.receita_insumos).joinedload(ReceitaInsumo.receita_processada)
    )
    
    if restaurante_id:
        query = query.filter(Receita.restaurante_id == restaurante_id)
    if grupo:
        query = query.filter(Receita.grupo == grupo)
    if ativo is not None:
        query = query.filter(Receita.ativo == ativo)
    
    return query.offset(skip).limit(limit).all()

def search_receitas(db: Session, termo: str, restaurante_id: Optional[int] = None) -> List[Receita]:
    """Busca receitas por termo (nome ou código)"""
    query = db.query(Receita).options(joinedload(Receita.restaurante))
    
    # Buscar por nome ou código
    search_filter = or_(
        Receita.nome.ilike(f"%{termo}%"),
        Receita.codigo.ilike(f"%{termo}%")
    )
    query = query.filter(search_filter)
    
    if restaurante_id:
        query = query.filter(Receita.restaurante_id == restaurante_id)
    
    return query.limit(50).all()

def update_receita(db: Session, receita_id: int, receita_update: ReceitaUpdate) -> Optional[Receita]:
    """Atualiza uma receita"""
    db_receita = get_receita_by_id(db, receita_id)
    if not db_receita:
        return None
    
    # Atualizar campos fornecidos
    update_data = receita_update.model_dump(exclude_unset=True)
    
    # Converter preços se fornecidos
    if 'preco_venda_real' in update_data and update_data['preco_venda_real'] is not None:
        update_data['preco_venda'] = int(update_data['preco_venda_real'] * 100)
        del update_data['preco_venda_real']
    
    if 'margem_percentual_real' in update_data and update_data['margem_percentual_real'] is not None:
        update_data['margem_percentual'] = int(update_data['margem_percentual_real'] * 100)
        del update_data['margem_percentual_real']
    
    for field, value in update_data.items():
        setattr(db_receita, field, value)
    
    db.commit()
    db.refresh(db_receita)
    return db_receita

def delete_receita(db: Session, receita_id: int) -> bool:
    """Deleta uma receita"""
    db_receita = get_receita_by_id(db, receita_id)
    if not db_receita:
        return False
    
    db.delete(db_receita)
    db.commit()
    return True

def clear_all_receitas(db: Session) -> dict:
    """
    Remove todas as receitas do sistema para limpeza completa - VERSÃO SIMPLIFICADA.
    
    PROCESSO DE LIMPEZA:
    1. Remove todos os relacionamentos receita-insumos
    2. Remove todas as receitas do banco
    3. Retorna estatísticas da operação
    
    ATENÇÃO: Esta operação é irreversível!
    
    Returns:
        dict: Estatísticas da limpeza realizada
    """
    try:
        # Contar registros antes da limpeza
        total_receitas = db.query(Receita).count()
        total_receita_insumos = db.query(ReceitaInsumo).count()
        
        # Passo 1: Remover todos os relacionamentos receita-insumos
        db.query(ReceitaInsumo).delete()
        
        # Passo 2: Remover todas as receitas
        db.query(Receita).delete()
        
        # Confirmar transação
        db.commit()
        
        return {
            "receitas_removidas": total_receitas,
            "relacionamentos_removidos": total_receita_insumos,
            "status": "sucesso"
        }
    
    except Exception as e:
        # Reverter transação em caso de erro
        db.rollback()
        raise e

# ===================================================================================================
# CRUD Receita-Insumos (COM AUTOMAÇÃO COMPLETA)
# ===================================================================================================

def add_insumo_to_receita(db: Session, receita_id: int, receita_insumo: ReceitaInsumoCreate) -> ReceitaInsumo:
    """
    Adiciona insumo à receita com cálculo automático de custo.
    
    AUTOMAÇÃO IMPLEMENTADA:
    1. Calcula custo do insumo automaticamente
    2. Salva o relacionamento receita-insumo
    3. Recalcula CMV total da receita automaticamente
    4. Atualiza preços sugeridos automaticamente
    """
    # Verificar se insumo existe
    insumo = db.query(Insumo).filter(Insumo.id == receita_insumo.insumo_id).first()
    if not insumo:
        raise ValueError("Insumo não encontrado")
    
    # Calcular custo automaticamente
    custo_calculado = calcular_custo_insumo(
        insumo, 
        receita_insumo.quantidade_necessaria,
        receita_insumo.unidade_medida
    )
    
    # Criar relacionamento
    db_receita_insumo = ReceitaInsumo(
        receita_id=receita_id,
        insumo_id=receita_insumo.insumo_id,
        quantidade_necessaria=receita_insumo.quantidade_necessaria,
        unidade_medida=receita_insumo.unidade_medida,
        custo_calculado=custo_calculado,
        observacoes=receita_insumo.observacoes
    )

    db.add(db_receita_insumo)
    db.commit()
    db.refresh(db_receita_insumo)

    # ✅ AUTOMAÇÃO: Atualizar CMV total da receita
    calcular_cmv_receita(db, receita_id)

    return db_receita_insumo

def update_insumo_in_receita(
        db: Session,
        receita_insumo_id: int,
        receita_insumo_update: ReceitaInsumoUpdate
) -> Optional[ReceitaInsumo]:
    """
    Atualiza quantidade ou dados de um insumo na receita.
    
    AUTOMAÇÃO IMPLEMENTADA:
    1. Atualiza dados do relacionamento
    2. Recalcula custo se quantidade mudou
    3. Recalcula CMV total da receita automaticamente
    4. Atualiza preços sugeridos automaticamente
    """
    db_receita_insumo = db.query(ReceitaInsumo).options(
        joinedload(ReceitaInsumo.insumo)
    ).filter(ReceitaInsumo.id == receita_insumo_id).first()

    if not db_receita_insumo:
        return None
    
    # Atualizar campos fornecidos
    for field, value in receita_insumo_update.model_dump(exclude_unset=True).items():
        setattr(db_receita_insumo, field, value)

    # Recalcular custo se quantidade ou unidade foi alterada
    update_fields = receita_insumo_update.model_dump(exclude_unset=True)
    if 'quantidade_necessaria' in update_fields or 'unidade_medida' in update_fields:
        custo_recalculado = calcular_custo_insumo(
            db_receita_insumo.insumo, 
            db_receita_insumo.quantidade_necessaria,
            db_receita_insumo.unidade_medida
        )
        db_receita_insumo.custo_calculado = custo_recalculado

    db.commit()
    db.refresh(db_receita_insumo)

    # ✅ AUTOMAÇÃO: Atualizar CMV da receita
    calcular_cmv_receita(db, db_receita_insumo.receita_id)

    return db_receita_insumo

def remove_insumo_from_receita(db: Session, receita_insumo_id: int) -> bool:
    """
    Remove um insumo de uma receita.
    
    AUTOMAÇÃO IMPLEMENTADA:
    1. Remove o relacionamento
    2. Recalcula CMV total da receita automaticamente
    3. Atualiza preços sugeridos automaticamente
    """
    db_receita_insumo = db.query(ReceitaInsumo).filter(
        ReceitaInsumo.id == receita_insumo_id
    ).first()

    if not db_receita_insumo:
        return False
    
    receita_id = db_receita_insumo.receita_id

    db.delete(db_receita_insumo)
    db.commit()

    # ✅ AUTOMAÇÃO: Atualizar CMV da receita
    calcular_cmv_receita(db, receita_id)

    return True

def get_receita_insumos(db: Session, receita_id: int) -> List[ReceitaInsumo]:
    """Lista todos os insumos de uma receita"""
    return db.query(ReceitaInsumo).options(
        joinedload(ReceitaInsumo.insumo)
    ).filter(ReceitaInsumo.receita_id == receita_id).all()

# ===================================================================================================
# FUNÇÕES DE CÁLCULO (CORRIGIDAS COM SISTEMA DE PREÇOS AUTOMÁTICO)
# ===================================================================================================

def calcular_cmv_receita(db: Session, receita_id: int) -> float:
    """
    Recalcula o CMV de uma receita baseado nos insumos.
    
    AUTOMAÇÃO IMPLEMENTADA:
    - Soma todos os custos calculados dos insumos da receita
    - Recalcula custos individuais se necessário
    - Atualiza registro da receita automaticamente
    
    Args:
        db (Session): Sessão do banco de dados
        receita_id (int): ID da receita
        
    Returns:
        float: Custo total de produção em reais
    """
    receita = get_receita_by_id(db, receita_id)
    if not receita:
        return 0.0
    
    # Somar custos de todos os insumos
    total_custo = 0.0
    receita_insumos = get_receita_insumos(db, receita_id)
    
    for receita_insumo in receita_insumos:
        # Recalcular custo do insumo se necessário
        if receita_insumo.insumo:
            custo_recalculado = calcular_custo_insumo(
                receita_insumo.insumo, 
                receita_insumo.quantidade_necessaria,
                receita_insumo.unidade_medida
            )
            # Atualizar custo no relacionamento se mudou
            if abs(custo_recalculado - (receita_insumo.custo_calculado or 0)) > 0.001:
                receita_insumo.custo_calculado = custo_recalculado
                db.add(receita_insumo)
            
            total_custo += custo_recalculado
    
    # Dividir pelo fator para obter o custo unitário
    fator_receita = receita.fator if receita.fator and receita.fator > 0 else 1.0
    custo_unitario = total_custo / fator_receita
    
    # Atualizar CMV na receita (em centavos e reais)
    receita.cmv = int(total_custo * 100)

    db.add(receita)
    db.commit()
    db.refresh(receita)

    return custo_unitario

def calcular_precos_sugeridos(db: Session, receita_id: int) -> dict:
    """
    Calcula preços sugeridos para uma receita baseado no custo de produção atual.
    
    SISTEMA CORRIGIDO:
    - custo_producao = quanto custa para fazer a receita
    - precos_sugeridos = quanto cobrar do cliente para ter lucro
    
    Fórmula: Preço de venda = Custo ÷ (1 - Margem decimal)
    
    Args:
        db (Session): Sessão do banco de dados
        receita_id (int): ID da receita
        
    Returns:
        dict: Dicionário com custo e preços sugeridos formatados conforme schema
    """
    receita = get_receita_by_id(db, receita_id)
    if not receita:
        return {"error": "Receita não encontrada"}
    
    # Garantir que custo está atualizado
    custo_producao = calcular_cmv_receita(db, receita_id)
    
    if custo_producao <= 0:
        return {
            "receita_id": receita_id,
            "custo_producao": 0.0,
            "precos_sugeridos": {
                "margem_20_porcento": 0.0,
                "margem_25_porcento": 0.0,
                "margem_30_porcento": 0.0
            }
        }

    # Calcular preços com margem sobre custo
    # Fórmula: Preço = Custo ÷ Margem decimal
    precos_sugeridos = {
        "margem_20_porcento": round(custo_producao / 0.20, 2),  # Custo ÷ 0.20 = Custo × 5
        "margem_25_porcento": round(custo_producao / 0.25, 2),  # Custo ÷ 0.25 = Custo × 4
        "margem_30_porcento": round(custo_producao / 0.30, 2),  # Custo ÷ 0.30 = Custo × 3.33
    }

    return {
        "receita_id": receita_id,
        "custo_producao": round(custo_producao, 2),
        "precos_sugeridos": precos_sugeridos
    }

# ===================================================================================================
# Funções Utilitárias
# ===================================================================================================

def get_insumos_disponiveis(db: Session, termo: Optional[str] = None) -> List[Dict]:
    """
    Lista insumos disponíveis para adicionar em receitas.
    Inclui tanto insumos da tabela principal quanto receitas processadas.
    
    Útil para:
    - Dropdown de seleção de insumos
    - Autocomplete ao adicionar insumos
    
    Returns:
        List[Dict]: Lista combinada de insumos e receitas processadas
    """
    # ============================================================================
    # FILTRO DE BUSCA POR TERMO (NOME OU CODIGO)
    # ============================================================================
    if termo:
        search_filter = or_(
            Insumo.nome.ilike(f"%{termo}%"),
            Insumo.codigo.ilike(f"%{termo}%")
        )
        query_insumos = query_insumos.filter(search_filter)
    
    # ============================================================================
    # LIMITE AUMENTADO PARA EXIBIR TODOS OS INSUMOS NO SELECT
    # Antes: limit(50) - causava problema de exibir apenas 20 insumos alfabeticos
    # Agora: limit(1000) - permite carregar todos os insumos para o dropdown
    # ============================================================================
    insumos = query_insumos.order_by(Insumo.nome).all()
    
    # ===================================================================================================
    # BUSCAR RECEITAS PROCESSADAS (QUE PODEM SER USADAS COMO INSUMOS)
    # ===================================================================================================
    query_receitas = db.query(Receita).filter(Receita.processada == True)
    
    # ============================================================================
    # FILTRO DE BUSCA POR TERMO (NOME OU CODIGO) PARA RECEITAS PROCESSADAS
    # ============================================================================
    if termo:
        search_filter_receitas = or_(
            Receita.nome.ilike(f"%{termo}%"),
            Receita.codigo.ilike(f"%{termo}%")
        )
        query_receitas = query_receitas.filter(search_filter_receitas)
    
    # ============================================================================
    # LIMITE AUMENTADO PARA EXIBIR TODAS AS RECEITAS PROCESSADAS NO SELECT
    # Antes: limit(50) - limitava receitas processadas disponiveis
    # Agora: limit(500) - permite carregar todas as receitas processadas
    # ============================================================================
    receitas_processadas = query_receitas.order_by(Receita.nome).all()
    
    # ===================================================================================================
    # COMBINAR RESULTADOS EM FORMATO PADRONIZADO
    # ===================================================================================================
    resultados = []
    
    # Adicionar insumos tradicionais
    for insumo in insumos:
        resultados.append({
            'id': insumo.id,
            'nome': insumo.nome,
            'codigo': insumo.codigo,
            'unidade': insumo.unidade,
            'grupo': insumo.grupo,
            'subgrupo': insumo.subgrupo,
            'tipo': 'insumo',  # Identificador do tipo
            'preco_compra_real': insumo.preco_compra_real
        })
    
    # Adicionar receitas processadas
    for receita in receitas_processadas:
        # Calcular custo por rendimento
        custo_por_rendimento = receita.cmv_real if receita.cmv_real else 0.0
        if receita.rendimento_porcoes and receita.rendimento_porcoes > 0:
            custo_por_rendimento = float(custo_por_rendimento) / float(receita.rendimento_porcoes)
        
        resultados.append({
            'id': receita.id,
            'nome': f"{receita.nome} (Processado)",  # Indicador visual
            'codigo': receita.codigo,
            'unidade': receita.unidade,
            'grupo': receita.grupo,
            'subgrupo': receita.subgrupo,
            'tipo': 'receita_processada',  # Identificador do tipo
            'preco_compra_real': custo_por_rendimento,  # Custo por rendimento
            'rendimento_porcoes': receita.rendimento_porcoes,  # Adicionar rendimento para exibição
            'cmv_total': receita.cmv_real  # Custo total para referência
        })
    
    return resultados

def get_grupos_receitas(db: Session, restaurante_id: Optional[int] = None) -> List[str]:
    """Lista grupos únicos de receitas"""
    query = db.query(Receita.grupo).distinct()
    if restaurante_id:
        query = query.filter(Receita.restaurante_id == restaurante_id)
    return [grupo[0] for grupo in query.order_by(Receita.grupo).all()]

def get_subgrupos_receitas(db: Session, grupo: str, restaurante_id: Optional[int] = None) -> List[str]:
    """Lista subgrupos únicos de um grupo específico."""
    query = db.query(Receita.subgrupo).filter(Receita.grupo == grupo).distinct()
    if restaurante_id:
        query = query.filter(Receita.restaurante_id == restaurante_id)
    return [subgrupo[0] for subgrupo in query.order_by(Receita.subgrupo).all()]

def get_receitas_stats(db: Session, restaurante_id: Optional[int] = None) -> dict:
    """Retorna estatísticas das receitas."""
    query = db.query(Receita)
    if restaurante_id:
        query = query.filter(Receita.restaurante_id == restaurante_id)
    
    total_receitas = query.count()
    receitas_ativas = query.filter(Receita.ativo == True).count()
    receitas_com_cmv = query.filter(Receita.cmv > 0).count()
    
    return {
        "total_receitas": total_receitas,
        "receitas_ativas": receitas_ativas,
        "receitas_inativas": total_receitas - receitas_ativas,
        "receitas_com_custo": receitas_com_cmv,
        "receitas_sem_custo": total_receitas - receitas_com_cmv
    }