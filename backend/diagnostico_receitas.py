"""
============================================================================
SCRIPT DE DIAGNÓSTICO - RECEITAS NO BANCO DE DADOS
============================================================================
Descrição: Verifica a quantidade real de receitas por restaurante
Data: 12/12/2025
Autor: Will - Empresa: IOGAR
============================================================================
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import get_db
from app.models.receita import Receita, Restaurante
from sqlalchemy import func

# ============================================================================
# CONFIGURAÇÃO DO BANCO
# ============================================================================

def obter_session():
    """Obtém sessão do banco de dados"""
    from app.database import SessionLocal
    return SessionLocal()

# ============================================================================
# FUNÇÃO PRINCIPAL DE DIAGNÓSTICO
# ============================================================================

def diagnosticar_receitas():
    """
    Executa diagnóstico completo das receitas no banco.
    """
    print("=" * 80)
    print("🔍 DIAGNÓSTICO DE RECEITAS NO BANCO DE DADOS")
    print("=" * 80)
    print()
    
    db = obter_session()
    
    try:
        # ====================================================================
        # 1. CONTAR TOTAL DE RECEITAS (SEM FILTROS)
        # ====================================================================
        total_receitas_geral = db.query(func.count(Receita.id)).scalar()
        print(f"📊 TOTAL GERAL DE RECEITAS NO BANCO: {total_receitas_geral}")
        print()
        
        # ====================================================================
        # 2. RECEITAS COM restaurante_id NULL
        # ====================================================================
        receitas_sem_restaurante = db.query(func.count(Receita.id)).filter(
            Receita.restaurante_id.is_(None)
        ).scalar()
        print(f"⚠️  Receitas SEM restaurante_id: {receitas_sem_restaurante}")
        print()
        
        # ====================================================================
        # 3. RECEITAS POR RESTAURANTE
        # ====================================================================
        print("📍 RECEITAS POR RESTAURANTE:")
        print("-" * 80)
        
        restaurantes = db.query(Restaurante).all()
        
        for restaurante in restaurantes:
            total = db.query(func.count(Receita.id)).filter(
                Receita.restaurante_id == restaurante.id
            ).scalar()
            
            print(f"   ID {restaurante.id:3d} | {restaurante.nome:30s} | {total:4d} receitas")
        
        print()
        
        # ====================================================================
        # 4. RECEITAS POR GRUPO
        # ====================================================================
        print("📂 RECEITAS POR GRUPO:")
        print("-" * 80)
        
        grupos = db.query(
            Receita.grupo,
            func.count(Receita.id).label('total')
        ).filter(
            Receita.restaurante_id.isnot(None)
        ).group_by(Receita.grupo).all()
        
        for grupo, total in grupos:
            print(f"   {grupo:20s} | {total:4d} receitas")
        
        print()
        
        # ====================================================================
        # 5. ÚLTIMAS 10 RECEITAS CRIADAS
        # ====================================================================
        print("🆕 ÚLTIMAS 10 RECEITAS CRIADAS:")
        print("-" * 80)
        
        ultimas_receitas = db.query(Receita).order_by(
            Receita.created_at.desc()
        ).limit(10).all()
        
        for receita in ultimas_receitas:
            rest_nome = "SEM RESTAURANTE"
            if receita.restaurante_id:
                rest = db.query(Restaurante).filter(
                    Restaurante.id == receita.restaurante_id
                ).first()
                rest_nome = rest.nome if rest else "RESTAURANTE INVÁLIDO"
            
            print(f"   ID: {receita.id:4d} | {receita.nome:30s} | Rest: {rest_nome}")
        
        print()
        
        # ====================================================================
        # 6. VERIFICAR FILTRO USADO NO ENDPOINT
        # ====================================================================
        print("🔍 SIMULANDO FILTRO DO ENDPOINT get_receitas():")
        print("-" * 80)
        
        # Simular query do crud
        query_simulada = db.query(Receita).filter(
            Receita.restaurante_id.isnot(None)
        )
        
        total_com_filtro = query_simulada.count()
        print(f"   Total com filtro restaurante_id.isnot(None): {total_com_filtro}")
        print()
        
        # ====================================================================
        # 7. RESUMO FINAL
        # ====================================================================
        print("=" * 80)
        print("📋 RESUMO DO DIAGNÓSTICO:")
        print("=" * 80)
        print(f"   Total de receitas no banco: {total_receitas_geral}")
        print(f"   Receitas sem restaurante_id: {receitas_sem_restaurante}")
        print(f"   Receitas COM restaurante_id: {total_com_filtro}")
        print(f"   Total de restaurantes: {len(restaurantes)}")
        print()
        
        if receitas_sem_restaurante > 0:
            print("⚠️  ATENÇÃO: Existem receitas órfãs (sem restaurante_id)")
            print("   Estas receitas NÃO aparecem na listagem devido ao filtro.")
            print()
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

# ============================================================================
# EXECUTAR DIAGNÓSTICO
# ============================================================================

if __name__ == "__main__":
    diagnosticar_receitas()