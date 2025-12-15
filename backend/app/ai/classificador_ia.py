# ============================================================================
# SISTEMA DE IA LOCAL GRATUITA - CLASSIFICADOR DE INSUMOS INTEGRADO
# ============================================================================
# Descrição: Core da IA integrada ao sistema existente de taxonomias
# Tecnologias: spaCy, fuzzywuzzy, re, json (100% gratuito)
# Sistema de aprendizado com feedback do usuário
# Data: 10/09/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

import json
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
import unicodedata

# Bibliotecas gratuitas para NLP
try:
    import spacy
    from spacy.lang.pt import Portuguese
except ImportError:
    spacy = None
    Portuguese = None

try:
    from fuzzywuzzy import fuzz, process
except ImportError:
    fuzz = None
    process = None

from collections import Counter
from sqlalchemy.orm import Session

# Imports do projeto
from app.crud import taxonomia as crud_taxonomia

# ============================================================================
# CONFIGURAÇÕES E CONSTANTES
# ============================================================================

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Caminhos dos arquivos de dados
PADROES_APRENDIDOS_PATH = Path("backend/app/ai/data/padroes_aprendidos.json")
LOGS_FEEDBACK_PATH = Path("backend/app/ai/data/logs_feedback.json")

# Criar diretórios se não existirem
PADROES_APRENDIDOS_PATH.parent.mkdir(parents=True, exist_ok=True)

# ============================================================================
# CLASSE PRINCIPAL DO CLASSIFICADOR IA INTEGRADO
# ============================================================================

