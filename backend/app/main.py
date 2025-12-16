#   ===================================================================================================
#   Aplicação Principal FastAPI
#   Descrição: Este é o arquivo principal que configura e inicia a aplicação FastAPI
#   com todas as rotas de insumos e receitas
#   Data: 15/08/2025
#   Autor: Will - Empresa: IOGAR
#   ===================================================================================================

# Imports principais do FastAPI e configurações
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

import logging
import sys

# Configurar logging para exibir no console (stdout)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Logger para o módulo principal
logger = logging.getLogger(__name__)
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Imports dos routers/endpoints das APIs
try:
    from app.api.endpoints import insumos, receitas, fornecedores, taxonomias, ia, importacoes

     # Importar endpoint de autenticação
    try:
        from app.api.endpoints import auth
        HAS_AUTH = True
        print("[OK] Módulo auth importado com sucesso")
    except ImportError as e:
        print(f"⚠️  Módulo auth não encontrado: {e}")
        HAS_AUTH = False

    # Importar endpoint de gerenciamento de usuários (ADMIN)
    try:
        from app.api.endpoints import users
        HAS_USERS = True
        print("[OK] Módulo users importado com sucesso")
    except ImportError as e:
        print(f"❌ ERRO CRÍTICO: Módulo users não encontrado: {e}")
        print(f"   Traceback completo:")
        import traceback
        traceback.print_exc()
        HAS_USERS = False
    except Exception as e:
        print(f"❌ ERRO CRÍTICO ao importar users: {type(e).__name__}: {e}")
        print(f"   Traceback completo:")
        import traceback
        traceback.print_exc()
        HAS_USERS = False

    # Importar endpoint de limpeza de dados (ADMIN)
    try:
        from app.api.endpoints import limpeza_dados
        HAS_LIMPEZA_DADOS = True
        print("[OK] Módulo limpeza_dados importado com sucesso")
    except ImportError as e:
        print(f"⚠️  Módulo limpeza_dados não encontrado: {e}")
        HAS_LIMPEZA_DADOS = False
    
    # Importar endpoints de restaurantes
    try:
        from app.api.endpoints import restaurantes
        HAS_RESTAURANTES = True
        print("[OK] Modulo restaurantes importado com sucesso")
    except ImportError as e:
        print(f"⚠️  Módulo restaurantes não encontrado: {e}")
        HAS_RESTAURANTES = False
    
    # Tentar importar o módulo fornecedor_insumos
    try:
        from app.api.endpoints import fornecedor_insumos
        HAS_FORNECEDOR_INSUMOS = True
    except ImportError:
        print("⚠️  Módulo fornecedor_insumos não encontrado, pulando...")
        HAS_FORNECEDOR_INSUMOS = False

    # Tentar importar o módulo importacoes
    try:
        from app.api.endpoints import importacoes
        HAS_IMPORTACOES = True
        print("[OK] Módulo importacoes importado com sucesso")
    except ImportError as e:
        print(f"⚠️  Módulo importacoes não encontrado: {e}")
        HAS_IMPORTACOES = False
    
    # Tentar importar o módulo taxonomia_aliases
    try:
        from app.api.endpoints import taxonomia_aliases
        HAS_TAXONOMIA_ALIASES = True
        print("[OK] Módulo taxonomia_aliases importado com sucesso")
    except ImportError as e:
        print(f"⚠️  Módulo taxonomia_aliases não encontrado: {e}")
        HAS_TAXONOMIA_ALIASES = False

    # Tentar importar o módulo codigos
    try:
        from app.api.endpoints import codigos
        HAS_CODIGOS = True
        print("[OK] Módulo codigos importado com sucesso")
    except ImportError as e:
        print(f"⚠️  Módulo codigos não encontrado: {e}")
        HAS_CODIGOS = False

    # Tentar importar o módulo importacoes
    try:
        from app.api.endpoints import importacoes
        HAS_IMPORTACOES = True
        print("[OK] Módulo importacoes importado com sucesso")
    except ImportError as e:
        print(f"⚠️  Módulo importacoes não encontrado: {e}")
        HAS_IMPORTACOES = False

    # Tentar importar o módulo importacao_receitas
    try:
        from app.api.endpoints import importacao_receitas
        HAS_IMPORTACAO_RECEITAS = True
        print("[OK] Módulo importacao_receitas importado com sucesso")
    except ImportError as e:
        print(f"⚠️  Módulo importacao_receitas não encontrado: {e}")
        HAS_IMPORTACAO_RECEITAS = False
        
except ImportError as e:
    print(f"❌ Erro ao importar endpoints: {e}")
    raise


# Imports para configuração do banco de dados
from app.database import engine
from app.models.base import Base

# ============================================================================
# IMPORTAÇÕES DOS MODELOS (para registrar no SQLAlchemy)
# ============================================================================
from app.models import taxonomia, taxonomia_alias, insumo, fornecedor, fornecedor_insumo, receita

# Imports para variáveis de ambiente
from app.core.config import settings
import os
import time
from datetime import datetime

# ============================================================================
# TRATAMENTO DE SINAIS E SHUTDOWN GRACIOSOS
# ============================================================================
import signal
import sys

# ============================================================================
# FORÇAR MIGRAÇÃO AUTOMÁTICA NO STAGING (Render Free Tier)
# ============================================================================
import os
from pathlib import Path

