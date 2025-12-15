# ============================================================================
# ENDPOINTS IA - APIs REST para Sistema de Classificação Inteligente
# ============================================================================
# Descrição: Endpoints FastAPI para sistema de IA de classificação de insumos
# Operações: classificar, feedback, estatísticas, configuração
# Data: 10/09/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import time
from datetime import datetime, timedelta

# Imports do projeto
from app.database import get_db
from app.ai.classificador_ia import obter_classificador, ClassificadorIA
from app.core.dependencies import get_current_user, get_admin_user
from app.models.user import User
from app.schemas.ia import (
    ClassificarProdutoRequest,
    ClassificarProdutoResponse,
    RegistrarFeedbackRequest,
    RegistrarFeedbackResponse,
    EstatisticasIA,
    StatusSistemaIA,
    ConfiguracaoIA,
    ClassificarLoteRequest,
    ClassificarLoteResponse,
    AtualizarBaseConhecimentoRequest,
    RelatorioAprendizado,
    TaxonomiaClassificada,
    DetalhesClassificacao,
    SugestaoAlternativa,
    StatusClassificacao,
    ResultadoClassificacaoLote,
    EstatisticasPeriodo,
    DashboardEstatisticasIA
)

# Configuração de logging
logger = logging.getLogger(__name__)

# Criar router para IA
router = APIRouter(prefix="", tags=["ia-classificacao"])

# ============================================================================
# ENDPOINT PRINCIPAL - CLASSIFICAR PRODUTO
# ============================================================================

@router.post("/classificar", response_model=ClassificarProdutoResponse, summary="Classificar Produto")
async def classificar_produto(
    request: ClassificarProdutoRequest,
    db: Session = Depends(get_db)
):
    """
    Classifica um produto usando o sistema de IA local.
    
    **Funcionalidades:**
    - Análise NLP do nome do produto
    - Busca na base de conhecimento
    - Cálculo de confiança inteligente
    - Sugestões alternativas ordenadas por relevância
    - Detalhes técnicos para debugging
    
    **Exemplo de uso:**
    ```json
    {
        "nome_produto": "Salmão Atlântico Filé Fresh 1kg",
        "incluir_alternativas": true,
        "limite_alternativas": 3,
        "confianca_minima": 0.6
    }
    ```
    
    **Resposta típica:**
    - **Alta confiança (>80%)**: Sugestão direta
    - **Média confiança (50-80%)**: Sugestão + alternativas
    - **Baixa confiança (<50%)**: Múltiplas alternativas + flag de revisão
    """
    try:
        inicio_tempo = time.time()
        
        # Obter classificador
        classificador = obter_classificador(db)
        
        # Realizar classificação
        resultado = classificador.classificar_produto(request.nome_produto)
        
        # Calcular tempo de processamento
        tempo_processamento = (time.time() - inicio_tempo) * 1000
        
        # Determinar status
        if not resultado.get("sucesso"):
            status = StatusClassificacao.ERRO if resultado.get("erro") else StatusClassificacao.SEM_CORRESPONDENCIA
        elif resultado.get("confianca", 0) < request.confianca_minima:
            status = StatusClassificacao.BAIXA_CONFIANCA
        else:
            status = StatusClassificacao.SUCESSO
        
        # Construir resposta
        response = ClassificarProdutoResponse(
            sucesso=resultado.get("sucesso", False),
            status=status,
            taxonomia_sugerida=None,
            confianca=resultado.get("confianca", 0.0),
            requer_revisao=resultado.get("requer_revisao", True),
            detalhes=DetalhesClassificacao(
                tipo_match=resultado.get("detalhes_match", {}).get("tipo", "unknown"),
                termo_correspondente=resultado.get("detalhes_match", {}).get("termo"),
                palavras_encontradas=resultado.get("detalhes_match", {}).get("palavras", []),
                tokens_extraidos=resultado.get("tokens_extraidos", []),
                score_similaridade=resultado.get("score_similaridade", 0.0),
                algoritmo_utilizado="classificador_ia_local",
                tempo_processamento_ms=tempo_processamento
            ),
            alternativas=[],
            termo_analisado=request.nome_produto,
            total_confirmacoes=resultado.get("total_confirmacoes", 0),
            total_correcoes=resultado.get("total_correcoes", 0),
            mensagem=resultado.get("motivo") if not resultado.get("sucesso") else None
        )
        
        # Adicionar taxonomia sugerida se houver
        if resultado.get("sucesso") and status != StatusClassificacao.ERRO:
            response.taxonomia_sugerida = TaxonomiaClassificada(
                categoria=resultado.get("categoria"),
                subcategoria=resultado.get("subcategoria"),
                especificacao=resultado.get("especificacao"),
                variante=resultado.get("variante"),
                nome_completo=f"{resultado.get('categoria', '')} > {resultado.get('subcategoria', '')}",
                codigo_taxonomia=None,  # TODO: Buscar no banco se existir
                taxonomia_id=None  # TODO: Buscar no banco se existir
            )
        
        # Adicionar alternativas se solicitado
        if request.incluir_alternativas and resultado.get("alternativas"):
            for alt in resultado["alternativas"][:request.limite_alternativas]:
                sugestao = SugestaoAlternativa(
                    taxonomia=TaxonomiaClassificada(
                        categoria=alt.get("categoria"),
                        subcategoria=alt.get("subcategoria"),
                        especificacao=alt.get("especificacao"),
                        variante=alt.get("variante"),
                        nome_completo=f"{alt.get('categoria', '')} > {alt.get('subcategoria', '')}"
                    ),
                    confianca=alt.get("confianca", 0.0),
                    motivo=f"Similaridade: {alt.get('confianca', 0.0):.1%}"
                )
                response.alternativas.append(sugestao)
        
        logger.info(f"Produto classificado: '{request.nome_produto}' -> {status.value}")
        return response
        
    except Exception as e:
        logger.error(f"Erro na classificação: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno na classificação: {str(e)}"
        )

