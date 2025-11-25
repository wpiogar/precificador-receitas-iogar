# ============================================================================
# SCRIPT DE DEPLOY - STAGING (RENDER)
# ============================================================================
# Descrição: Deploy automático para ambiente de staging no Render
# Branch: staging
# Data: 25/11/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Blue
Write-Host "  DEPLOY STAGING - FOOD COST SYSTEM" -ForegroundColor Blue
Write-Host "============================================================================" -ForegroundColor Blue
Write-Host ""

# Verificar se está na branch correta
$currentBranch = git branch --show-current

if ($currentBranch -ne "staging") {
    Write-Host "AVISO: Você está na branch '$currentBranch', não 'staging'" -ForegroundColor Yellow
    $continue = Read-Host "Deseja continuar mesmo assim? (s/N)"
    if ($continue -notmatch "^[Ss]$") {
        Write-Host "Deploy cancelado." -ForegroundColor Red
        exit 1
    }
}

# Verificar se há mudanças não commitadas
$status = git status --porcelain
if ($status) {
    Write-Host ""
    Write-Host "AVISO: Há mudanças não commitadas:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    $continue = Read-Host "Deseja continuar? As mudanças não commitadas não serão deployadas (s/N)"
    if ($continue -notmatch "^[Ss]$") {
        Write-Host "Deploy cancelado." -ForegroundColor Red
        exit 1
    }
}

# Push para staging
Write-Host ""
Write-Host "Fazendo push para branch staging..." -ForegroundColor Cyan
git push origin staging

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Deploy iniciado com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Acompanhe o deploy em:" -ForegroundColor Cyan
    Write-Host "https://dashboard.render.com" -ForegroundColor White
    Write-Host ""
    Write-Host "Após o deploy, acesse:" -ForegroundColor Cyan
    Write-Host "Frontend: https://food-cost-frontend-staging.onrender.com" -ForegroundColor White
    Write-Host "Backend:  https://food-cost-backend-staging.onrender.com" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Erro ao fazer push!" -ForegroundColor Red
    exit 1
}