# ============================================================================
# VERIFICAÇÃO DE DEPENDÊNCIAS CRÍTICAS
# ============================================================================
def verificar_dependencias_criticas():
    """
    Verifica se todas as dependências críticas estão instaladas.
    Emite avisos se alguma dependência estiver faltando.
    
    Dependências verificadas:
    - pandas: Necessário para importação de Excel
    - openpyxl: Necessário para leitura de arquivos .xlsx
    - numpy: Necessário para cálculos numéricos do pandas
    """
    dependencias_faltando = []
    avisos = []
    
    # Verificar pandas
    try:
        import pandas as pd
        print(f"✅ pandas {pd.__version__} instalado")
    except ImportError:
        dependencias_faltando.append("pandas")
        avisos.append("❌ pandas NÃO encontrado - Importação de Excel NÃO funcionará!")
    
    # Verificar openpyxl
    try:
        import openpyxl
        print(f"✅ openpyxl {openpyxl.__version__} instalado")
    except ImportError:
        dependencias_faltando.append("openpyxl")
        avisos.append("❌ openpyxl NÃO encontrado - Leitura de arquivos .xlsx NÃO funcionará!")
    
    # Verificar numpy
    try:
        import numpy as np
        print(f"✅ numpy {np.__version__} instalado")
    except ImportError:
        dependencias_faltando.append("numpy")
        avisos.append("❌ numpy NÃO encontrado - Cálculos numéricos podem falhar!")
    
    # Emitir avisos se houver dependências faltando
    if dependencias_faltando:
        print("\n" + "=" * 80)
        print("⚠️  AVISO: DEPENDÊNCIAS CRÍTICAS FALTANDO")
        print("=" * 80)
        for aviso in avisos:
            print(aviso)
        print("\n💡 Para corrigir, execute:")
        print(f"   pip install {' '.join(dependencias_faltando)}")
        print("=" * 80 + "\n")
        
        # Em produção, isso é CRÍTICO
        if os.getenv("ENVIRONMENT") in ["staging", "production"]:
            print("🚨 AMBIENTE DE PRODUÇÃO: Dependências faltando podem causar falhas!")
            print("🚨 Recomenda-se rebuild completo no Render")
    else:
        print("✅ Todas as dependências críticas estão instaladas\n")
    
    return len(dependencias_faltando) == 0

# Executar verificação de dependências no startup
print("=" * 80)
print("🔍 VERIFICANDO DEPENDÊNCIAS CRÍTICAS")
print("=" * 80)
verificar_dependencias_criticas()

def run_migrations_on_startup():
    """
    Executa migrações e adiciona coluna fator se não existir.
    """
    try:
        print("=" * 80)
        print("🚀 VERIFICANDO SCHEMA DO BANCO")
        print("=" * 80)
        
        from sqlalchemy import text
        from app.database import engine
        
        # Verificar e adicionar coluna fator se não existir
        with engine.connect() as conn:
            # Verificar se coluna existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='insumos' AND column_name='fator'
            """))
            
            if result.fetchone() is None:
                print("⚠️  Coluna 'fator' não encontrada, criando...")
                conn.execute(text("""
                    ALTER TABLE insumos 
                    ADD COLUMN fator FLOAT DEFAULT 1.0
                """))
                conn.commit()
                print("✅ Coluna 'fator' criada com sucesso!")
            else:
                print("✅ Coluna 'fator' já existe")
        
        print("=" * 80)
        
        # Executar migrações normais do Alembic
        from alembic.config import Config
        from alembic import command
        from pathlib import Path
        
        alembic_ini = Path(__file__).parent.parent / "alembic.ini"
        
        if alembic_ini.exists():
            print("🔄 Executando migrações do Alembic...")
            alembic_cfg = Config(str(alembic_ini))
            alembic_cfg.set_main_option("script_location", str(Path(__file__).parent.parent / "alembic"))
            command.upgrade(alembic_cfg, "heads")
            print("✅ Migrações concluídas!")
        
        print("=" * 80)
            
    except Exception as e:
        print("=" * 80)
        print(f"❌ ERRO: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()

# Executar migrações apenas em staging/produção
if os.getenv("ENVIRONMENT") in ["staging", "production"]:
    run_migrations_on_startup()

#   ===================================================================================================
#   Configuração do ciclo de vida da aplicação
#   ===================================================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação FastAPI.
    Executa tarefas na inicialização e finalização.
    """

    # Log de inicializacao
    logger.info("=" * 80)
    logger.info("FOOD COST API INICIANDO")
    logger.info("Logging configurado e ativo")
    logger.info("=" * 80)
    # Startup: Criar tabelas no banco se não existirem
    print("🚀 Iniciando Food Cost System...")
    try:
        # Cria todas as tabelas definidas nos modelos
        Base.metadata.create_all(bind=engine)
        print("[OK] Tabelas do banco de dados verificadas/criadas")
    except Exception as e:
        print(f"❌ Erro ao conectar com o banco: {e}")
    
    # Informações úteis para o desenvolvedor
    print("🔐 Autenticação: http://localhost:8000/api/v1/auth/login")
    print("👥 Gerenciar Usuários: http://localhost:8000/api/v1/users")
    print("🔍 CRUD Insumos: http://localhost:8000/api/v1/insumos")
    print("🔍 CRUD Receitas: http://localhost:8000/api/v1/receitas")
    print("🏪 CRUD Restaurantes: http://localhost:8000/api/v1/restaurantes")
    print("📖 Documentação: http://localhost:8000/docs")
    print("🔄 ReDoc: http://localhost:8000/redoc")
    
    yield  # Aplicação roda aqui
    
    # Shutdown: Limpeza se necessário
    print("🛑 Finalizando Food Cost System...")

