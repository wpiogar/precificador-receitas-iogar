# SCRIPTS DE AUTOMACAO DOCKER - FOOD COST SYSTEM (POWERSHELL)
# Descricao: Scripts PowerShell para facilitar operacoes com Docker no Windows
# Funcionalidades: Build, start, stop, reset, logs, backup
# Data: 17/09/2025 - Autor: Will - IOGAR

param(
    [Parameter(Mandatory=$true)]
    [string]$Command,
    [string]$Service = ""
)

# Nome do projeto
$PROJECT_NAME = "foodcost"

# FUNCOES AUXILIARES
function Write-Header {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Blue
    Write-Host "  FOOD COST SYSTEM - DOCKER MANAGEMENT" -ForegroundColor Blue
    Write-Host "================================================================================" -ForegroundColor Blue
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

# Verificar se Docker esta instalado
function Test-Docker {
    try {
        $null = Get-Command docker -ErrorAction Stop
        $null = Get-Command docker-compose -ErrorAction Stop
        return $true
    }
    catch {
        Write-Error "Docker ou Docker Compose nao esta instalado!"
        return $false
    }
}

# Verificar se arquivo .env existe
function Test-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Warning "Arquivo .env nao encontrado!"
        Write-Info "Copiando .env.example para .env..."
        
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Warning "IMPORTANTE: Edite o arquivo .env e configure as variaveis antes de continuar!"
            return $false
        } else {
            Write-Error "Arquivo .env.example nao encontrado!"
            return $false
        }
    }
    return $true
}

# FUNCOES PRINCIPAIS
function Invoke-Setup {
    Write-Header
    Write-Info "Configurando ambiente inicial..."
    
    if (-not (Test-Docker)) {
        exit 1
    }
    
    if (-not (Test-EnvFile)) {
        exit 1
    }
    
    # Criar diretorios necessarios se nao existirem
    $directories = @("database", "backend\app\ai\data", "backend\app\ai\logs")
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Success "Setup inicial concluido!"
}

function Invoke-Build {
    Write-Header
    Write-Info "Construindo imagens Docker..."
    
    Invoke-Setup
    
    # Build das imagens
    & docker-compose build --no-cache
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Build das imagens concluido!"
    } else {
        Write-Error "Falha no build das imagens!"
        exit 1
    }
}

function Invoke-Start {
    Write-Header
    Write-Info "Iniciando todos os servicos..."
    
    Invoke-Setup
    
    # Iniciar servicos em background
    & docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Todos os servicos foram iniciados!"
        Write-Info "Frontend: http://localhost"
        Write-Info "Backend API: http://localhost:8000"
        Write-Info "API Docs: http://localhost:8000/docs"
        Write-Info "PostgreSQL: localhost:5432"
    } else {
        Write-Error "Falha ao iniciar os servicos!"
        exit 1
    }
}

function Invoke-Stop {
    Write-Header
    Write-Info "Parando todos os servicos..."
    
    & docker-compose down
    
    Write-Success "Todos os servicos foram parados!"
}

function Invoke-Restart {
    Write-Header
    Write-Info "Reiniciando todos os servicos..."
    
    Invoke-Stop
    Invoke-Start
}

function Invoke-Reset {
    Write-Header
    Write-Warning "ATENCAO: Esta operacao ira remover TODOS os dados!"
    
    $confirmation = Read-Host "Tem certeza que deseja continuar? (s/N)"
    
    if ($confirmation -match "^[Ss]$") {
        Write-Info "Removendo containers, volumes e imagens..."
        
        # Parar e remover containers
        & docker-compose down -v --remove-orphans
        
        # Remover imagens do projeto
        $images = & docker images -q "$PROJECT_NAME*" 2>$null
        if ($images) {
            & docker rmi $images 2>$null
        }
        
        # Remover volumes
        $volumes = @(
            "${PROJECT_NAME}_postgres_data",
            "${PROJECT_NAME}_redis_data", 
            "${PROJECT_NAME}_ai_data",
            "${PROJECT_NAME}_ai_logs"
        )
        
        foreach ($volume in $volumes) {
            & docker volume rm $volume 2>$null
        }
        
        Write-Success "Reset completo concluido!"
    } else {
        Write-Info "Operacao cancelada."
    }
}

function Invoke-Logs {
    param([string]$ServiceName = "")
    
    if ([string]::IsNullOrEmpty($ServiceName)) {
        Write-Info "Exibindo logs de todos os servicos..."
        & docker-compose logs -f
    } else {
        Write-Info "Exibindo logs do servico: $ServiceName"
        & docker-compose logs -f $ServiceName
    }
}

function Invoke-Status {
    Write-Header
    Write-Info "Status dos servicos:"
    & docker-compose ps
}

function Invoke-Backup {
    Write-Header
    Write-Info "Criando backup do banco de dados..."
    
    # Criar diretorio de backup se nao existir
    if (-not (Test-Path "backups")) {
        New-Item -ItemType Directory -Path "backups" -Force | Out-Null
    }
    
    # Nome do arquivo de backup com timestamp
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "backups\foodcost_backup_$timestamp.sql"
    
    # Executar backup
    & docker-compose exec -T db pg_dump -U $env:POSTGRES_USER $env:POSTGRES_DB | Out-File -FilePath $backupFile -Encoding UTF8
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Backup criado: $backupFile"
    } else {
        Write-Error "Falha ao criar backup!"
    }
}

function Show-Help {
    Write-Header
    Write-Host "Comandos disponiveis:" -ForegroundColor White
    Write-Host ""
    Write-Host "  setup     - Configuracao inicial do ambiente" -ForegroundColor Gray
    Write-Host "  build     - Construir imagens Docker" -ForegroundColor Gray
    Write-Host "  start     - Iniciar todos os servicos" -ForegroundColor Gray
    Write-Host "  stop      - Parar todos os servicos" -ForegroundColor Gray
    Write-Host "  restart   - Reiniciar todos os servicos" -ForegroundColor Gray
    Write-Host "  reset     - Reset completo (REMOVE TODOS OS DADOS)" -ForegroundColor Gray
    Write-Host "  logs      - Exibir logs" -ForegroundColor Gray
    Write-Host "  status    - Status dos servicos" -ForegroundColor Gray
    Write-Host "  backup    - Backup do banco de dados" -ForegroundColor Gray
    Write-Host "  help      - Exibir esta ajuda" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Exemplos:" -ForegroundColor White
    Write-Host "  .\docker-scripts.ps1 start" -ForegroundColor Yellow
    Write-Host "  .\docker-scripts.ps1 logs -Service backend" -ForegroundColor Yellow
    Write-Host "  .\docker-scripts.ps1 backup" -ForegroundColor Yellow
    Write-Host ""
}

# EXECUCAO PRINCIPAL
switch ($Command.ToLower()) {
    "setup" { Invoke-Setup }
    "build" { Invoke-Build }
    "start" { Invoke-Start }
    "stop" { Invoke-Stop }
    "restart" { Invoke-Restart }
    "reset" { Invoke-Reset }
    "logs" { Invoke-Logs -ServiceName $Service }
    "status" { Invoke-Status }
    "backup" { Invoke-Backup }
    "help" { Show-Help }
    default {
        Write-Error "Comando invalido: $Command"
        Write-Host ""
        Show-Help
        exit 1
    }
}