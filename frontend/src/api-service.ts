/*
====================================================================
API SERVICE - COMUNICAÇÃO COM BACKEND
====================================================================
Descrição: Serviço centralizado para todas as chamadas à API
Data: 21/08/2025
Autor: Will - Empresa: IOGAR
====================================================================
*/

// ============================================================================
// IMPORTAR CONFIGURAÇÃO CENTRALIZADA
// ============================================================================
import { API_BASE_URL } from './config';

// ============================================================================
// CONFIGURAÇÃO BASE DA API COM DETECÇÃO AUTOMÁTICA DE PORTA
// ============================================================================
// const API_CONFIG = {
//   // Detecta automaticamente se está em produção ou desenvolvimento
//   baseURL: (() => {
//     // Se estiver rodando no Render (producao)
//     if (window.location.hostname.includes('render.com') || 
//         window.location.hostname.includes('food-cost-frontend')) {
//       return 'https://food-cost-backend.onrender.com';
//     }
//     // Senao, tenta pegar da variavel de ambiente ou usa localhost
//     return import.meta.env.VITE_API_URL || 'http://localhost:8000';
//   })(),
//   timeout: 10000,
//   headers: {
//     'Content-Type': 'application/json',
//   }
// };

// ============================================================================
// CONFIGURAÇÃO BASE DA API - USA CONFIG.TS CENTRALIZADO
// ============================================================================
const API_CONFIG = {
  // Usa detecção automática de ambiente do config.ts
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
};

// Classe principal para gerenciar chamadas à API
class ApiService {
  private baseURL: string;
  private isProduction: boolean;

  constructor() {
    // Usar URL detectada automaticamente pelo config.ts
    this.baseURL = API_CONFIG.baseURL;
    this.isProduction = !this.baseURL.includes('localhost');
    
    console.log('🌐 API Service inicializado');
    console.log('  - URL Base:', this.baseURL);
    console.log('  - Modo:', this.isProduction ? 'PRODUÇÃO' : 'DESENVOLVIMENTO');
  }

  // Método para detectar porta disponível (APENAS EM DESENVOLVIMENTO)
  // private async detectarPortaDisponivel(): Promise<void> {
  //   console.log('🔍 Detectando porta disponível...');
  //   const portas = [8000, 8001];

  //   for (const porta of portas) {
  //     try {
  //       const testURL = `http://localhost:${porta}/health`;
  //       const response = await fetch(testURL, {
  //         method: 'GET',
  //         signal: AbortSignal.timeout(2000)
  //       });

  //       if (response.ok) {
  //         this.baseURL = `http://localhost:${porta}`;
  //         console.log(`✅ Backend encontrado na porta ${porta}`);
  //         return;
  //       }
  //     } catch (error) {
  //       // Continua tentando próxima porta
  //     }
  //   }

  //   console.warn('⚠️ Usando porta padrão 8000');
  // }

