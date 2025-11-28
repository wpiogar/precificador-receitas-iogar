# ============================================================================
# SERVICE DE GERACAO DE CODIGOS AUTOMATICOS
# ============================================================================
# Descricao: Logica de negocio para geracao automatica de codigos unicos
# Autor: Will - Empresa: IOGAR
# Data: 15/10/2025
# ============================================================================

from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Optional
import logging

# Imports do projeto
from app.config.codigo_config import TipoCodigo, obter_faixa, formatar_codigo, validar_codigo_na_faixa
from app.models.receita import Receita
from app.models.insumo import Insumo

# Configurar logger
logger = logging.getLogger(__name__)

# ============================================================================
# FUNCAO PRINCIPAL DE GERACAO
# ============================================================================

def gerar_proximo_codigo(db: Session, tipo: TipoCodigo, restaurante_id: int) -> str:
    """
    Gera o proximo codigo disponivel para o tipo especificado dentro do restaurante.
    USA TABELA DE SEQUÊNCIA para garantir que códigos nunca sejam reusados.
    
    IMPORTANTE: Cada restaurante possui sua própria sequência de códigos independente.
    O mesmo número de código pode existir em restaurantes diferentes.
    
    Args:
        db: Sessao do banco de dados
        tipo: Tipo de codigo a gerar (TipoCodigo enum)
        restaurante_id: ID do restaurante para o qual gerar o código
        
    Returns:
        Codigo gerado no formato "NUMERO" (ex: "5000")
        
    Raises:
        ValueError: Se a faixa estiver esgotada ou restaurante_id inválido
        Exception: Erros de banco de dados
    """
    try:
        # Importar modelo de sequência
        from app.models.codigo_sequence import CodigoSequence
        
        # Validar restaurante_id
        if restaurante_id is None or restaurante_id < -1:
            raise ValueError("restaurante_id é obrigatório e não pode ser menor que -1")
        
        # Obter configuracao da faixa
        faixa = obter_faixa(tipo)
        inicio = faixa["inicio"]
        fim = faixa["fim"]
        
        # Buscar ou criar registro de sequência para este restaurante + tipo
        tipo_str = tipo.value if hasattr(tipo, 'value') else str(tipo)
        
        sequence = db.query(CodigoSequence).filter(
            CodigoSequence.restaurante_id == restaurante_id,
            CodigoSequence.tipo_codigo == tipo_str
        ).first()
        
        if sequence is None:
            # Primeira vez gerando código para este restaurante + tipo
            # Buscar se já existe algum código no banco (dados legados)
            ultimo_numero_legado = _buscar_ultimo_codigo_usado(db, tipo, restaurante_id)
            
            if ultimo_numero_legado is None:
                # Começar do início da faixa
                proximo_numero = inicio
            else:
                # Começar do próximo após o último legado
                proximo_numero = ultimo_numero_legado + 1
            
            # Criar novo registro de sequência
            sequence = CodigoSequence(
                restaurante_id=restaurante_id,
                tipo_codigo=tipo_str,
                ultimo_numero=proximo_numero
            )
            db.add(sequence)
            db.flush()  # Garantir que foi inserido
            
        else:
            # Já existe sequência, incrementar
            proximo_numero = sequence.ultimo_numero + 1
            sequence.ultimo_numero = proximo_numero
            sequence.updated_at = func.now()
        
        # Validar se ainda ha codigos disponiveis na faixa
        # NOTA: Para insumos, o limite é muito alto (999999), praticamente infinito
        if proximo_numero > fim:
            raise ValueError(
                f"Limite máximo de códigos atingido para {faixa['descricao']} ({fim}). "
                f"Entre em contato com o suporte técnico."
            )
        
        # Commit da atualização da sequência
        db.commit()
        
        # Formatar e retornar o codigo (apenas o número)
        codigo_gerado = str(proximo_numero)
        
        logger.info(
            f"Codigo gerado: {codigo_gerado} (tipo: {tipo}, restaurante_id: {restaurante_id})"
        )
        
        return codigo_gerado
        
    except Exception as e:
        db.rollback()
        logger.error(
            f"Erro ao gerar codigo para tipo {tipo} e restaurante {restaurante_id}: {str(e)}"
        )
        raise

# ============================================================================
# FUNCOES AUXILIARES
# ============================================================================

