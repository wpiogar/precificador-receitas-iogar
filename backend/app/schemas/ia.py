# ============================================================================
# SCHEMAS IA - Sistema de Classificação Inteligente de Insumos
# ============================================================================
# Descrição: Schemas Pydantic para APIs do sistema de IA de classificação
# Operações: classificar, feedback, estatísticas, aprendizado
# Data: 10/09/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ============================================================================
# ENUMS PARA CONTROLE DE AÇÕES E STATUS
# ============================================================================

class AcaoFeedback(str, Enum):
    """Ações possíveis para feedback do usuário"""
    ACEITAR = "aceitar"
    CORRIGIR = "corrigir"

class StatusClassificacao(str, Enum):
    """Status da classificação realizada"""
    SUCESSO = "sucesso"
    ERRO = "erro"
    SEM_CORRESPONDENCIA = "sem_correspondencia"
    BAIXA_CONFIANCA = "baixa_confianca"

class TipoSugestao(str, Enum):
    """Tipos de sugestão do sistema"""
    AUTOMATICA = "automatica"
    MANUAL = "manual"
    IA_APRENDIZADO = "ia_aprendizado"

# ============================================================================
# SCHEMAS DE ENTRADA - REQUESTS
# ============================================================================

class ClassificarProdutoRequest(BaseModel):
    """
    Schema para solicitação de classificação de produto.
    
    Entrada principal do sistema de IA para analisar um nome de produto
    e retornar sugestões de taxonomia hierárquica.
    """
    
    nome_produto: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Nome do produto a ser classificado"
    )
    
    incluir_alternativas: bool = Field(
        default=True,
        description="Se deve incluir sugestões alternativas na resposta"
    )
    
    limite_alternativas: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Número máximo de alternativas a retornar"
    )
    
    confianca_minima: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confiança mínima para considerar sugestão válida"
    )
    
    @field_validator('nome_produto')
    @classmethod
    def validar_nome_produto(cls, valor: str) -> str:
        """Valida e limpa o nome do produto."""
        if not valor or not valor.strip():
            raise ValueError("Nome do produto não pode estar vazio")
        return valor.strip()

class RegistrarFeedbackRequest(BaseModel):
    """
    Schema para registro de feedback do usuário.
    
    Usado para treinar o sistema com base na aprovação ou correção
    feita pelo usuário nas sugestões de classificação.
    """
    
    nome_produto: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Nome do produto que foi classificado"
    )
    
    acao: AcaoFeedback = Field(
        ...,
        description="Ação realizada pelo usuário (aceitar ou corrigir)"
    )
    
    classificacao_sugerida: Dict[str, Any] = Field(
        ...,
        description="Classificação que foi sugerida pelo sistema"
    )
    
    taxonomia_correta: Optional[Dict[str, Any]] = Field(
        None,
        description="Taxonomia correta (obrigatório se ação for 'corrigir')"
    )
    
    confianca_usuario: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Nível de confiança do usuário na correção"
    )
    
    observacoes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Observações adicionais do usuário"
    )
    
    @field_validator('taxonomia_correta')
    @classmethod
    def validar_taxonomia_correta(cls, valor: Optional[Dict], info) -> Optional[Dict]:
        """Valida taxonomia correta quando ação for 'corrigir'."""
        acao = info.data.get('acao')
        if acao == AcaoFeedback.CORRIGIR and not valor:
            raise ValueError("Taxonomia correta é obrigatória quando ação for 'corrigir'")
        return valor

class AtualizarBaseConhecimentoRequest(BaseModel):
    """
    Schema para atualização manual da base de conhecimento.
    
    Permite que administradores adicionem ou modifiquem entradas
    na base de conhecimento diretamente.
    """
    
    chave_entrada: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Chave única da entrada na base"
    )
    
    aliases: List[str] = Field(
        ...,
        min_items=1,
        description="Lista de aliases/sinônimos para o produto"
    )
    
    palavras_chave: List[str] = Field(
        ...,
        min_items=1,
        description="Palavras-chave relevantes para classificação"
    )
    
    categoria: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Categoria da taxonomia"
    )
    
    subcategoria: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Subcategoria da taxonomia"
    )
    
    especificacao: Optional[str] = Field(
        None,
        max_length=100,
        description="Especificação da taxonomia"
    )
    
    variante: Optional[str] = Field(
        None,
        max_length=100,
        description="Variante da taxonomia"
    )
    
    confianca_inicial: float = Field(
        default=0.7,
        ge=0.1,
        le=1.0,
        description="Confiança inicial da entrada"
    )