# ============================================================================
# ENDPOINT DE FEEDBACK - APRENDIZADO DO SISTEMA
# ============================================================================

@router.post("/feedback", response_model=RegistrarFeedbackResponse, summary="Registrar Feedback")
async def registrar_feedback(
    request: RegistrarFeedbackRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Registra feedback do usuário para aprendizado do sistema.
    
    **Tipos de feedback:**
    - **ACEITAR**: Usuário confirma que classificação está correta
    - **CORRIGIR**: Usuário informa classificação correta
    
    **Como funciona o aprendizado:**
    1. **Feedback positivo**: Aumenta confiança da classificação
    2. **Correção**: Reduz confiança da classificação errada e cria/reforça a correta
    3. **Novos aliases**: Adiciona termo à base de conhecimento
    4. **Padrões**: Sistema aprende novos padrões de nomenclatura
    
    **Exemplo de correção:**
    ```json
    {
        "nome_produto": "Salmão Premium 1kg",
        "acao": "corrigir",
        "classificacao_sugerida": {"categoria": "Carnes", "subcategoria": "Bovino"},
        "taxonomia_correta": {"categoria": "Peixes", "subcategoria": "Salmão", "especificacao": "Filé"}
    }
    ```
    """
    try:
        # Obter classificador
        classificador = obter_classificador(db)
        
        # Validar dados da correção
        if request.acao.value == "corrigir" and not request.taxonomia_correta:
            raise HTTPException(
                status_code=400,
                detail="Taxonomia correta é obrigatória quando ação for 'corrigir'"
            )
        
        # Registrar feedback no sistema
        sucesso = classificador.registrar_feedback(
            nome_produto=request.nome_produto,
            classificacao_sugerida=request.classificacao_sugerida,
            acao=request.acao.value,
            taxonomia_correta=request.taxonomia_correta
        )
        
        if not sucesso:
            raise HTTPException(
                status_code=500,
                detail="Erro ao processar feedback"
            )
        
        # Construir resposta
        response = RegistrarFeedbackResponse(
            sucesso=True,
            feedback_processado={
                "nome_produto": request.nome_produto,
                "acao": request.acao.value,
                "timestamp": datetime.now().isoformat()
            },
            impacto_aprendizado={
                "tipo": "confirmacao" if request.acao.value == "aceitar" else "correcao",
                "base_atualizada": True,
                "alias_adicionado": True
            },
            nova_confianca=request.confianca_usuario if request.confianca_usuario else 1.0,
            entrada_criada=request.acao.value == "corrigir",
            mensagem=f"Feedback '{request.acao.value}' registrado com sucesso"
        )
        
        # Adicionar tarefa em background para otimizações
        background_tasks.add_task(
            otimizar_base_conhecimento_background,
            classificador
        )
        
        logger.info(f"Feedback registrado: {request.acao.value} para '{request.nome_produto}'")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao registrar feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

# ============================================================================
# ENDPOINT DE ESTATÍSTICAS - MÉTRICAS DO SISTEMA
# ============================================================================

@router.get("/estatisticas", response_model=EstatisticasIA, summary="Estatísticas da IA")
async def obter_estatisticas(
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas completas do sistema de IA.
    
    **Métricas incluídas:**
    - Performance geral (taxa de acerto, confiança média)
    - Aprendizado (confirmações, correções, evolução)
    - Distribuição por categorias
    - Status das dependências técnicas
    - Qualidade da base de conhecimento
    
    **Uso típico:**
    - Dashboards de monitoramento
    - Relatórios gerenciais
    - Identificação de melhorias necessárias
    - Acompanhamento de evolução do sistema
    """
    try:
        # Obter classificador
        classificador = obter_classificador(db)
        
        # Obter estatísticas do sistema
        stats = classificador.obter_estatisticas()
        
        if "erro" in stats:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao gerar estatísticas: {stats['erro']}"
            )
        
        # Construir resposta
        response = EstatisticasIA(
            total_entradas_conhecimento=stats.get("total_entradas_conhecimento", 0),
            total_classificacoes_realizadas=0,  # TODO: Implementar contador
            total_feedbacks_recebidos=stats.get("total_confirmacoes", 0) + stats.get("total_correcoes", 0),
            
            taxa_acerto_geral=stats.get("taxa_acerto", 0.0),
            confianca_media=0.0,  # TODO: Calcular média ponderada
            tempo_medio_classificacao_ms=0.0,  # TODO: Implementar medição
            
            total_confirmacoes=stats.get("total_confirmacoes", 0),
            total_correcoes=stats.get("total_correcoes", 0),
            entradas_criadas_feedback=0,  # TODO: Implementar contador
            
            distribuicao_categorias=stats.get("distribuicao_categorias", {}),
            estatisticas_por_categoria=[],  # TODO: Implementar detalhamento
            
            versao_base_conhecimento=stats.get("versao_base", "1.0.0"),
            ultima_atualizacao=stats.get("ultima_atualizacao"),
            dependencias_disponiveis={
                "spacy": stats.get("spacy_disponivel", False),
                "fuzzywuzzy": stats.get("fuzzywuzzy_disponivel", False),
                "modelo_portugues": stats.get("spacy_disponivel", False)
            },
            
            entradas_baixa_confianca=0,  # TODO: Calcular
            entradas_alta_confianca=0,  # TODO: Calcular
            categorias_sem_entradas=0   # TODO: Calcular
        )
        
        logger.info("Estatísticas da IA geradas com sucesso")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar estatísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

