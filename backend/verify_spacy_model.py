# ============================================================================
# SCRIPT DE VERIFICAÇÃO - Modelo spaCy em Produção
# ============================================================================
# Descrição: Verifica instalação e carregamento do modelo spaCy
# Objetivo: Diagnosticar problemas no ambiente Render
# Data: 08/12/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

import sys
import os

def verificar_spacy():
    """
    Verifica instalação e carregamento do modelo spaCy.
    Imprime diagnóstico detalhado para debugging em produção.
    """
    print("=" * 80)
    print("DIAGNÓSTICO - Modelo spaCy")
    print("=" * 80)
    
    # Verificar Python
    print(f"\n[1] Versão Python: {sys.version}")
    print(f"[2] Executável Python: {sys.executable}")
    print(f"[3] PATH: {os.environ.get('PATH', 'N/A')}")
    
    # Verificar instalação do spaCy
    print("\n[4] Verificando spaCy...")
    try:
        import spacy
        print(f"    ✅ spaCy instalado: {spacy.__version__}")
        print(f"    📁 spaCy path: {spacy.__file__}")
    except ImportError as e:
        print(f"    ❌ spaCy não instalado: {e}")
        return False
    
    # Listar modelos instalados
    print("\n[5] Modelos spaCy instalados:")
    try:
        from spacy.cli.info import info as spacy_info
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "spacy", "info"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
    except Exception as e:
        print(f"    ⚠️ Não foi possível listar modelos: {e}")
    
    # Tentar carregar modelo português
    print("\n[6] Carregando modelo pt_core_news_sm...")
    try:
        nlp = spacy.load("pt_core_news_sm")
        print("    ✅ Modelo carregado com sucesso!")
        print(f"    📊 Pipeline: {nlp.pipe_names}")
        print(f"    🌍 Idioma: {nlp.lang}")
        return True
    except OSError as e:
        print(f"    ❌ Modelo não encontrado: {e}")
        
        # Tentar localizar onde o modelo deveria estar
        print("\n[7] Procurando modelo no sistema...")
        site_packages = [p for p in sys.path if 'site-packages' in p]
        for path in site_packages:
            pt_path = os.path.join(path, 'pt_core_news_sm')
            if os.path.exists(pt_path):
                print(f"    📁 Encontrado em: {pt_path}")
            else:
                print(f"    ❌ Não encontrado em: {pt_path}")
        
        return False
    except Exception as e:
        print(f"    ❌ Erro ao carregar: {e}")
        return False

if __name__ == "__main__":
    print("\n")
    sucesso = verificar_spacy()
    print("\n" + "=" * 80)
    if sucesso:
        print("✅ DIAGNÓSTICO: Modelo spaCy OK")
        sys.exit(0)
    else:
        print("❌ DIAGNÓSTICO: Problema com modelo spaCy")
        sys.exit(1)
    print("=" * 80)