# ============================================================================
# SCHEMAS DE RESPOSTA - RESPONSES
# ============================================================================

class TaxonomiaClassificada(BaseModel):
    """
    Schema para taxonomia classificada pelo sistema.
    
    Representa uma sugestão de classificação com dados hierárquicos
    e informações de confiança.
    """
    
    categoria: Optional[str] = Field(description="Categoria da taxonomia")
    subcategoria: Optional[str] = Field(description="Subcategoria da taxonomia")
    especificacao: Optional[str] = Field(description="Especificação da taxonomia")
    variante: Optional[str] = Field(description="Variante da taxonomia")
    nome_completo: Optional[str] = Field(description="Nome completo hierárquico")
    codigo_taxonomia: Optional[str] = Field(description="Código da taxonomia (se existir no banco)")
    taxonomia_id: Optional[int] = Field(description="ID da taxonomia no banco (se encontrada)")

class DetalhesClassificacao(BaseModel):
    """
    Schema para detalhes da classificação realizada.
    
    Informações técnicas sobre como a classificação foi realizada,
    útil para debugging e melhoria do algoritmo.
    """
    
    tipo_match: str = Field(description="Tipo de correspondência encontrada")
    termo_correspondente: Optional[str] = Field(description="Termo que fez a correspondência")
    palavras_encontradas: List[str] = Field(default=[], description="Palavras-chave encontradas")
    tokens_extraidos: List[str] = Field(default=[], description="Tokens extraídos do nome")
    score_similaridade: float = Field(description="Score de similaridade (0.0 a 1.0)")
    algoritmo_utilizado: str = Field(default="base_conhecimento", description="Algoritmo usado")
    tempo_processamento_ms: Optional[float] = Field(description="Tempo de processamento")

class SugestaoAlternativa(BaseModel):
    """
    Schema para sugestões alternativas de classificação.
    
    Quando o sistema não tem certeza absoluta, oferece alternativas
    ordenadas por relevância.
    """
    
    taxonomia: TaxonomiaClassificada = Field(description="Dados da taxonomia alternativa")
    confianca: float = Field(description="Confiança desta alternativa")
    motivo: Optional[str] = Field(description="Motivo da sugestão alternativa")

class ClassificarProdutoResponse(BaseModel):
    """
    Schema de resposta para classificação de produto.
    
    Resposta principal do sistema de IA contendo a classificação
    sugerida, alternativas e informações de confiança.
    """
    
    sucesso: bool = Field(description="Se a classificação foi bem-sucedida")
    status: StatusClassificacao = Field(description="Status da classificação")
    
    # Dados da classificação principal
    taxonomia_sugerida: Optional[TaxonomiaClassificada] = Field(
        description="Taxonomia sugerida (melhor correspondência)"
    )
    
    confianca: float = Field(
        description="Nível de confiança da sugestão (0.0 a 1.0)"
    )
    
    requer_revisao: bool = Field(
        description="Se a sugestão requer revisão manual"
    )
    
    # Informações técnicas
    detalhes: DetalhesClassificacao = Field(
        description="Detalhes técnicos da classificação"
    )
    
    # Alternativas
    alternativas: List[SugestaoAlternativa] = Field(
        default=[],
        description="Sugestões alternativas ordenadas por relevância"
    )
    
    # Dados de entrada
    termo_analisado: str = Field(description="Termo que foi analisado")
    
    # Informações de aprendizado
    total_confirmacoes: int = Field(default=0, description="Total de confirmações desta classificação")
    total_correcoes: int = Field(default=0, description="Total de correções desta classificação")
    
    # Mensagens e sugestões
    mensagem: Optional[str] = Field(description="Mensagem explicativa para o usuário")
    sugestoes_melhoria: List[str] = Field(default=[], description="Sugestões para melhorar a classificação")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da classificação")