# ============================================================================
# INICIALIZAÇÃO DA APLICAÇÃO FASTAPI
# ============================================================================

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    **Sistema de Controle de Custos para Restaurantes**
    
    Esta API permite:
    - 📦 Gerenciar insumos (ingredientes, matérias-primas)
    - 🍕 Criar e calcular custos de receitas
    - 🏪 Organizar por restaurantes
    - 💰 Calcular automaticamente CMV e preços sugeridos
    - 🔍 Buscar e filtrar dados
    
    **Funcionalidades principais:**
    - CRUD completo de insumos e receitas
    - Cálculos automáticos de custos
    - Preços sugeridos baseados em margens
    - Sistema de variações de receitas
    - Relacionamento receitas ↔ insumos
    """,
    version=settings.VERSION,
    contact={
        "name": "Will - Food Cost System",
        "email": "will@foodcost.com",
    },
    license_info={
        "name": "MIT",
    },
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG,
    lifespan=lifespan
)

@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    """
    Handler explícito para requisições OPTIONS (preflight CORS)
    """
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )


# ===================================================================================================
# Configuração de CORS para permitir acesso do frontend
# ===================================================================================================
# Configuração do backend para produção
from fastapi.middleware.cors import CORSMiddleware
import os

# ============================================================================
# CONFIGURAÇÃO DE CORS - Desenvolvimento e Produção
# ============================================================================
# Configuração de CORS com suporte para rede local (mobile)
if os.getenv("ENVIRONMENT") == "production":
    # Produção - origens específicas incluindo staging
    allowed_origins = [
        "https://food-cost-frontend.onrender.com",
        "https://food-cost-frontend-staging.onrender.com",
    ]
    cors_extra = os.getenv("CORS_ORIGINS", "")
    if cors_extra:
        allowed_origins.extend([origin.strip() for origin in cors_extra.split(",") if origin.strip()])
else:
    # Desenvolvimento - permitir localhost e rede local
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://0.0.0.0:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
    
    # Adicionar automaticamente qualquer origem da rede local 192.168.x.x
    # Isso permite acesso de dispositivos móveis na mesma rede
    import socket
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        if local_ip.startswith('192.168'):
            allowed_origins.extend([
                f"http://{local_ip}:3000",
                f"http://{local_ip}:5173",
            ])
            print(f"📱 IP da rede local detectado: {local_ip}")
    except Exception as e:
        print(f"⚠️ Não foi possível detectar IP local: {e}")

# Log das origens permitidas para debug
print(f"🔒 CORS - Origens permitidas: {allowed_origins}")

# ============================================================================
# CONFIGURAÇÃO DE CORS - Suporte a múltiplos ambientes
# ============================================================================
# Em desenvolvimento: aceita localhost
# Em produção: aceita apenas domínios permitidos da variável ALLOWED_ORIGINS
# ============================================================================

import os

# Obter origens permitidas da variável de ambiente
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

# ============================================================================
# CONFIGURAÇÃO DE CORS - Suporte a múltiplos ambientes
# ============================================================================

from fastapi.middleware.cors import CORSMiddleware

# Adicionar middleware CORS usando configurações centralizadas
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Lista de origens do config.py
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
# ============================================================================
# DEBUG: Verificar origens CORS configuradas
# ============================================================================
print(f"🌐 CORS - Origens permitidas:")
for origin in settings.ALLOWED_ORIGINS:
    print(f"   ✓ {origin}")

# Log das origens permitidas para debug
print(f"🔒 CORS configurado com origens: {settings.ALLOWED_ORIGINS}")

@app.get("/test-cors", summary="Testar CORS")
def test_cors():
    """
    Endpoint simples para testar se CORS está funcionando
    """
    return {
        "message": "CORS está funcionando!",
        "headers_received": "Ok",
        "status": "success"
    }

# ===================================================================================================
# Endpoints básicos de status e saúde
# ===================================================================================================

@app.get("/", summary="Status da API")
def root():
    """
    Endpoint raiz que retorna o status da API.
    Útil para verificar se o serviço está rodando.
    """
    return {
        "message": "Food Cost System API",
        "status": "running",
        "version": "1.0.0",
        "docs": "http://localhost:8000/docs"
    }

@app.get("/health", summary="Health Check")
def health_check():
    """
    Endpoint de verificação de saúde do serviço.
    Útil para monitoramento e load balancers.
    """
    return {"status": "healthy", "service": "food-cost-api"}

@app.get("/test-db", summary="Testar conexão com banco")
def test_database():
    """
    Testa a conexão com o banco de dados PostgreSQL.
    Retorna status da conexão.
    """
    try:
        from app.database import engine
        from sqlalchemy import text

        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            # Verificar se a query retornou resultado
            row = result.fetchone()
            if row and row[0] == 1:
                return {"database": "connected", "status": "ok"}
            else:
                return {"database": "error", "status": "failed", "error": "Query não retornou resultado esperado"}

    except Exception as e:
        return {"database": "error", "status": "failed", "error": str(e)}


@app.get("/debug-tables", summary="Debug - Verificar tabelas")
def debug_tables():
    """
    Endpoint temporário para verificar quais tabelas existem no banco
    """
    try:
        from app.database import engine
        from sqlalchemy import text, inspect

        inspector = inspect(engine)
        tabelas = inspector.get_table_names()

        # Verificar se tabela restaurantes existe
        tem_restaurantes = 'restaurantes' in tabelas

        # Se existir, verificar colunas
        colunas_restaurantes = []
        if tem_restaurantes:
            colunas_restaurantes = [col['name'] for col in inspector.get_columns('restaurantes')]

        return {
            "todas_tabelas": sorted(tabelas),
            "tem_tabela_restaurantes": tem_restaurantes,
            "colunas_restaurantes": sorted(colunas_restaurantes) if colunas_restaurantes else [],
            "total_tabelas": len(tabelas),
            "ambiente": "casa",
            "status": "ok"
        }

    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

@app.get("/debug-insumos", summary="Debug - Verificar tabela insumos")
def debug_insumos():
    """
    Endpoint para verificar colunas da tabela insumos
    """
    try:
        from app.database import engine
        from sqlalchemy import inspect

        inspector = inspect(engine)

        # Verificar se tabela insumos existe
        tem_insumos = 'insumos' in inspector.get_table_names()

        # Se existir, verificar colunas
        colunas_insumos = []
        if tem_insumos:
            colunas_insumos = [col['name'] for col in inspector.get_columns('insumos')]

        return {
            "tem_tabela_insumos": tem_insumos,
            "colunas_insumos": sorted(colunas_insumos) if colunas_insumos else [],
            "total_colunas": len(colunas_insumos),
            "status": "ok"
        }

    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

@app.get("/debug-completo", summary="Debug completo do sistema")
def debug_completo():
    """
    Diagnóstico completo para identificar o problema
    """
    try:
        from app.database import engine
        from sqlalchemy import text, inspect
        import sqlalchemy

        resultados = {
            "sqlalchemy_version": sqlalchemy.__version__,
            "python_version": "",
            "conexao_banco": "ok",
            "teste_query_insumos": "",
            "teste_query_fornecedores": "",
            "erro_detalhado": ""
        }

        # Versão Python
        import sys
        resultados["python_version"] = sys.version

        # Teste conexão e query direta
        with engine.connect() as connection:

            # Teste 1: Query simples na tabela insumos
            try:
                result = connection.execute(text("SELECT COUNT(*) FROM insumos"))
                count = result.fetchone()[0]
                resultados["teste_query_insumos"] = f"OK - {count} registros"
            except Exception as e:
                resultados["teste_query_insumos"] = f"ERRO: {str(e)}"

            # Teste 2: Query com as colunas problemáticas
            try:
                result = connection.execute(text(
                    "SELECT id, nome, fornecedor_insumo_id, eh_fornecedor_anonimo FROM insumos LIMIT 1"
                ))
                row = result.fetchone()
                resultados["teste_query_colunas_novas"] = f"OK - Row: {dict(row) if row else 'Sem dados'}"
            except Exception as e:
                resultados["teste_query_colunas_novas"] = f"ERRO: {str(e)}"

            # Teste 3: Query na tabela fornecedores
            try:
                result = connection.execute(text("SELECT COUNT(*) FROM fornecedores"))
                count = result.fetchone()[0]
                resultados["teste_query_fornecedores"] = f"OK - {count} registros"
            except Exception as e:
                resultados["teste_query_fornecedores"] = f"ERRO: {str(e)}"

        # Teste 4: Importar o modelo e ver se há conflito
        try:
            from app.models.insumo import Insumo
            from app.crud.insumo import get_insumos
            resultados["import_modelo"] = "OK - Modelo importado"
        except Exception as e:
            resultados["import_modelo"] = f"ERRO: {str(e)}"
            resultados["erro_detalhado"] = str(e)

        return resultados

    except Exception as e:
        return {
            "erro_geral": str(e),
            "status": "failed"
        }

@app.get("/fix-all-tables", summary="Corrigir todas as tabelas")
def fix_all_tables():
    """
    Adiciona todas as colunas faltantes nas tabelas do sistema
    """
    try:
        from app.database import engine
        from sqlalchemy import text

        resultados = []

        with engine.connect() as connection:

            # ============================================================================
            # CORRIGIR TABELA FORNECEDORES
            # ============================================================================
            comandos_fornecedores = [
                "ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS cpf_cnpj VARCHAR(20)",
                "ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS ramo VARCHAR(100)",
                "ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS cidade VARCHAR(100)",
                "ALTER TABLE fornecedores ADD COLUMN IF NOT EXISTS estado VARCHAR(2)"
            ]

            for comando in comandos_fornecedores:
                try:
                    connection.execute(text(comando))
                    resultados.append(f"[OK] FORNECEDORES: {comando}")
                except Exception as e:
                    resultados.append(f"❌ FORNECEDORES: {comando} - Erro: {str(e)}")

            # ============================================================================
            # CORRIGIR TABELA RESTAURANTES
            # ============================================================================
            comandos_restaurantes = [
                "ALTER TABLE restaurantes ADD COLUMN IF NOT EXISTS bairro VARCHAR(100)",
                "ALTER TABLE restaurantes ADD COLUMN IF NOT EXISTS cidade VARCHAR(100)",
                "ALTER TABLE restaurantes ADD COLUMN IF NOT EXISTS estado VARCHAR(2)",
                "ALTER TABLE restaurantes ADD COLUMN IF NOT EXISTS tipo VARCHAR(50) DEFAULT 'restaurante'",
                "ALTER TABLE restaurantes ADD COLUMN IF NOT EXISTS tem_delivery BOOLEAN DEFAULT false",
                "ALTER TABLE restaurantes ADD COLUMN IF NOT EXISTS eh_matriz BOOLEAN DEFAULT true",
                "ALTER TABLE restaurantes ADD COLUMN IF NOT EXISTS restaurante_pai_id INTEGER REFERENCES restaurantes(id)"
            ]

            # ============================================================================
            # CORRIGIR TABELA FORNECEDOR_INSUMOS
            # ============================================================================
            comandos_fornecedor_insumos = [
                "ALTER TABLE fornecedor_insumos ADD COLUMN IF NOT EXISTS quantidade DECIMAL(10,3) DEFAULT 1.0",
                "ALTER TABLE fornecedor_insumos ADD COLUMN IF NOT EXISTS fator DECIMAL(10,3) DEFAULT 1.0"
            ]

            for comando in comandos_fornecedor_insumos:
                try:
                    connection.execute(text(comando))
                    resultados.append(f"✅ FORNECEDOR_INSUMOS: {comando}")
                except Exception as e:
                    resultados.append(f"❌ FORNECEDOR_INSUMOS: {comando} - Erro: {str(e)}")

            for comando in comandos_restaurantes:
                try:
                    connection.execute(text(comando))
                    resultados.append(f"✅ RESTAURANTES: {comando}")
                except Exception as e:
                    resultados.append(f"❌ RESTAURANTES: {comando} - Erro: {str(e)}")

            # ============================================================================
            # CORRIGIR TABELA INSUMOS
            # ============================================================================
            comandos_insumos = [
                "ALTER TABLE insumos ADD COLUMN IF NOT EXISTS fornecedor_insumo_id INTEGER REFERENCES fornecedor_insumos(id)",
                "ALTER TABLE insumos ADD COLUMN IF NOT EXISTS eh_fornecedor_anonimo BOOLEAN DEFAULT false",
                "ALTER TABLE insumos ADD COLUMN IF NOT EXISTS taxonomia_id INTEGER",
                "ALTER TABLE insumos ADD COLUMN IF NOT EXISTS aguardando_classificacao BOOLEAN DEFAULT false"
            ]

            for comando in comandos_insumos:
                try:
                    connection.execute(text(comando))
                    resultados.append(f"✅ INSUMOS: {comando}")
                except Exception as e:
                    resultados.append(f"❌ INSUMOS: {comando} - Erro: {str(e)}")

            # Commit todas as alterações
            connection.commit()

        return {
            "status": "completed",
            "comandos_executados": resultados,
            "message": "Estrutura de todas as tabelas corrigida",
            "total_comandos": len(resultados)
        }

    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

@app.get("/fix-fornecedores-null", summary="Corrigir fornecedores com CPF/CNPJ nulo")
def fix_fornecedores_null():
    """
    Corrige fornecedores com cpf_cnpj NULL
    """
    try:
        from app.database import engine
        from sqlalchemy import text

        with engine.connect() as connection:

            # Verificar fornecedores com campos NULL
            result = connection.execute(text("""
                SELECT id, nome_razao_social, cpf_cnpj, telefone, ramo, cidade, estado
                FROM fornecedores
                WHERE cpf_cnpj IS NULL OR cpf_cnpj = ''
            """))

            fornecedores_problema = result.fetchall()

            if fornecedores_problema:
                # Corrigir fornecedores com CPF/CNPJ NULL ou vazio
                for fornecedor in fornecedores_problema:
                    cpf_temporario = f"0000000000{fornecedor[0]}"  # Usar ID como base
                    connection.execute(text("""
                        UPDATE fornecedores
                        SET cpf_cnpj = :cpf_cnpj
                        WHERE id = :id
                    """), {"cpf_cnpj": cpf_temporario, "id": fornecedor[0]})

                connection.commit()

                return {
                    "status": "success",
                    "message": f"Corrigidos {len(fornecedores_problema)} fornecedores",
                    "fornecedores_corrigidos": [
                        {
                            "id": f[0],
                            "nome": f[1],
                            "cpf_cnpj_antigo": f[2],
                            "cpf_cnpj_novo": f"0000000000{f[0]}"
                        }
                        for f in fornecedores_problema
                    ]
                }
            else:
                return {
                    "status": "ok",
                    "message": "Nenhum fornecedor com problemas encontrado"
                }

    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }
    
@app.get("/emergency-clean-insumos/{restaurante_id}", summary="[EMERGÊNCIA] Limpar insumos de restaurante específico")
def emergency_clean_insumos(
    restaurante_id: int,
    confirm_token: str,
):
    """
    ENDPOINT EMERGENCIAL - Limpa TODOS os insumos de um restaurante específico
    
    ⚠️ ATENÇÃO: Esta ação é IRREVERSÍVEL!
    
    Parâmetros:
    - restaurante_id: ID do restaurante (ex: 23 para CALMA BAR)
    - confirm_token: Token de confirmação (use: "CONFIRMO_LIMPEZA_TOTAL")
    
    Uso:
    POST /emergency-clean-insumos/23?confirm_token=CONFIRMO_LIMPEZA_TOTAL
    """
    try:
        from app.database import engine
        from sqlalchemy import text
        
        # Validação de segurança
        if confirm_token != "CONFIRMO_LIMPEZA_TOTAL":
            return {
                "error": "Token de confirmação inválido",
                "status": "denied",
                "message": "Use confirm_token=CONFIRMO_LIMPEZA_TOTAL para confirmar"
            }
        
        # Verificar se restaurante existe
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT nome FROM restaurantes WHERE id = :id"),
                {"id": restaurante_id}
            )
            restaurante = result.fetchone()
            
            if not restaurante:
                return {
                    "error": f"Restaurante ID {restaurante_id} não encontrado",
                    "status": "not_found"
                }
            
            nome_restaurante = restaurante[0]
            
            # Contar insumos antes de deletar
            result = connection.execute(
                text("""
                    SELECT COUNT(*) 
                    FROM insumos 
                    WHERE restaurante_id = :restaurante_id
                """),
                {"restaurante_id": restaurante_id}
            )
            total_insumos = result.scalar()
            
            if total_insumos == 0:
                return {
                    "status": "already_clean",
                    "message": f"Restaurante '{nome_restaurante}' já está sem insumos",
                    "restaurante_id": restaurante_id,
                    "restaurante_nome": nome_restaurante
                }
            
            # DELETAR TODOS OS INSUMOS deste restaurante
            connection.execute(
                text("""
                    DELETE FROM insumos 
                    WHERE restaurante_id = :restaurante_id
                """),
                {"restaurante_id": restaurante_id}
            )
            
            connection.commit()
            
            # Verificar se foram deletados
            result = connection.execute(
                text("""
                    SELECT COUNT(*) 
                    FROM insumos 
                    WHERE restaurante_id = :restaurante_id
                """),
                {"restaurante_id": restaurante_id}
            )
            total_apos = result.scalar()
            
            return {
                "status": "success",
                "message": f"✅ Insumos limpos com sucesso",
                "restaurante_id": restaurante_id,
                "restaurante_nome": nome_restaurante,
                "insumos_deletados": total_insumos,
                "insumos_restantes": total_apos,
                "timestamp": datetime.now().isoformat()
            }
    
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }
    
@app.get("/debug-insumos-restaurante/{restaurante_id}", summary="[DEBUG] Ver insumos do restaurante")
def debug_insumos_restaurante(restaurante_id: int):
    """
    Endpoint para verificar quais insumos existem no restaurante
    """
    try:
        from app.database import engine
        from sqlalchemy import text
        
        with engine.connect() as connection:
            # Verificar restaurante
            result = connection.execute(
                text("SELECT nome FROM restaurantes WHERE id = :id"),
                {"id": restaurante_id}
            )
            restaurante = result.fetchone()
            
            if not restaurante:
                return {"error": f"Restaurante {restaurante_id} não encontrado"}
            
            # Buscar insumos
            result = connection.execute(
                text("""
                    SELECT id, codigo, nome, preco_compra, created_at
                    FROM insumos 
                    WHERE restaurante_id = :restaurante_id
                    ORDER BY codigo
                    LIMIT 50
                """),
                {"restaurante_id": restaurante_id}
            )
            
            insumos = []
            for row in result:
                insumos.append({
                    "id": row[0],
                    "codigo": row[1],
                    "nome": row[2],
                    "preco_compra": row[3],
                    "created_at": str(row[4]) if row[4] else None
                })
            
            # Contar total
            result = connection.execute(
                text("SELECT COUNT(*) FROM insumos WHERE restaurante_id = :restaurante_id"),
                {"restaurante_id": restaurante_id}
            )
            total = result.scalar()
            
            return {
                "restaurante_id": restaurante_id,
                "restaurante_nome": restaurante[0],
                "total_insumos": total,
                "primeiros_50": insumos,
                "timestamp": datetime.now().isoformat()
            }
    
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

@app.get("/fix-cpf-valido", summary="Corrigir fornecedor com CPF válido")
def fix_cpf_valido():
    """
    Atualiza o fornecedor com um CPF matematicamente válido
    """
    try:
        from app.database import engine
        from sqlalchemy import text

        # CPF válido para testes: 11144477735 (dígitos verificadores corretos)
        cpf_valido = "11144477735"

        with engine.connect() as connection:

            # Atualizar o fornecedor com CPF válido
            result = connection.execute(text("""
                UPDATE fornecedores
                SET cpf_cnpj = :cpf_cnpj
                WHERE id = 1
            """), {"cpf_cnpj": cpf_valido})

            connection.commit()

            # Verificar se foi atualizado
            verificacao = connection.execute(text("""
                SELECT id, nome_razao_social, cpf_cnpj
                FROM fornecedores
                WHERE id = 1
            """)).fetchone()

            return {
                "status": "success",
                "message": "CPF atualizado com sucesso",
                "fornecedor": {
                    "id": verificacao[0],
                    "nome": verificacao[1],
                    "cpf_cnpj": verificacao[2]
                }
            }

    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }
@app.get("/debug-fornecedor-422", summary="Debug erro 422 cadastro fornecedor")
def debug_fornecedor_422():
    """
    Simula um cadastro de fornecedor para identificar o erro 422
    """
    try:
        from app.schemas.fornecedor import FornecedorCreate

        # Dados de teste similares aos enviados pelo frontend
        dados_teste = {
            "nome_razao_social": "Teste Fornecedor",
            "cpf_cnpj": "02304307880",  # Mesmo CPF que deu erro
            "telefone": "11999999999",
            "ramo": "Alimenticio",
            "cidade": "São Paulo",
            "estado": "SP"
        }

        # Tentar validar com Pydantic
        try:
            fornecedor_schema = FornecedorCreate(**dados_teste)
            return {
                "status": "validation_success",
                "message": "Dados passaram na validação Pydantic",
                "dados_validados": fornecedor_schema.dict(),
                "cpf_cnpj_limpo": fornecedor_schema.cpf_cnpj
            }
        except Exception as validation_error:
            return {
                "status": "validation_error",
                "message": "Erro na validação Pydantic",
                "erro": str(validation_error),
                "tipo_erro": type(validation_error).__name__,
                "dados_enviados": dados_teste
            }

    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

@app.get("/debug-modelo-fornecedor", summary="Debug modelo fornecedor SQLAlchemy")
def debug_modelo_fornecedor():
    """
    Verifica como o SQLAlchemy está mapeando a tabela fornecedores
    """
    try:
        from app.models.fornecedor import Fornecedor
        from sqlalchemy import inspect

        # Verificar colunas do modelo Python
        colunas_modelo = [col.name for col in Fornecedor.__table__.columns]

        # Verificar colunas reais do banco
        from app.database import engine
        inspector = inspect(engine)
        colunas_banco = [col['name'] for col in inspector.get_columns('fornecedores')]

        return {
            "status": "debug_completo",
            "colunas_modelo_python": sorted(colunas_modelo),
            "colunas_banco_real": sorted(colunas_banco),
            "discrepancias": {
                "faltam_no_modelo": [col for col in colunas_banco if col not in colunas_modelo],
                "faltam_no_banco": [col for col in colunas_modelo if col not in colunas_banco]
            }
        }

    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }
@app.get("/fix-remover-coluna-cnpj", summary="Remover coluna cnpj órfã")
def fix_remover_coluna_cnpj():
    """
    Remove a coluna cnpj antiga que está causando conflito
    """
    try:
        from app.database import engine
        from sqlalchemy import text

        with engine.connect() as connection:

            # Verificar se há restrições na coluna cnpj
            restricoes = connection.execute(text("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_name = 'fornecedores'
                AND constraint_name LIKE '%cnpj%'
            """)).fetchall()

            # Remover restrições relacionadas à coluna cnpj
            for restricao in restricoes:
                try:
                    connection.execute(text(f"""
                        ALTER TABLE fornecedores
                        DROP CONSTRAINT IF EXISTS {restricao[0]}
                    """))
                except:
                    pass  # Ignorar se não conseguir remover

            # Remover a coluna cnpj antiga
            connection.execute(text("""
                ALTER TABLE fornecedores
                DROP COLUMN IF EXISTS cnpj
            """))

            connection.commit()

            # Verificar se foi removida
            from sqlalchemy import inspect
            inspector = inspect(engine)
            colunas_atuais = [col['name'] for col in inspector.get_columns('fornecedores')]

            return {
                "status": "success",
                "message": "Coluna cnpj órfã removida com sucesso",
                "colunas_restantes": sorted(colunas_atuais),
                "cnpj_removido": "cnpj" not in colunas_atuais
            }

    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }
    
# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================
# Endpoint usado pelo Render para verificar se o serviço está funcionando
# Retorna status da API e conexão com banco de dados
# ============================================================================

from fastapi import status
from sqlalchemy import text
from app.database import SessionLocal

@app.get(
    "/api/v1/health",
    status_code=status.HTTP_200_OK,
    tags=["Health Check"]
)
async def health_check():
    """
    Endpoint de health check para monitoramento
    
    Verifica:
    - Status da API
    - Conexão com banco de dados
    
    Returns:
        dict: Status da aplicação
    """
    # Verificar conexão com banco de dados
    db_status = "unknown"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "service": "Food Cost API",
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "version": "settings.VERSION"
    }

# ============================================================================
# REGISTRAR ROUTERS - AUTENTICAÇÃO (PRIORIDADE)
# ============================================================================

# Router de autenticação (sem prefixo adicional, fica em /api/v1/auth)
if HAS_AUTH:
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticação"])
    print("[OK] Router de autenticação registrado: /api/v1/auth")

# ============================================================================
# REGISTRAR ROUTER DE USUÁRIOS
# ============================================================================
# Tentar forçar importação direta se a primeira falhou
if not HAS_USERS:
    print("⚠️ Tentando importação forçada do módulo users...")
    try:
        import app.api.endpoints.users as users_module
        users = users_module
        HAS_USERS = True
        print("✅ Importação forçada bem-sucedida!")
    except Exception as e:
        print(f"❌ Importação forçada falhou: {e}")
        import traceback
        traceback.print_exc()