def _buscar_ultimo_codigo_usado(db: Session, tipo: TipoCodigo, restaurante_id: int) -> Optional[int]:
    """
    Busca o ultimo numero de codigo usado para um tipo especifico dentro de um restaurante
    
    IMPORTANTE: A busca é restrita ao restaurante especificado, garantindo que
    cada restaurante tenha sua própria sequência independente de códigos.
    
    Args:
        db: Sessao do banco de dados
        tipo: Tipo de codigo
        restaurante_id: ID do restaurante
        
    Returns:
        Ultimo numero usado ou None se nao existir nenhum
    """
    faixa = obter_faixa(tipo)
    inicio = faixa["inicio"]
    fim = faixa["fim"]
    
    try:
        # Determinar qual tabela consultar e adicionar filtro de restaurante
        if tipo == TipoCodigo.RECEITA_NORMAL:
            # Buscar em receitas normais (processada = False) do restaurante específico
            query = db.query(Receita).filter(
                Receita.restaurante_id == restaurante_id,
                Receita.processada == False,
                Receita.codigo.isnot(None)
            )
            
        elif tipo == TipoCodigo.RECEITA_PROCESSADA:
            # Buscar em receitas processadas (processada = True) do restaurante específico
            query = db.query(Receita).filter(
                Receita.restaurante_id == restaurante_id,
                Receita.processada == True,
                Receita.codigo.isnot(None)
            )
            
        elif tipo == TipoCodigo.INSUMO:
            # Buscar em insumos do restaurante específico
            # NOTA: Verificar se insumos têm restaurante_id. Se não tiverem, ajustar lógica
            query = db.query(Insumo).filter(
                Insumo.restaurante_id == restaurante_id,
                Insumo.codigo.isnot(None)
            )
        else:
            return None
        
        # Buscar todos os codigos existentes
        registros = query.all()
        
        # Extrair numeros dos codigos que estao na faixa
        numeros_validos = []
        for registro in registros:
            try:
                codigo_str = str(registro.codigo).strip()
                
                # Tentar extrair número do código
                # Aceita formatos: "5000", "INS-5000", "5000-EXTRA"
                if "-" in codigo_str:
                    # Formato com hífen: pegar a parte numérica
                    partes = codigo_str.split("-")
                    # Tentar cada parte para ver qual é número
                    for parte in partes:
                        try:
                            numero = int(parte.strip())
                            if inicio <= numero <= fim:
                                numeros_validos.append(numero)
                                break  # Encontrou o número, sair do loop
                        except ValueError:
                            continue
                else:
                    # Formato sem hífen: código direto (ex: "5000")
                    numero = int(codigo_str)
                    if inicio <= numero <= fim:
                        numeros_validos.append(numero)
                        
            except (ValueError, AttributeError, IndexError):
                # Ignorar codigos com formato invalido
                continue
        
        # Retornar o maior numero encontrado
        if numeros_validos:
            return max(numeros_validos)
        
        return None
        
    except Exception as e:
        logger.error(
            f"Erro ao buscar ultimo codigo (tipo: {tipo}, restaurante: {restaurante_id}): {str(e)}"
        )
        return None

def verificar_codigo_disponivel(db: Session, codigo: str, tipo: TipoCodigo, restaurante_id: int) -> bool:
    """
    Verifica se um codigo especifico esta disponivel dentro de um restaurante
    
    IMPORTANTE: A verificação é feita apenas dentro do contexto do restaurante.
    O mesmo código pode estar em uso em outro restaurante sem conflito.
    
    Args:
        db: Sessao do banco de dados
        codigo: Codigo a verificar
        tipo: Tipo de codigo
        restaurante_id: ID do restaurante
        
    Returns:
        True se disponivel no restaurante, False se ja existe
    """
    try:
        # Validar formato do codigo
        if not validar_codigo_na_faixa(codigo, tipo):
            return False
        
        # Verificar se ja existe no banco para este restaurante especifico
        if tipo in [TipoCodigo.RECEITA_NORMAL, TipoCodigo.RECEITA_PROCESSADA]:
            existe = db.query(Receita).filter(
                Receita.codigo == codigo,
                Receita.restaurante_id == restaurante_id
            ).first()
        elif tipo == TipoCodigo.INSUMO:
            existe = db.query(Insumo).filter(
                Insumo.codigo == codigo,
                Insumo.restaurante_id == restaurante_id
            ).first()
        else:
            return False
        
        return existe is None
        
    except Exception as e:
        logger.error(
            f"Erro ao verificar disponibilidade do codigo (restaurante: {restaurante_id}): {str(e)}"
        )
        return False

def obter_estatisticas_codigos(db: Session, tipo: TipoCodigo, restaurante_id: int) -> dict:
    """
    Retorna estatisticas de uso da faixa de codigos para um restaurante especifico
    
    IMPORTANTE: As estatísticas são calculadas apenas para o restaurante informado.
    Cada restaurante tem sua própria sequência e estatísticas independentes.
    
    Args:
        db: Sessao do banco de dados
        tipo: Tipo de codigo
        restaurante_id: ID do restaurante
        
    Returns:
        Dicionario com estatisticas (usados, disponiveis, percentual, restaurante)
    """
    try:
        # Validar restaurante_id
        if not restaurante_id or restaurante_id <= 0:
            raise ValueError("restaurante_id é obrigatório e deve ser maior que zero")
        
        faixa = obter_faixa(tipo)
        total_faixa = faixa["fim"] - faixa["inicio"] + 1
        
        # Contar codigos usados para este restaurante
        ultimo_numero = _buscar_ultimo_codigo_usado(db, tipo, restaurante_id)
        
        if ultimo_numero is None:
            codigos_usados = 0
        else:
            codigos_usados = ultimo_numero - faixa["inicio"] + 1
        
        codigos_disponiveis = total_faixa - codigos_usados
        percentual_uso = (codigos_usados / total_faixa) * 100
        
        return {
            "restaurante_id": restaurante_id,
            "tipo": tipo,
            "descricao": faixa["descricao"],
            "inicio": faixa["inicio"],
            "fim": faixa["fim"],
            "total": total_faixa,
            "usados": codigos_usados,
            "disponiveis": codigos_disponiveis,
            "percentual_uso": round(percentual_uso, 2),
            "proximo_codigo": formatar_codigo(
                ultimo_numero + 1 if ultimo_numero else faixa["inicio"], 
                tipo
            )
        }
        
    except Exception as e:
        logger.error(
            f"Erro ao obter estatisticas (tipo: {tipo}, restaurante: {restaurante_id}): {str(e)}"
        )
        raise