class RegistrarFeedbackResponse(BaseModel):
    """
    Schema de resposta para registro de feedback.
    
    Confirma que o feedback foi processado e mostra impacto
    no aprendizado do sistema.
    """
    
    sucesso: bool = Field(description="Se o feedback foi registrado com sucesso")
    
    feedback_processado: Dict[str, Any] = Field(
        description="Detalhes do feedback processado"
    )
    
    impacto_aprendizado: Dict[str, Any] = Field(
        description="Como o feedback impactou o aprendizado"
    )
    
    nova_confianca: Optional[float] = Field(
        description="Nova confiança da entrada após feedback"
    )
    
    entrada_criada: bool = Field(
        default=False,
        description="Se uma nova entrada foi criada na base"
    )
    
    mensagem: str = Field(description="Mensagem de confirmação")
    
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp do feedback")

# ============================================================================
# SCHEMAS DE ESTATÍSTICAS E RELATÓRIOS
# ============================================================================

class EstatisticasCategoria(BaseModel):
    """
    Schema para estatísticas por categoria.
    """
    
    categoria: str = Field(description="Nome da categoria")
    total_entradas: int = Field(description="Total de entradas na categoria")
    total_confirmacoes: int = Field(description="Total de confirmações")
    total_correcoes: int = Field(description="Total de correções")
    taxa_acerto: float = Field(description="Taxa de acerto da categoria")
    confianca_media: float = Field(description="Confiança média da categoria")

class EstatisticasIA(BaseModel):
    """
    Schema para estatísticas gerais do sistema de IA.
    
    Fornece métricas sobre performance, aprendizado e uso do sistema.
    """
    
    # Estatísticas gerais
    total_entradas_conhecimento: int = Field(description="Total de entradas na base")
    total_classificacoes_realizadas: int = Field(description="Total de classificações realizadas")
    total_feedbacks_recebidos: int = Field(description="Total de feedbacks recebidos")
    
    # Performance
    taxa_acerto_geral: float = Field(description="Taxa de acerto geral do sistema")
    confianca_media: float = Field(description="Confiança média das classificações")
    tempo_medio_classificacao_ms: float = Field(description="Tempo médio de classificação")
    
    # Aprendizado
    total_confirmacoes: int = Field(description="Total de confirmações recebidas")
    total_correcoes: int = Field(description="Total de correções recebidas")
    entradas_criadas_feedback: int = Field(description="Entradas criadas via feedback")
    
    # Distribuição
    distribuicao_categorias: Dict[str, int] = Field(description="Distribuição por categoria")
    estatisticas_por_categoria: List[EstatisticasCategoria] = Field(
        default=[],
        description="Estatísticas detalhadas por categoria"
    )
    
    # Sistema
    versao_base_conhecimento: str = Field(description="Versão da base de conhecimento")
    ultima_atualizacao: Optional[str] = Field(description="Data da última atualização")
    dependencias_disponiveis: Dict[str, bool] = Field(description="Status das dependências")
    
    # Qualidade
    entradas_baixa_confianca: int = Field(description="Entradas com confiança < 70%")
    entradas_alta_confianca: int = Field(description="Entradas com confiança > 90%")
    categorias_sem_entradas: int = Field(description="Categorias sem entradas")
    
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp das estatísticas")


# ============================================================================
# SCHEMAS PARA DASHBOARD DE ESTATÍSTICAS COMPLETAS
# ============================================================================

class EstatisticasPeriodo(BaseModel):
    """
    Schema para estatísticas filtradas por período de tempo.
    
    Permite análise temporal do desempenho da IA.
    """
    
    periodo_inicio: datetime = Field(description="Data inicial do período")
    periodo_fim: datetime = Field(description="Data final do período")
    total_dias: int = Field(description="Total de dias no período")
    
    # Métricas principais
    total_classificacoes: int = Field(description="Total de classificações no período")
    total_confirmacoes: int = Field(description="Classificações aceitas sem alteração")
    total_correcoes: int = Field(description="Classificações corrigidas manualmente")
    taxa_acerto_percentual: float = Field(description="Taxa de acerto em %")
    
    # Performance
    tempo_medio_classificacao_ms: float = Field(description="Tempo médio por classificação")
    classificacoes_por_dia: float = Field(description="Média de classificações por dia")
    
    # Distribuição temporal
    classificacoes_por_data: Dict[str, int] = Field(
        description="Classificações agrupadas por data (formato YYYY-MM-DD)"
    )
    taxa_acerto_por_data: Dict[str, float] = Field(
        description="Taxa de acerto por data"
    )
    
    # Top categorias
    top_10_categorias: List[Dict[str, Any]] = Field(
        description="Top 10 categorias mais classificadas"
    )
    
    # Distribuição por tipo
    distribuicao_tipo: Dict[str, int] = Field(
        description="Automáticas vs Manuais"
    )