if HAS_USERS:
    try:
        app.include_router(users.router, prefix="/api/v1/users", tags=["Usuários"])
        print("[OK] Router de usuários registrado: /api/v1/users")
        
        # Verificar se o router tem rotas registradas
        print(f"   Rotas registradas no router users: {len(users.router.routes)}")
        for route in users.router.routes:
            print(f"   - {route.methods} {route.path}")
    except Exception as e:
        print(f"❌ ERRO ao registrar router users: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ CRÍTICO: Router users NÃO foi registrado!")
    print("   A tela de gerenciamento de usuários NÃO funcionará!")

# ============================================================================
# REGISTRAR ROUTER DE PERMISSÕES
# ============================================================================

# Importar router de permissions
try:
    from app.api.endpoints import permissions
    HAS_PERMISSIONS = True
    print("✅ Módulo permissions importado com sucesso")
except ImportError as e:
    HAS_PERMISSIONS = False
    print(f"❌ Módulo permissions não encontrado: {e}")

# Registrar router de permissions
if HAS_PERMISSIONS:
    try:
        app.include_router(
            permissions.router, 
            prefix="/api/v1/permissions", 
            tags=["Permissões"],
            responses={
                403: {"description": "Acesso negado - apenas ADMIN"},
                404: {"description": "Permissão não encontrada"},
                422: {"description": "Erro de validação"}
            }
        )
        print("[OK] Router de permissões registrado: /api/v1/permissions")
        
        # Verificar se o router tem rotas registradas
        print(f"   Rotas registradas no router permissions: {len(permissions.router.routes)}")
        for route in permissions.router.routes:
            print(f"   - {route.methods} {route.path}")
    except Exception as e:
        print(f"❌ ERRO ao registrar router permissions: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ CRÍTICO: Router permissions NÃO foi registrado!")
    print("   O gerenciamento de permissões NÃO funcionará!")

