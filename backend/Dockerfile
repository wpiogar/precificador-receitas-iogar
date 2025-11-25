# ============================================================================
# DOCKERFILE - BACKEND FOOD COST SYSTEM
# ============================================================================
# Descrição: Container Python com FastAPI e Sistema de IA
# Base: Python 3.11-slim
# Data: 25/11/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

# ============================================================================
# STAGE 1: BASE
# ============================================================================
FROM python:3.11-slim as base

# Variáveis de ambiente para Python (otimizações)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho
WORKDIR /app

# ============================================================================
# STAGE 2: DEPENDÊNCIAS DO SISTEMA
# ============================================================================
# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ============================================================================
# STAGE 3: DEPENDÊNCIAS PYTHON
# ============================================================================
# Copiar apenas arquivos de dependências primeiro (para cache do Docker)
COPY requirements.txt ./

# Copiar requirements-ia.txt se existir
COPY requirements-ia.txt* ./

# Instalar dependências Python principais
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Instalar dependências de IA (se arquivo existir)
RUN if [ -f requirements-ia.txt ]; then \
        pip install --no-cache-dir -r requirements-ia.txt; \
    fi

# Baixar modelo português do spaCy para classificação de ingredientes
RUN python -m spacy download pt_core_news_sm || \
    echo "Aviso: Não foi possível baixar modelo spaCy"

# ============================================================================
# STAGE 4: CÓDIGO DA APLICAÇÃO
# ============================================================================
# Copiar código da aplicação
COPY . .

# ============================================================================
# STAGE 5: CONFIGURAÇÃO DE PERMISSÕES E USUÁRIO
# ============================================================================
# Criar estrutura de diretórios para sistema de IA
RUN mkdir -p /app/app/ai/data \
             /app/app/ai/logs \
             /app/app/ai/models && \
    chmod -R 755 /app/app/ai

# Executar setup automático do sistema de IA (se existir)
RUN if [ -f setup_ia.py ]; then \
        python setup_ia.py --docker-mode --auto || \
        echo "Aviso: Setup IA não executado completamente"; \
    fi

# Criar usuário não-root para segurança
RUN groupadd -r foodcost && \
    useradd -r -g foodcost -s /bin/bash foodcost

# Definir permissões corretas
RUN chown -R foodcost:foodcost /app && \
    chmod -R 755 /app/app/ai

# Mudar para usuário não-root
USER foodcost

# ============================================================================
# STAGE 6: CONFIGURAÇÃO FINAL
# ============================================================================
# Expor porta padrão do FastAPI
EXPOSE 8000

# Health check para monitoramento (ajustado para endpoint correto)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Comando de inicialização
# Produção: usar --workers baseado em CPU cores
# Desenvolvimento: usar --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================================================
# NOTAS DE USO
# ============================================================================
# Build: docker build -t foodcost-backend .
# Run: docker run -p 8000:8000 --env-file .env foodcost-backend
# 
# Para desenvolvimento com hot-reload:
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
#
# Para produção com múltiplos workers:
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
# ============================================================================