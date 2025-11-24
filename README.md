# Food Cost System

<div align="center">

![Version](https://img.shields.io/badge/version-3.1-blue.svg)
![Status](https://img.shields.io/badge/status-production-success.svg)
![License](https://img.shields.io/badge/license-proprietary-red.svg)

**Sistema Profissional de Gestão de Custos para Restaurantes**

[Características](#características) •
[Tecnologias](#tecnologias) •
[Arquitetura](#arquitetura) •
[Instalação](#instalação) •
[Documentação](#documentação) •
[Equipe](#equipe)

</div>

---

## Sobre o Projeto

O **Food Cost System** é uma solução completa desenvolvida pela **IOGAR Consultoria** para gestão de custos em restaurantes. O sistema permite controle detalhado de ingredientes, receitas, fornecedores e precificação, com funcionalidades avançadas como classificação inteligente por IA, geração de relatórios PDF e gestão hierárquica de receitas.

### Público-Alvo

- **Restaurantes individuais**: Controle completo de custos e precificação
- **Redes de restaurantes**: Gestão centralizada com dados compartilhados
- **Consultores gastronômicos**: Ferramentas profissionais de análise

---

## Características

### Funcionalidades Principais

- **Gestão de Ingredientes**
  - Cadastro completo com taxonomia hierárquica (Categoria → Grupo → Subgrupo)
  - Controle de unidades de medida e conversões
  - Histórico de preços e fornecedores
  - Importação via Excel (integração TOTVS)
  - Classificação automática por IA

- **Receitas Inteligentes**
  - Estrutura hierárquica (receitas como ingredientes de outras receitas)
  - Cálculo automático de custos com yield
  - Gestão de porções e rendimentos
  - Geração de fichas técnicas em PDF
  - Upload de fotos das receitas

- **Gestão de Fornecedores**
  - Cadastro completo de fornecedores
  - Vinculação de ingredientes por fornecedor
  - Comparativo de preços entre fornecedores
  - Histórico de compras

- **Sistema de Permissões**
  - 5 níveis de acesso (Admin, Consultor, Proprietário, Gerente, Operador)
  - Controle granular de recursos e ações
  - Escopo de dados configurável (Todos, Rede, Loja, Próprios)

- **Relatórios e Exportação**
  - PDF de fichas técnicas
  - Exportação Excel completa
  - Geração de cardápios profissionais
  - Relatórios de custos e análises

- **Inteligência Artificial**
  - Classificação automática de ingredientes
  - Sistema de aprendizado contínuo
  - 100% gratuito (spaCy + NLP)

---

## Tecnologias

### Stack Principal

#### Backend
```
- Python 3.11
- FastAPI (framework web)
- SQLAlchemy (ORM)
- Alembic (migrations)
- PostgreSQL (banco de dados)
- JWT (autenticação)
- spaCy (IA/NLP)
```

#### Frontend
```
- React 18
- TypeScript
- Vite (build tool)
- Tailwind CSS
- Axios (HTTP client)
- React Router (navegação)
```

#### Infraestrutura
```
- Render.com (deploy)
- Cloudinary (armazenamento de imagens)
- GitHub Actions (CI/CD)
```

### Bibliotecas Adicionais

| Categoria | Tecnologias |
|-----------|------------|
| **PDF** | ReportLab, jsPDF |
| **Excel** | openpyxl, papaparse |
| **IA** | spaCy, fuzzywuzzy |
| **Segurança** | bcrypt, python-jose |

---

## Arquitetura

### Estrutura de Diretórios

```
food-cost-system/
├── backend/                    # API FastAPI
│   ├── app/
│   │   ├── api/               # Endpoints REST
│   │   │   └── endpoints/     # Controladores
│   │   ├── core/              # Configurações
│   │   ├── models/            # Modelos SQLAlchemy
│   │   ├── schemas/           # Schemas Pydantic
│   │   ├── services/          # Lógica de negócio
│   │   ├── ai/                # Sistema de IA
│   │   └── utils/             # Utilitários
│   ├── alembic/               # Migrations
│   └── tests/                 # Testes
│
├── frontend/                   # Aplicação React
│   ├── src/
│   │   ├── components/        # Componentes React
│   │   ├── pages/             # Páginas
│   │   ├── services/          # Serviços API
│   │   ├── utils/             # Utilitários
│   │   ├── constants/         # Constantes
│   │   └── types/             # Tipos TypeScript
│   └── public/                # Arquivos estáticos
│
├── docs/                       # Documentação
└── README.md                   # Este arquivo
```

### Fluxo de Dados

```
┌─────────────┐      HTTPS      ┌──────────────┐
│   React     │ ◄──────────────► │   FastAPI    │
│  Frontend   │      REST API    │   Backend    │
└─────────────┘                  └──────┬───────┘
                                        │
                                        │ SQLAlchemy
                                        ▼
                                 ┌──────────────┐
                                 │  PostgreSQL  │
                                 │   Database   │
                                 └──────────────┘
```

### Sistema de Autenticação

```
1. Login → JWT Token (access + refresh)
2. Token em localStorage
3. Interceptor Axios adiciona token em requests
4. Backend valida token
5. Permissões verificadas por role + resource + action
```

---

## Instalação

### Pré-requisitos

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Git

### Backend

```bash
# Clonar repositório
git clone https://github.com/iogar/food-cost-system.git
cd food-cost-system/backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Baixar modelo de IA (português)
python -m spacy download pt_core_news_sm

# Configurar banco de dados
cp .env.example .env
# Editar .env com suas credenciais PostgreSQL

# Executar migrations
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload
```

O backend estará disponível em: `http://localhost:8000`

### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com URL do backend

# Iniciar servidor de desenvolvimento
npm run dev
```

O frontend estará disponível em: `http://localhost:5173`

---

## Configuração

### Variáveis de Ambiente

#### Backend (.env)

```bash
# Banco de Dados
DATABASE_URL=postgresql://user:password@localhost:5432/foodcost

# Segurança
SECRET_KEY=sua_chave_secreta_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_V1_STR=/api/v1
PROJECT_NAME=Food Cost System

# CORS
ALLOWED_ORIGINS=http://localhost:5173

# Ambiente
ENVIRONMENT=development
DEBUG=True
```

#### Frontend (.env)

```bash
# API Backend
VITE_API_URL=http://localhost:8000

# Ambiente
VITE_ENVIRONMENT=development
```

---

## Uso

### Primeiro Acesso

1. **Acesse o sistema**: `http://localhost:5173`
2. **Login padrão de administrador**:
   - Email: `admin@iogar.com.br`
   - Senha: `admin123`
3. **Altere a senha** no primeiro acesso
4. **Configure seu restaurante** em Configurações

### Fluxo Básico de Uso

1. **Cadastrar Fornecedores**
   - Menu: Gestão → Fornecedores
   - Adicionar dados completos dos fornecedores

2. **Importar/Cadastrar Ingredientes**
   - Menu: Gestão → Ingredientes
   - Importar via Excel ou cadastrar manualmente
   - Usar IA para classificação automática

3. **Criar Receitas**
   - Menu: Gestão → Receitas
   - Adicionar ingredientes
   - Definir rendimento e porções
   - Upload de foto (opcional)

4. **Gerar Relatórios**
   - Menu: Relatórios
   - Fichas técnicas em PDF
   - Análises de custo
   - Exportação para Excel

---

## Sistema de Permissões

### Níveis de Acesso

| Role | Descrição | Acesso |
|------|-----------|--------|
| **ADMIN** | Administrador do sistema | Acesso total irrestrito |
| **CONSULTANT** | Consultor IOGAR | Gestão completa exceto configurações |
| **OWNER** | Proprietário da rede | Dados de toda a rede |
| **MANAGER** | Gerente da loja | Dados da loja específica |
| **OPERATOR** | Operador | Apenas visualização |

### Recursos Controlados

- Dashboard
- Ingredientes
- Receitas
- Fornecedores
- Restaurantes
- Usuários
- IA Classificação
- Relatórios
- Configurações
- Monitoramento

### Ações Disponíveis

- VISUALIZAR
- CRIAR
- EDITAR
- DELETAR
- GERENCIAR

---

## API

### Endpoints Principais

#### Autenticação
```
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
```

#### Ingredientes
```
GET    /api/v1/ingredientes
POST   /api/v1/ingredientes
GET    /api/v1/ingredientes/{id}
PUT    /api/v1/ingredientes/{id}
DELETE /api/v1/ingredientes/{id}
POST   /api/v1/ingredientes/importar/excel
```

#### Receitas
```
GET    /api/v1/receitas
POST   /api/v1/receitas
GET    /api/v1/receitas/{id}
PUT    /api/v1/receitas/{id}
DELETE /api/v1/receitas/{id}
GET    /api/v1/receitas/{id}/pdf
POST   /api/v1/receitas/{id}/foto
```

#### IA
```
POST   /api/v1/ia/classificar
POST   /api/v1/ia/classificar-lote
POST   /api/v1/ia/feedback
```

### Documentação Completa

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Testes

### Backend

```bash
cd backend

# Executar todos os testes
pytest

# Testes com cobertura
pytest --cov=app tests/

# Testes específicos
pytest tests/test_ingredientes.py
```

### Frontend

```bash
cd frontend

# Executar testes
npm test

# Testes com cobertura
npm run test:coverage
```

---

## Deploy

### Deploy no Render

O sistema utiliza deploy automático via GitHub Actions.

#### Backend

1. Criar Web Service no Render
2. Conectar repositório GitHub
3. Configurar build command:
   ```bash
   pip install -r requirements.txt && python -m spacy download pt_core_news_sm && alembic upgrade head
   ```
4. Start command:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

#### Frontend

1. Criar Static Site no Render
2. Build command:
   ```bash
   npm ci && npm run build
   ```
3. Publish directory: `dist`

### Variáveis de Ambiente em Produção

Configure as seguintes variáveis no painel do Render:

```
DATABASE_URL=postgresql://...
SECRET_KEY=...
ENVIRONMENT=production
DEBUG=False
ALLOWED_ORIGINS=https://seu-dominio.com
```

---

## Segurança

### Boas Práticas Implementadas

- Autenticação JWT com refresh tokens
- Senhas criptografadas com bcrypt
- CORS configurado corretamente
- SQL Injection prevenido (SQLAlchemy ORM)
- XSS prevenido (sanitização de inputs)
- Rate limiting (em desenvolvimento)
- Logs de auditoria completos

### Recomendações

1. **Sempre use HTTPS em produção**
2. **Rotacione SECRET_KEY periodicamente**
3. **Mantenha dependências atualizadas**
4. **Faça backups regulares do banco**
5. **Monitore logs de acesso**

---

## Contribuindo

### Fluxo de Trabalho

1. Fork do projeto
2. Criar branch de feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit das alterações (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para o branch (`git push origin feature/nova-funcionalidade`)
5. Abrir Pull Request

### Padrões de Código

#### Python (Backend)

- Seguir PEP 8
- Docstrings em todas as funções
- Type hints sempre que possível
- Comentários explicativos em blocos complexos
- Testes unitários obrigatórios

```python
# Exemplo de padrão
def calcular_custo_receita(
    receita_id: int,
    considerar_yield: bool = True
) -> Decimal:
    """
    Calcula o custo total de uma receita.
    
    Args:
        receita_id: ID da receita
        considerar_yield: Se deve considerar rendimento
        
    Returns:
        Custo total em Decimal
        
    Raises:
        ReceitaNotFoundError: Se receita não existir
    """
    # Implementação...
    pass
```

#### TypeScript (Frontend)

- Interfaces para todos os tipos
- Componentes funcionais com hooks
- Comentários JSDoc
- CSS com Tailwind

```typescript
// Exemplo de padrão
interface Receita {
  id: number;
  nome: string;
  custo_total: number;
  rendimento: number;
}

/**
 * Componente para exibir detalhes de uma receita
 */
const ReceitaDetalhes: React.FC<{ receita: Receita }> = ({ receita }) => {
  // Implementação...
};
```

### Commits

Usar conventional commits:

```
feat: adiciona nova funcionalidade
fix: corrige bug
docs: atualiza documentação
style: formatação de código
refactor: refatoração de código
test: adiciona testes
chore: tarefas de manutenção
```

---

## Roadmap

### Em Desenvolvimento

- [ ] Upload de fotos de receitas
- [ ] Geração de cardápios PDF
- [ ] Sistema de notificações
- [ ] Relatórios avançados

### Planejado (Q1 2025)

- [ ] App mobile (React Native)
- [ ] Integração com PDV
- [ ] Dashboard executivo
- [ ] Sistema de custos preditivo (IA)

### Futuro

- [ ] Multi-idioma (EN, ES)
- [ ] Dark mode
- [ ] API pública
- [ ] Marketplace de receitas

---

## Suporte

### Documentação

- **Manual do Usuário**: `/docs/manual-usuario.pdf`
- **Manual do Desenvolvedor**: `/docs/manual-desenvolvedor.pdf`
- **FAQ**: `/docs/FAQ.md`

### Contato

- **Email**: suporte@iogar.com.br
- **Telefone**: +55 (11) 1234-5678
- **Website**: https://iogar.com.br

### Reportar Bugs

1. Verificar se já existe issue aberta
2. Criar nova issue no GitHub
3. Incluir:
   - Descrição detalhada
   - Passos para reproduzir
   - Screenshots (se aplicável)
   - Ambiente (OS, navegador, versão)

---

## Equipe

### Desenvolvimento

| Nome | Função | GitHub |
|------|--------|--------|
| Will | Full Stack Developer | [@willzin](https://github.com/willzin) |

### IOGAR Consultoria

- **CEO**: [Nome]
- **CTO**: [Nome]
- **Product Owner**: [Nome]

---

## Licença

Este projeto é propriedade da **IOGAR Consultoria** e está sob licença proprietária. 

**Todos os direitos reservados © 2025 IOGAR Consultoria**

Para uso comercial ou licenciamento, entre em contato através de: contato@iogar.com.br

---

## Agradecimentos

Agradecimentos especiais a:

- Equipe IOGAR pela visão do produto
- Restaurantes parceiros pelos feedbacks
- Comunidade open-source pelas ferramentas utilizadas

---

<div align="center">

**Desenvolvido com ❤️ pela [IOGAR Consultoria](https://iogar.com.br)**

[⬆ Voltar ao topo](#food-cost-system)

</div>