# Router de limpeza de dados (apenas ADMIN)
if HAS_LIMPEZA_DADOS:
    app.include_router(
        limpeza_dados.router, 
        prefix="/api/v1/limpeza-dados", 
        tags=["Limpeza de Dados"],
        responses={
            403: {"description": "Acesso negado - apenas ADMIN"},
            500: {"description": "Erro ao executar limpeza"}
        }
    )
    print("[OK] Router de limpeza de dados registrado: /api/v1/limpeza-dados")
    
#   ===================================================================================================
#   REGISTRAR ROUTERS - MÓDULOS DO SISTEMA
#   ===================================================================================================

# Incluir routers de insumos 
app.include_router(
    insumos.router,
    prefix="/api/v1/insumos",
    tags=["insumos"]
)

# APIs de Receitas e Restaurantes (novas)
app.include_router(
    receitas.router,
    prefix="/api/v1/receitas", 
    tags=["receitas"]
)

# Incluir router de códigos (se disponível)
if HAS_CODIGOS:
    app.include_router(
        codigos.router, 
        prefix="/api/v1/codigos", 
        tags=["codigos"]
    )
    print("✅ Router de códigos registrado: /api/v1/codigos")

# Router para operações com fornecedores
app.include_router(
    fornecedores.router, 
    prefix="/api/v1/fornecedores", 
    tags=["fornecedores"],
    responses={
        404: {"description": "Fornecedor não encontrado"},
        422: {"description": "Erro de validação"},
        500: {"description": "Erro interno do servidor"}
    }
)