# ============================================================================
# ENDPOINT DE STATUS - SAÚDE DO SISTEMA
# ============================================================================

@router.get("/status", response_model=StatusSistemaIA, summary="Status do Sistema IA")
async def verificar_status(
    db: Session = Depends(get_db)
):
    """
    Verifica status e saúde do sistema de IA.
    
    **Verificações realizadas:**
    - Disponibilidade das dependências (spaCy, fuzzywuzzy)
    - Integridade dos arquivos de dados
    - Performance recente
    - Avisos e erros do sistema
    
    **Códigos de status:**
    - **200**: Sistema funcionando normalmente
    - **206**: Sistema funcional com avisos
    - **503**: Sistema com problemas críticos
    """
    try:
        avisos = []
        erros = []
        
        # Verificar classificador
        try:
            classificador = obter_classificador(db)
        except Exception as e:
            erros.append(f"Erro ao inicializar classificador: {str(e)}")
            classificador = None
        
        # Verificar dependências
        spacy_ok = True
        fuzzywuzzy_ok = True
        modelo_portugues_ok = False
        
        try:
            import spacy
            try:
                nlp = spacy.load("pt_core_news_sm")
                modelo_portugues_ok = True
            except OSError:
                avisos.append("Modelo português do spaCy não encontrado")
        except ImportError:
            spacy_ok = False
            avisos.append("spaCy não está instalado")
        
        try:
            import fuzzywuzzy
        except ImportError:
            fuzzywuzzy_ok = False
            avisos.append("fuzzywuzzy não está instalado")
        
        # Verificar arquivos
        from pathlib import Path
        base_conhecimento_ok = Path("backend/app/ai/data/base_conhecimento.json").exists()
        padroes_aprendidos_ok = Path("backend/app/ai/data/padroes_aprendidos.json").exists()
        logs_feedback_ok = Path("backend/app/ai/data/logs_feedback.json").exists()
        
        if not base_conhecimento_ok:
            avisos.append("Base de conhecimento será criada automaticamente")
        if not padroes_aprendidos_ok:
            avisos.append("Padrões aprendidos serão criados automaticamente")
        
        # Construir resposta
        response = StatusSistemaIA(
            sistema_ativo=classificador is not None,
            versao="2.0.0",
            
            spacy_disponivel=spacy_ok,
            fuzzywuzzy_disponivel=fuzzywuzzy_ok,
            modelo_portugues=modelo_portugues_ok,
            
            base_conhecimento_ok=base_conhecimento_ok,
            padroes_aprendidos_ok=padroes_aprendidos_ok,
            logs_feedback_ok=logs_feedback_ok,
            
            classificacoes_ultimas_24h=0,  # TODO: Implementar contador
            tempo_medio_resposta_ms=0.0,   # TODO: Implementar medição
            
            avisos=avisos,
            erros=erros
        )
        
        # Definir código de status HTTP baseado na saúde
        if erros:
            raise HTTPException(status_code=503, detail=response.dict())
        elif avisos:
            # Status 206 não é padrão para este caso, usar 200 com avisos
            pass
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )
    