class ClassificadorIA:
    """
    Sistema de IA local gratuita para classificação automática de insumos.
    INTEGRADO ao sistema existente de taxonomias e aliases.
    
    Funcionalidades:
    - Análise NLP de nomes de produtos
    - Integração com sistema de taxonomias existente
    - Sistema de scoring e confiança
    - Aprendizado contínuo com feedback
    - Complementa mapeamento inteligente existente
    
    Tecnologias utilizadas:
    - spaCy: processamento de linguagem natural
    - fuzzywuzzy: similaridade entre strings
    - Sistema de taxonomias existente
    - Sistema de aliases existente
    """
    
    def __init__(self, db_session: Session = None):
        """
        Inicializa o classificador IA integrado ao sistema existente.
        
        Args:
            db_session: Sessão do banco para acessar taxonomias
        """
        self.db_session = db_session
        self.nlp = None
        self.padroes_aprendidos = {}
        
        # Inicializar componentes
        self._inicializar_nlp()
        self._carregar_padroes_aprendidos()
        
        # Importar CRUDs do sistema existente (com fallback)
        self.crud_taxonomia = crud_taxonomia
        self.crud_alias = None
        self.mapeamento_inteligente = None
        
        try:
            from app.crud import taxonomia_alias as crud_alias
            self.crud_alias = crud_alias
        except ImportError:
            logger.warning("Módulo taxonomia_alias não encontrado")
        
        try:
            from app.utils import mapeamento_inteligente
            self.mapeamento_inteligente = mapeamento_inteligente
        except ImportError:
            logger.warning("Módulo mapeamento_inteligente não encontrado")
        
        logger.info("ClassificadorIA inicializado com sucesso")
    
    def _inicializar_nlp(self) -> None:
        """
        Inicializa processador de linguagem natural.
        
        Tenta carregar modelo português do spaCy, 
        senão usa processamento básico.
        """
        try:
            if spacy:
                # Tentar carregar modelo português
                try:
                    self.nlp = spacy.load("pt_core_news_sm")
                    logger.info("Modelo spaCy português carregado")
                except OSError:
                    # Modelo não instalado, usar processador básico
                    self.nlp = Portuguese()
                    logger.warning("Modelo pt_core_news_sm não encontrado, usando processador básico")
            else:
                logger.warning("spaCy não instalado, usando processamento básico de texto")
        except Exception as e:
            logger.error(f"Erro ao inicializar NLP: {e}")
            self.nlp = None
    
    def _carregar_padroes_aprendidos(self) -> None:
        """
        Carrega padrões aprendidos do arquivo JSON.
        
        Padrões incluem: sufixos de unidade, prefixos de marca,
        palavras de estado, termos regionais, etc.
        """
        try:
            if PADROES_APRENDIDOS_PATH.exists():
                with open(PADROES_APRENDIDOS_PATH, 'r', encoding='utf-8') as file:
                    self.padroes_aprendidos = json.load(file)
                logger.info("Padrões aprendidos carregados")
            else:
                # Criar padrões iniciais
                self.padroes_aprendidos = self._criar_padroes_iniciais()
                self._salvar_padroes_aprendidos()
                logger.info("Padrões iniciais criados")
        except Exception as e:
            logger.error(f"Erro ao carregar padrões aprendidos: {e}")
            self.padroes_aprendidos = self._criar_padroes_iniciais()
    
    def _criar_padroes_iniciais(self) -> Dict:
        """
        Cria padrões iniciais aprendidos pelo sistema.
        
        Returns:
            Dict: Padrões organizados por categoria
        """
        return {
            "sufixos_unidade": ["kg", "g", "l", "ml", "cx", "un", "und", "lata", "pct"],
            "prefixos_marca": ["seara", "sadia", "perdigao", "aurora", "tio", "uncle"],
            "palavras_estado": ["fresco", "fresh", "congelado", "frozen", "seco", "dry"],
            "termos_qualidade": ["premium", "select", "extra", "especial", "gourmet"],
            "termos_origem": ["atlantico", "pacifico", "brasileiro", "nacional", "importado"],
            "palavras_ignorar": ["de", "da", "do", "com", "para", "em", "no", "na"],
            "sinonimos_regionais": {
                "macaxeira": "mandioca",
                "aipim": "mandioca", 
                "jerimum": "abobora",
                "chuchu": "chuchu"
            }
        }
    
    def _salvar_padroes_aprendidos(self) -> None:
        """Salva padrões aprendidos no arquivo JSON."""
        try:
            with open(PADROES_APRENDIDOS_PATH, 'w', encoding='utf-8') as file:
                json.dump(self.padroes_aprendidos, file, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar padrões aprendidos: {e}")
    
    def normalizar_texto(self, texto: str) -> str:
        """
        Normaliza texto removendo acentos, caracteres especiais e convertendo para minúsculas.
        
        Args:
            texto (str): Texto original
            
        Returns:
            str: Texto normalizado
        """
        if not texto:
            return ""
        
        # Converter para minúsculas
        texto = texto.lower()
        
        # Remover acentos
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(char for char in texto if unicodedata.category(char) != 'Mn')
        
        # Remover caracteres especiais e números (exceto espaços e hífens)
        texto = re.sub(r'[^\w\s\-]', ' ', texto)
        
        # Normalizar espaços múltiplos
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        return texto
    
    def extrair_tokens(self, nome_produto: str) -> List[str]:
        """
        Extrai tokens (palavras) relevantes do nome do produto.
        
        Args:
            nome_produto (str): Nome do produto a ser analisado
            
        Returns:
            List[str]: Lista de tokens extraídos
        """
        texto_normalizado = self.normalizar_texto(nome_produto)
        
        if self.nlp:
            # Usar spaCy para tokenização avançada
            doc = self.nlp(texto_normalizado)
            tokens = [token.lemma_ for token in doc if not token.is_stop and len(token.text) > 2]
        else:
            # Tokenização básica
            tokens = texto_normalizado.split()
        
        # Remover palavras irrelevantes usando padrões aprendidos
        palavras_ignorar = self.padroes_aprendidos.get("palavras_ignorar", [])
        tokens_filtrados = [token for token in tokens if token not in palavras_ignorar]
        
        # Remover sufixos de unidade
        sufixos_unidade = self.padroes_aprendidos.get("sufixos_unidade", [])
        tokens_sem_unidade = [token for token in tokens_filtrados if token not in sufixos_unidade]
        
        return tokens_sem_unidade
    
    def calcular_similaridade(self, texto1: str, texto2: str) -> float:
        """
        Calcula similaridade entre dois textos usando fuzzywuzzy.
        
        Args:
            texto1 (str): Primeiro texto
            texto2 (str): Segundo texto
            
        Returns:
            float: Score de similaridade (0.0 a 1.0)
        """
        if not fuzz:
            # Fallback simples se fuzzywuzzy não estiver disponível
            return 1.0 if texto1.lower() == texto2.lower() else 0.0
        
        # Normalizar ambos os textos
        texto1_norm = self.normalizar_texto(texto1)
        texto2_norm = self.normalizar_texto(texto2)
        
        # Usar diferentes algoritmos do fuzzywuzzy e pegar a melhor pontuação
        ratio = fuzz.ratio(texto1_norm, texto2_norm)
        partial_ratio = fuzz.partial_ratio(texto1_norm, texto2_norm)
        token_sort = fuzz.token_sort_ratio(texto1_norm, texto2_norm)
        token_set = fuzz.token_set_ratio(texto1_norm, texto2_norm)
        
        # Retornar a melhor pontuação convertida para 0.0-1.0
        melhor_score = max(ratio, partial_ratio, token_sort, token_set)
        return melhor_score / 100.0
    
    def _analisar_nlp_complementar(self, nome_produto: str) -> List[Dict]:
        """
        Análise NLP complementar quando sistema existente não encontra correspondência.
        
        Args:
            nome_produto: Nome do produto para análise
            
        Returns:
            Lista de candidatos baseados em análise NLP
        """
        candidatos = []
        tokens = self.extrair_tokens(nome_produto)
        
        if len(tokens) < 1:
            return candidatos
        
        # Padrões básicos baseados em palavras-chave conhecidas
        padroes_categorias = {
            'carnes': ['alcatra', 'bife', 'lombo', 'frango', 'peito', 'carne'],
            'peixes': ['salmao', 'salmão', 'tilapia', 'peixe', 'file'],
            'verduras': ['tomate', 'cebola', 'alface', 'verdura'],
            'laticinios': ['leite', 'queijo', 'iogurte', 'manteiga'],
            'temperos': ['sal', 'pimenta', 'oregano', 'tempero'],
            'oleos': ['oleo', 'óleo', 'azeite']
        }
        
        for categoria, palavras_chave in padroes_categorias.items():
            for token in tokens:
                for palavra in palavras_chave:
                    similaridade = self.calcular_similaridade(token, palavra)
                    if similaridade > 0.7:
                        candidatos.append({
                            "tipo": "nlp_analise",
                            "categoria_sugerida": categoria.title(),
                            "score": similaridade * 0.6,  # Score reduzido para priorizar sistema existente
                            "fonte": "analise_nlp",
                            "palavra_encontrada": palavra
                        })
        
        return candidatos
    
    def _remover_duplicatas_taxonomias(self, candidatos: List[Dict]) -> List[Dict]:
        """Remove candidatos duplicados baseados na taxonomia."""
        candidatos_unicos = []
        taxonomias_vistas = set()
        
        for candidato in candidatos:
            # Identificador único da taxonomia
            if candidato.get("taxonomia"):
                taxonomia = candidato["taxonomia"]
                identificador = f"{taxonomia.categoria}_{taxonomia.subcategoria}_{taxonomia.especificacao}"
            elif candidato.get("taxonomia_data"):
                data = candidato["taxonomia_data"]
                identificador = f"{data.get('categoria', '')}_{data.get('subcategoria', '')}_{data.get('especificacao', '')}"
            else:
                identificador = candidato.get("categoria_sugerida", str(len(candidatos_unicos)))
            
            if identificador not in taxonomias_vistas:
                taxonomias_vistas.add(identificador)
                candidatos_unicos.append(candidato)
        
        return candidatos_unicos
    
    def buscar_taxonomias_existentes(self, nome_produto: str) -> List[Dict]:
        """
        Busca correspondências no sistema de taxonomias e aliases existente.
        
        Args:
            nome_produto (str): Nome do produto a ser classificado
            
        Returns:
            List[Dict]: Lista de possíveis classificações com score
        """
        if not self.db_session:
            return []
        
        candidatos = []
        
        # 1. Buscar no sistema de aliases existente (se disponível)
        if self.crud_alias:
            try:
                # Tentar diferentes métodos de busca de aliases
                if hasattr(self.crud_alias, 'buscar_aliases_por_termo'):
                    aliases_encontrados = self.crud_alias.buscar_aliases_por_termo(
                        db=self.db_session, 
                        termo=nome_produto, 
                        limite=5
                    )
                elif hasattr(self.crud_alias, 'buscar_por_termo'):
                    aliases_encontrados = self.crud_alias.buscar_por_termo(
                        db=self.db_session, 
                        termo=nome_produto
                    )
                else:
                    aliases_encontrados = []
                
                for alias_match in aliases_encontrados:
                    if hasattr(alias_match, 'taxonomia') and alias_match.taxonomia:
                        candidatos.append({
                            "tipo": "alias_existente",
                            "taxonomia": alias_match.taxonomia,
                            "score": getattr(alias_match, 'confianca', 80) / 100.0,
                            "fonte": "sistema_aliases"
                        })
            except Exception as e:
                logger.warning(f"Erro ao buscar aliases: {e}")
        
        # 2. Usar mapeamento inteligente existente (se disponível)
        if self.mapeamento_inteligente:
            try:
                if hasattr(self.mapeamento_inteligente, 'sugerir_taxonomias_inteligente'):
                    sugestoes_mapeamento = self.mapeamento_inteligente.sugerir_taxonomias_inteligente(
                        db=self.db_session,
                        nome_insumo=nome_produto,
                        limite=3
                    )
                elif hasattr(self.mapeamento_inteligente, 'mapear_produto_para_taxonomia'):
                    resultado = self.mapeamento_inteligente.mapear_produto_para_taxonomia(
                        db=self.db_session,
                        nome_insumo=nome_produto
                    )
                    sugestoes_mapeamento = [resultado] if resultado else []
                else:
                    sugestoes_mapeamento = []
                
                for sugestao in sugestoes_mapeamento:
                    if sugestao:
                        candidatos.append({
                            "tipo": "mapeamento_inteligente",
                            "taxonomia_data": sugestao,
                            "score": sugestao.get('score', 0.7) if isinstance(sugestao, dict) else 0.7,
                            "fonte": "mapeamento_existente"
                        })
            except Exception as e:
                logger.warning(f"Erro no mapeamento inteligente: {e}")
        
        # 3. Complementar com análise NLP própria
        candidatos_nlp = self._analisar_nlp_complementar(nome_produto)
        candidatos.extend(candidatos_nlp)
        
        # Ordenar por score e remover duplicatas
        candidatos_unicos = self._remover_duplicatas_taxonomias(candidatos)
        candidatos_unicos.sort(key=lambda x: x["score"], reverse=True)
        
        return candidatos_unicos[:5]
    
    def classificar_produto(self, nome_produto: str) -> Dict[str, Any]:
        """
        Classifica um produto usando sistema integrado (aliases + mapeamento + IA).
        """
        if not nome_produto or not nome_produto.strip():
            return {
                "sucesso": False,
                "erro": "Nome do produto não pode estar vazio",
                "confianca": 0.0
            }
        
        try:
            # Buscar usando sistema integrado
            candidatos = self.buscar_taxonomias_existentes(nome_produto)
            
            if not candidatos:
                return {
                    "sucesso": False,
                    "motivo": "Nenhuma correspondência encontrada no sistema",
                    "termo_analisado": nome_produto,
                    "tokens_extraidos": self.extrair_tokens(nome_produto),
                    "confianca": 0.0,
                    "requer_aprendizado": True,
                    "sugestao_acao": "Considere adicionar manualmente ao sistema de taxonomias"
                }
            
            # Processar melhor candidato
            melhor_candidato = candidatos[0]
            
            # Converter resultado baseado na fonte
            if melhor_candidato["tipo"] == "alias_existente":
                taxonomia = melhor_candidato["taxonomia"]
                return {
                    "sucesso": True,
                    "categoria": taxonomia.categoria,
                    "subcategoria": taxonomia.subcategoria,
                    "especificacao": taxonomia.especificacao,
                    "variante": taxonomia.variante,
                    "taxonomia_id": taxonomia.id,
                    "codigo_taxonomia": taxonomia.codigo_taxonomia,
                    "confianca": melhor_candidato["score"],
                    "fonte": "sistema_aliases",
                    "termo_analisado": nome_produto,
                    "detalhes_match": {
                        "tipo": "alias",
                        "fonte": "sistema_existente"
                    },
                    "alternativas": self._formatar_alternativas(candidatos[1:3]),
                    "requer_revisao": melhor_candidato["score"] < 0.8
                }
                
            elif melhor_candidato["tipo"] == "mapeamento_inteligente":
                data = melhor_candidato["taxonomia_data"]
                return {
                    "sucesso": True,
                    "categoria": data.get("categoria"),
                    "subcategoria": data.get("subcategoria"),
                    "especificacao": data.get("especificacao"),
                    "variante": data.get("variante"),
                    "taxonomia_id": data.get("taxonomia_id"),
                    "codigo_taxonomia": data.get("codigo_taxonomia"),
                    "confianca": melhor_candidato["score"],
                    "fonte": "mapeamento_inteligente",
                    "termo_analisado": nome_produto,
                    "detalhes_match": {
                        "tipo": "mapeamento",
                        "palavras_encontradas": data.get("palavras_encontradas", [])
                    },
                    "alternativas": self._formatar_alternativas(candidatos[1:3]),
                    "requer_revisao": melhor_candidato["score"] < 0.7
                }
                
            else:  # Análise NLP complementar
                return {
                    "sucesso": True,
                    "categoria": melhor_candidato.get("categoria_sugerida"),
                    "subcategoria": "A definir",  # NLP não define subcategoria
                    "especificacao": None,
                    "variante": None,
                    "confianca": melhor_candidato["score"],
                    "fonte": "analise_nlp",
                    "termo_analisado": nome_produto,
                    "detalhes_match": {
                        "tipo": "nlp",
                        "palavra_encontrada": melhor_candidato.get("palavra_encontrada")
                    },
                    "alternativas": [],
                    "requer_revisao": True,  # NLP sempre requer revisão
                    "sugestao_acao": "Revise e complete a classificação manualmente"
                }
                
        except Exception as e:
            logger.error(f"Erro na classificação: {e}")
            return {
                "sucesso": False,
                "erro": f"Erro interno: {str(e)}",
                "confianca": 0.0
            }
    
    def _formatar_alternativas(self, candidatos: List[Dict]) -> List[Dict]:
        """Formata candidatos alternativos para resposta."""
        alternativas = []
        
        for candidato in candidatos:
            if candidato["tipo"] == "alias_existente":
                taxonomia = candidato["taxonomia"]
                alternativas.append({
                    "categoria": taxonomia.categoria,
                    "subcategoria": taxonomia.subcategoria,
                    "especificacao": taxonomia.especificacao,
                    "variante": taxonomia.variante,
                    "confianca": candidato["score"]
                })
            elif candidato["tipo"] == "mapeamento_inteligente":
                data = candidato["taxonomia_data"]
                alternativas.append({
                    "categoria": data.get("categoria"),
                    "subcategoria": data.get("subcategoria"),
                    "especificacao": data.get("especificacao"),
                    "variante": data.get("variante"),
                    "confianca": candidato["score"]
                })
        
        return alternativas
    
    def registrar_feedback(self, nome_produto: str, classificacao_sugerida: Dict, 
                          acao: str, taxonomia_correta: Dict = None) -> bool:
        """
        Registra feedback do usuário integrando com sistema existente.
        """
        try:
            if not self.db_session:
                return False
            
            if acao == "aceitar":
                return self._processar_feedback_positivo_integrado(nome_produto, classificacao_sugerida)
            elif acao == "corrigir":
                return self._processar_correcao_integrada(nome_produto, classificacao_sugerida, taxonomia_correta)
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao registrar feedback: {e}")
            return False
    
    def _processar_feedback_positivo_integrado(self, nome_produto: str, classificacao: Dict) -> bool:
        """Processa feedback positivo usando sistema de aliases existente."""
        try:
            # Buscar taxonomia no banco
            taxonomia = self._buscar_taxonomia_por_classificacao(classificacao)
            if not taxonomia:
                return False
            
            # Se crud_alias disponível, criar/atualizar alias
            if self.crud_alias:
                # Verificar se alias já existe
                alias_existente = None
                if hasattr(self.crud_alias, 'buscar_alias_por_nome'):
                    alias_existente = self.crud_alias.buscar_alias_por_nome(
                        db=self.db_session,
                        nome_alternativo=nome_produto
                    )
                
                if not alias_existente:
                    # Criar novo alias usando sistema existente
                    try:
                        from app.schemas.taxonomia_alias import TaxonomiaAliasCreate
                        
                        novo_alias = TaxonomiaAliasCreate(
                            nome_alternativo=nome_produto,
                            taxonomia_id=taxonomia.id,
                            tipo="sinonimo",
                            origem="ia",
                            confianca=80,
                            ativo=True
                        )
                        
                        self.crud_alias.create_alias(db=self.db_session, alias=novo_alias)
                        logger.info(f"Novo alias criado via IA: '{nome_produto}' -> {taxonomia.nome_completo}")
                    except Exception as e:
                        logger.warning(f"Erro ao criar alias: {e}")
                else:
                    # Incrementar confiança do alias existente
                    if hasattr(self.crud_alias, 'incrementar_confirmacao'):
                        self.crud_alias.incrementar_confirmacao(db=self.db_session, alias_id=alias_existente.id)
            
            # Salvar log de feedback
            self._salvar_log_feedback({
                "timestamp": datetime.now().isoformat(),
                "nome_produto": nome_produto,
                "acao": "aceitar",
                "classificacao": classificacao,
                "resultado": "alias_criado_ou_confirmado"
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Erro no feedback positivo: {e}")
            return False
    
    def _processar_correcao_integrada(self, nome_produto: str, classificacao_errada: Dict, 
                                     taxonomia_correta: Dict) -> bool:
        """Processa correção usando sistema de taxonomias existente."""
        try:
            # Buscar ou criar taxonomia correta
            taxonomia = self._buscar_ou_criar_taxonomia(taxonomia_correta)
            if not taxonomia:
                return False
            
            # Criar alias para a taxonomia correta (se crud_alias disponível)
            if self.crud_alias:
                try:
                    from app.schemas.taxonomia_alias import TaxonomiaAliasCreate
                    
                    alias_correto = TaxonomiaAliasCreate(
                        nome_alternativo=nome_produto,
                        taxonomia_id=taxonomia.id,
                        tipo="sinonimo",
                        origem="ia",
                        confianca=70,  # Confiança inicial moderada
                        ativo=True
                    )
                    
                    self.crud_alias.create_alias(db=self.db_session, alias=alias_correto)
                    logger.info(f"Correção aplicada via IA: '{nome_produto}' -> {taxonomia.nome_completo}")
                except Exception as e:
                    logger.warning(f"Erro ao criar alias de correção: {e}")
            
            # Salvar log de feedback
            self._salvar_log_feedback({
                "timestamp": datetime.now().isoformat(),
                "nome_produto": nome_produto,
                "acao": "corrigir",
                "classificacao_errada": classificacao_errada,
                "taxonomia_correta": taxonomia_correta,
                "resultado": "correcao_aplicada"
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Erro na correção: {e}")
            return False
    
    def _buscar_taxonomia_por_classificacao(self, classificacao: Dict):
        """Busca taxonomia no banco baseada na classificação sugerida."""
        if not self.db_session:
            return None
        
        try:
            if hasattr(self.crud_taxonomia, 'get_taxonomia_by_hierarquia'):
                return self.crud_taxonomia.get_taxonomia_by_hierarquia(
                    db=self.db_session,
                    categoria=classificacao.get("categoria"),
                    subcategoria=classificacao.get("subcategoria"),
                    especificacao=classificacao.get("especificacao"),
                    variante=classificacao.get("variante")
                )
            else:
                # Busca alternativa
                return self.crud_taxonomia.get_taxonomia_by_id(
                    db=self.db_session,
                    taxonomia_id=classificacao.get("taxonomia_id")
                )
        except Exception as e:
            logger.error(f"Erro ao buscar taxonomia: {e}")
            return None
    
    def _buscar_ou_criar_taxonomia(self, taxonomia_data: Dict):
        """Busca taxonomia existente ou cria nova se não existir."""
        if not self.db_session:
            return None
        
        try:
            # Primeiro tentar buscar existente
            taxonomia = self._buscar_taxonomia_por_classificacao(taxonomia_data)
            
            if taxonomia:
                return taxonomia
            
            # Criar nova taxonomia se não existir
            try:
                from app.schemas.taxonomia import TaxonomiaCreate
                
                nova_taxonomia = TaxonomiaCreate(
                    categoria=taxonomia_data["categoria"],
                    subcategoria=taxonomia_data["subcategoria"],
                    especificacao=taxonomia_data.get("especificacao"),
                    variante=taxonomia_data.get("variante"),
                    descricao=f"Criada automaticamente via IA para produto: {taxonomia_data.get('produto_origem', 'N/A')}",
                    ativo=True
                )
                
                return self.crud_taxonomia.create_taxonomia(db=self.db_session, taxonomia=nova_taxonomia)
            except Exception as e:
                logger.warning(f"Erro ao criar nova taxonomia: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar/criar taxonomia: {e}")
            return None
    
    def _salvar_log_feedback(self, feedback_log: Dict) -> None:
        """Salva log de feedback para auditoria."""
        try:
            logs = []
            if LOGS_FEEDBACK_PATH.exists():
                with open(LOGS_FEEDBACK_PATH, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    logs = data.get("logs", []) if isinstance(data, dict) else data
            
            logs.append(feedback_log)
            
            # Manter apenas últimos 1000 logs
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            # Salvar logs com estrutura atualizada
            logs_data = {
                "versao": "2.0.0",
                "created_at": datetime.now().isoformat(),
                "descricao": "Logs de feedback do sistema de IA integrado",
                "logs": logs
            }
            
            with open(LOGS_FEEDBACK_PATH, 'w', encoding='utf-8') as file:
                json.dump(logs_data, file, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Erro ao salvar log de feedback: {e}")
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do sistema de IA integrado.
        
        Returns:
            Dict: Estatísticas do sistema
        """
        try:
            # Estatísticas do sistema integrado
            stats = {
                "versao_sistema": "2.0.0",
                "tipo": "integrado",
                "spacy_disponivel": self.nlp is not None,
                "fuzzywuzzy_disponivel": fuzz is not None,
                "crud_alias_disponivel": self.crud_alias is not None,
                "mapeamento_inteligente_disponivel": self.mapeamento_inteligente is not None
            }
            
            # Estatísticas de logs se disponível
            try:
                if LOGS_FEEDBACK_PATH.exists():
                    with open(LOGS_FEEDBACK_PATH, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        logs = data.get("logs", []) if isinstance(data, dict) else data
                        
                        total_feedbacks = len(logs)
                        total_confirmacoes = sum(1 for log in logs if log.get("acao") == "aceitar")
                        total_correcoes = sum(1 for log in logs if log.get("acao") == "corrigir")
                        
                        if total_feedbacks > 0:
                            taxa_acerto = total_confirmacoes / total_feedbacks
                        else:
                            taxa_acerto = 0.0
                        
                        stats.update({
                            "total_feedbacks": total_feedbacks,
                            "total_confirmacoes": total_confirmacoes,
                            "total_correcoes": total_correcoes,
                            "taxa_acerto": round(taxa_acerto, 3)
                        })
                else:
                    stats.update({
                        "total_feedbacks": 0,
                        "total_confirmacoes": 0,
                        "total_correcoes": 0,
                        "taxa_acerto": 0.0
                    })
            except Exception as e:
                logger.warning(f"Erro ao carregar estatísticas de logs: {e}")
                stats.update({
                    "erro_logs": str(e),
                    "total_feedbacks": 0,
                    "total_confirmacoes": 0,
                    "total_correcoes": 0,
                    "taxa_acerto": 0.0
                })
            
            # Estatísticas do banco se disponível
            if self.db_session and self.crud_taxonomia:
                try:
                    # Tentar obter estatísticas das taxonomias
                    if hasattr(self.crud_taxonomia, 'get_estatisticas'):
                        stats_banco = self.crud_taxonomia.get_estatisticas(db=self.db_session)
                        stats.update(stats_banco)
                    else:
                        stats["total_taxonomias"] = "N/A"
                except Exception as e:
                    logger.warning(f"Erro ao obter estatísticas do banco: {e}")
                    stats["erro_banco"] = str(e)
            
            stats["ultima_atualizacao"] = datetime.now().isoformat()
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas: {e}")
            return {"erro": str(e)}

def obter_estatisticas_completas(
        self, 
        periodo_inicio: Optional[datetime] = None,
        periodo_fim: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Retorna estatísticas completas para o dashboard.
        
        Calcula todas as métricas necessárias para visualizações,
        filtradas por período de tempo se especificado.
        
        Args:
            periodo_inicio: Data inicial do período (None = sem filtro)
            periodo_fim: Data final do período (None = agora)
            
        Returns:
            Dicionário com todas as estatísticas do dashboard
        """
        try:
            # Definir período padrão se não especificado
            if periodo_fim is None:
                periodo_fim = datetime.now()
            
            if periodo_inicio is None:
                # Padrão: últimos 30 dias
                from datetime import timedelta
                periodo_inicio = periodo_fim - timedelta(days=30)
            
            # Calcular total de dias no período
            total_dias = (periodo_fim - periodo_inicio).days + 1
            
            # Carregar logs de feedback filtrados por período
            logs_periodo = self._carregar_logs_feedback_periodo(periodo_inicio, periodo_fim)
            
            # Calcular métricas principais
            total_classificacoes = len(logs_periodo)
            total_confirmacoes = len([log for log in logs_periodo if log.get('tipo_feedback') == 'confirmacao'])
            total_correcoes = len([log for log in logs_periodo if log.get('tipo_feedback') == 'correcao'])
            
            # Taxa de acerto
            taxa_acerto = (total_confirmacoes / total_classificacoes * 100) if total_classificacoes > 0 else 0.0
            
            # Tempo médio de classificação
            tempos = [log.get('tempo_processamento_ms', 0) for log in logs_periodo if log.get('tempo_processamento_ms')]
            tempo_medio = sum(tempos) / len(tempos) if tempos else 0.0
            
            # Classificações por dia
            classificacoes_por_dia = total_classificacoes / total_dias if total_dias > 0 else 0.0
            
            # Agrupar classificações por data
            classificacoes_por_data = self._agrupar_por_data(logs_periodo)
            
            # Calcular taxa de acerto por data
            taxa_acerto_por_data = self._calcular_taxa_acerto_por_data(logs_periodo)
            
            # Top 10 categorias
            top_categorias = self._calcular_top_categorias(logs_periodo, limite=10)
            
            # Distribuição por tipo (automático vs manual)
            distribuicao_tipo = {
                'automatica': total_confirmacoes,
                'manual': total_correcoes
            }
            
            # Preparar dados para gráficos
            grafico_evolucao = self._preparar_grafico_evolucao(classificacoes_por_data)
            grafico_pizza = self._preparar_grafico_pizza(distribuicao_tipo)
            grafico_barras = self._preparar_grafico_barras(top_categorias)
            grafico_taxa_acerto = self._preparar_grafico_taxa_acerto(taxa_acerto_por_data)
            
            # Preparar tabela de categorias
            tabela_categorias = self._preparar_tabela_categorias(logs_periodo)
            
            # Cards principais (KPIs)
            cards_principais = {
                'taxa_acerto': {
                    'valor': round(taxa_acerto, 1),
                    'unidade': '%',
                    'label': 'Taxa de Acerto',
                    'variacao': self._calcular_variacao_periodo_anterior(taxa_acerto, periodo_inicio)
                },
                'total_classificacoes': {
                    'valor': total_classificacoes,
                    'unidade': '',
                    'label': 'Classificações Automáticas',
                    'variacao': None
                },
                'total_correcoes': {
                    'valor': total_correcoes,
                    'unidade': '',
                    'label': 'Correções Manuais',
                    'variacao': None
                },
                'tempo_medio': {
                    'valor': round(tempo_medio, 0),
                    'unidade': 'ms',
                    'label': 'Tempo Médio de Classificação',
                    'variacao': None
                }
            }
            
            # Montar resposta completa
            return {
                'cards_principais': cards_principais,
                'estatisticas_periodo': {
                    'periodo_inicio': periodo_inicio.isoformat(),
                    'periodo_fim': periodo_fim.isoformat(),
                    'total_dias': total_dias,
                    'total_classificacoes': total_classificacoes,
                    'total_confirmacoes': total_confirmacoes,
                    'total_correcoes': total_correcoes,
                    'taxa_acerto_percentual': round(taxa_acerto, 2),
                    'tempo_medio_classificacao_ms': round(tempo_medio, 2),
                    'classificacoes_por_dia': round(classificacoes_por_dia, 2),
                    'classificacoes_por_data': classificacoes_por_data,
                    'taxa_acerto_por_data': taxa_acerto_por_data,
                    'top_10_categorias': top_categorias,
                    'distribuicao_tipo': distribuicao_tipo
                },
                'grafico_evolucao_temporal': grafico_evolucao,
                'grafico_distribuicao_tipo': grafico_pizza,
                'grafico_top_categorias': grafico_barras,
                'grafico_taxa_acerto_temporal': grafico_taxa_acerto,
                'tabela_categorias': tabela_categorias,
                'data_geracao': datetime.now().isoformat(),
                'filtros_aplicados': {
                    'periodo_inicio': periodo_inicio.isoformat(),
                    'periodo_fim': periodo_fim.isoformat(),
                    'total_dias': total_dias
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas completas: {e}")
            return self._estatisticas_vazias()
    
def _carregar_logs_feedback_periodo(
    self, 
    periodo_inicio: datetime, 
    periodo_fim: datetime
) -> List[Dict]:
    """
    Carrega logs de feedback filtrados por período.
    
    Args:
        periodo_inicio: Data inicial
        periodo_fim: Data final
        
    Returns:
        Lista de logs no período especificado
    """
    try:
        if not LOGS_FEEDBACK_PATH.exists():
            return []
        
        with open(LOGS_FEEDBACK_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
            logs = data.get("logs", []) if isinstance(data, dict) else data
        
        # Filtrar por período
        logs_filtrados = []
        for log in logs:
            timestamp_str = log.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if periodo_inicio <= timestamp <= periodo_fim:
                        logs_filtrados.append(log)
                except (ValueError, AttributeError):
                    continue
        
        return logs_filtrados
        
    except Exception as e:
        logger.error(f"Erro ao carregar logs de feedback: {e}")
        return []

def _agrupar_por_data(self, logs: List[Dict]) -> Dict[str, int]:
    """
    Agrupa logs por data (formato YYYY-MM-DD).
    
    Args:
        logs: Lista de logs
        
    Returns:
        Dicionário com contagem por data
    """
    from collections import defaultdict
    contagem = defaultdict(int)
    
    for log in logs:
        timestamp_str = log.get('timestamp')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                data_str = timestamp.strftime('%Y-%m-%d')
                contagem[data_str] += 1
            except (ValueError, AttributeError):
                continue
    
    return dict(contagem)

def _calcular_taxa_acerto_por_data(self, logs: List[Dict]) -> Dict[str, float]:
    """
    Calcula taxa de acerto agrupada por data.
    
    Args:
        logs: Lista de logs
        
    Returns:
        Dicionário com taxa de acerto por data
    """
    from collections import defaultdict
    
    confirmacoes_por_data = defaultdict(int)
    total_por_data = defaultdict(int)
    
    for log in logs:
        timestamp_str = log.get('timestamp')
        tipo_feedback = log.get('tipo_feedback')
        
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                data_str = timestamp.strftime('%Y-%m-%d')
                total_por_data[data_str] += 1
                
                if tipo_feedback == 'confirmacao':
                    confirmacoes_por_data[data_str] += 1
                    
            except (ValueError, AttributeError):
                continue
    
    # Calcular taxa de acerto por data
    taxa_por_data = {}
    for data in total_por_data:
        total = total_por_data[data]
        confirmacoes = confirmacoes_por_data.get(data, 0)
        taxa_por_data[data] = round((confirmacoes / total * 100), 2) if total > 0 else 0.0
    
    return taxa_por_data

def _calcular_top_categorias(self, logs: List[Dict], limite: int = 10) -> List[Dict[str, Any]]:
    """
    Calcula as categorias mais classificadas.
    
    Args:
        logs: Lista de logs
        limite: Número máximo de categorias a retornar
        
    Returns:
        Lista com top categorias e suas contagens
    """
    from collections import Counter
    
    categorias = []
    for log in logs:
        classificacao = log.get('classificacao_sugerida', {})
        categoria = classificacao.get('categoria')
        if categoria:
            categorias.append(categoria)
    
    contador = Counter(categorias)
    top = contador.most_common(limite)
    
    total = len(categorias)
    resultado = []
    for categoria, quantidade in top:
        percentual = round((quantidade / total * 100), 2) if total > 0 else 0.0
        resultado.append({
            'categoria': categoria,
            'quantidade': quantidade,
            'percentual': percentual
        })
    
    return resultado

def _preparar_grafico_evolucao(self, classificacoes_por_data: Dict[str, int]) -> List[Dict[str, Any]]:
        """
        Prepara dados para gráfico de linha - evolução temporal.
        
        Args:
            classificacoes_por_data: Dicionário com contagem por data
            
        Returns:
            Lista de pontos para o gráfico de linha
        """
        # Ordenar por data
        datas_ordenadas = sorted(classificacoes_por_data.keys())
        
        dados_grafico = []
        for data in datas_ordenadas:
            dados_grafico.append({
                'data': data,
                'quantidade': classificacoes_por_data[data],
                'data_formatada': self._formatar_data_br(data)
            })
        
        return dados_grafico
    
def _preparar_grafico_pizza(self, distribuicao_tipo: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    Prepara dados para gráfico de pizza - distribuição por tipo.
    
    Args:
        distribuicao_tipo: Dicionário com automáticas vs manuais
        
    Returns:
        Lista de segmentos para o gráfico de pizza
    """
    total = sum(distribuicao_tipo.values())
    
    dados_grafico = []
    for tipo, quantidade in distribuicao_tipo.items():
        percentual = round((quantidade / total * 100), 1) if total > 0 else 0.0
        
        # Labels em português
        label = 'Automáticas' if tipo == 'automatica' else 'Manuais'
        cor = '#10b981' if tipo == 'automatica' else '#f59e0b'
        
        dados_grafico.append({
            'tipo': tipo,
            'label': label,
            'quantidade': quantidade,
            'percentual': percentual,
            'cor': cor
        })
    
    return dados_grafico

def _preparar_grafico_barras(self, top_categorias: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prepara dados para gráfico de barras - top categorias.
    
    Args:
        top_categorias: Lista com categorias e quantidades
        
    Returns:
        Lista formatada para gráfico de barras
    """
    # Os dados já estão no formato correto, apenas adicionar cores
    cores = [
        '#10b981', '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b',
        '#14b8a6', '#6366f1', '#a855f7', '#f43f5e', '#06b6d4'
    ]
    
    dados_grafico = []
    for idx, item in enumerate(top_categorias):
        dados_grafico.append({
            'categoria': item['categoria'],
            'quantidade': item['quantidade'],
            'percentual': item['percentual'],
            'cor': cores[idx % len(cores)]
        })
    
    return dados_grafico

def _preparar_grafico_taxa_acerto(self, taxa_acerto_por_data: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Prepara dados para gráfico de linha - taxa de acerto ao longo do tempo.
    
    Args:
        taxa_acerto_por_data: Dicionário com taxa por data
        
    Returns:
        Lista de pontos para o gráfico de linha
    """
    # Ordenar por data
    datas_ordenadas = sorted(taxa_acerto_por_data.keys())
    
    dados_grafico = []
    for data in datas_ordenadas:
        dados_grafico.append({
            'data': data,
            'taxa_acerto': taxa_acerto_por_data[data],
            'data_formatada': self._formatar_data_br(data)
        })
    
    return dados_grafico

def _preparar_tabela_categorias(self, logs: List[Dict]) -> List[Dict[str, Any]]:
    """
    Prepara dados detalhados para tabela de categorias.
    
    Args:
        logs: Lista de logs
        
    Returns:
        Lista com estatísticas detalhadas por categoria
    """
    from collections import defaultdict
    
    # Estruturas para agregação
    categorias_stats = defaultdict(lambda: {
        'total': 0,
        'confirmacoes': 0,
        'correcoes': 0,
        'tempos': []
    })
    
    # Processar logs
    for log in logs:
        classificacao = log.get('classificacao_sugerida', {})
        categoria = classificacao.get('categoria')
        
        if not categoria:
            continue
        
        tipo_feedback = log.get('tipo_feedback')
        tempo = log.get('tempo_processamento_ms', 0)
        
        stats = categorias_stats[categoria]
        stats['total'] += 1
        
        if tipo_feedback == 'confirmacao':
            stats['confirmacoes'] += 1
        elif tipo_feedback == 'correcao':
            stats['correcoes'] += 1
        
        if tempo > 0:
            stats['tempos'].append(tempo)
    
    # Calcular métricas por categoria
    resultado = []
    for categoria, stats in categorias_stats.items():
        total = stats['total']
        confirmacoes = stats['confirmacoes']
        taxa_acerto = round((confirmacoes / total * 100), 1) if total > 0 else 0.0
        tempo_medio = round(sum(stats['tempos']) / len(stats['tempos']), 0) if stats['tempos'] else 0.0
        
        resultado.append({
            'categoria': categoria,
            'total_classificacoes': total,
            'confirmacoes': confirmacoes,
            'correcoes': stats['correcoes'],
            'taxa_acerto_percentual': taxa_acerto,
            'tempo_medio_ms': tempo_medio
        })
    
    # Ordenar por total de classificações (decrescente)
    resultado.sort(key=lambda x: x['total_classificacoes'], reverse=True)
    
    return resultado

def _calcular_variacao_periodo_anterior(self, valor_atual: float, periodo_inicio: datetime) -> Optional[float]:
    """
    Calcula variação em relação ao período anterior.
    
    Args:
        valor_atual: Valor do período atual
        periodo_inicio: Data de início do período atual
        
    Returns:
        Variação percentual ou None se não houver dados anteriores
    """
    try:
        # Calcular período anterior (mesma duração)
        from datetime import timedelta
        duracao = (datetime.now() - periodo_inicio).days
        periodo_anterior_fim = periodo_inicio
        periodo_anterior_inicio = periodo_inicio - timedelta(days=duracao)
        
        # Carregar logs do período anterior
        logs_anteriores = self._carregar_logs_feedback_periodo(
            periodo_anterior_inicio, 
            periodo_anterior_fim
        )
        
        if not logs_anteriores:
            return None
        
        # Calcular valor do período anterior
        total = len(logs_anteriores)
        confirmacoes = len([log for log in logs_anteriores if log.get('tipo_feedback') == 'confirmacao'])
        valor_anterior = (confirmacoes / total * 100) if total > 0 else 0.0
        
        # Calcular variação percentual
        if valor_anterior == 0:
            return None
        
        variacao = round(((valor_atual - valor_anterior) / valor_anterior * 100), 1)
        return variacao
        
    except Exception as e:
        logger.error(f"Erro ao calcular variação: {e}")
        return None

def _formatar_data_br(self, data_iso: str) -> str:
    """
    Formata data de YYYY-MM-DD para DD/MM/YYYY.
    
    Args:
        data_iso: Data em formato ISO (YYYY-MM-DD)
        
    Returns:
        Data formatada em padrão brasileiro
    """
    try:
        data_obj = datetime.strptime(data_iso, '%Y-%m-%d')
        return data_obj.strftime('%d/%m/%Y')
    except ValueError:
        return data_iso

def _estatisticas_vazias(self) -> Dict[str, Any]:
    """
    Retorna estrutura de estatísticas vazia para casos de erro.
    
    Returns:
        Dicionário com estrutura vazia mas válida
    """
    return {
        'cards_principais': {
            'taxa_acerto': {'valor': 0, 'unidade': '%', 'label': 'Taxa de Acerto', 'variacao': None},
            'total_classificacoes': {'valor': 0, 'unidade': '', 'label': 'Classificações Automáticas', 'variacao': None},
            'total_correcoes': {'valor': 0, 'unidade': '', 'label': 'Correções Manuais', 'variacao': None},
            'tempo_medio': {'valor': 0, 'unidade': 'ms', 'label': 'Tempo Médio', 'variacao': None}
        },
        'estatisticas_periodo': {
            'periodo_inicio': datetime.now().isoformat(),
            'periodo_fim': datetime.now().isoformat(),
            'total_dias': 0,
            'total_classificacoes': 0,
            'total_confirmacoes': 0,
            'total_correcoes': 0,
            'taxa_acerto_percentual': 0.0,
            'tempo_medio_classificacao_ms': 0.0,
            'classificacoes_por_dia': 0.0,
            'classificacoes_por_data': {},
            'taxa_acerto_por_data': {},
            'top_10_categorias': [],
            'distribuicao_tipo': {'automatica': 0, 'manual': 0}
        },
        'grafico_evolucao_temporal': [],
        'grafico_distribuicao_tipo': [],
        'grafico_top_categorias': [],
        'grafico_taxa_acerto_temporal': [],
        'tabela_categorias': [],
        'data_geracao': datetime.now().isoformat(),
        'filtros_aplicados': {}
    }






# ============================================================================
# INSTÂNCIA GLOBAL DO CLASSIFICADOR
# ============================================================================

# Instância global que será reutilizada
_classificador_global = None

def obter_classificador(db_session: Session = None) -> ClassificadorIA:
    """
    Obtém instância global do classificador IA.
    
    Args:
        db_session: Sessão do banco (opcional)
        
    Returns:
        ClassificadorIA: Instância do classificador
    """
    global _classificador_global
    
    if _classificador_global is None:
        _classificador_global = ClassificadorIA(db_session)
    elif db_session:
        _classificador_global.db_session = db_session
    
    return _classificador_global