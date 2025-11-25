#!/bin/bash

# ============================================================================
# SCRIPTS DE AUTOMAÇÃO DOCKER - FOOD COST SYSTEM
# ============================================================================
# Descrição: Scripts para facilitar operações com Docker
# Funcionalidades: Build, start, stop, reset, logs, backup
# Data: 17/09/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Nome do projeto
PROJECT_NAME="foodcost"

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

# Função para exibir cabeçalho
print_header() {
    echo -e "${BLUE}"
    echo "============================================================================"
    echo "  FOOD COST SYSTEM - DOCKER MANAGEMENT"
    echo "============================================================================"
    echo -e "${NC}"
}

# Função para exibir mensagens de sucesso
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Função para exibir mensagens de erro
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Função para exibir mensagens de aviso
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Função para exibir mensagens informativas
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Verificar se Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker não está instalado!"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose não está instalado!"
        exit 1
    fi
}

# Verificar se arquivo .env existe
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning "Arquivo .env não encontrado!"
        print_info "Copiando .env.example para .env..."
        cp .env.example .env
        print_warning "IMPORTANTE: Edite o arquivo .env e configure as variáveis antes de continuar!"
        exit 1
    fi
}

# ============================================================================
# FUNÇÕES PRINCIPAIS
# ============================================================================

# Função para setup inicial
setup() {
    print_header
    print_info "Configurando ambiente inicial..."
    
    check_docker
    check_env_file
    
    # Criar diretórios necessários se não existirem
    mkdir -p database
    mkdir -p backend/app/ai/data
    mkdir -p backend/app/ai/logs
    
    print_success "Setup inicial concluído!"
}

# Função para build das imagens
build() {
    print_header
    print_info "Construindo imagens Docker..."
    
    setup
    
    # Build das imagens
    docker-compose build --no-cache
    
    if [ $? -eq 0 ]; then
        print_success "Build das imagens concluído!"
    else
        print_error "Falha no build das imagens!"
        exit 1
    fi
}

# Função para iniciar todos os serviços
start() {
    print_header
    print_info "Iniciando todos os serviços..."
    
    setup
    
    # Iniciar serviços em background
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        print_success "Todos os serviços foram iniciados!"
        print_info "Frontend: http://localhost"
        print_info "Backend API: http://localhost:8000"
        print_info "API Docs: http://localhost:8000/docs"
        print_info "PostgreSQL: localhost:5432"
    else
        print_error "Falha ao iniciar os serviços!"
        exit 1
    fi
}

# Função para parar todos os serviços
stop() {
    print_header
    print_info "Parando todos os serviços..."
    
    docker-compose down
    
    print_success "Todos os serviços foram parados!"
}

# Função para restart de todos os serviços
restart() {
    print_header
    print_info "Reiniciando todos os serviços..."
    
    stop
    start
}

# Função para reset completo (remove containers, volumes, imagens)
reset() {
    print_header
    print_warning "ATENÇÃO: Esta operação irá remover TODOS os dados!"
    read -p "Tem certeza que deseja continuar? (s/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        print_info "Removendo containers, volumes e imagens..."
        
        # Parar e remover containers
        docker-compose down -v --remove-orphans
        
        # Remover imagens do projeto
        docker rmi $(docker images -q "${PROJECT_NAME}*") 2>/dev/null || true
        
        # Remover volumes
        docker volume rm ${PROJECT_NAME}_postgres_data 2>/dev/null || true
        docker volume rm ${PROJECT_NAME}_redis_data 2>/dev/null || true
        docker volume rm ${PROJECT_NAME}_ai_data 2>/dev/null || true
        docker volume rm ${PROJECT_NAME}_ai_logs 2>/dev/null || true
        
        print_success "Reset completo concluído!"
    else
        print_info "Operação cancelada."
    fi
}

# Função para exibir logs
logs() {
    service=${2:-""}
    
    if [ -z "$service" ]; then
        print_info "Exibindo logs de todos os serviços..."
        docker-compose logs -f
    else
        print_info "Exibindo logs do serviço: $service"
        docker-compose logs -f "$service"
    fi
}

# Função para exibir status dos serviços
status() {
    print_header
    print_info "Status dos serviços:"
    docker-compose ps
}

# Função para backup do banco de dados
backup() {
    print_header
    print_info "Criando backup do banco de dados..."
    
    # Criar diretório de backup se não existir
    mkdir -p backups
    
    # Nome do arquivo de backup com timestamp
    backup_file="backups/foodcost_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # Executar backup
    docker-compose exec -T db pg_dump -U postgres food_cost_db > "$backup_file"
    
    if [ $? -eq 0 ]; then
        print_success "Backup criado: $backup_file"
    else
        print_error "Falha ao criar backup!"
    fi
}

# Função para exibir ajuda
help() {
    print_header
    echo "Comandos disponíveis:"
    echo ""
    echo "  setup     - Configuração inicial do ambiente"
    echo "  build     - Construir imagens Docker"
    echo "  start     - Iniciar todos os serviços"
    echo "  stop      - Parar todos os serviços"
    echo "  restart   - Reiniciar todos os serviços"
    echo "  reset     - Reset completo (REMOVE TODOS OS DADOS)"
    echo "  logs      - Exibir logs (usar: logs [nome_do_serviço])"
    echo "  status    - Status dos serviços"
    echo "  backup    - Backup do banco de dados"
    echo "  help      - Exibir esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  ./docker-scripts.sh start"
    echo "  ./docker-scripts.sh logs backend"
    echo "  ./docker-scripts.sh backup"
    echo ""
}

# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================

case "${1}" in
    setup)
        setup
        ;;
    build)
        build
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    reset)
        reset
        ;;
    logs)
        logs "$@"
        ;;
    status)
        status
        ;;
    backup)
        backup
        ;;
    help|--help|-h)
        help
        ;;
    *)
        print_error "Comando inválido: ${1}"
        echo ""
        help
        exit 1
        ;;
esac