# Router para operações com taxonomias hierárquicas
app.include_router(
    taxonomias.router,
    prefix="/api/v1/taxonomias",
    tags=["taxonomias"],
    responses={
        404: {"description": "Taxonomia não encontrada"},
        422: {"description": "Erro de validação"},
        500: {"description": "Erro interno do servidor"}
    }
)

# Router para sistema de IA de classificação
try:
    from app.api.endpoints import ia as ia_endpoints
    app.include_router(
        ia_endpoints.router,
        prefix="/api/v1/ia",
        tags=["ia-classificacao"],
        responses={
            404: {"description": "Recurso não encontrado"},
            422: {"description": "Erro de validação"},
            500: {"description": "Erro interno do servidor"},
            503: {"description": "Sistema de IA indisponível"}
        }
    )
    print("✅ Router de IA incluído com sucesso")
except ImportError as e:
    print(f"⚠️  Sistema de IA não disponível: {e}")
    print("💡 Instale as dependências: pip install spacy fuzzywuzzy python-levenshtein")
except Exception as e:
    print(f"❌ Erro ao carregar sistema de IA: {e}")

# Router para operações com restaurantes (Sistema de Gestão - Fase 3)
if HAS_RESTAURANTES:
    app.include_router(
        restaurantes.router,
        prefix="/api/v1/restaurantes",
        tags=["restaurantes"],
        responses={
            404: {"description": "Restaurante não encontrado"},
            422: {"description": "Erro de validação"},
            500: {"description": "Erro interno do servidor"}
        }
    )
    print("✅ Router restaurantes incluído com sucesso")
