#   ===================================================================================================
#   Inicialização dos modelos -  Importa todos os modelos do sistema
#   Descrição: Este arquivo importa todos os modelos para que o SQLAlchemy e 
#   Alembic possam detectá-los automaticamente para migrações.
#   Data: 08/08/2025
#   Autor: Will - Empresa: IOGAR
#   ===================================================================================================

# Importar modelos de fornecedores e insumos
from .fornecedor import Fornecedor
from .fornecedor_insumo import FornecedorInsumo
from .insumo import Insumo
# from app.models.receita_insumo import ReceitaInsumo
# Importar modelos de taxonomia
from .taxonomia import Taxonomia
# Importar modelos de taxonomia
from .taxonomia import Taxonomia
from .taxonomia_alias import TaxonomiaAlias
from app.models.codigo_sequence import CodigoSequence
# Importar modelos de receitas
from .receita import Restaurante, Receita, ReceitaInsumo

# Importar modelo de códigos automáticos
from .codigo_disponivel import CodigoDisponivel

# Importar modelo de usuários
from .user import User, UserRole

# Importar modelo de permissões
from .permission import Permission, ResourceType, ActionType, DataScope

# Lista de todos os modelos para exportação
__all__ = [
    "Base", 
    "BaseModel", 
    "Fornecedor",
    "FornecedorInsumo", 
    "Insumo",
    "Taxonomia",
    "Restaurante",
    "Receita",
    "ReceitaInsumo",
    "CodigoDisponivel",
    "User",
    "UserRole",
    "Permission",
    "ResourceType",
    "ActionType",
    "DataScope"
    ]
