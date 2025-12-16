# ============================================================================
# SCRIPT DE DIAGNÓSTICO - Verificar Permissões do CONSULTANT
# ============================================================================
# Descrição: Verifica se CONSULTANT tem permissões habilitadas
# Data: 16/12/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal

def verificar_permissoes_consultant():
    """
    Verifica permissões do perfil CONSULTANT no banco de dados
    """
    db: Session = SessionLocal()
    
    try:
        print("\n" + "=" * 80)
        print("DIAGNÓSTICO: Permissões do CONSULTANT")
        print("=" * 80)
        
        # Buscar todas as permissões do CONSULTANT usando SQL direto
        query = text("""
            SELECT id, role, resource, action, data_scope, enabled
            FROM permissions
            WHERE role = 'CONSULTANT'
            ORDER BY resource, action
        """)
        
        result = db.execute(query)
        permissoes_raw = result.fetchall()
        
        # Converter para objetos simples
        class PermissaoSimples:
            def __init__(self, row):
                self.id = row[0]
                self.role = row[1]
                self.resource = row[2]
                self.action = row[3]
                self.data_scope = row[4]
                self.enabled = row[5]
        
        permissoes = [PermissaoSimples(row) for row in permissoes_raw]
        
        if not permissoes:
            print("\nNENHUMA PERMISSÃO ENCONTRADA PARA CONSULTANT!")
            print("Execute: POST /api/v1/permissions/generate/CONSULTANT")
            return
        
        print(f"\nTotal de permissões cadastradas: {len(permissoes)}")
        print("\n" + "-" * 80)
        print("RECURSOS CRÍTICOS PARA DASHBOARD:")
        print("-" * 80)
        
        recursos_criticos = ['DASHBOARD', 'INSUMOS', 'RECEITAS']
        
        for recurso in recursos_criticos:
            print(f"\n{recurso}:")
            perms_recurso = [p for p in permissoes if p.resource == recurso]
            
            if not perms_recurso:
                print(f"  NENHUMA PERMISSÃO CADASTRADA!")
            else:
                for perm in perms_recurso:
                    status = "HABILITADA" if perm.enabled else "DESABILITADA"
                    print(f"  - {perm.action}: {status} (escopo: {perm.data_scope})")
        
        # Verificar especificamente VISUALIZAR
        print("\n" + "-" * 80)
        print("PERMISSÕES DE VISUALIZAR (necessárias para Dashboard):")
        print("-" * 80)
        
        visualizar_perms = [p for p in permissoes if p.action == "VISUALIZAR"]
        
        if not visualizar_perms:
            print("NENHUMA PERMISSÃO DE VISUALIZAR ENCONTRADA!")
        else:
            habilitadas = [p for p in visualizar_perms if p.enabled]
            desabilitadas = [p for p in visualizar_perms if not p.enabled]
            
            print(f"\nHabilitadas ({len(habilitadas)}):")
            for perm in habilitadas:
                print(f"  - {perm.resource}")
            
            print(f"\nDesabilitadas ({len(desabilitadas)}):")
            for perm in desabilitadas:
                print(f"  - {perm.resource}")
        
        print("\n" + "=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    verificar_permissoes_consultant()