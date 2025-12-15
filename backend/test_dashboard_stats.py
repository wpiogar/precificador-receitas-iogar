# ============================================================================
# SCRIPT DE TESTE - Dashboard de Estatísticas da IA
# ============================================================================
# Descrição: Testa endpoints de estatísticas completas
# Data: 08/12/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

import requests
import json
from datetime import datetime, timedelta

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

# URL da API (ajustar conforme ambiente)
BASE_URL = "http://localhost:8000/api/v1"
# BASE_URL = "https://food-cost-backend.onrender.com/api/v1"

# Credenciais de teste (ajustar conforme seu usuário)
USERNAME = "admin"
PASSWORD = "admin123"

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def fazer_login():
    """
    Realiza login e retorna o token de acesso.
    
    Returns:
        Token JWT ou None em caso de erro
    """
    print("\n" + "=" * 80)
    print("🔐 FAZENDO LOGIN")
    print("=" * 80)
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": USERNAME,
                "password": PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Login realizado com sucesso")
            return token
        else:
            print(f"❌ Erro no login: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao fazer login: {e}")
        return None


def testar_dashboard_30_dias(token):
    """
    Testa endpoint do dashboard com período de 30 dias.
    
    Args:
        token: Token JWT de autenticação
    """
    print("\n" + "=" * 80)
    print("📊 TESTE 1: Dashboard - Últimos 30 Dias")
    print("=" * 80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/ia/estatisticas/dashboard?periodo=30d",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ Sucesso! Dados recebidos:")
            print(f"\n📌 Cards Principais:")
            cards = data.get('cards_principais', {})
            for key, card in cards.items():
                print(f"   - {card['label']}: {card['valor']} {card['unidade']}")
            
            print(f"\n📌 Estatísticas do Período:")
            periodo = data.get('estatisticas_periodo', {})
            print(f"   - Total de classificações: {periodo.get('total_classificacoes', 0)}")
            print(f"   - Taxa de acerto: {periodo.get('taxa_acerto_percentual', 0)}%")
            print(f"   - Classificações por dia: {periodo.get('classificacoes_por_dia', 0)}")
            
            print(f"\n📌 Gráficos:")
            print(f"   - Evolução temporal: {len(data.get('grafico_evolucao_temporal', []))} pontos")
            print(f"   - Distribuição tipo: {len(data.get('grafico_distribuicao_tipo', []))} segmentos")
            print(f"   - Top categorias: {len(data.get('grafico_top_categorias', []))} barras")
            print(f"   - Taxa acerto temporal: {len(data.get('grafico_taxa_acerto_temporal', []))} pontos")
            
            print(f"\n📌 Tabela de Categorias:")
            tabela = data.get('tabela_categorias', [])
            print(f"   - Total de categorias: {len(tabela)}")
            if tabela:
                print(f"\n   Top 5 categorias:")
                for cat in tabela[:5]:
                    print(f"      • {cat['categoria']}: {cat['total_classificacoes']} classificações ({cat['taxa_acerto_percentual']}% acerto)")
            
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False


def testar_dashboard_7_dias(token):
    """
    Testa endpoint do dashboard com período de 7 dias.
    
    Args:
        token: Token JWT de autenticação
    """
    print("\n" + "=" * 80)
    print("📊 TESTE 2: Dashboard - Últimos 7 Dias")
    print("=" * 80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/ia/estatisticas/dashboard?periodo=7d",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Sucesso! Dashboard de 7 dias carregado")
            
            periodo = data.get('estatisticas_periodo', {})
            print(f"   - Total de classificações: {periodo.get('total_classificacoes', 0)}")
            print(f"   - Taxa de acerto: {periodo.get('taxa_acerto_percentual', 0)}%")
            
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False


def testar_periodo_customizado(token):
    """
    Testa endpoint com período customizado.
    
    Args:
        token: Token JWT de autenticação
    """
    print("\n" + "=" * 80)
    print("📊 TESTE 3: Dashboard - Período Customizado")
    print("=" * 80)
    
    try:
        # Período: últimos 15 dias
        data_fim = datetime.now()
        data_inicio = data_fim - timedelta(days=15)
        
        data_inicio_str = data_inicio.strftime('%Y-%m-%d')
        data_fim_str = data_fim.strftime('%Y-%m-%d')
        
        print(f"\n📅 Período: {data_inicio_str} até {data_fim_str}")
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/ia/estatisticas/dashboard?data_inicio={data_inicio_str}&data_fim={data_fim_str}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Sucesso! Dashboard customizado carregado")
            
            filtros = data.get('filtros_aplicados', {})
            print(f"   - Período processado: {filtros.get('total_dias', 0)} dias")
            
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False


def testar_estatisticas_categorias(token):
    """
    Testa endpoint de estatísticas por categoria.
    
    Args:
        token: Token JWT de autenticação
    """
    print("\n" + "=" * 80)
    print("📊 TESTE 4: Estatísticas por Categoria")
    print("=" * 80)
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/ia/estatisticas/categorias?periodo=30d&limite=10&ordenar_por=taxa_acerto",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Sucesso! Estatísticas por categoria carregadas")
            
            print(f"   - Total de categorias: {data.get('total_categorias', 0)}")
            print(f"   - Ordenação: {data.get('ordenacao', 'N/A')}")
            
            categorias = data.get('categorias', [])
            if categorias:
                print(f"\n   Top 3 categorias por taxa de acerto:")
                for cat in categorias[:3]:
                    print(f"      • {cat['categoria']}: {cat['taxa_acerto_percentual']}% ({cat['total_classificacoes']} classificações)")
            
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False


# ============================================================================
# EXECUÇÃO DOS TESTES
# ============================================================================

def main():
    """
    Função principal - executa todos os testes.
    """
    print("\n" + "=" * 80)
    print("🧪 TESTES DO DASHBOARD DE ESTATÍSTICAS DA IA")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Usuário: {USERNAME}")
    
    # Fazer login
    token = fazer_login()
    
    if not token:
        print("\n❌ Não foi possível fazer login. Testes abortados.")
        return
    
    # Executar testes
    resultados = []
    
    resultados.append(("Dashboard 30 dias", testar_dashboard_30_dias(token)))
    resultados.append(("Dashboard 7 dias", testar_dashboard_7_dias(token)))
    resultados.append(("Período customizado", testar_periodo_customizado(token)))
    resultados.append(("Estatísticas por categoria", testar_estatisticas_categorias(token)))
    
    # Resumo
    print("\n" + "=" * 80)
    print("📋 RESUMO DOS TESTES")
    print("=" * 80)
    
    total = len(resultados)
    sucessos = sum(1 for _, sucesso in resultados if sucesso)
    
    for nome, sucesso in resultados:
        status = "✅ PASSOU" if sucesso else "❌ FALHOU"
        print(f"{status} - {nome}")
    
    print(f"\nTotal: {sucessos}/{total} testes passaram")
    
    if sucessos == total:
        print("\n🎉 Todos os testes passaram com sucesso!")
    else:
        print(f"\n⚠️ {total - sucessos} teste(s) falharam")
    
    print("=" * 80)


if __name__ == "__main__":
    main()