  // Método genérico para fazer requisições
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseURL}${endpoint}`;
      
      // Obter token de autenticacao do localStorage
      const token = localStorage.getItem('foodcost_access_token');
      console.log('🔑 Token encontrado:', token ? 'SIM' : 'NÃO', token?.substring(0, 20) + '...'); // Ver se tem token
      
      const config = {
        ...options,
        headers: {
          ...API_CONFIG.headers,
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
          ...options.headers,
        },
      };

      console.log('🌐 Fazendo requisição:', { method: options.method || 'GET', url, body: options.body });

      const response = await fetch(url, config);
      
      if (!response.ok) {
        // ============================================================================
        // 🔐 INTERCEPTOR: ERRO 401 - TOKEN EXPIRADO
        // ============================================================================
        if (response.status === 401) {
          console.warn('⚠️ Token expirado (401), tentando renovar...');
          
          // Tentar renovar o token
          const newToken = await this.refreshAccessToken();
          
          if (newToken) {
            console.log('✅ Token renovado, repetindo requisição original...');
            
            // Repetir a requisição original com o novo token
            const retryConfig = {
              ...options,
              headers: {
                ...API_CONFIG.headers,
                'Authorization': `Bearer ${newToken}`,
                ...options.headers,
              },
            };
            
            const retryResponse = await fetch(url, retryConfig);
            
            if (retryResponse.ok) {
              const retryData = await retryResponse.json();
              console.log('✅ Requisição repetida com sucesso');
              return { data: retryData };
            }
          }
          
          // Se não conseguiu renovar ou retry falhou, redirecionar para login
          console.error('❌ Não foi possível renovar token, redirecionando para login');
          localStorage.removeItem('foodcost_access_token');
          localStorage.removeItem('foodcost_refresh_token');
          localStorage.removeItem('foodcost_user');
          window.location.href = '/login';
          
          return { error: 'Sessão expirada. Faça login novamente.' };
        }
        
        // ============================================================================
        // 🔍 CAPTURAR DETALHES DO ERRO 422 (VALIDAÇÃO)
        // ============================================================================
        let errorDetails = {};
        try {
          errorDetails = await response.json();
          console.error('❌ Erro HTTP detalhado:', {
            status: response.status,
            statusText: response.statusText,
            details: errorDetails
          });
        } catch (e) {
          console.error('❌ Erro HTTP:', response.status, response.statusText);
        }
        
        // Retornar erro detalhado para 422
        if (response.status === 422) {
          return { 
            error: `Erro de validação (422): ${JSON.stringify(errorDetails, null, 2)}` 
          };
        }
        
        throw new Error(`Erro HTTP: ${response.status} - ${JSON.stringify(errorDetails)}`);
      }

      const data = await response.json();
      console.log('✅ Resposta bem-sucedida:', data);
      return { data };
    } catch (error) {
      console.error('💥 Erro na requisição:', error);
      return { 
        error: error instanceof Error ? error.message : 'Erro desconhecido' 
      };
    }
  }

  // ============================================================================
// RENOVAR TOKEN (REFRESH)
// ============================================================================
/**
 * Renova o access token usando o refresh token
 * Chamado automaticamente quando o access token expira
 */
async refreshAccessToken(): Promise<string | null> {
  console.log('🔄 Renovando access token...');
  
  try {
    const refreshToken = localStorage.getItem('foodcost_refresh_token');
    
    if (!refreshToken) {
      console.error('❌ Refresh token não encontrado');
      return null;
    }

    const response = await fetch(`${this.baseURL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        refresh_token: refreshToken
      })
    });

    if (!response.ok) {
      console.error('❌ Erro ao renovar token:', response.status);
      
      // Se refresh token expirou, limpar tudo e redirecionar
      localStorage.removeItem('foodcost_access_token');
      localStorage.removeItem('foodcost_refresh_token');
      localStorage.removeItem('foodcost_user');
      window.location.href = '/login';
      
      return null;
    }

    const data = await response.json();
    
    if (data.access_token) {
      // Salvar novo access token
      localStorage.setItem('foodcost_access_token', data.access_token);
      console.log('✅ Access token renovado com sucesso');
      
      return data.access_token;
    }
    
    return null;
  } catch (error) {
    console.error('❌ Erro ao renovar token:', error);
    return null;
  }
}

  // ================================
  // MÉTODOS PARA INSUMOS - AJUSTADOS PARA SEU BACKEND
  // ================================

  // Listar todos os insumos com filtros opcionais
  async getInsumos(params: { restaurante_id?: number; incluir_globais?: boolean } = {}): Promise<ApiResponse<any[]>> {
    // Construir query string com parâmetros
    const queryParams = new URLSearchParams({ limit: '1000' });
    
    // Adicionar restaurante_id se fornecido
    if (params.restaurante_id) {
      queryParams.append('restaurante_id', params.restaurante_id.toString());
    }
    
    // Adicionar incluir_globais se fornecido
    if (params.incluir_globais !== undefined) {
      queryParams.append('incluir_globais', params.incluir_globais.toString());
    }
    
    const url = `/api/v1/insumos/?${queryParams.toString()}`;
    console.log('📡 API getInsumos:', url);
    
    return this.request<any[]>(url);
  }

  // Listar insumos com paginação server-side
  async getInsumosPaginados(params: {
    page?: number;
    per_page?: number;
    restaurante_id?: number;
    incluir_globais?: boolean;
    grupo?: string;
    subgrupo?: string;
    codigo?: string;
    nome?: string;
    unidade?: string;
    preco_min?: number;
    preco_max?: number;
  } = {}): Promise<ApiResponse<{
    data: any[];
    total: number;
    page: number;
    pages: number;
    per_page: number;
  }>> {
    // Construir query string com parâmetros de paginação
    const queryParams = new URLSearchParams();
    
    // Parâmetros de paginação
    if (params.page) {
      queryParams.append('page', params.page.toString());
    }
    if (params.per_page) {
      queryParams.append('per_page', params.per_page.toString());
    }
    
    // Parâmetros de filtro de restaurante
    if (params.restaurante_id) {
      queryParams.append('restaurante_id', params.restaurante_id.toString());
    }
    if (params.incluir_globais !== undefined) {
      queryParams.append('incluir_globais', params.incluir_globais.toString());
    }
    
    // Parâmetros de filtros adicionais
    if (params.grupo) {
      queryParams.append('grupo', params.grupo);
    }
    if (params.subgrupo) {
      queryParams.append('subgrupo', params.subgrupo);
    }
    if (params.codigo) {
      queryParams.append('codigo', params.codigo);
    }
    if (params.nome) {
      queryParams.append('nome', params.nome);
    }
    if (params.unidade) {
      queryParams.append('unidade', params.unidade);
    }
    if (params.preco_min !== undefined) {
      queryParams.append('preco_min', params.preco_min.toString());
    }
    if (params.preco_max !== undefined) {
      queryParams.append('preco_max', params.preco_max.toString());
    }
    
    const url = `/api/v1/insumos/paginado?${queryParams.toString()}`;
    console.log('📡 API getInsumosPaginados:', url);
    
    return this.request<{
      data: any[];
      total: number;
      page: number;
      pages: number;
      per_page: number;
    }>(url);
  }

  // Buscar insumos disponíveis (inclui receitas processadas)
  async getInsumosDisponiveis(termo?: string): Promise<ApiResponse<any[]>> {
    const query = termo ? `?termo=${encodeURIComponent(termo)}` : '';
    return this.request<any[]>(`/api/v1/receitas/utils/insumos-disponiveis${query}`);
  }

  // Buscar insumo por ID
  async getInsumoById(id: number): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/v1/insumos/${id}`);
  }

  // Criar novo insumo
  async createInsumo(insumo: any): Promise<ApiResponse<any>> {
    console.log('🎯 === DEBUG COMPLETO createInsumo ===');
    console.log('📥 Dados ORIGINAIS recebidos:', insumo);
    
    // ============================================================================
    // 🔍 VALIDAÇÃO MANUAL ANTES DE ENVIAR
    // ============================================================================
    
    if (!insumo.nome || insumo.nome.trim() === '') {
      console.error('❌ ERRO: nome vazio');
      return { error: 'Nome é obrigatório' };
    }
    
    // Verificar se tem preço total OU preço por unidade
    const precoParaValidar = insumo.preco_compra_total || insumo.preco_compra_real;
    if (precoParaValidar && Number(precoParaValidar) <= 0) {
      console.error('❌ ERRO: preço inválido quando informado');
      return { error: 'Se informado, o preço deve ser maior que zero' };
    }
    
    // ============================================================================
    // USAR RESTAURANTE_ID DO FORMULÁRIO OU DO USUÁRIO LOGADO
    // ============================================================================
    // PRIORIDADE:
    // 1. Se veio do formulário (insumo.restaurante_id), usar esse valor (pode ser null para global)
    // 2. Se não veio do formulário, usar o do usuário logado
    // 3. Se usuário não tem restaurante, usar null (insumo global)
    
    let restauranteIdFinal;
    
    if (insumo.restaurante_id !== undefined) {
      // Veio do formulário - usar exatamente esse valor (null ou ID)
      restauranteIdFinal = insumo.restaurante_id;
      console.log('🔍 Usando restaurante_id do FORMULÁRIO:', restauranteIdFinal);
    } else {
      // Não veio do formulário - buscar do usuário logado
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      restauranteIdFinal = user.restaurante_id || null;
      console.log('🔍 Usando restaurante_id do USUÁRIO:', restauranteIdFinal);
    }
    
    const dadosBackend = {
      grupo: String(insumo.grupo || 'Geral').trim(),
      subgrupo: String(insumo.subgrupo || 'Geral').trim(),
      nome: String(insumo.nome || '').trim(),
      quantidade: Number(insumo.quantidade) || 1,
      fator: Number(insumo.fator) || 1.0,
      unidade: String(insumo.unidade || 'kg').trim(),
      preco_compra_real: insumo.preco_compra_real || insumo.preco_compra_total || null,
      preco_unitario: insumo.preco_unitario || insumo.preco_compra_total || insumo.preco_compra_real || null,
      fornecedor_id: insumo.fornecedor_id || null,
      fornecedor_insumo_id: insumo.fornecedor_insumo_id || null,
      // Usar o valor final determinado acima (null para global, ID para específico)
      restaurante_id: restauranteIdFinal
    };

    console.log('📦 Dados MAPEADOS para backend:', dadosBackend);
    console.log('🔍 Verificação de tipos:', {
      grupo: `${typeof dadosBackend.grupo} = "${dadosBackend.grupo}"`,
      subgrupo: `${typeof dadosBackend.subgrupo} = "${dadosBackend.subgrupo}"`,
      codigo: `${typeof dadosBackend.codigo} = "${dadosBackend.codigo}"`,
      nome: `${typeof dadosBackend.nome} = "${dadosBackend.nome}"`,
      quantidade: `${typeof dadosBackend.quantidade} = ${dadosBackend.quantidade}`,
      fator: `${typeof dadosBackend.fator} = ${dadosBackend.fator}`,
      unidade: `${typeof dadosBackend.unidade} = "${dadosBackend.unidade}"`,
      preco_compra_real: `${typeof dadosBackend.preco_compra_real} = ${dadosBackend.preco_compra_real}`,
      fornecedor_id: `${typeof dadosBackend.fornecedor_id} = ${dadosBackend.fornecedor_id}`
    });

    // ============================================================================
    // 🌐 FAZER REQUISIÇÃO COM CAPTURA DE ERRO DETALHADA
    // ============================================================================
    
    try {
      const url = `${this.baseURL}/api/v1/insumos/`;
      const config = {
        method: 'POST',
        headers: API_CONFIG.headers,
        body: JSON.stringify(dadosBackend)
      };

      console.log('🚀 Enviando para:', url);
      console.log('📋 Configuração:', config);
      console.log('📤 JSON enviado:', config.body);

      const response = await fetch(url, config);
      
      console.log('📡 Status da resposta:', response.status);
      console.log('📡 Status text:', response.statusText);
      
      if (!response.ok) {
        // Tentar capturar detalhes do erro
        let errorDetails;
        try {
          errorDetails = await response.json();
          console.error('💥 Detalhes do erro 422:', errorDetails);
        } catch (e) {
          console.error('💥 Erro ao capturar detalhes:', e);
          errorDetails = { message: 'Erro de validação sem detalhes' };
        }
        
        return { 
          error: `Erro ${response.status}: ${JSON.stringify(errorDetails, null, 2)}` 
        };
      }

      const data = await response.json();
      console.log('✅ Sucesso! Resposta:', data);
      return { data };

    } catch (error) {
      console.error('💥 Erro na requisição:', error);
      return { 
        error: error instanceof Error ? error.message : 'Erro desconhecido' 
      };
    }
  }

  // Atualizar insumo existente
  async updateInsumo(id: number, insumo: any): Promise<ApiResponse<any>> {
    console.log('🔄 === updateInsumo COMPLETO ===');
    console.log('📥 ID:', id);
    console.log('📥 Dados recebidos:', insumo);
    
    try {
      const url = `${this.baseURL}/api/v1/insumos/${id}`;
      
      // ============================================================================
      // 🆕 MAPEAR DADOS PARA UPDATE (SÓ CAMPOS FORNECIDOS)
      // ============================================================================
      const dadosUpdate = {};
      
      // Incluir apenas campos que existem e não são vazios
      if (insumo.nome && insumo.nome.trim()) {
        dadosUpdate.nome = String(insumo.nome).trim();
      }
      if (insumo.codigo && insumo.codigo.trim()) {
        dadosUpdate.codigo = String(insumo.codigo).trim().toUpperCase();
      }
      if (insumo.grupo) {
        dadosUpdate.grupo = String(insumo.grupo).trim();
      }
      if (insumo.subgrupo) {
        dadosUpdate.subgrupo = String(insumo.subgrupo).trim();
      }
      if (insumo.unidade) {
        dadosUpdate.unidade = String(insumo.unidade).trim();
      }
      if (insumo.preco_compra_real !== undefined && insumo.preco_compra_real > 0) {
        dadosUpdate.preco_compra_real = Number(insumo.preco_compra_real);
      }
      if (insumo.quantidade !== undefined && insumo.quantidade > 0) {
        dadosUpdate.quantidade = Number(insumo.quantidade);
      }
      // ====================================================================
      // CAMPO FATOR - DESABILITADO (17/11/2025)
      // ====================================================================
      // if (insumo.fator !== undefined && insumo.fator > 0) {
      //   dadosUpdate.fator = Number(insumo.fator);
      // }
      
      console.log('📦 Dados para update (apenas campos válidos):', dadosUpdate);
      
      // ============================================================================
      // 🌐 FAZER REQUISIÇÃO SIMPLES (IGUAL AO TESTE QUE FUNCIONOU)
      // ============================================================================
      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dadosUpdate)
      });
      
      console.log('📡 Status HTTP:', response.status);
      console.log('📡 Status Text:', response.statusText);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('💥 Erro HTTP:', errorText);
        return { error: `Erro HTTP ${response.status}: ${errorText}` };
      }
      
      const data = await response.json();
      console.log('✅ Update realizado com sucesso:', data);
      return { data };
      
    } catch (error) {
      console.error('💥 Erro de fetch:', error);
      return { error: `Erro de conexão: ${error.message}` };
    }
  }

  // Deletar insumo
  async deleteInsumo(id: number): Promise<ApiResponse<any>> {
    console.log('🗑️ API Service deletando insumo ID:', id);
    
    try {
      const response = await fetch(`${this.baseURL}/api/v1/insumos/${id}`, {
        method: 'DELETE',
        headers: API_CONFIG.headers,
      });

      if (response.ok) {
        return { data: { success: true } };
      } else {
        throw new Error(`Erro HTTP: ${response.status}`);
      }
    } catch (error) {
      return { 
        error: error instanceof Error ? error.message : 'Erro desconhecido' 
      };
    }
  }

  // ================================
  // MÉTODOS PARA RECEITAS - AJUSTADOS PARA SEU BACKEND
  // ================================

  // Listar todas as receitas
  async getReceitas(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/api/v1/receitas/');
  }

  // Buscar receitas por restaurante
  async getReceitasByRestaurante(restauranteId: number): Promise<ApiResponse<any[]>> {
    return this.request<any[]>(`/api/v1/receitas/restaurante/${restauranteId}`);
  }

  // Buscar receita por ID
  async getReceitaById(id: number): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/v1/receitas/${id}`);
  }

  // Criar nova receita
  async createReceita(receita: any): Promise<ApiResponse<any>> {
    // ===================================================================================================
    // CORREÇÃO: Não enviar código em modo criação (backend gera automaticamente)
    // ===================================================================================================
    const isEdicao = Boolean(receita.id);
    
    // Mapear campos para o formato esperado pelo backend
    const dadosBackend = {
      // Incluir o ID se fornecido (para edição via POST)
      ...(isEdicao && { id: receita.id }),
      
      // ===================================================================================================
      // CORREÇÃO: Só incluir código se estiver em modo edição
      // ===================================================================================================
      ...(isEdicao && receita.codigo && { codigo: receita.codigo }),
      
      nome: receita.nome,
      descricao: receita.descricao || '',
      responsavel: receita.responsavel || null,
      categoria: receita.categoria || 'Geral',
      grupo: receita.categoria || 'Geral',
      subgrupo: receita.categoria || 'Geral', 
      unidade: receita.unidade || 'un',    
      rendimento: receita.rendimento_porcoes || receita.porcoes || receita.rendimento || 1,
      sugestao_valor: receita.sugestao_valor || 0,
      tempo_preparo: receita.tempo_preparo_minutos || receita.tempo_preparo || 30,
      restaurante_id: receita.restaurante_id || 1,
      processada: receita.processada || false,
      insumos: receita.insumos || []
    };
  
  return this.request<any>('/api/v1/receitas/', {
    method: 'POST',
    body: JSON.stringify(dadosBackend),
  });
}

