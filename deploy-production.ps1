# ============================================================================
# SCRIPT DE DEPLOY - PRODUCTION (RENDER)
# ============================================================================
# Descrição: Deploy automático para ambiente de produção no Render
# Branch: main
# Data: 25/11/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Red
Write-Host "  DEPLOY PRODUCTION - FOOD COST SYSTEM" -ForegroundColor Red
Write-Host "============================================================================" -ForegroundColor Red
Write-Host ""

# Verificar se está na branch correta
$currentBranch = git branch --show-current

if ($currentBranch -ne "main") {
    Write-Host "ERRO: Você deve estar na branch 'main' para deploy em produção!" -ForegroundColor Red
    Write-Host "Branch atual: $currentBranch" -ForegroundColor Yellow
    exit 1
}

# Verificar se há mudanças não commitadas
$status = git status --porcelain
if ($status) {
    Write-Host ""
    Write-Host "ERRO: Há mudanças não commitadas!" -ForegroundColor Red
    git status --short
    Write-Host ""
    Write-Host "Commit todas as mudanças antes de fazer deploy em produção." -ForegroundColor Yellow
    exit 1
}

# Confirmação de deploy em produção
Write-Host ""
Write-Host "ATENÇÃO: Você está prestes a fazer deploy em PRODUÇÃO!" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Tem certeza que deseja continuar? Digite 'PRODUÇÃO' para confirmar"

if ($confirm -ne "PRODUÇÃO") {
    Write-Host ""
    Write-Host "Deploy cancelado." -ForegroundColor Red
    exit 1
}

# Push para main
Write-Host ""
Write-Host "Fazendo push para branch main..." -ForegroundColor Cyan
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Deploy em PRODUÇÃO iniciado com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Acompanhe o deploy em:" -ForegroundColor Cyan
    Write-Host "https://dashboard.render.com" -ForegroundColor White
    Write-Host ""
    Write-Host "Após o deploy, acesse:" -ForegroundColor Cyan
    Write-Host "Frontend: https://food-cost-frontend.onrender.com" -ForegroundColor White
    Write-Host "Backend:  https://food-cost-backend.onrender.com" -ForegroundColor White
    Write-Host ""
    Write-Host "IMPORTANTE: Teste tudo em staging antes de usar em produção!" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Erro ao fazer push!" -ForegroundColor Red
    exit 1
}