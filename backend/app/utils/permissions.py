# ============================================================================
# UTILS PERMISSIONS - Sistema de Verificação de Permissões
# ============================================================================
# Descrição: Funções e decorators para verificar permissões configuráveis
# Permite validação dinâmica baseada nas permissões do banco de dados
# Data: 21/10/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

from functools import wraps
from typing import List, Optional
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.permission import Permission, ResourceType, ActionType, DataScope
from app.api.deps import get_db, get_current_user


# ============================================================================
# CACHE DE PERMISSÕES EM MEMÓRIA (PERFORMANCE)
# ============================================================================

_permissions_cache = {}
_cache_timestamp = None
_cache_ttl = 300  # 5 minutos

def _clear_permissions_cache():
    """Limpa o cache de permissões"""
    global _permissions_cache, _cache_timestamp
    _permissions_cache = {}
    _cache_timestamp = None


def _get_user_permissions(db: Session, user: User) -> List[dict]:
    """
    Busca todas as permissões de um usuário (com cache).
    
    IMPORTANTE: Retorna dicionários ao invés de objetos Permission
    para evitar DetachedInstanceError do SQLAlchemy.
    
    Args:
        db: Sessão do banco de dados
        user: Usuário autenticado
    
    Returns:
        Lista de dicionários com dados das permissões
    """
    import time
    global _permissions_cache, _cache_timestamp
    
    # Verificar se cache expirou
    current_time = time.time()
    if _cache_timestamp is None or (current_time - _cache_timestamp) > _cache_ttl:
        _clear_permissions_cache()
        _cache_timestamp = current_time
    
    # Verificar se permissões do usuário estão em cache
    cache_key = f"{user.role}_{user.id}"
    if cache_key in _permissions_cache:
        return _permissions_cache[cache_key]
    
    # Buscar permissões do banco
    permissions = db.query(Permission).filter(
        Permission.role == user.role.value,
        Permission.enabled == True
    ).all()
    
    # Converter objetos Permission para dicionários (evita DetachedInstanceError)
    permissions_data = [
        {
            'id': p.id,
            'role': p.role,
            'resource': p.resource,
            'action': p.action,
            'data_scope': p.data_scope,
            'enabled': p.enabled
        }
        for p in permissions
    ]
    
    # Guardar em cache
    _permissions_cache[cache_key] = permissions_data
    
    return permissions_data


# ============================================================================
# FUNÇÃO PRINCIPAL DE VERIFICAÇÃO DE PERMISSÃO
# ============================================================================

def check_user_permission(
    user: User,
    resource: ResourceType,
    action: ActionType,
    db: Session
) -> tuple[bool, Optional[DataScope]]:
    """
    Verifica se o usuário tem permissão para executar uma ação em um recurso.
    
    Args:
        user: Usuário autenticado
        resource: Recurso do sistema (DASHBOARD, INSUMOS, etc)
        action: Ação desejada (VISUALIZAR, CRIAR, etc)
        db: Sessão do banco de dados
    
    Returns:
        Tupla (tem_permissao: bool, escopo_dados: DataScope)
    
    Exemplo:
        has_perm, scope = check_user_permission(user, ResourceType.RECEITAS, ActionType.CRIAR, db)
        if not has_perm:
            raise HTTPException(403, "Sem permissão")
    """
    # ========================================================================
    # BYPASS AUTOMÁTICO PARA ADMIN
    # ========================================================================
    # ADMIN tem acesso total a todos os recursos e ações, sem precisar de
    # permissões cadastradas no banco de dados
    if user.role.value == "ADMIN":
        return True, DataScope.TODOS
    
    # ========================================================================
    # USUÁRIOS NÃO-ADMIN: Verificar permissões no banco de dados
    # ========================================================================
    # Buscar permissões do usuário (retorna lista de dicionários)
    permissions = _get_user_permissions(db, user)
    
    # Procurar permissão específica
    for permission in permissions:
        # Comparar strings ao invés de enums (permission agora é dict)
        if permission['resource'] == resource.value and permission['action'] == action.value:
            return True, DataScope(permission['data_scope'])
    
    # Verificar se usuário tem permissão de GERENCIAR (implica todas as outras)
    for permission in permissions:
        if permission['resource'] == resource.value and permission['action'] == ActionType.GERENCIAR.value:
            return True, DataScope(permission['data_scope'])
    
    return False, None


# ============================================================================
# DECORATOR PARA ROTAS - VERIFICAÇÃO DE PERMISSÃO
# ============================================================================