// Atualizar receita existente - MAPEAMENTO CORRETO PARA SCHEMA ReceitaUpdate
async updateReceita(id: number, receita: any): Promise<ApiResponse<any>> {
  console.log('🔄 === updateReceita IMPLEMENTAÇÃO COMPLETA ===');
  console.log('📥 ID da receita:', id);
  console.log('📥 Dados recebidos:', receita);
  
  // ============================================================================
  // MAPEAR CAMPOS PARA O FORMATO ESPERADO PELO SCHEMA ReceitaUpdate
  // ============================================================================
  const dadosUpdate: any = {};
  
  // Campos básicos diretos (nomes idênticos no schema)
  if (receita.codigo !== undefined) dadosUpdate.codigo = receita.codigo;
  if (receita.nome !== undefined) dadosUpdate.nome = receita.nome;
  if (receita.descricao !== undefined) dadosUpdate.descricao = receita.descricao;
  if (receita.unidade !== undefined) dadosUpdate.unidade = receita.unidade;
  if (receita.quantidade !== undefined) dadosUpdate.quantidade = receita.quantidade;
  // ====================================================================
  // CAMPO FATOR - DESABILITADO (17/11/2025)
  // ====================================================================
  // if (receita.fator !== undefined) dadosUpdate.fator = receita.fator;
  if (receita.ativo !== undefined) dadosUpdate.ativo = receita.ativo;
  
  // Campos que precisam de mapeamento
  if (receita.categoria !== undefined) {
    dadosUpdate.grupo = receita.categoria;
    dadosUpdate.subgrupo = receita.categoria;
  }
  if (receita.grupo !== undefined) dadosUpdate.grupo = receita.grupo;
  if (receita.subgrupo !== undefined) dadosUpdate.subgrupo = receita.subgrupo;
  
  // Campos de tempo e rendimento
  if (receita.porcoes !== undefined) dadosUpdate.rendimento_porcoes = receita.porcoes;
  if (receita.rendimento_porcoes !== undefined) dadosUpdate.rendimento_porcoes = receita.rendimento_porcoes;
  if (receita.tempo_preparo !== undefined) dadosUpdate.tempo_preparo_minutos = receita.tempo_preparo;
  if (receita.tempo_preparo_minutos !== undefined) dadosUpdate.tempo_preparo_minutos = receita.tempo_preparo_minutos;

  console.log('📤 Dados mapeados para ReceitaUpdate:', dadosUpdate);
  
  try {
    // Fazer requisição PUT usando apenas os campos de update (sem insumos)
    const response = await this.request<any>(`/api/v1/receitas/${id}`, {
      method: 'PUT',
      body: JSON.stringify(dadosUpdate),
    });
    
    if (response.data) {
      console.log('✅ updateReceita - Sucesso:', response.data);
      
      // ============================================================================
      // ATUALIZAR INSUMOS SEPARADAMENTE (se fornecidos)
      // ============================================================================
      if (receita.insumos && receita.insumos.length > 0) {
        console.log('🔧 Atualizando insumos da receita...');
        // TODO: Implementar atualização de insumos via endpoints específicos
        // Por enquanto, apenas log para debug
        console.log('📋 Insumos para atualizar:', receita.insumos);
      }
      
    } else if (response.error) {
      console.error('❌ updateReceita - Erro:', response.error);
    }
    
    return response;
  } catch (error) {
    console.error('💥 updateReceita - Exceção:', error);
    return {
      error: error instanceof Error ? error.message : 'Erro desconhecido ao atualizar receita'
    };
  }
}

  // ================================
  // MÉTODOS PARA RESTAURANTES - AJUSTADOS PARA SEU BACKEND
  // ================================

  // Listar restaurantes em formato grid otimizado
  async getRestaurantesGrid(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/api/v1/restaurantes/grid');
  }

  // Listar restaurantes com unidades/filiais aninhadas
  async getRestaurantesComUnidades(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/api/v1/restaurantes/com-unidades');
  }

  // Listar tipos de estabelecimento disponíveis
  async getTiposRestaurante(): Promise<ApiResponse<string[]>> {
    return this.request<string[]>('/api/v1/restaurantes/tipos');
  }

  // Buscar restaurante específico por ID
  async getRestauranteById(id: number): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/v1/restaurantes/${id}`);
  }

  // Buscar estatísticas de um restaurante
  async getRestauranteEstatisticas(id: number): Promise<ApiResponse<any>> {
    console.log('🔍 API - ID recebido:', id, 'Tipo:', typeof id);
    return this.request<any>(`/api/v1/restaurantes/${id}/estatisticas`);
  }

  // Criar novo restaurante matriz
  async createRestaurante(restaurante: any): Promise<ApiResponse<any>> {
    // Validar CNPJ obrigatório para matriz
    if (!restaurante.cnpj) {
      return {
        error: true,
        message: 'CNPJ é obrigatório para restaurante matriz'
      };
    }

    const dadosBackend = {
      nome: restaurante.nome,
      cnpj: restaurante.cnpj,
      tipo: restaurante.tipo || 'restaurante',
      tem_delivery: restaurante.tem_delivery || false,
      endereco: restaurante.endereco || null,
      bairro: restaurante.bairro || null,
      cidade: restaurante.cidade || null,
      estado: restaurante.estado || null,
      telefone: restaurante.telefone || null,
      ativo: restaurante.ativo !== false
    };

    console.log('📤 Enviando dados para criar restaurante:', dadosBackend);
    
    return this.request<any>('/api/v1/restaurantes/', {
      method: 'POST',
      body: JSON.stringify(dadosBackend),
    });
  }

  // Criar nova unidade/filial
  async createUnidade(restauranteMatrizId: number, unidade: any): Promise<ApiResponse<any>> {
    // Validar dados obrigatórios da unidade
    if (!unidade.endereco || !unidade.bairro || !unidade.cidade || !unidade.estado) {
      return {
        error: true,
        message: 'Endereço, bairro, cidade e estado são obrigatórios para unidade'
      };
    }

    const dadosUnidade = {
      endereco: unidade.endereco,
      bairro: unidade.bairro,
      cidade: unidade.cidade,
      estado: unidade.estado,
      telefone: unidade.telefone || null,
      tem_delivery: unidade.tem_delivery
    };

    console.log('📤 Enviando dados para criar unidade:', dadosUnidade);
    
    return this.request<any>(`/api/v1/restaurantes/${restauranteMatrizId}/unidades`, {
      method: 'POST',
      body: JSON.stringify(dadosUnidade),
    });
  }

  // Atualizar restaurante existente
  async updateRestaurante(id: number, restaurante: any): Promise<ApiResponse<any>> {
    // Enviar apenas campos que foram alterados (patch)
    const dadosUpdate: any = {};
    
    if (restaurante.nome !== undefined) dadosUpdate.nome = restaurante.nome;
    if (restaurante.cnpj !== undefined) dadosUpdate.cnpj = restaurante.cnpj;
    if (restaurante.tipo !== undefined) dadosUpdate.tipo = restaurante.tipo;
    if (restaurante.tem_delivery !== undefined) dadosUpdate.tem_delivery = restaurante.tem_delivery;
    if (restaurante.endereco !== undefined) dadosUpdate.endereco = restaurante.endereco;
    if (restaurante.bairro !== undefined) dadosUpdate.bairro = restaurante.bairro;
    if (restaurante.cidade !== undefined) dadosUpdate.cidade = restaurante.cidade;
    if (restaurante.estado !== undefined) dadosUpdate.estado = restaurante.estado;
    if (restaurante.telefone !== undefined) dadosUpdate.telefone = restaurante.telefone;
    if (restaurante.ativo !== undefined) dadosUpdate.ativo = restaurante.ativo;

    console.log('📤 Enviando dados para atualizar restaurante:', dadosUpdate);
    
    return this.request<any>(`/api/v1/restaurantes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(dadosUpdate),
    });
  }

  // Excluir restaurante
  async deleteRestaurante(id: number): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/v1/restaurantes/${id}`, {
      method: 'DELETE',
    });
  }

  // Listar restaurantes simples (para dropdowns)
  async getRestaurantesSimples(incluirFiliais: boolean = false): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams();
    if (incluirFiliais) params.append('incluir_filiais', 'true');
    
    const url = `/api/v1/restaurantes/${params.toString() ? '?' + params.toString() : ''}`;
    return this.request<any[]>(url);
  }

  // Método legacy mantido para compatibilidade (aponta para grid)
  async getRestaurantes(): Promise<ApiResponse<any[]>> {
    console.log('⚠️ Método getRestaurantes() é legacy. Use getRestaurantesGrid()');
    return this.getRestaurantesGrid();
  }

  // ================================
  // MÉTODOS DE UTILITÁRIOS
  // ================================

  // Testar conexão com a API
  async testConnection(): Promise<boolean> {
    try {
      const response = await this.request('/health');
      return !response.error;
    } catch {
      return false;
    }
  }

  // Verificar status da API
  async getApiStatus(): Promise<ApiResponse<any>> {
    return this.request('/');
  }

  // ================================
  //  MÉTODOS PARA FORNECEDORES
  // ================================

  // Listar todos os fornecedores
  async getFornecedores(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/fornecedores/');
  }

  // Buscar fornecedor por ID
  async getFornecedorById(id: number): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/v1/fornecedores/${id}`);
  }

  // Criar novo fornecedor
  async createFornecedor(fornecedor: any): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/fornecedores/', {
      method: 'POST',
      body: JSON.stringify(fornecedor),
    });
  }

  // Atualizar fornecedor
  async updateFornecedor(id: number, fornecedor: any): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/v1/fornecedores/${id}`, {
      method: 'PUT',
      body: JSON.stringify(fornecedor),
    });
  }

  // Excluir fornecedor
  async deleteFornecedor(id: number): Promise<ApiResponse<any>> {
    return this.request<any>(`/api/v1/fornecedores/${id}`, {
      method: 'DELETE',
    });
  }

  // ================================
  // 🆕 MÉTODOS PARA INSUMOS DE FORNECEDORES
  // ================================

  // Listar insumos de um fornecedor
  async getFornecedorInsumos(fornecedorId: number): Promise<ApiResponse<any[]>> {
    return this.request<any[]>(`/api/v1/fornecedores/${fornecedorId}/insumos/`);
  }

  // Listar insumos de um fornecedor para seleção (simplificado)
  async getFornecedorInsumosParaSelecao(fornecedorId: number, termo?: string): Promise<ApiResponse<any[]>> {
    const query = termo ? `?termo=${encodeURIComponent(termo)}` : '';
    return this.request<any[]>(`/api/v1/fornecedores/${fornecedorId}/insumos/selecao/${query}`);
  }

  // Criar insumo no catálogo de fornecedor (CORRIGIDO)
  async createFornecedorInsumo(fornecedorId: number, insumo: any): Promise<ApiResponse<any>> {
    console.log('🎯 Criando insumo de fornecedor:', { fornecedorId, insumo });
    
    const dadosFornecedorInsumo = {
      codigo: String(insumo.codigo || '').trim().toUpperCase(),
      nome: String(insumo.nome || '').trim(),
      unidade: String(insumo.unidade || 'kg').trim(),
      preco_unitario: Number(insumo.preco_unitario || insumo.preco_compra_real || 0),
      descricao: String(insumo.descricao || '').trim()
    };

    console.log('📦 Dados formatados para fornecedor insumo:', dadosFornecedorInsumo);

    return this.request<any>(`/api/v1/fornecedores/${fornecedorId}/insumos/`, {
      method: 'POST',
      body: JSON.stringify(dadosFornecedorInsumo),
    });
  }

  // Busca global de insumos em todos os fornecedores
  async buscarInsumosGlobal(termo: string): Promise<ApiResponse<any[]>> {
    return this.request<any[]>(`/api/v1/insumos/busca-global/?termo=${encodeURIComponent(termo)}`);
  }

  // ================================
  // 🆕 MÉTODOS UTILITÁRIOS
  // ================================

  // Buscar estados brasileiros
  async getEstadosBrasil(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>('/api/v1/fornecedores/utils/estados');
  }

  // ================================
  // MÉTODOS PARA LIMPEZA DE DADOS (ADMIN)
  // ================================

  // Obter estatísticas de dados
  async getEstatisticasLimpeza(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/limpeza-dados/estatisticas', {
      method: 'GET'
    });
  }

  // Limpar receitas
  async limparReceitas(filtros?: any): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/limpeza-dados/receitas', {
      method: 'DELETE',
      body: filtros ? JSON.stringify(filtros) : undefined
    });
  }

  // Limpar insumos
  async limparInsumos(filtros?: any): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/limpeza-dados/insumos', {
      method: 'DELETE',
      body: filtros ? JSON.stringify(filtros) : undefined
    });
  }

  // Limpar fornecedores
  async limparFornecedores(): Promise<ApiResponse<any>> {
    return this.request<any>('/api/v1/limpeza-dados/fornecedores', {
      method: 'DELETE'
    });
  }

  // Limpar restaurantes
  async limparRestaurantes(manterPrimeiro: boolean = true, restauranteId?: number): Promise<ApiResponse<any>> {
    let url = `/api/v1/limpeza-dados/restaurantes?manter_primeiro=${manterPrimeiro}`;
    if (restauranteId) {
      url += `&restaurante_id=${restauranteId}`;
    }
    return this.request<any>(url, { method: 'DELETE' });
  }

  // Limpar tudo (reset completo)
  async limparTudo(confirmacao: string): Promise<ApiResponse<any[]>> {
    return this.request<any[]>(
      `/api/v1/limpeza-dados/limpar-tudo?confirmacao=${encodeURIComponent(confirmacao)}`,
      { method: 'DELETE' }
    );
  }


} // ← ESTA CHAVE FECHA A CLASSE ApiService

// ================================
// EXPORTS - FORA DA CLASSE
// ================================

// Instância única do serviço de API
export const apiService = new ApiService();

// Exportar a classe para uso
export default ApiService;