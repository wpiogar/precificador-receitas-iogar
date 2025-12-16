# ============================================================================
# SCRIPT DE DIAGNÓSTICO VIA API - Verificar Permissões do CONSULTANT
# ============================================================================
# Descrição: Verifica permissões via API em produção
# Data: 16/12/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

import requests
import json

# Configurações
BASE_URL = "http://localhost:8000/api/v1"
# BASE_URL = "http://localhost:8000/api/v1"  # Usar local se preferir

def fazer_login():
    """Faz login e retorna o token"""
    print("\n" + "=" * 80)
    print("FAZENDO LOGIN")
    print("=" * 80)
    print("\nPara verificar permissões, precisamos logar como ADMIN")
    print("(CONSULTANT não pode ver suas próprias permissões)")
    
    # Solicitar credenciais
    email = input("\nEmail do ADMIN: ")
    senha = input("Senha: ")
    
    # Testar URL primeiro
    url_login = f"{BASE_URL}/auth/login"
    print(f"\nTestando URL: {url_login}")
    
    # Tentar formato JSON (conforme código do backend)
    print("Tentando login com JSON...")
    response = requests.post(
        url_login,
        json={"username": email, "password": senha}
    )
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text[:200]}")
    
    # Se não funcionar, tentar JSON
    if response.status_code == 404:
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": email, "password": senha}
        )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Login realizado com sucesso!")
        return token
    else:
        print(f"❌ Erro no login: {response.status_code}")
        print(response.text)
        return None

def verificar_permissoes(token):
    """Verifica permissões do CONSULTANT"""
    print("\n" + "=" * 80)
    print("VERIFICANDO PERMISSÕES DO CONSULTANT")
    print("=" * 80)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/permissions/role/CONSULTANT",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Erro ao buscar permissões: {response.status_code}")
        print(response.text)
        return
    
    permissoes = response.json()
    
    print(f"\nTotal de permissões: {len(permissoes)}")
    
    # Agrupar por recurso
    por_recurso = {}
    for perm in permissoes:
        recurso = perm['resource']
        if recurso not in por_recurso:
            por_recurso[recurso] = []
        por_recurso[recurso].append(perm)
    
    print("\n" + "-" * 80)
    print("RECURSOS CRÍTICOS PARA DASHBOARD:")
    print("-" * 80)
    
    recursos_criticos = ['DASHBOARD', 'INSUMOS', 'RECEITAS']
    
    for recurso in recursos_criticos:
        print(f"\n{recurso}:")
        if recurso not in por_recurso:
            print("  ❌ NENHUMA PERMISSÃO CADASTRADA!")
        else:
            for perm in por_recurso[recurso]:
                status = "✅ HABILITADA" if perm['enabled'] else "❌ DESABILITADA"
                print(f"  - {perm['action']}: {status} (escopo: {perm['data_scope']})")
    
    # Resumo de permissões habilitadas
    print("\n" + "-" * 80)
    print("RESUMO:")
    print("-" * 80)
    
    habilitadas = [p for p in permissoes if p['enabled']]
    desabilitadas = [p for p in permissoes if not p['enabled']]
    
    print(f"\n✅ Permissões habilitadas: {len(habilitadas)}")
    print(f"❌ Permissões desabilitadas: {len(desabilitadas)}")
    
    # Verificar especificamente VISUALIZAR nos recursos críticos
    print("\n" + "-" * 80)
    print("ANÁLISE: Permissões VISUALIZAR necessárias para Dashboard")
    print("-" * 80)
    
    for recurso in recursos_criticos:
        visualizar = next(
            (p for p in permissoes if p['resource'] == recurso and p['action'] == 'VISUALIZAR'),
            None
        )
        
        if visualizar is None:
            print(f"❌ {recurso}: PERMISSÃO NÃO EXISTE")
        elif not visualizar['enabled']:
            print(f"❌ {recurso}: PERMISSÃO EXISTE MAS ESTÁ DESABILITADA (ID: {visualizar['id']})")
        else:
            print(f"✅ {recurso}: PERMISSÃO HABILITADA")

if __name__ == "__main__":
    token = fazer_login()
    if token:
        verificar_permissoes(token)