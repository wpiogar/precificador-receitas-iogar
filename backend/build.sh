#!/usr/bin/env bash
# ============================================================================
# SCRIPT DE BUILD PARA RENDER - FOOD COST SYSTEM
# ============================================================================
# Descrição: Garante instalação correta de pandas e todas as dependências
# Data: 03/12/2025
# Autor: Will - IOGAR
# ============================================================================

set -o errexit  # Parar se houver erro

echo "============================================================================"
echo "🔧 FOOD COST SYSTEM - BUILD CUSTOMIZADO"
echo "============================================================================"

# Verificar versão do Python
python --version

# Atualizar pip
echo "📦 Atualizando pip..."
pip install --upgrade pip

# Instalar pandas EXPLICITAMENTE antes de tudo
echo "============================================================================"
echo "📥 INSTALANDO PANDAS (CRÍTICO)"
echo "============================================================================"
pip install --no-cache-dir pandas==2.2.0

# Verificar se pandas foi instalado
echo "🔍 Verificando instalação do pandas..."
python -c "import pandas as pd; print(f'✅ pandas {pd.__version__} instalado com sucesso!')" || {
    echo "❌ ERRO: pandas não foi instalado corretamente"
    exit 1
}

# Instalar demais dependências do requirements.txt
echo "============================================================================"
echo "📦 INSTALANDO DEMAIS DEPENDÊNCIAS"
echo "============================================================================"
pip install --no-cache-dir -r requirements.txt

# Verificação final
echo "============================================================================"
echo "✅ VERIFICAÇÃO FINAL"
echo "============================================================================"
python -c "import pandas; print(f'✅ pandas {pandas.__version__}')"
python -c "import numpy; print(f'✅ numpy {numpy.__version__}')"
python -c "import openpyxl; print(f'✅ openpyxl {openpyxl.__version__}')"
python -c "import fastapi; print(f'✅ fastapi {fastapi.__version__}')"

echo "============================================================================"
echo "✅ BUILD CONCLUÍDO COM SUCESSO"
echo "============================================================================"