"""
Modulo de dependencias para autenticacao e autorizacao.
Fornece funcoes que verificam tokens JWT e permissoes de usuarios.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import ALGORITHM
from app.database import get_db
from app.models.user import User

# Configuracao do esquema de seguranca Bearer
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependencia que verifica o token JWT e retorna o usuario atual.
    
    Args:
        credentials: Credenciais HTTP Bearer com o token JWT
        db: Sessao do banco de dados
    
    Returns:
        Usuario autenticado
    
    Raises:
        HTTPException: Se o token for invalido ou o usuario nao existir
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nao foi possivel validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extrair o token das credenciais
        token = credentials.credentials
        
        # Decodificar o token JWT
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[int] = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Buscar usuario no banco de dados
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if user is None:
        raise credentials_exception
    
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inativo"
        )
    
    return user


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependencia que verifica se o usuario atual e um administrador.
    
    Args:
        current_user: Usuario autenticado pela dependencia get_current_user
    
    Returns:
        Usuario administrador autenticado
    
    Raises:
        HTTPException: Se o usuario nao tiver permissoes de administrador
    """
    if current_user.tipo_usuario != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissoes insuficientes. Apenas administradores podem acessar este recurso"
        )
    
    return current_user


async def get_consultant_or_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependencia que verifica se o usuario e consultor ou administrador.
    
    Args:
        current_user: Usuario autenticado pela dependencia get_current_user
    
    Returns:
        Usuario consultor ou administrador autenticado
    
    Raises:
        HTTPException: Se o usuario nao tiver permissoes adequadas
    """
    if current_user.tipo_usuario not in ["ADMIN", "CONSULTANT"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissoes insuficientes. Apenas administradores e consultores podem acessar este recurso"
        )
    
    return current_user