class DashboardEstatisticasIA(BaseModel):
    """
    Schema completo para o dashboard de estatísticas da IA.
    
    Agrupa todas as métricas e visualizações necessárias.
    """
    
    # Cards principais (KPIs)
    cards_principais: Dict[str, Any] = Field(
        description="Métricas principais para cards do dashboard"
    )
    
    # Estatísticas do período selecionado
    estatisticas_periodo: EstatisticasPeriodo = Field(
        description="Estatísticas filtradas por período"
    )
    
    # Dados para gráficos
    grafico_evolucao_temporal: List[Dict[str, Any]] = Field(
        description="Dados para gráfico de linha - evolução diária"
    )
    
    grafico_distribuicao_tipo: List[Dict[str, Any]] = Field(
        description="Dados para gráfico de pizza - auto vs manual"
    )
    
    grafico_top_categorias: List[Dict[str, Any]] = Field(
        description="Dados para gráfico de barras - top categorias"
    )
    
    grafico_taxa_acerto_temporal: List[Dict[str, Any]] = Field(
        description="Dados para gráfico de linha - taxa de acerto ao longo do tempo"
    )
    
    # Tabela de categorias
    tabela_categorias: List[Dict[str, Any]] = Field(
        description="Dados detalhados para tabela de categorias"
    )
    
    # Metadados
    data_geracao: datetime = Field(
        default_factory=datetime.now,
        description="Data/hora de geração do dashboard"
    )
    
    filtros_aplicados: Dict[str, Any] = Field(
        description="Filtros que foram aplicados para gerar os dados"
    )

class RelatorioAprendizado(BaseModel):
    """
    Schema para relatório detalhado de aprendizado.
    
    Mostra evolução do sistema ao longo do tempo e identifica
    áreas que precisam de melhoria.
    """
    
    periodo_inicio: datetime = Field(description="Início do período analisado")
    periodo_fim: datetime = Field(description="Fim do período analisado")
    
    # Evolução da performance
    taxa_acerto_inicio: float = Field(description="Taxa de acerto no início do período")
    taxa_acerto_fim: float = Field(description="Taxa de acerto no fim do período")
    melhoria_percentual: float = Field(description="Melhoria percentual da taxa de acerto")
    
    # Novos aprendizados
    novas_entradas_criadas: int = Field(description="Novas entradas criadas no período")
    aliases_adicionados: int = Field(description="Novos aliases adicionados")
    padroes_descobertos: List[str] = Field(description="Novos padrões descobertos")
    
    # Problemas identificados
    produtos_nao_classificados: List[str] = Field(description="Produtos que não conseguiu classificar")
    classificacoes_incorretas: List[Dict] = Field(description="Classificações que foram corrigidas")
    sugestoes_melhoria: List[str] = Field(description="Sugestões para melhorar o sistema")
    
    # Próximos passos
    areas_foco: List[str] = Field(description="Áreas que precisam de foco")
    treinamento_recomendado: List[str] = Field(description="Treinamentos recomendados")

# ============================================================================
# SCHEMAS PARA OPERAÇÕES EM LOTE
# ============================================================================

class ClassificarLoteRequest(BaseModel):
    """
    Schema para classificação em lote.
    
    Permite classificar múltiplos produtos de uma vez,
    útil para importações e processamento em massa.
    """
    
    produtos: List[str] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="Lista de nomes de produtos para classificar"
    )
    
    confianca_minima: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confiança mínima para todas as classificações"
    )
    
    incluir_alternativas: bool = Field(
        default=False,
        description="Se deve incluir alternativas (pode ser lento para lotes grandes)"
    )