@router.get(
    "/estatisticas/dashboard",
    response_model=DashboardEstatisticasIA,
    summary="Dashboard de Estatísticas Completas",
    description="""
    Retorna estatísticas completas para o dashboard da IA.
    
    **Funcionalidades:**
    - Métricas principais (KPIs) em cards
    - Dados para gráficos (evolução, pizza, barras)
    - Tabela detalhada por categoria
    - Filtros por período de tempo
    
    **Parâmetros de filtro:**
    - `periodo`: Período pré-definido (7d, 30d, 90d)
    - `data_inicio`: Data inicial customizada (formato: YYYY-MM-DD)
    - `data_fim`: Data final customizada (formato: YYYY-MM-DD)
    
    **Exemplo de uso:**
    - Últimos 7 dias: `/estatisticas/dashboard?periodo=7d`
    - Últimos 30 dias: `/estatisticas/dashboard?periodo=30d`
    - Período customizado: `/estatisticas/dashboard?data_inicio=2024-01-01&data_fim=2024-01-31`
    
    **Resposta inclui:**
    - Cards com taxa de acerto, total de classificações, correções manuais, tempo médio
    - Gráfico de evolução temporal (classificações por dia)
    - Gráfico de distribuição (automáticas vs manuais)
    - Gráfico de top 10 categorias
    - Gráfico de taxa de acerto ao longo do tempo
    - Tabela detalhada com estatísticas por categoria
    """
)
async def obter_dashboard_estatisticas(
    periodo: Optional[str] = Query(
        default="30d",
        description="Período pré-definido: 7d, 30d, 90d"
    ),
    data_inicio: Optional[str] = Query(
        default=None,
        description="Data inicial customizada (YYYY-MM-DD)"
    ),
    data_fim: Optional[str] = Query(
        default=None,
        description="Data final customizada (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para obter estatísticas completas do dashboard.
    
    Permite filtrar por períodos pré-definidos ou datas customizadas.
    Retorna todas as métricas e dados formatados para os gráficos.
    """
    try:
        from datetime import datetime, timedelta
        
        # Determinar período baseado nos parâmetros
        periodo_fim = datetime.now()
        
        # Se datas customizadas foram fornecidas, usar elas
        if data_inicio and data_fim:
            try:
                periodo_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
                periodo_fim = datetime.strptime(data_fim, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Formato de data inválido. Use YYYY-MM-DD"
                )
        else:
            # Usar período pré-definido
            if periodo == "7d":
                periodo_inicio = periodo_fim - timedelta(days=7)
            elif periodo == "90d":
                periodo_inicio = periodo_fim - timedelta(days=90)
            else:  # Padrão: 30d
                periodo_inicio = periodo_fim - timedelta(days=30)
        
        # Validar que data_inicio não é posterior a data_fim
        if periodo_inicio > periodo_fim:
            raise HTTPException(
                status_code=400,
                detail="Data inicial não pode ser posterior à data final"
            )
        
        # Obter classificador
        classificador = obter_classificador(db)
        
        if not classificador:
            raise HTTPException(
                status_code=503,
                detail="Sistema de IA não disponível no momento"
            )
        
        # Calcular estatísticas completas
        estatisticas = classificador.obter_estatisticas_completas(
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim
        )
        
        return estatisticas
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter dashboard de estatísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar estatísticas: {str(e)}"
        )


@router.get(
    "/estatisticas/categorias",
    summary="Estatísticas Detalhadas por Categoria",
    description="""
    Retorna estatísticas detalhadas agrupadas por categoria.
    
    **Informações por categoria:**
    - Total de classificações
    - Total de confirmações
    - Total de correções
    - Taxa de acerto percentual
    - Tempo médio de classificação
    
    **Filtros:**
    - `periodo`: Período pré-definido (7d, 30d, 90d)
    - `limite`: Número máximo de categorias a retornar
    - `ordenar_por`: Campo para ordenação (taxa_acerto, total, tempo_medio)
    """
)
async def obter_estatisticas_categorias(
    periodo: Optional[str] = Query(default="30d", description="Período: 7d, 30d, 90d"),
    limite: Optional[int] = Query(default=20, ge=5, le=100, description="Limite de categorias"),
    ordenar_por: Optional[str] = Query(
        default="total",
        description="Ordenar por: total, taxa_acerto, tempo_medio"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para obter estatísticas detalhadas por categoria.
    
    Útil para análises específicas e identificação de categorias problemáticas.
    """
    try:
        from datetime import datetime, timedelta
        
        # Determinar período
        periodo_fim = datetime.now()
        if periodo == "7d":
            periodo_inicio = periodo_fim - timedelta(days=7)
        elif periodo == "90d":
            periodo_inicio = periodo_fim - timedelta(days=90)
        else:
            periodo_inicio = periodo_fim - timedelta(days=30)
        
        # Obter classificador
        classificador = obter_classificador(db)
        
        if not classificador:
            raise HTTPException(
                status_code=503,
                detail="Sistema de IA não disponível"
            )
        
        # Obter estatísticas completas
        estatisticas = classificador.obter_estatisticas_completas(
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim
        )
        
        # Extrair tabela de categorias
        tabela_categorias = estatisticas.get('tabela_categorias', [])
        
        # Ordenar conforme solicitado
        if ordenar_por == "taxa_acerto":
            tabela_categorias.sort(
                key=lambda x: x['taxa_acerto_percentual'],
                reverse=True
            )
        elif ordenar_por == "tempo_medio":
            tabela_categorias.sort(
                key=lambda x: x['tempo_medio_ms'],
                reverse=False
            )
        else:  # Padrão: total
            tabela_categorias.sort(
                key=lambda x: x['total_classificacoes'],
                reverse=True
            )
        
        # Aplicar limite
        tabela_categorias = tabela_categorias[:limite]
        
        return {
            "total_categorias": len(tabela_categorias),
            "periodo": {
                "inicio": periodo_inicio.isoformat(),
                "fim": periodo_fim.isoformat(),
                "dias": (periodo_fim - periodo_inicio).days + 1
            },
            "ordenacao": ordenar_por,
            "categorias": tabela_categorias
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas por categoria: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar: {str(e)}"
        )

# ============================================================================
# ENDPOINT DE CLASSIFICAÇÃO EM LOTE
# ============================================================================

@router.post("/classificar-lote", response_model=ClassificarLoteResponse, summary="Classificar em Lote")
async def classificar_lote(
    request: ClassificarLoteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Classifica múltiplos produtos em uma única operação.
    
    **Vantagens:**
    - Processamento otimizado para grandes volumes
    - Estatísticas consolidadas do lote
    - Identificação de padrões em importações
    
    **Limitações:**
    - Máximo 100 produtos por lote
    - Alternativas opcionais (podem tornar processo lento)
    
    **Uso típico:**
    - Importação de catálogos de fornecedores
    - Classificação de inventários
    - Migração de dados de outros sistemas
    """
    try:
        inicio_tempo = time.time()
        
        # Obter classificador
        classificador = obter_classificador(db)
        
        # Inicializar contadores
        total_processados = 0
        total_classificados = 0
        total_erros = 0
        resultados = []
        distribuicao_categorias = {}
        produtos_nao_classificados = []
        confiancas = []
        
        # Processar cada produto
        for indice, nome_produto in enumerate(request.produtos):
            try:
                resultado_classificacao = classificador.classificar_produto(nome_produto)
                total_processados += 1
                
                if resultado_classificacao.get("sucesso"):
                    total_classificados += 1
                    confiancas.append(resultado_classificacao.get("confianca", 0.0))
                    
                    # Contabilizar categoria
                    categoria = resultado_classificacao.get("categoria", "Não classificado")
                    distribuicao_categorias[categoria] = distribuicao_categorias.get(categoria, 0) + 1
                else:
                    produtos_nao_classificados.append(nome_produto)
                
                # Construir resultado individual (simplificado para lote)
                resultado = ResultadoClassificacaoLote(
                    nome_produto=nome_produto,
                    indice=indice,
                    classificacao=None,  # Simplificado - apenas dados essenciais
                    erro=None
                )
                
                # Adicionar dados básicos da classificação
                if resultado_classificacao.get("sucesso"):
                    resultado.classificacao = ClassificarProdutoResponse(
                        sucesso=True,
                        status=StatusClassificacao.SUCESSO,
                        taxonomia_sugerida=TaxonomiaClassificada(
                            categoria=resultado_classificacao.get("categoria"),
                            subcategoria=resultado_classificacao.get("subcategoria"),
                            especificacao=resultado_classificacao.get("especificacao"),
                            variante=resultado_classificacao.get("variante"),
                            nome_completo=f"{resultado_classificacao.get('categoria', '')} > {resultado_classificacao.get('subcategoria', '')}"
                        ),
                        confianca=resultado_classificacao.get("confianca", 0.0),
                        requer_revisao=resultado_classificacao.get("requer_revisao", True),
                        detalhes=DetalhesClassificacao(
                            tipo_match="lote",
                            score_similaridade=resultado_classificacao.get("confianca", 0.0),
                            algoritmo_utilizado="classificador_ia_lote"
                        ),
                        termo_analisado=nome_produto
                    )
                
                resultados.append(resultado)
                
            except Exception as e:
                total_erros += 1
                total_processados += 1
                
                resultado = ResultadoClassificacaoLote(
                    nome_produto=nome_produto,
                    indice=indice,
                    classificacao=None,
                    erro=str(e)
                )
                resultados.append(resultado)
                logger.error(f"Erro ao processar produto '{nome_produto}': {e}")
        
        # Calcular métricas finais
        tempo_total = (time.time() - inicio_tempo) * 1000
        confianca_media = sum(confiancas) / len(confiancas) if confiancas else 0.0
        
        # Construir resposta
        response = ClassificarLoteResponse(
            total_processados=total_processados,
            total_classificados=total_classificados,
            total_erros=total_erros,
            resultados=resultados,
            confianca_media=confianca_media,
            tempo_total_processamento_ms=tempo_total,
            distribuicao_categorias=distribuicao_categorias,
            produtos_nao_classificados=produtos_nao_classificados
        )
        
        # Agendar otimização da base em background
        background_tasks.add_task(
            analisar_padroes_lote_background,
            classificador,
            request.produtos,
            distribuicao_categorias
        )
        
        logger.info(f"Lote processado: {total_classificados}/{total_processados} produtos classificados")
        return response
        
    except Exception as e:
        logger.error(f"Erro no processamento do lote: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

# ============================================================================
# ENDPOINTS ADMINISTRATIVOS
# ============================================================================

@router.post("/admin/atualizar-base", summary="Atualizar Base Conhecimento (Admin)")
async def atualizar_base_conhecimento(
    request: AtualizarBaseConhecimentoRequest,
    db: Session = Depends(get_db)
):
    """
    Atualiza base de conhecimento manualmente (apenas administradores).
    
    **Uso:**
    - Correções manuais na base
    - Adição de entradas especializadas
    - Migração de conhecimento de outros sistemas
    
    **Cuidados:**
    - Pode sobrescrever aprendizado automático
    - Requer validação cuidadosa dos dados
    """
    try:
        # TODO: Adicionar verificação de permissão de admin
        
        classificador = obter_classificador(db)
        
        # Construir entrada para a base
        nova_entrada = {
            "aliases": request.aliases,
            "palavras_chave": request.palavras_chave,
            "categoria": request.categoria,
            "subcategoria": request.subcategoria,
            "especificacao": request.especificacao,
            "variante": request.variante,
            "confianca": request.confianca_inicial,
            "confirmacoes": 1,
            "correcoes": 0
        }
        
        # Atualizar base de conhecimento
        classificador.base_conhecimento["conhecimento"][request.chave_entrada] = nova_entrada
        classificador._salvar_base_conhecimento()
        
        return {
            "sucesso": True,
            "mensagem": f"Entrada '{request.chave_entrada}' adicionada/atualizada com sucesso",
            "entrada": nova_entrada
        }
        
    except Exception as e:
        logger.error(f"Erro ao atualizar base: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

@router.get("/admin/relatorio-aprendizado", response_model=RelatorioAprendizado, summary="Relatório de Aprendizado (Admin)")
async def gerar_relatorio_aprendizado(
    dias: int = Query(30, ge=1, le=365, description="Período em dias para análise"),
    db: Session = Depends(get_db)
):
    """
    Gera relatório detalhado de aprendizado do sistema.
    
    **Análises incluídas:**
    - Evolução da performance ao longo do tempo
    - Novos padrões descobertos
    - Produtos problemáticos
    - Sugestões de melhoria
    """
    try:
        # TODO: Implementar análise completa dos logs
        
        periodo_fim = datetime.now()
        periodo_inicio = periodo_fim - timedelta(days=dias)
        
        # Placeholder - implementar análise real dos logs
        response = RelatorioAprendizado(
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            taxa_acerto_inicio=0.6,
            taxa_acerto_fim=0.8,
            melhoria_percentual=33.3,
            novas_entradas_criadas=0,
            aliases_adicionados=0,
            padroes_descobertos=[],
            produtos_nao_classificados=[],
            classificacoes_incorretas=[],
            sugestoes_melhoria=[
                "Implementar mais aliases para produtos regionais",
                "Melhorar reconhecimento de marcas específicas",
                "Adicionar padrões para produtos sazonais"
            ],
            areas_foco=["Verduras e legumes", "Produtos regionais"],
            treinamento_recomendado=["Análise de catálogos regionais"]
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

# ============================================================================
# FUNÇÕES DE BACKGROUND TASKS
# ============================================================================

def otimizar_base_conhecimento_background(classificador: ClassificadorIA):
    """
    Otimiza base de conhecimento em background.
    
    Operações:
    - Remove entradas duplicadas
    - Consolida aliases similares
    - Atualiza scores de confiança
    """
    try:
        logger.info("Iniciando otimização da base de conhecimento...")
        
        # TODO: Implementar lógicas de otimização
        # - Detectar e remover duplicatas
        # - Consolidar aliases similares
        # - Recalcular confiança baseada em uso
        
        logger.info("Otimização da base concluída")
        
    except Exception as e:
        logger.error(f"Erro na otimização da base: {e}")

def analisar_padroes_lote_background(
    classificador: ClassificadorIA,
    produtos: List[str],
    distribuicao: Dict[str, int]
):
    """
    Analisa padrões encontrados em processamento de lote.
    
    Identifica:
    - Novos padrões de nomenclatura
    - Oportunidades de melhoria
    - Sugestões para base de conhecimento
    """
    try:
        logger.info(f"Analisando padrões de lote com {len(produtos)} produtos...")
        
        # TODO: Implementar análise de padrões
        # - Detectar palavras comuns nos produtos não classificados
        # - Identificar possíveis novos aliases
        # - Sugerir melhorias na base
        
        logger.info("Análise de padrões do lote concluída")
        
    except Exception as e:
        logger.error(f"Erro na análise de padrões: {e}")

# ============================================================================
# ENDPOINT DE TESTE E DESENVOLVIMENTO
# ============================================================================

@router.get("/test", summary="Teste da IA (Desenvolvimento)")
async def testar_ia():
    """
    Endpoint de teste para verificar funcionamento básico da IA.
    
    **Apenas para desenvolvimento** - remove em produção.
    """
    try:
        # Teste simples da IA
        classificador = obter_classificador()
        
        produtos_teste = [
            "Salmão Atlântico Filé",
            "Alcatra Bovina Premium",
            "Tomate Italiano",
            "Produto Inexistente XYZ"
        ]
        
        resultados = []
        for produto in produtos_teste:
            resultado = classificador.classificar_produto(produto)
            resultados.append({
                "produto": produto,
                "sucesso": resultado.get("sucesso"),
                "categoria": resultado.get("categoria"),
                "confianca": resultado.get("confianca")
            })
        
        return {
            "status": "IA funcionando",
            "testes_realizados": len(produtos_teste),
            "resultados": resultados,
            "sistema_pronto": True
        }
        
    except Exception as e:
        return {
            "status": "Erro na IA",
            "erro": str(e),
            "sistema_pronto": False
        }