else:
    print("[AVISO] Router restaurantes não incluído (módulo não disponível)")

# Router para operações com aliases de taxonomias (Sistema de Mapeamento - Fase 2)
if HAS_TAXONOMIA_ALIASES:
    app.include_router(
        taxonomia_aliases.router,
        prefix="/api/v1/taxonomias",
        tags=["taxonomia-aliases"],
        responses={
            404: {"description": "Alias não encontrado"},
            422: {"description": "Erro de validação"},
            500: {"description": "Erro interno do servidor"}
        }
    )
    print("✅ Router taxonomia_aliases incluído com sucesso")
else:
    print("[AVISO]  Router taxonomia_aliases não incluído (módulo não disponível)")

# Router para operações com insumos do catálogo dos fornecedores (condicional)
if HAS_FORNECEDOR_INSUMOS:
    app.include_router(
        fornecedor_insumos.router,
        prefix="/api/v1", 
        tags=["fornecedor-insumos"],
        responses={
            404: {"description": "Insumo ou fornecedor não encontrado"},
            422: {"description": "Erro de validação"},
            500: {"description": "Erro interno do servidor"}
        }
    )

# Router para importação de insumos via Excel/TOTVS (Sistema de Automação)
if HAS_IMPORTACOES:
    app.include_router(
        importacoes.router,
        prefix="/api/v1/importacoes",
        tags=["importacoes"],
        responses={
            404: {"description": "Importação não encontrada"},
            422: {"description": "Erro de validação"},
            400: {"description": "Requisição inválida"},
            500: {"description": "Erro interno do servidor"}
        }
    )
    print("✅ Router importacoes incluído com sucesso")
else:
    print("[AVISO] Router importacoes não incluído (módulo não disponível)")

# Router para importação de receitas via Excel/TOTVS (Sistema de Automação)
if HAS_IMPORTACAO_RECEITAS:
    app.include_router(
        importacao_receitas.router,
        prefix="/api/v1/importacao-receitas",
        tags=["importacao-receitas"],
        responses={
            404: {"description": "Importação não encontrada"},
            422: {"description": "Erro de validação"},
            400: {"description": "Requisição inválida"},
            500: {"description": "Erro interno do servidor"}
        }
    )
    print("✅ Router importacao_receitas incluído com sucesso")
else:
    print("[AVISO] Router importacao_receitas não incluído (módulo não disponível)")

#   ===================================================================================================
#   Middleware para logging de requisições
#   ===================================================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware para monitorar requisições
    """
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Log simples apenas do tempo de resposta
    if process_time > 1.0:  # Só loga se demorar mais de 1 segundo
        print(f"⚠️  Requisição lenta: {request.method} {request.url.path} - {process_time:.2f}s")
    
    return response

#   ===================================================================================================
#   Tratamento de erros globais
#   ===================================================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handler customizado para erros 404"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Recurso não encontrado",
            "message": "O endpoint solicitado não existe",
            "path": str(request.url.path),
            "method": request.method
        }
    )

@app.exception_handler(422)
async def validation_error_handler(request: Request, exc: HTTPException):
    """Handler customizado para erros de validação"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Erro de validação",
            "message": "Os dados fornecidos não são válidos",
            "details": exc.detail if hasattr(exc, 'detail') else str(exc)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Handler customizado para erros internos"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "message": "Ocorreu um erro inesperado",
            "path": str(request.url.path)
        }
    )

#   ===================================================================================================
#   Executar a aplicação (apenas se executado diretamente)
#   ===================================================================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando Food Cost System API...")
    print("🌐 Local: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