class ResultadoClassificacaoLote(BaseModel):
    """
    Schema para resultado individual de classificação em lote.
    """
    
    nome_produto: str = Field(description="Nome do produto classificado")
    indice: int = Field(description="Índice na lista original")
    classificacao: Optional[ClassificarProdutoResponse] = Field(description="Resultado da classificação")
    erro: Optional[str] = Field(description="Erro ocorrido (se houver)")

class ClassificarLoteResponse(BaseModel):
    """
    Schema de resposta para classificação em lote.
    """
    
    total_processados: int = Field(description="Total de produtos processados")
    total_classificados: int = Field(description="Total classificados com sucesso")
    total_erros: int = Field(description="Total de erros")
    
    resultados: List[ResultadoClassificacaoLote] = Field(description="Resultados detalhados")
    
    # Estatísticas do lote
    confianca_media: float = Field(description="Confiança média do lote")
    tempo_total_processamento_ms: float = Field(description="Tempo total de processamento")
    
    # Resumo por categoria
    distribuicao_categorias: Dict[str, int] = Field(description="Distribuição por categoria encontrada")
    produtos_nao_classificados: List[str] = Field(description="Produtos que não foram classificados")
    
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp do processamento")

# ============================================================================
# SCHEMAS PARA CONFIGURAÇÃO E MANUTENÇÃO
# ============================================================================

class ConfiguracaoIA(BaseModel):
    """
    Schema para configuração do sistema de IA.
    
    Permite ajustar parâmetros de funcionamento do sistema.
    """
    
    confianca_minima_padrao: float = Field(
        default=0.6,
        ge=0.1,
        le=1.0,
        description="Confiança mínima padrão para classificações"
    )
    
    limite_alternativas_padrao: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Número padrão de alternativas a retornar"
    )
    
    threshold_aprendizado: float = Field(
        default=0.5,
        ge=0.1,
        le=1.0,
        description="Threshold para considerar um match válido"
    )
    
    max_entradas_base: int = Field(
        default=10000,
        ge=100,
        le=50000,
        description="Máximo de entradas na base de conhecimento"
    )
    
    auto_salvar_feedback: bool = Field(
        default=True,
        description="Se deve salvar feedback automaticamente"
    )
    
    habilitar_logs_detalhados: bool = Field(
        default=False,
        description="Se deve manter logs detalhados (pode impactar performance)"
    )

class StatusSistemaIA(BaseModel):
    """
    Schema para status do sistema de IA.
    
    Informações sobre saúde e funcionamento do sistema.
    """
    
    sistema_ativo: bool = Field(description="Se o sistema está ativo")
    versao: str = Field(description="Versão do sistema")
    
    # Status das dependências
    spacy_disponivel: bool = Field(description="Se spaCy está disponível")
    fuzzywuzzy_disponivel: bool = Field(description="Se fuzzywuzzy está disponível")
    modelo_portugues: bool = Field(description="Se modelo português está carregado")
    
    # Status dos arquivos
    base_conhecimento_ok: bool = Field(description="Se base de conhecimento está OK")
    padroes_aprendidos_ok: bool = Field(description="Se padrões aprendidos estão OK")
    logs_feedback_ok: bool = Field(description="Se logs de feedback estão OK")
    
    # Performance
    classificacoes_ultimas_24h: int = Field(description="Classificações nas últimas 24h")
    tempo_medio_resposta_ms: float = Field(description="Tempo médio de resposta")
    
    # Avisos e erros
    avisos: List[str] = Field(default=[], description="Avisos do sistema")
    erros: List[str] = Field(default=[], description="Erros encontrados")
    
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp do status")

# ============================================================================
# VALIDADORES GLOBAIS
# ============================================================================

def validar_confianca(valor: float) -> float:
    """Valida valor de confiança."""
    if not 0.0 <= valor <= 1.0:
        raise ValueError("Confiança deve estar entre 0.0 e 1.0")
    return valor

def validar_taxonomia_dados(taxonomia: Dict[str, Any]) -> Dict[str, Any]:
    """Valida dados de taxonomia."""
    campos_obrigatorios = ["categoria", "subcategoria"]
    for campo in campos_obrigatorios:
        if not taxonomia.get(campo):
            raise ValueError(f"Campo '{campo}' é obrigatório na taxonomia")
    return taxonomia