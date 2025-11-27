# ============================================================================
# CONFIGURACAO DE CODIGOS AUTOMATICOS
# ============================================================================
# Descricao: Define as faixas de codigos para cada tipo de entidade
# Autor: Will - Empresa: IOGAR
# Data: 15/10/2025
# ============================================================================

from enum import Enum

# ============================================================================
# ENUMS DE TIPOS DE CODIGO
# ============================================================================

class TipoCodigo(str, Enum):
    """
    Tipos de entidades que recebem codigos automaticos
    """
    RECEITA_NORMAL = "receita_normal"
    RECEITA_PROCESSADA = "receita_processada"
    INSUMO = "insumo"

# ============================================================================
# FAIXAS DE CODIGOS
# ============================================================================

FAIXAS_CODIGOS = {
    TipoCodigo.RECEITA_NORMAL: {
        "inicio": 3000,
        "fim": 3999,
        "prefixo": "",  # Sem prefixo - apenas números
        "descricao": "Receitas Normais"
    },
    TipoCodigo.RECEITA_PROCESSADA: {
        "inicio": 4000,
        "fim": 4999,
        "prefixo": "",  # Sem prefixo - apenas números
        "descricao": "Receitas Processadas"
    },
    TipoCodigo.INSUMO: {
        "inicio": 5000,
        "fim": 7999,
        "prefixo": "",  # Sem prefixo - apenas números
        "descricao": "Insumos"
    }
}

# ============================================================================
# FUNCOES AUXILIARES
# ============================================================================

def obter_faixa(tipo: TipoCodigo) -> dict:
    """
    Retorna a configuracao da faixa para um tipo especifico
    
    Args:
        tipo: Tipo de codigo (TipoCodigo enum)
        
    Returns:
        dict com inicio, fim, prefixo e descricao
        
    Raises:
        ValueError: Se o tipo nao existe
    """
    if tipo not in FAIXAS_CODIGOS:
        raise ValueError(f"Tipo de codigo invalido: {tipo}")
    
    return FAIXAS_CODIGOS[tipo]

def validar_codigo_na_faixa(codigo: str, tipo: TipoCodigo) -> bool:
    """
    Valida se um codigo esta dentro da faixa esperada
    
    Args:
        codigo: Codigo a validar (ex: "REC-3045")
        tipo: Tipo de codigo esperado
        
    Returns:
        True se o codigo esta na faixa correta, False caso contrario
    """
    faixa = obter_faixa(tipo)
    
    # Extrair numero do codigo (remove prefixo e hifen)
    try:
        numero = int(codigo.split("-")[1])
    except (IndexError, ValueError):
        return False
    
    # Verificar se esta na faixa
    return faixa["inicio"] <= numero <= faixa["fim"]

def formatar_codigo(numero: int, tipo: TipoCodigo) -> str:
    """
    Formata um numero no padrao de codigo (apenas numeros, sem prefixo)
    
    Args:
        numero: Numero do codigo
        tipo: Tipo de codigo
        
    Returns:
        Codigo formatado (ex: "3045", "5001")
    """
    # Retornar apenas o número como string
    return str(numero)