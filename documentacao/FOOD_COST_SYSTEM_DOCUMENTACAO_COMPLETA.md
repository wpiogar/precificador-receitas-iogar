# 📚 DOCUMENTAÇÃO TÉCNICA COMPLETA
# FOOD COST SYSTEM - IOGAR

**Versão do Sistema:** 3.1  
**Data da Documentação:** Dezembro 2025  
**Desenvolvedor:** Will - IOGAR  
**Status:** Em Produção (Render.com)  
**Repositório:** GitHub Projects (wpiogar/pecificador-receitas-logar)

---

## 📑 ÍNDICE

1. [Visão Geral](#1-visão-geral)
2. [Objetivo do Projeto](#2-objetivo-do-projeto)
3. [Arquitetura do Sistema](#3-arquitetura-do-sistema)
4. [Stack Tecnológica](#4-stack-tecnológica)
5. [Estrutura de Diretórios](#5-estrutura-de-diretórios)
6. [Banco de Dados e Modelos](#6-banco-de-dados-e-modelos)
7. [Módulos do Sistema](#7-módulos-do-sistema)
8. [API REST - Endpoints](#8-api-rest---endpoints)
9. [Sistema de Autenticação](#9-sistema-de-autenticação)
10. [Sistema de IA](#10-sistema-de-ia)
11. [Fluxo Operacional](#11-fluxo-operacional)
12. [Instalação e Configuração](#12-instalação-e-configuração)
13. [Deploy e Ambientes](#13-deploy-e-ambientes)
14. [Guia de Desenvolvimento](#14-guia-de-desenvolvimento)
15. [Troubleshooting](#15-troubleshooting)
16. [Melhorias Futuras](#16-melhorias-futuras)
17. [Referências](#17-referências)

---

# 1. VISÃO GERAL

## 1.1 Contexto do Projeto

O **Food Cost System** é uma solução completa de gestão de custos desenvolvida pela **IOGAR Consultoria** para restaurantes e empresas de food service. O sistema permite controle detalhado de:

- **Ingredientes (Insumos)** com classificação automática por IA
- **Receitas hierárquicas** com cálculo automático de custos
- **Fornecedores** com comparativo de preços
- **Restaurantes** com suporte a redes multi-unidades
- **Relatórios profissionais** em PDF e Excel
- **Sistema de permissões** granular com 5 níveis de acesso

## 1.2 Características Principais

### ✅ Gestão Completa de Custos
- Controle de preços por fornecedor
- Cálculo automático de custo de receitas
- Histórico de preços (30 dias)
- Comparativo entre fornecedores

### 🤖 Inteligência Artificial
- Classificação automática de ingredientes (100% gratuita)
- Processamento de linguagem natural com spaCy
- Sistema de aprendizado contínuo
- Base com 400+ categorias

### 🔐 Segurança e Controle
- Autenticação JWT com refresh tokens
- 5 níveis de acesso (Admin, Consultant, Owner, Manager, Operator)
- Permissões configuráveis por recurso
- Logs de auditoria

### 📊 Relatórios e Exportações
- PDFs profissionais com marca IOGAR
- Fichas técnicas de receitas
- Exportação Excel/CSV
- Cardápios personalizáveis (planejado)

### 🏢 Multi-Tenancy
- Suporte a múltiplos restaurantes
- Isolamento de dados
- Compartilhamento opcional de ingredientes globais

---

# 2. OBJETIVO DO PROJETO

## 2.1 Problema de Negócio

Restaurantes enfrentam desafios na gestão de custos:
- Descontrole de variação de preços
- Cálculos manuais em planilhas Excel
- Falta de visão sobre custos reais
- Dificuldade em comparar fornecedores
- Desperdício por falta de controle
- Precificação sem embasamento técnico

## 2.2 Solução Proposta

O Food Cost System resolve através de:
- Automação completa de cálculos
- Classificação inteligente de ingredientes
- Importação em massa via Excel
- Base única centralizada
- Histórico automático de preços
- Receitas hierárquicas com cálculo em cascata
- Relatórios profissionais prontos

## 2.3 Benefícios Esperados

**Para o Restaurante:**
- ✅ Redução de custos em 15-20%
- ✅ Aumento de margem de lucro
- ✅ Decisões baseadas em dados
- ✅ Controle de desperdício

**Para o Consultor:**
- ✅ Ferramenta profissional
- ✅ Relatórios prontos
- ✅ Ganho de 70% de produtividade
- ✅ Base de conhecimento compartilhada

---

# 3. ARQUITETURA DO SISTEMA

## 3.1 Visão Arquitetural

O sistema segue arquitetura de **três camadas**:

```
┌─────────────────────────────────────────┐
│       CAMADA DE APRESENTAÇÃO             │
│   React 18 + TypeScript + Tailwind      │
│   - SPA com routing                      │
│   - State management local               │
│   - Axios para HTTP                      │
└─────────────────────────────────────────┘
              │ HTTPS / REST API
              ▼
┌─────────────────────────────────────────┐
│       CAMADA DE APLICAÇÃO                │
│   FastAPI + Python 3.11                  │
│   - Endpoints REST                       │
│   - Autenticação JWT                     │
│   - Validação Pydantic                   │
│   - Sistema de IA (spaCy)                │
└─────────────────────────────────────────┘
              │ SQLAlchemy ORM
              ▼
┌─────────────────────────────────────────┐
│       CAMADA DE PERSISTÊNCIA             │
│   PostgreSQL 15 + Redis 7                │
│   - Dados principais                     │
│   - Cache e sessões                      │
└─────────────────────────────────────────┘
```

## 3.2 Padrões Arquiteturais

**Clean Architecture:**
```
backend/app/
├── api/          # Interface Layer (Controllers)
├── services/     # Use Cases (Business Logic)
├── crud/         # Data Access Layer
├── models/       # Entities (Domain Models)
├── schemas/      # DTOs (Pydantic)
└── core/         # Infrastructure
```

**Design Patterns:**
- Repository Pattern (crud/)
- Service Layer Pattern (services/)
- Dependency Injection (FastAPI)
- DTO Pattern (schemas/)

---

# 4. STACK TECNOLÓGICA

## 4.1 Backend

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| Python | 3.11 | Linguagem principal |
| FastAPI | 0.104+ | Framework web |
| SQLAlchemy | 2.0+ | ORM |
| Alembic | 1.12+ | Migrations |
| PostgreSQL | 15 | Banco de dados |
| Redis | 7 | Cache e sessões |
| spaCy | 3.7+ | NLP/IA |
| ReportLab | 4.0+ | Geração de PDF |
| openpyxl | 3.1+ | Leitura/escrita Excel |

## 4.2 Frontend

| Tecnologia | Versão | Uso |
|------------|--------|-----|
| React | 18.2 | Library UI |
| TypeScript | 5.2 | Type safety |
| Vite | 5.0 | Build tool |
| Tailwind CSS | 3.3 | Styling |
| Axios | 1.6 | HTTP client |
| jsPDF | 2.5 | PDF no cliente |

## 4.3 Infraestrutura

| Tecnologia | Uso |
|------------|-----|
| Docker | Containerização |
| Docker Compose | Orquestração local |
| Render.com | Deploy cloud |
| Nginx | Reverse proxy (frontend) |
| GitHub | Controle de versão |

---

# 5. ESTRUTURA DE DIRETÓRIOS

## 5.1 Visão Geral

```
food-cost-system/
├── backend/                 # API FastAPI
├── frontend/                # SPA React
├── docs/                    # Documentação
├── docker-compose.yml       # Orquestração local
└── README.md                # Documentação principal
```

## 5.2 Backend Detalhado

```
backend/
├── alembic/                 # Migrations
│   └── versions/            # Arquivos de migration
├── app/
│   ├── main.py              # ⭐ Entry point
│   ├── database.py          # Conexão DB
│   ├── api/
│   │   ├── deps.py          # Dependências globais
│   │   └── endpoints/       # Controllers REST
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── restaurantes.py
│   │       ├── fornecedores.py
│   │       ├── insumos.py
│   │       ├── receitas.py
│   │       ├── ia.py
│   │       └── importacoes.py
│   ├── models/              # Entidades SQLAlchemy
│   │   ├── user.py
│   │   ├── receita.py
│   │   ├── insumo.py
│   │   ├── fornecedor.py
│   │   ├── fornecedor_insumo.py
│   │   ├── restaurante.py
│   │   ├── taxonomia.py
│   │   └── permission.py
│   ├── schemas/             # DTOs Pydantic
│   ├── crud/                # Data Access Layer
│   ├── services/            # Lógica de negócio
│   ├── ai/                  # Sistema de IA
│   │   ├── classificador_ia.py
│   │   └── data/
│   │       ├── base_conhecimento.json
│   │       └── padroes_aprendidos.json
│   ├── core/                # Infraestrutura
│   │   ├── config.py
│   │   └── security.py
│   └── utils/               # Utilitários
├── uploads/                 # Arquivos temporários
├── Dockerfile
├── requirements.txt
└── alembic.ini
```

## 5.3 Frontend Detalhado

```
frontend/
├── public/                  # Assets estáticos
├── src/
│   ├── App.tsx              # ⭐ Componente principal (9070+ linhas)
│   ├── main.tsx             # Entry point
│   ├── config.ts            # Configurações
│   ├── api-service.ts       # Cliente HTTP
│   ├── components/          # Componentes reutilizáveis
│   ├── types/               # TypeScript types
│   └── utils/               # Funções auxiliares
├── Dockerfile
├── nginx.conf
├── package.json
└── vite.config.ts
```

---

# 6. BANCO DE DADOS E MODELOS

## 6.1 Diagrama ER Simplificado

```
USERS (usuários)
  ├─ 1:N → RESTAURANTES
  └─ role (ADMIN, CONSULTANT, OWNER, MANAGER, OPERATOR)

RESTAURANTES
  ├─ 1:N → INSUMOS (ingredientes)
  ├─ 1:N → RECEITAS
  └─ is_rede (boolean)

INSUMOS
  ├─ N:N → FORNECEDORES (via FORNECEDOR_INSUMO com preço)
  ├─ N:1 → TAXONOMIA (classificação IA)
  └─ código único por restaurante (5000-5999)

RECEITAS
  ├─ N:N → INSUMOS (via RECEITA_INSUMO)
  ├─ N:N → RECEITAS (hierárquica via eh_processada)
  └─ código único por restaurante (3000-4999)

FORNECEDORES
  └─ N:N → INSUMOS (com preço em centavos)

TAXONOMIA (IA)
  ├─ categoria / grupo / subgrupo
  └─ 1:N → TAXONOMIA_ALIAS (aprendizado)

PERMISSIONS (sistema de permissões)
  ├─ role + resource + action
  └─ data_scope (TODOS, REDE, LOJA, PROPRIOS)
```

## 6.2 Tabelas Principais

### USERS
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  nome VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,
  restaurante_id INTEGER REFERENCES restaurantes(id),
  password_hash VARCHAR(255) NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP
);
```

### INSUMOS
```sql
CREATE TABLE insumos (
  id SERIAL PRIMARY KEY,
  codigo VARCHAR(20) NOT NULL,
  nome VARCHAR(255) NOT NULL,
  unidade VARCHAR(10) NOT NULL,
  quantidade NUMERIC(10,4) NOT NULL,
  grupo VARCHAR(100),
  subgrupo VARCHAR(100),
  restaurante_id INTEGER REFERENCES restaurantes(id) ON DELETE CASCADE,
  taxonomia_id INTEGER REFERENCES taxonomia(id),
  aguardando_classificacao BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP,
  UNIQUE (restaurante_id, codigo)
);
```

### RECEITAS
```sql
CREATE TABLE receitas (
  id SERIAL PRIMARY KEY,
  codigo VARCHAR(20) NOT NULL,
  nome VARCHAR(255) NOT NULL,
  categoria VARCHAR(100),
  porcoes INTEGER NOT NULL CHECK (porcoes > 0),
  rendimento NUMERIC(10,4) NOT NULL CHECK (rendimento > 0),
  unidade_rendimento VARCHAR(10) NOT NULL,
  descricao TEXT,
  modo_preparo TEXT,
  eh_processada BOOLEAN DEFAULT false,
  restaurante_id INTEGER REFERENCES restaurantes(id) ON DELETE CASCADE,
  foto_url VARCHAR(500),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP,
  UNIQUE (restaurante_id, codigo)
);
```

### RECEITA_INSUMO (N:N)
```sql
CREATE TABLE receita_insumo (
  id SERIAL PRIMARY KEY,
  receita_id INTEGER REFERENCES receitas(id) ON DELETE CASCADE,
  insumo_id INTEGER REFERENCES insumos(id) ON DELETE CASCADE,
  quantidade NUMERIC(10,4) NOT NULL CHECK (quantidade > 0),
  unidade VARCHAR(10) NOT NULL,
  ordem INTEGER DEFAULT 0,
  observacao TEXT
);
```

## 6.3 Códigos Automáticos

| Tipo | Faixa | Exemplo |
|------|-------|---------|
| Receitas Normais | 3000-3999 | 3001 |
| Receitas Processadas | 4000-4999 | 4001 |
| Insumos | 5000-5999 | 5001 |

**Características:**
- Únicos por restaurante
- Gerados automaticamente
- Reutilizam códigos deletados

---

# 7. MÓDULOS DO SISTEMA

## 7.1 Autenticação (Auth)

**Responsabilidades:**
- Login de usuários
- Geração de tokens JWT
- Refresh de tokens
- Validação de permissões

**Endpoints:**
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`

**Fluxo:**
1. Usuário envia email + senha
2. Backend valida com bcrypt
3. Gera access_token (30min) + refresh_token (7 dias)
4. Frontend armazena em localStorage
5. Inclui token em todas as requisições

## 7.2 Usuários

**Responsabilidades:**
- CRUD de usuários
- Gerenciamento de roles
- Associação com restaurantes

**Endpoints:**
- `GET /api/v1/users/`
- `POST /api/v1/users/`
- `PUT /api/v1/users/{id}`
- `DELETE /api/v1/users/{id}`

**5 Níveis de Acesso:**
1. **ADMIN** - Acesso total ao sistema
2. **CONSULTANT** - Múltiplos restaurantes
3. **OWNER** - Proprietário (rede)
4. **MANAGER** - Gerente (loja)
5. **OPERATOR** - Operador (básico)

## 7.3 Restaurantes

**Responsabilidades:**
- CRUD de restaurantes
- Gestão de redes
- Configurações

**Endpoints:**
- `GET /api/v1/restaurantes/`
- `POST /api/v1/restaurantes/`
- `PUT /api/v1/restaurantes/{id}`

**Campos Principais:**
- nome, cnpj (único)
- endereco, cidade, estado
- tipo_cozinha
- is_rede (boolean)

## 7.4 Insumos (Ingredientes)

**Responsabilidades:**
- CRUD de insumos
- Classificação automática por IA
- Controle de preços
- Comparativo entre fornecedores
- Importação via Excel

**Endpoints:**
- `GET /api/v1/insumos/`
- `POST /api/v1/insumos/`
- `PUT /api/v1/insumos/{id}`
- `POST /api/v1/insumos/importar`

**Funcionalidades:**
- Códigos automáticos (5000-5999)
- Classificação IA em tempo real
- Histórico de preços (30 dias)
- Comparativo de fornecedores

## 7.5 Receitas

**Responsabilidades:**
- CRUD de receitas
- Cálculo automático de custos
- Receitas hierárquicas
- Upload de fotos
- Geração de PDF

**Endpoints:**
- `GET /api/v1/receitas/`
- `POST /api/v1/receitas/`
- `PUT /api/v1/receitas/{id}`
- `GET /api/v1/receitas/{id}/pdf`

**Características:**
- Códigos automáticos (3000-4999)
- Receitas processadas como ingredientes
- Cálculo em cascata de custos
- Fichas técnicas em PDF

## 7.6 Fornecedores

**Responsabilidades:**
- CRUD de fornecedores
- Vinculação de insumos
- Gestão de preços

**Endpoints:**
- `GET /api/v1/fornecedores/`
- `POST /api/v1/fornecedores/`
- `POST /api/v1/fornecedores/{id}/insumos`

**Funcionalidades:**
- CPF/CNPJ único
- Preços em centavos
- Comparativo automático

## 7.7 Sistema de IA

**Responsabilidades:**
- Classificação de ingredientes
- Matching fuzzy
- Aprendizado contínuo
- Gestão de taxonomias

**Endpoints:**
- `POST /api/v1/ia/classificar`
- `POST /api/v1/ia/feedback`
- `GET /api/v1/ia/historico`

**Tecnologias:**
- spaCy (NLP português)
- fuzzywuzzy (similaridade)
- Base de conhecimento (400+ categorias)

## 7.8 Importação

**Responsabilidades:**
- Importação Excel de insumos
- Importação Excel de receitas
- Matching inteligente
- Validação e preview

**Endpoints:**
- `POST /api/v1/importacoes/upload`
- `POST /api/v1/importacoes/confirmar`
- `GET /api/v1/importacoes/`

**Fluxo:**
1. Upload do arquivo
2. Validação de estrutura
3. Matching de insumos existentes
4. Preview para usuário
5. Confirmação e execução
6. Log detalhado

---

# 8. API REST - ENDPOINTS

## 8.1 Autenticação

```
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
```

## 8.2 Usuários

```
GET    /api/v1/users/
GET    /api/v1/users/{id}
POST   /api/v1/users/
PUT    /api/v1/users/{id}
DELETE /api/v1/users/{id}
PATCH  /api/v1/users/{id}/toggle-active
```

## 8.3 Restaurantes

```
GET    /api/v1/restaurantes/
GET    /api/v1/restaurantes/{id}
POST   /api/v1/restaurantes/
PUT    /api/v1/restaurantes/{id}
DELETE /api/v1/restaurantes/{id}
```

## 8.4 Insumos

```
GET    /api/v1/insumos/
GET    /api/v1/insumos/{id}
POST   /api/v1/insumos/
PUT    /api/v1/insumos/{id}
DELETE /api/v1/insumos/{id}
POST   /api/v1/insumos/importar
```

## 8.5 Receitas

```
GET    /api/v1/receitas/
GET    /api/v1/receitas/{id}
POST   /api/v1/receitas/
PUT    /api/v1/receitas/{id}
DELETE /api/v1/receitas/{id}
GET    /api/v1/receitas/{id}/pdf
POST   /api/v1/receitas/{id}/foto
```

## 8.6 Fornecedores

```
GET    /api/v1/fornecedores/
GET    /api/v1/fornecedores/{id}
POST   /api/v1/fornecedores/
PUT    /api/v1/fornecedores/{id}
DELETE /api/v1/fornecedores/{id}
POST   /api/v1/fornecedores/{id}/insumos
```

## 8.7 IA

```
POST   /api/v1/ia/classificar
POST   /api/v1/ia/classificar-lote
POST   /api/v1/ia/feedback
GET    /api/v1/ia/taxonomias
GET    /api/v1/ia/historico
```

## 8.8 Importações

```
POST   /api/v1/importacoes/upload
POST   /api/v1/importacoes/confirmar
GET    /api/v1/importacoes/
GET    /api/v1/importacoes/{id}
GET    /api/v1/importacoes/template
```

---

# 9. SISTEMA DE AUTENTICAÇÃO

## 9.1 JWT Tokens

**Access Token:**
- Validade: 30 minutos
- Uso: Autenticação em requests
- Armazenamento: localStorage

**Refresh Token:**
- Validade: 7 dias
- Uso: Renovação de access_token
- Armazenamento: localStorage

## 9.2 Fluxo de Autenticação

```
1. Login
   POST /api/v1/auth/login
   {email, password}
   ↓
2. Backend valida
   - Busca usuário por email
   - Verifica senha (bcrypt)
   - Verifica is_active
   ↓
3. Gera tokens
   - access_token (30min)
   - refresh_token (7 dias)
   ↓
4. Frontend armazena
   localStorage.setItem('foodcost_access_token', token)
   ↓
5. Requisições subsequentes
   Authorization: Bearer {access_token}
   ↓
6. Token expira
   Frontend detecta 401
   ↓
7. Refresh
   POST /api/v1/auth/refresh
   {refresh_token}
   ↓
8. Novo access_token
```

## 9.3 Segurança

**Hashing de Senhas:**
```python
import bcrypt

hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
is_valid = bcrypt.checkpw(password.encode(), hashed)
```

**Validação de Token:**
```python
from jose import jwt

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
```

---

# 10. SISTEMA DE IA

## 10.1 Tecnologias

- **spaCy** - NLP em português (pt_core_news_sm)
- **fuzzywuzzy** - Similaridade de strings
- **Levenshtein** - Distância de edição
- **unidecode** - Normalização de texto

## 10.2 Base de Conhecimento

**Estrutura:**
```json
{
  "Proteínas": {
    "Carnes": {
      "Bovina": ["alcatra", "picanha", "filé mignon"],
      "Suína": ["lombo suíno", "costela"],
      "Frango": ["peito de frango", "coxa"]
    }
  },
  "Hortaliças": {
    "Tomates": {
      "Tomate Comum": ["tomate", "tomate italiano"],
      "Tomate Cereja": ["tomate cereja", "tomate grape"]
    }
  }
}
```

## 10.3 Fluxo de Classificação

```
1. Usuário cria insumo "Tomate Cereja"
   ↓
2. Backend normaliza
   - Remove acentos
   - Lowercase
   - Remove stopwords
   ↓
3. Busca em taxonomia
   - Matching exato
   - Matching fuzzy (>80%)
   - Busca em aliases
   ↓
4. Retorna sugestão
   {
     "categoria": "Hortaliças",
     "grupo": "Tomates",
     "subgrupo": "Tomate Cereja",
     "confianca": 0.95
   }
   ↓
5. Usuário aceita ou corrige
   ↓
6. Sistema aprende
   - Se corrigido → cria alias
   - Salva feedback
```

## 10.4 Aprendizado Contínuo

Quando usuário corrige:
```python
def salvar_feedback(nome, sugestao_ia, correcao_usuario):
    # Criar alias
    alias = TaxonomiaAlias(
        taxonomia_id=taxonomia_correta_id,
        alias=nome.lower(),
        confianca=0.80
    )
    db.add(alias)
    
    # Log de feedback
    registrar_log({
        "nome": nome,
        "sugestao_ia": sugestao_ia,
        "correcao_usuario": correcao_usuario,
        "timestamp": now()
    })
```

---

# 11. FLUXO OPERACIONAL

## 11.1 Criar uma Receita (Completo)

```
ETAPA 1: Login
├─ Usuário acessa sistema
├─ Envia email + senha
├─ Recebe tokens JWT
└─ Frontend armazena tokens

ETAPA 2: Preparação (Ingredientes)
├─ Usuário acessa "Insumos"
├─ Cria ingredientes necessários
│  ├─ Nome: "Farinha de Trigo"
│  ├─ IA classifica automaticamente
│  └─ Define preço (via fornecedor)
└─ Sistema gera códigos (5000-5999)

ETAPA 3: Criar Receita
├─ Usuário clica "Nova Receita"
├─ Preenche dados básicos
│  ├─ Nome: "Bolo de Chocolate"
│  ├─ Categoria: "Sobremesa"
│  ├─ Porções: 8
│  └─ Rendimento: 1.2 kg
├─ Adiciona ingredientes
│  ├─ Farinha: 500g
│  ├─ Chocolate: 200g
│  └─ Ovos: 6 unidades
└─ Sistema calcula custos automaticamente

ETAPA 4: Resultado
├─ Receita criada com código 3001
├─ Custo total: R$ 28.50
├─ Custo por porção: R$ 3.56
└─ Ficha técnica disponível (PDF)
```

## 11.2 Importar Insumos via Excel

```
ETAPA 1: Preparar Excel
├─ Baixar template
├─ Preencher colunas obrigatórias
│  ├─ código
│  ├─ descrição
│  ├─ unidade
│  ├─ quantidade
│  └─ preço
└─ Salvar arquivo .xlsx

ETAPA 2: Upload
├─ Usuário faz upload
├─ Backend valida estrutura
│  ├─ Colunas corretas?
│  ├─ Tipos de dados válidos?
│  └─ Valores dentro dos limites?
└─ Processa matching

ETAPA 3: Preview
├─ Backend mostra resumo
│  ├─ Total de linhas: 150
│  ├─ Insumos existentes: 80
│  ├─ Insumos novos: 70
│  └─ Erros: 0
└─ Usuário revisa

ETAPA 4: Confirmação
├─ Usuário confirma importação
├─ Backend executa
│  ├─ Cria novos insumos
│  ├─ Atualiza preços existentes
│  ├─ Classifica com IA
│  └─ Gera log completo
└─ Retorna resultado
```

---

# 12. INSTALAÇÃO E CONFIGURAÇÃO

## 12.1 Pré-requisitos

- Docker Desktop instalado
- Git
- VS Code (recomendado)

## 12.2 Instalação Local (Docker)

### Passo 1: Clonar Repositório
```bash
git clone https://github.com/iogar/food-cost-system.git
cd food-cost-system
```

### Passo 2: Configurar Variáveis de Ambiente
```bash
# Copiar template
cp .env.example .env

# Editar .env (IMPORTANTE: alterar senhas!)
```

**.env Exemplo:**
```env
# Database
DATABASE_URL=postgresql://postgres:senha@db:5432/foodcost_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=senha_segura
POSTGRES_DB=foodcost_db

# Backend
SECRET_KEY=gerar_chave_segura_aqui
ALLOWED_ORIGINS=http://localhost,http://localhost:3000

# Redis
REDIS_URL=redis://redis:6379/0
```

### Passo 3: Iniciar Sistema
```bash
# Iniciar containers
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f
```

### Passo 4: Acessar Sistema

| Serviço | URL | Descrição |
|---------|-----|-----------|
| Frontend | http://localhost | Interface principal |
| Backend API | http://localhost:8000 | API REST |
| Swagger Docs | http://localhost:8000/docs | Documentação API |
| PostgreSQL | localhost:5432 | Banco de dados |
| Redis | localhost:6379 | Cache |

**Login Padrão:**
- Email: `admin@iogar.com.br`
- Senha: `admin123`

## 12.3 Scripts Úteis

**Linux/Mac:**
```bash
# Setup completo
./docker-scripts.sh setup

# Iniciar
./docker-scripts.sh start

# Parar
./docker-scripts.sh stop

# Ver logs
./docker-scripts.sh logs

# Rebuild
./docker-scripts.sh build
```

**Windows (PowerShell):**
```powershell
# Setup completo
.\docker-scripts.ps1 setup

# Iniciar
.\docker-scripts.ps1 start

# Parar
.\docker-scripts.ps1 stop
```

---

# 13. DEPLOY E AMBIENTES

## 13.1 Ambientes

### 1. LOCAL (Docker)
- **Branch:** develop
- **URL Backend:** http://localhost:8000
- **URL Frontend:** http://localhost:3000
- **Banco:** PostgreSQL local
- **Deploy:** Manual (docker-compose)

### 2. STAGING (Render)
- **Branch:** staging
- **URL Backend:** https://food-cost-backend-staging.onrender.com
- **URL Frontend:** https://food-cost-frontend-staging.onrender.com
- **Banco:** PostgreSQL Render (separado)
- **Deploy:** Automático via push

### 3. PRODUCTION (Render)
- **Branch:** main
- **URL Backend:** https://food-cost-backend.onrender.com
- **URL Frontend:** https://food-cost-frontend.onrender.com
- **Banco:** PostgreSQL Render
- **Deploy:** Automático via push

## 13.2 Workflow Git

```
develop (local)
    ↓ merge
staging (QA/testes)
    ↓ merge (após aprovação)
main (produção)
```

## 13.3 Deploy para Staging

```bash
# 1. Certificar que está na develop
git checkout develop
git pull origin develop

# 2. Merge para staging
git checkout staging
git merge develop

# 3. Push (trigger deploy automático)
git push origin staging

# Ou usar script
.\deploy-staging.ps1
```

## 13.4 Deploy para Production

```bash
# 1. Testar em staging primeiro!

# 2. Merge staging para main
git checkout main
git merge staging

# 3. Push (trigger deploy automático)
git push origin main

# Ou usar script
.\deploy-production.ps1
```

## 13.5 Variáveis de Ambiente (Render)

**Backend:**
```
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<gerado_automaticamente>
DATABASE_URL=<do_postgresql_render>
ALLOWED_ORIGINS=https://food-cost-frontend.onrender.com
```

**Frontend:**
```
VITE_API_URL=https://food-cost-backend.onrender.com
VITE_ENVIRONMENT=production
GENERATE_SOURCEMAP=false
```

---

# 14. GUIA DE DESENVOLVIMENTO

## 14.1 Padrões de Código

### Python (Backend)

**✅ Clean Code:**
```python
# BOM - descritivo e claro
def calcular_custo_total_receita(receita_id: int) -> Decimal:
    """
    Calcula o custo total de uma receita somando todos os ingredientes.
    
    Args:
        receita_id: ID da receita
        
    Returns:
        Custo total em Decimal
    """
    pass

# RUIM - sem contexto
def calc(r): 
    pass
```

**✅ Comentários Obrigatórios:**
```python
# ============================================================================
# CÁLCULO DE CUSTOS DE RECEITAS
# ============================================================================
# Descrição: Calcula custos com base em ingredientes e quantidades
# Data: 15/12/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

def calcular_custo_receita(receita_id: int) -> dict:
    # Buscar receita com ingredientes
    receita = buscar_receita_com_ingredientes(receita_id)
    
    # Calcular custo de cada ingrediente
    custo_total = sum(
        calcular_custo_ingrediente(ri) 
        for ri in receita.receita_insumos
    )
    
    return {
        "custo_total": custo_total,
        "custo_por_porcao": custo_total / receita.porcoes
    }
```

### TypeScript (Frontend)

**✅ Interfaces bem definidas:**
```typescript
// BOM - type safety
interface Receita {
  id: number;
  nome: string;
  custo_total: number;
  porcoes: number;
}

function exibirReceita(receita: Receita) {
  console.log(receita.nome);
}

// RUIM - any
function exibirReceita(receita: any) {
  console.log(receita.nome);
}
```

## 14.2 Commits Convencionais

**Formato:**
```
<tipo>: <descrição curta>

<descrição detalhada opcional>
```

**Tipos:**
- `feat` - Nova funcionalidade
- `fix` - Correção de bug
- `refactor` - Refatoração
- `docs` - Documentação
- `style` - Formatação
- `test` - Testes
- `chore` - Manutenção

**Exemplos:**
```bash
feat: adicionar filtro por grupo na listagem de ingredientes

- Implementado select com grupos disponíveis
- Adicionado filtro no backend com query parameter
- Atualizado componente de listagem
- Testado em todos os perfis de usuário
```

## 14.3 Testes

**Backend (pytest):**
```python
def test_criar_receita():
    """Testa criação de receita"""
    response = client.post("/api/v1/receitas/", json={
        "nome": "Bolo Teste",
        "porcoes": 8,
        "rendimento": 1.0,
        "unidade_rendimento": "kg"
    })
    assert response.status_code == 201
    assert response.json()["nome"] == "Bolo Teste"
```

**Frontend (Vitest - planejado):**
```typescript
describe('ReceitaForm', () => {
  it('valida campos obrigatórios', () => {
    render(<ReceitaForm />);
    // ... testes
  });
});
```

## 14.4 Debugging

**Backend:**
```python
import logging

logger = logging.getLogger(__name__)

def funcao_complexa():
    logger.info("Iniciando processamento...")
    logger.debug(f"Dados recebidos: {dados}")
    logger.error(f"Erro inesperado: {erro}")
```

**Frontend:**
```typescript
console.log('Debug:', data);
console.error('Erro:', error);

// Network tab do navegador
// Verificar requests HTTP
```

---

# 15. TROUBLESHOOTING

## 15.1 Problemas Comuns

### Erro: Containers não iniciam

**Sintomas:**
- `docker-compose up` falha
- Containers em estado "Restarting"

**Solução:**
```bash
# Ver logs detalhados
docker-compose logs

# Rebuild completo
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Erro: Frontend não conecta com Backend

**Sintomas:**
- CORS error
- Network error no console

**Solução:**
```bash
# Verificar ALLOWED_ORIGINS no backend
# backend/.env
ALLOWED_ORIGINS=http://localhost,http://localhost:3000,http://localhost:5173

# Verificar VITE_API_URL no frontend
# frontend/.env.local
VITE_API_URL=http://localhost:8000

# Reiniciar containers
docker-compose restart
```

### Erro: Token inválido/expirado

**Sintomas:**
- 401 Unauthorized
- Redirecionamento para login

**Solução:**
```typescript
// Frontend: Verificar nome da chave no localStorage
const TOKEN_KEY = 'foodcost_access_token';  // Padrão correto

// Limpar e fazer login novamente
localStorage.clear();
```

### Erro: Migrations falhando

**Sintomas:**
- Tabelas não criadas
- Erro ao acessar dados

**Solução:**
```bash
# Conectar no container backend
docker-compose exec backend bash

# Rodar migrations manualmente
alembic upgrade head

# Verificar se funcionou
alembic current
```

### Erro: Importação de insumos falha

**Sintomas:**
- Arquivo não processa
- Erros de validação

**Solução:**
1. Verificar estrutura do Excel
2. Colunas obrigatórias presentes?
3. Tipos de dados corretos?
4. Ver logs detalhados no backend

**Diagnóstico:**
```bash
# Ver logs do backend
docker-compose logs backend

# Procurar por erros de importação
docker-compose logs backend | grep "IMPORT ERROR"
```

## 15.2 Verificação de Saúde

```bash
# Verificar todos os serviços
docker-compose ps

# Esperado: todos "Up"
# Nome                Estado      Portas
# backend             Up          8000
# frontend            Up          80
# db                  Up          5432
# redis               Up          6379

# Testar backend
curl http://localhost:8000/api/v1/health

# Esperado: {"status":"ok"}

# Testar frontend
curl http://localhost/

# Esperado: HTML da aplicação
```

---

# 16. MELHORIAS FUTURAS

## 16.1 Roadmap (Prioridades)

### ✅ Prioridade 1 (Crítico)
- [ ] Correção completa da taxonomia em produção
- [ ] Melhorar relatório de receitas (gráficos, QR code)
- [ ] Histórico de preços com gráficos

### ✅ Prioridade 2 (Alto)
- [ ] Exportação avançada (múltiplos formatos)
- [ ] Importação de receitas via Excel
- [ ] Filtros avançados (grupo, subgrupo)
- [ ] Comparativo funcional de preços

### ✅ Prioridade 3 (Médio)
- [ ] Melhorias no módulo IA (histórico, estatísticas)
- [ ] Sistema de notificações
- [ ] Dashboard executivo
- [ ] App mobile (React Native)

### ✅ Prioridade 4 (Baixo)
- [ ] Upload de fotos de receitas (Cloudinary)
- [ ] Gerador de cardápio com templates
- [ ] Dark mode
- [ ] Multi-idioma (EN, ES)

### ✅ Prioridade 5 (Futuro)
- [ ] Sistema de monitoramento e logs
- [ ] Integração com PDV
- [ ] API pública para terceiros
- [ ] Marketplace de receitas

## 16.2 Melhorias Técnicas

### Performance
- [ ] Implementar cache Redis distribuído
- [ ] Otimizar queries N+1
- [ ] Implementar paginação server-side
- [ ] Lazy loading de imagens

### Segurança
- [ ] Rate limiting por IP
- [ ] 2FA (Two-Factor Authentication)
- [ ] Auditoria completa de ações
- [ ] Rotação automática de SECRET_KEY

### DevOps
- [ ] CI/CD com GitHub Actions
- [ ] Testes automatizados completos
- [ ] Monitoramento com Prometheus + Grafana
- [ ] Logs centralizados (ELK Stack)

### Qualidade de Código
- [ ] Coverage de testes > 80%
- [ ] Documentação de API completa
- [ ] Linting e formatação automatizados
- [ ] Code reviews obrigatórios

---

# 17. REFERÊNCIAS

## 17.1 Documentação Oficial

**Backend:**
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Alembic: https://alembic.sqlalchemy.org/
- Pydantic: https://docs.pydantic.dev/
- spaCy: https://spacy.io/

**Frontend:**
- React: https://react.dev/
- TypeScript: https://www.typescriptlang.org/
- Vite: https://vitejs.dev/
- Tailwind CSS: https://tailwindcss.com/

**Infraestrutura:**
- Docker: https://docs.docker.com/
- PostgreSQL: https://www.postgresql.org/docs/
- Redis: https://redis.io/docs/
- Render: https://render.com/docs

## 17.2 Recursos do Projeto

**Repositório:**
- GitHub Projects: wpiogar/pecificador-receitas-logar

**Deploy:**
- Frontend: https://food-cost-frontend.onrender.com
- Backend: https://food-cost-backend.onrender.com
- Swagger: https://food-cost-backend.onrender.com/docs

**Documentação Interna:**
- README.md
- DOCKER-README.md
- DEPLOY.md
- CHANGELOG_DEPLOY.md

## 17.3 Contato e Suporte

**Desenvolvedor:** Will  
**Empresa:** IOGAR Consultoria  
**Email:** contato@iogar.com.br  
**Última Atualização:** Dezembro 2025

---

<div align="center">

**🎉 FIM DA DOCUMENTAÇÃO TÉCNICA 🎉**

Sistema Food Cost v3.1  
Desenvolvido com ❤️ pela IOGAR

</div>