def require_permission(resource: ResourceType, action: ActionType):
    """
    Decorator que verifica se o usuário tem permissão antes de executar a rota.
    
    Args:
        resource: Recurso do sistema
        action: Ação necessária
    
    Raises:
        HTTPException 403: Se usuário não tem permissão
    
    Uso:
        @router.post("/receitas")
        @require_permission(ResourceType.RECEITAS, ActionType.CRIAR)
        def criar_receita(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
            # Só executa se usuário tiver permissão
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extrair db e user dos kwargs
            db = kwargs.get('db')
            user = kwargs.get('current_user') or kwargs.get('user')
            
            if not db or not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro interno: dependências não encontradas"
                )
            
            # Verificar permissão
            has_permission, data_scope = check_user_permission(user, resource, action, db)
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Você não tem permissão para {action.value} em {resource.value}"
                )
            
            # Adicionar escopo aos kwargs para uso na função
            kwargs['user_data_scope'] = data_scope
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# ============================================================================
# DEPENDENCY PARA FASTAPI - VERIFICAÇÃO DE PERMISSÃO
# ============================================================================

class PermissionChecker:
    """
    Dependency do FastAPI para verificar permissões.
    
    Uso mais recomendado que o decorator, pois é mais compatível com FastAPI.
    
    Exemplo:
        @router.post("/receitas")
        def criar_receita(
            db: Session = Depends(get_db),
            user: User = Depends(get_current_user),
            _: None = Depends(PermissionChecker(ResourceType.RECEITAS, ActionType.CRIAR))
        ):
            # Só executa se usuário tiver permissão
            pass
    """
    
    def __init__(self, resource: ResourceType, action: ActionType):
        self.resource = resource
        self.action = action
    
    def __call__(
        self,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> DataScope:
        """
        Verifica permissão e retorna o escopo de dados.
        
        Returns:
            DataScope: Escopo de dados do usuário
        
        Raises:
            HTTPException 403: Se não tiver permissão
        """

        # DEBUG: Logs detalhados
        print(f"🔐 === PERMISSION CHECKER ===")
        print(f"👤 Usuário: {user.username} (ID: {user.id})")
        print(f"🎭 Role: {user.role} (type: {type(user.role)})")
        print(f"🎭 Role.value: {user.role.value}")
        print(f"📦 Resource: {self.resource.value}")
        print(f"⚡ Action: {self.action.value}")

        has_permission, data_scope = check_user_permission(
            user, self.resource, self.action, db
        )

        print(f"✅ has_permission: {has_permission}")
        print(f"📊 data_scope: {data_scope}")
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Você não tem permissão para {self.action.value} em {self.resource.value}"
            )
        print(f"✅ PERMISSÃO CONCEDIDA!")
        return data_scope


# ============================================================================
# FUNÇÕES AUXILIARES DE FILTRO POR ESCOPO
# ============================================================================

def apply_data_scope_filter(
    query,
    user: User,
    data_scope: DataScope,
    restaurante_id_column,
    created_by_column=None,
    db: Session = None
):
    """
    Aplica filtro à query baseado no escopo de dados do usuário.
    
    Args:
        query: Query do SQLAlchemy
        user: Usuário autenticado
        data_scope: Escopo de dados (TODOS, REDE, LOJA, PROPRIOS)
        restaurante_id_column: Coluna de restaurante_id da tabela
        created_by_column: Coluna de created_by (opcional, para PROPRIOS)
        db: Sessão do banco (necessário para escopo REDE)
    
    Returns:
        Query filtrada
    
    Exemplo:
        query = db.query(Receita)
        query = apply_data_scope_filter(
            query, user, data_scope, 
            Receita.restaurante_id, 
            Receita.created_by
        )
    """
    from app.models.receita import Restaurante
    
    # TODOS: sem filtro
    if data_scope == DataScope.TODOS:
        return query
    
    # REDE: filtrar por todos restaurantes da rede
    if data_scope == DataScope.REDE:
        if not user.restaurante_id or not db:
            return query
        
        # Buscar restaurante do usuário
        restaurante_user = db.query(Restaurante).filter(
            Restaurante.id == user.restaurante_id
        ).first()
        
        if not restaurante_user:
            return query
        
        # Determinar IDs da rede
        if restaurante_user.eh_matriz:
            # Matriz: buscar matriz + unidades
            rede_ids = db.query(Restaurante.id).filter(
                (Restaurante.id == restaurante_user.id) |
                (Restaurante.restaurante_pai_id == restaurante_user.id)
            ).all()
        elif restaurante_user.restaurante_pai_id:
            # Unidade: buscar matriz + todas unidades
            matriz_id = restaurante_user.restaurante_pai_id
            rede_ids = db.query(Restaurante.id).filter(
                (Restaurante.id == matriz_id) |
                (Restaurante.restaurante_pai_id == matriz_id)
            ).all()
        else:
            # Sem rede, apenas o próprio
            rede_ids = [(user.restaurante_id,)]
        
        rede_ids = [r[0] for r in rede_ids]
        return query.filter(restaurante_id_column.in_(rede_ids))
    
    # LOJA: filtrar por restaurante do usuário
    if data_scope == DataScope.LOJA:
        if not user.restaurante_id:
            return query.filter(False)  # Sem acesso
        return query.filter(restaurante_id_column == user.restaurante_id)
    
    # PROPRIOS: filtrar por registros criados pelo usuário
    if data_scope == DataScope.PROPRIOS:
        if not created_by_column:
            # Se não tem coluna created_by, usar filtro de loja
            if not user.restaurante_id:
                return query.filter(False)
            return query.filter(restaurante_id_column == user.restaurante_id)
        return query.filter(created_by_column == user.id)
    
    # Fallback seguro: sem acesso
    return query.filter(False)


# ============================================================================
# FUNÇÃO PARA INVALIDAR CACHE (USAR QUANDO PERMISSÕES MUDAREM)
# ============================================================================

def invalidate_permissions_cache():
    """
    Invalida o cache de permissões.
    Deve ser chamado sempre que permissões forem alteradas no banco.
    
    Uso:
        # Após atualizar permissão
        db.commit()
        invalidate_permissions_cache()
    """
    _clear_permissions_cache()


# ============================================================================
# FUNÇÃO HELPER PARA VERIFICAR SE USUÁRIO PODE ACESSAR RECURSO
# ============================================================================

def can_access_resource(
    user: User,
    resource_owner_id: int,
    resource_restaurante_id: Optional[int],
    data_scope: DataScope,
    db: Session
) -> bool:
    """
    Verifica se usuário pode acessar um recurso específico baseado no escopo.
    
    Args:
        user: Usuário autenticado
        resource_owner_id: ID do criador do recurso
        resource_restaurante_id: ID do restaurante do recurso
        data_scope: Escopo de dados do usuário
        db: Sessão do banco
    
    Returns:
        bool: True se pode acessar, False caso contrário
    
    Exemplo:
        # Verificar se pode editar uma receita
        if not can_access_resource(user, receita.created_by, receita.restaurante_id, scope, db):
            raise HTTPException(403, "Sem acesso a este recurso")
    """
    from app.models.receita import Restaurante
    
    # TODOS: acesso total
    if data_scope == DataScope.TODOS:
        return True
    
    # REDE: verificar se recurso está na mesma rede
    if data_scope == DataScope.REDE:
        if not user.restaurante_id or not resource_restaurante_id:
            return False
        
        # Buscar restaurante do usuário
        restaurante_user = db.query(Restaurante).filter(
            Restaurante.id == user.restaurante_id
        ).first()
        
        # Buscar restaurante do recurso
        restaurante_resource = db.query(Restaurante).filter(
            Restaurante.id == resource_restaurante_id
        ).first()
        
        if not restaurante_user or not restaurante_resource:
            return False
        
        # Verificar se estão na mesma rede
        # Caso 1: Ambos têm o mesmo pai
        if (restaurante_user.restaurante_pai_id and 
            restaurante_user.restaurante_pai_id == restaurante_resource.restaurante_pai_id):
            return True
        
        # Caso 2: User é matriz e resource é unidade da matriz
        if (restaurante_user.eh_matriz and 
            restaurante_resource.restaurante_pai_id == restaurante_user.id):
            return True
        
        # Caso 3: User é unidade e resource é a matriz
        if (restaurante_user.restaurante_pai_id == restaurante_resource.id and
            restaurante_resource.eh_matriz):
            return True
        
        # Caso 4: São o mesmo restaurante
        if restaurante_user.id == restaurante_resource.id:
            return True
        
        return False
    
    # LOJA: verificar se é do mesmo restaurante
    if data_scope == DataScope.LOJA:
        if not user.restaurante_id or not resource_restaurante_id:
            return False
        return user.restaurante_id == resource_restaurante_id
    
    # PROPRIOS: verificar se é o criador
    if data_scope == DataScope.PROPRIOS:
        return user.id == resource_owner_id
    
    return False