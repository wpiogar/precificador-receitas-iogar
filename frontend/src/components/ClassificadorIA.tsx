// ============================================================================
// COMPONENTE REACT - CLASSIFICADOR IA COM FEEDBACK
// ============================================================================
// Descrição: Interface React para classificação de produtos e feedback da IA
// Funcionalidades: classificar, feedback, histórico, estatísticas
// Data: 10/09/2025
// Autor: Will - Empresa: IOGAR
// ============================================================================


import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  Search, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Clock,
  Target,
  BarChart3,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

// Importar componente do popup de classificação
import PopupClassificacaoIA from './PopupClassificacaoIA.tsx';

// Importar configuração centralizada da API
import { API_BASE_URL } from '../config';

// Importar funções de popup do sistema
declare global {
  function showSuccessPopup(title: string, message: string): void;
  function showErrorPopup(title: string, message: string): void;
}


// Interfaces
interface TaxonomiaClassificada {
  categoria: string;
  subcategoria: string;
  especificacao?: string;
  variante?: string;
  nome_completo: string;
  codigo_taxonomia?: string;
}

interface ClassificacaoResposta {
  sucesso: boolean;
  status: 'sucesso' | 'erro' | 'sem_correspondencia' | 'baixa_confianca';
  taxonomia_sugerida?: TaxonomiaClassificada;
  confianca: number;
  requer_revisao: boolean;
  alternativas?: TaxonomiaClassificada[];
  mensagem?: string;
  termo_analisado: string;
}

interface StatusSistema {
  sistema_ativo: boolean;
  versao: string;
  spacy_disponivel: boolean;
  fuzzywuzzy_disponivel: boolean;
  modelo_portugues: boolean;
  avisos: string[];
  erros: string[];
}

interface EstatisticasIA {
  total_entradas_conhecimento: number;
  total_classificacoes_realizadas: number;
  taxa_acerto_geral: number;
  confianca_media: number;
  total_confirmacoes: number;
  total_correcoes: number;
}

// ============================================================================
// COMPONENTE PARA INSUMOS SEM CLASSIFICAÇÃO
// ============================================================================

const InsumosSemClassificacao: React.FC = () => {
  const [insumosSemClassificacao, setInsumosSemClassificacao] = useState<any[]>([]);
  const [totalInsumosSemClassificacao, setTotalInsumosSemClassificacao] = useState(0);
  const [carregandoInsumos, setCarregandoInsumos] = useState(false);

  // ============================================================================
  // ESTADOS DE PAGINAÇÃO
  // ============================================================================
  const [paginaAtual, setPaginaAtual] = useState(1);
  const [itensPorPagina] = useState(20);

  // Calcular índices para paginação
  const insumosPaginados = insumosSemClassificacao;
  const totalPaginas = Math.ceil(totalInsumosSemClassificacao / itensPorPagina);


  // Função para carregar insumos sem classificação
  const carregarInsumosSemClassificacao = async () => {
    setCarregandoInsumos(true);
    try {
      // Calcular skip baseado na página atual
      const skip = (paginaAtual - 1) * itensPorPagina;
      
      // Carregar apenas a página atual
      const response = await fetch(`${API_BASE_URL}/api/v1/insumos/sem-classificacao?skip=${skip}&limit=${itensPorPagina}`);
      if (response.ok) {
        const insumos = await response.json();
        console.log('✅ Insumos sem classificacao carregados:', insumos.length);
        setInsumosSemClassificacao(insumos);
        
        // Buscar total real de insumos sem classificação
        const countResponse = await fetch(`${API_BASE_URL}/api/v1/insumos/sem-classificacao/count`);
        if (countResponse.ok) {
          const countData = await countResponse.json();
          setTotalInsumosSemClassificacao(countData.total || insumos.length);
        } else {
          setTotalInsumosSemClassificacao(insumos.length);
        }
      } else {
        console.error('❌ Erro na resposta:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('❌ Detalhes do erro:', errorText);
      }
    } catch (error) {
      console.error('❌ Erro ao carregar insumos:', error);
    } finally {
      setCarregandoInsumos(false);
    }
  };

  useEffect(() => {
    carregarInsumosSemClassificacao();
  }, []);

  // Recarregar quando mudar a página
  useEffect(() => {
    carregarInsumosSemClassificacao();
  }, [paginaAtual]);

  // Estados para controle do popup de classificação manual
  const [popupClassificacaoVisivel, setPopupClassificacaoVisivel] = useState(false);
  const [insumoSelecionado, setInsumoSelecionado] = useState<{id: number, nome: string} | null>(null);

  const classificarInsumo = (insumoId: number, nomeInsumo: string) => {
    // Definir insumo selecionado para o popup
    setInsumoSelecionado({ id: insumoId, nome: nomeInsumo });
    
    // Abrir popup de classificação manual diretamente
    // O popup se encarrega de fazer a classificação IA internamente
    setPopupClassificacaoVisivel(true);
  };

  // Função para fechar popup de classificação
  const fecharPopupClassificacao = () => {
    setPopupClassificacaoVisivel(false);
    setInsumoSelecionado(null);
  };

  // Callback quando classificação é aceita no popup
  const handleClassificacaoAceita = (taxonomiaId: number) => {
    console.log('Classificação aceita para taxonomia ID:', taxonomiaId);
    carregarInsumosSemClassificacao(); // Recarregar lista
    fecharPopupClassificacao();
  };

  // Callback quando feedback é enviado no popup (classificação manual)
  const handleFeedbackEnviado = async () => {
  console.log('Processando classificação manual...');
  
  try {
    // Recarregar a lista para que o insumo saia da tabela
    await carregarInsumosSemClassificacao();
    
    // REMOVER popup de sucesso daqui - será mostrado no PopupClassificacaoIA
    console.log('Lista de insumos recarregada após classificação');
    
  } catch (error) {
    console.error('Erro no feedback:', error);
  }
};

  if (carregandoInsumos) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-gray-500">Carregando insumos...</div>
      </div>
    );
  }

  if (insumosSemClassificacao.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-gray-500 mb-2">✅ Todos os insumos estão classificados!</div>
        <div className="text-sm text-gray-400">Nenhum insumo aguardando classificação</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* ============================================================================ */}
      {/* HEADER COM CONTADOR E PAGINAÇÃO */}
      {/* ============================================================================ */}
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-center gap-4 mb-6">
        {/* Titulo e contador de insumos */}
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Insumos Aguardando Classificação
          </h3>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center justify-center min-w-[28px] h-7 px-2.5 bg-orange-100 text-orange-700 font-bold rounded-full text-sm">
              {totalInsumosSemClassificacao}
            </span>
            <p className="text-sm text-gray-600">
              {totalInsumosSemClassificacao === 1 ? 'insumo aguardando' : 'insumos aguardando'} classificação pela IA
            </p>
          </div>
        </div>

        {/* Paginacao no topo */}
        {totalPaginas > 1 && (
          <div className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3 sm:px-6 rounded-lg">
            {/* Mobile - Botoes Anterior/Proxima */}
            <div className="flex flex-1 justify-between sm:hidden">
              <button
                onClick={() => setPaginaAtual(Math.max(1, paginaAtual - 1))}
                disabled={paginaAtual === 1}
                className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Anterior
              </button>
              <span className="text-sm text-gray-700">
                {paginaAtual} / {totalPaginas}
              </span>
              <button
                onClick={() => setPaginaAtual(Math.min(totalPaginas, paginaAtual + 1))}
                disabled={paginaAtual === totalPaginas}
                className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Próxima
              </button>
            </div>

            {/* Desktop - Paginacao Completa */}
            <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between sm:gap-8">
              <div>
                <p className="text-sm text-gray-700">
                  Mostrando 
                  <span className="font-medium"> {(paginaAtual - 1) * itensPorPagina + 1}</span> a{' '}
                  <span className="font-medium">
                    {Math.min(paginaAtual * itensPorPagina, totalInsumosSemClassificacao)}
                  </span>{' '}
                  de <span className="font-medium">{totalInsumosSemClassificacao}</span> insumos
                </p>
              </div>
              <div>
                <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                  <button
                    onClick={() => setPaginaAtual(Math.max(1, paginaAtual - 1))}
                    disabled={paginaAtual === 1}
                    className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Anterior</span>
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                  
                  {Array.from({ length: Math.min(5, totalPaginas) }, (_, i) => {
                    let pageNum;
                    if (totalPaginas <= 5) {
                      pageNum = i + 1;
                    } else if (paginaAtual <= 3) {
                      pageNum = i + 1;
                    } else if (paginaAtual >= totalPaginas - 2) {
                      pageNum = totalPaginas - 4 + i;
                    } else {
                      pageNum = paginaAtual - 2 + i;
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPaginaAtual(pageNum)}
                        className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ${
                          paginaAtual === pageNum
                            ? 'z-10 bg-green-600 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600'
                            : 'text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                  
                  <button
                    onClick={() => setPaginaAtual(Math.min(totalPaginas, paginaAtual + 1))}
                    disabled={paginaAtual === totalPaginas}
                    className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Próxima</span>
                    <ChevronRight className="h-5 w-5" />
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Produto
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Código
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Unidade
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Grupo Atual
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ações
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {insumosPaginados.map((insumo) => (
              <tr key={insumo.id} className="hover:bg-gray-50">

                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {insumo.nome}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {insumo.codigo}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {insumo.unidade}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {insumo.grupo} &gt; {insumo.subgrupo}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <button
                    onClick={() => classificarInsumo(insumo.id, insumo.nome)}
                    className="px-3 py-1.5 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700"
                  >
                    Classificar com IA
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* ============================================================================ */}
      {/* RODAPÉ COM INFORMAÇÕES E PAGINAÇÃO */}
      {/* ============================================================================ */}
      <div className="flex justify-between items-center pt-4 border-t border-gray-200 mt-4">
        {/* Botão atualizar e informação (esquerda) */}
        <div className="flex items-center gap-4">
          <button
            onClick={carregarInsumosSemClassificacao}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            🔄 Atualizar Lista
          </button>
          <div className="text-xs text-gray-500">
            Mostrando {(paginaAtual - 1) * itensPorPagina + 1} a {Math.min(paginaAtual * itensPorPagina, totalInsumosSemClassificacao)} de {totalInsumosSemClassificacao} insumos
          </div>
        </div>

        {/* Paginacao no rodape */}
        {totalPaginas > 1 && (
          <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6 rounded-lg mt-4">
            {/* Mobile - Botoes Anterior/Proxima */}
            <div className="flex flex-1 justify-between sm:hidden">
              <button
                onClick={() => setPaginaAtual(Math.max(1, paginaAtual - 1))}
                disabled={paginaAtual === 1}
                className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Anterior
              </button>
              <span className="text-sm text-gray-700">
                {paginaAtual} / {totalPaginas}
              </span>
              <button
                onClick={() => setPaginaAtual(Math.min(totalPaginas, paginaAtual + 1))}
                disabled={paginaAtual === totalPaginas}
                className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Próxima
              </button>
            </div>

            {/* Desktop - Paginacao Completa */}
            <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Mostrando 
                  <span className="font-medium"> {(paginaAtual - 1) * itensPorPagina + 1}</span> a{' '}
                  <span className="font-medium">
                    {Math.min(paginaAtual * itensPorPagina, totalInsumosSemClassificacao)}
                  </span>{' '}
                  de <span className="font-medium">{totalInsumosSemClassificacao}</span> insumos
                </p>
              </div>
              <div>
                <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                  <button
                    onClick={() => setPaginaAtual(Math.max(1, paginaAtual - 1))}
                    disabled={paginaAtual === 1}
                    className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Anterior</span>
                    <ChevronLeft className="h-5 w-5" />
                  </button>
                  
                  {Array.from({ length: Math.min(5, totalPaginas) }, (_, i) => {
                    let pageNum;
                    if (totalPaginas <= 5) {
                      pageNum = i + 1;
                    } else if (paginaAtual <= 3) {
                      pageNum = i + 1;
                    } else if (paginaAtual >= totalPaginas - 2) {
                      pageNum = totalPaginas - 4 + i;
                    } else {
                      pageNum = paginaAtual - 2 + i;
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPaginaAtual(pageNum)}
                        className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ${
                          paginaAtual === pageNum
                            ? 'z-10 bg-green-600 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600'
                            : 'text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                  
                  <button
                    onClick={() => setPaginaAtual(Math.min(totalPaginas, paginaAtual + 1))}
                    disabled={paginaAtual === totalPaginas}
                    className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Próxima</span>
                    <ChevronRight className="h-5 w-5" />
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>
    
        {/* Popup de Classificação Manual */}
        {insumoSelecionado && (
          <PopupClassificacaoIA
            isVisible={popupClassificacaoVisivel}
            nomeInsumo={insumoSelecionado.nome}
            insumoId={insumoSelecionado.id}
            onClose={fecharPopupClassificacao}
            onClassificacaoAceita={handleClassificacaoAceita}
            onFeedbackEnviado={handleFeedbackEnviado}
            showSuccessPopup={(title: string, message: string) => {
              if (typeof (window as any).showSuccessPopup === 'function') {
                (window as any).showSuccessPopup(title, message);
              }
            }}
            showErrorPopup={(title: string, message: string) => {
              if (typeof (window as any).showErrorPopup === 'function') {
                (window as any).showErrorPopup(title, message);
              }
            }}
          />
        )}
      </div>
  );
};

const ClassificadorIA: React.FC = () => {
  // Estados principais
  const [produtoInput, setProdutoInput] = useState('');
  const [classificacao, setClassificacao] = useState<ClassificacaoResposta | null>(null);
  const [status, setStatus] = useState<StatusSistema | null>(null);
  const [estatisticas, setEstatisticas] = useState<EstatisticasIA | null>(null);
  const [historico, setHistorico] = useState<ClassificacaoResposta[]>([]);
  
  // Estados de UI
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [abaSelecionada, setAbaSelecionada] = useState<'classificar' | 'historico' | 'estatisticas'>('classificar');
  const [comentarioFeedback, setComentarioFeedback] = useState('');

  // Funções de API
  const buscarStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/ia/status`);
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Erro ao buscar status:', error);
    }
  };

  const buscarEstatisticas = async () => {
    try {
      const response = await fetch('/api/v1/ia/estatisticas');
      if (response.ok) {
        const data = await response.json();
        setEstatisticas(data);
      }
    } catch (error) {
      console.error('Erro ao buscar estatísticas:', error);
    }
  };

  const classificarProduto = async () => {
    if (!produtoInput.trim()) {
      setErro('Digite o nome de um produto');
      return;
    }

    setCarregando(true);
    setErro(null);

    try {
      const response = await fetch('/api/v1/ia/classificar', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          nome_produto: produtoInput.trim(),
          incluir_alternativas: true,
          limite_alternativas: 3,
          confianca_minima: 0.5
        }),
      });

      if (response.ok) {
        const data: ClassificacaoResposta = await response.json();
        setClassificacao(data);
        setHistorico(prev => [data, ...prev.slice(0, 9)]);
      } else {
        setErro('Erro ao classificar produto');
      }
    } catch (error) {
      setErro('Erro de conexão com a API');
      console.error('Erro:', error);
    } finally {
      setCarregando(false);
    }
  };

  const enviarFeedback = async (acao: 'aceitar' | 'corrigir') => {
    if (!classificacao) return;

    try {
      const response = await fetch('/api/v1/ia/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          nome_produto: classificacao.termo_analisado,
          classificacao_sugerida: classificacao.taxonomia_sugerida,
          acao,
          taxonomia_correta: classificacao.taxonomia_sugerida,
          observacoes: comentarioFeedback
        }),
      });

      if (response.ok) {
        buscarEstatisticas();
        setComentarioFeedback('');
        alert(acao === 'aceitar' ? 'Feedback positivo enviado!' : 'Correção enviada!');
      }
    } catch (error) {
      console.error('Erro ao enviar feedback:', error);
      alert('Erro ao enviar feedback');
    }
  };

  useEffect(() => {
    buscarStatus();
    buscarEstatisticas();
  }, []);

  // Funções auxiliares
  const obterCorConfianca = (confianca: number): string => {
    if (confianca >= 0.8) return 'text-green-600';
    if (confianca >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const obterIconeStatus = (status: string) => {
    switch (status) {
      case 'sucesso': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'baixa_confianca': return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'sem_correspondencia': return <XCircle className="w-5 h-5 text-red-500" />;
      default: return <AlertTriangle className="w-5 h-5 text-gray-500" />;
    }
  };

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      <div className="flex items-center gap-3">
        <Brain className="w-8 h-8 text-green-600" />
        <div>
          <h1 className="text-3xl font-bold">Sistema de IA</h1>
          <p className="text-gray-600">Classificação Inteligente de Insumos</p>
        </div>
      </div>

      {/* Status do Sistema */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        
        {status ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <span className={`px-2 py-1 text-xs rounded-full ${
                status.sistema_ativo ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}>
                {status.sistema_ativo ? "Ativo" : "Inativo"}
              </span>
              <span className="text-sm text-gray-600">Sistema</span>
            </div>
            
            <div className="flex items-center gap-2">
              <span className={`px-2 py-1 text-xs rounded-full ${
                status.spacy_disponivel ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
              }`}>
                {status.spacy_disponivel ? "OK" : "N/A"}
              </span>
              <span className="text-sm text-gray-600">spaCy</span>
            </div>
            
            <div className="flex items-center gap-2">
              <span className={`px-2 py-1 text-xs rounded-full ${
                status.fuzzywuzzy_disponivel ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
              }`}>
                {status.fuzzywuzzy_disponivel ? "OK" : "N/A"}
              </span>
              <span className="text-sm text-gray-600">FuzzyWuzzy</span>
            </div>
            
            <div className="flex items-center gap-2">
              <span className={`px-2 py-1 text-xs rounded-full ${
                status.modelo_portugues ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
              }`}>
                {status.modelo_portugues ? "OK" : "N/A"}
              </span>
              <span className="text-sm text-gray-600">Português</span>
            </div>
          </div>
        ) : (
          <p className="text-gray-500">Carregando status...</p>
        )}
        
        {status?.avisos && status.avisos.length > 0 && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <p className="text-yellow-800">{status.avisos.join(', ')}</p>
          </div>
        )}
      </div>

      {/* Navegação por abas */}
      <div className="flex space-x-1 border-b bg-white rounded-t-lg">
        <button
          onClick={() => setAbaSelecionada('classificar')}
          className={`px-4 py-2 border-b-2 font-medium text-sm ${
            abaSelecionada === 'classificar'
              ? 'border-green-500 text-green-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Classificar
        </button>
        <button
          onClick={() => setAbaSelecionada('historico')}
          className={`px-4 py-2 border-b-2 font-medium text-sm ${
            abaSelecionada === 'historico'
              ? 'border-green-500 text-green-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Histórico
        </button>
        <button
          onClick={() => setAbaSelecionada('estatisticas')}
          className={`px-4 py-2 border-b-2 font-medium text-sm ${
            abaSelecionada === 'estatisticas'
              ? 'border-green-500 text-green-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Estatísticas
        </button>
      </div>

      {/* Conteúdo das abas */}
      <div className="mt-6">
        {abaSelecionada === 'classificar' && (
          <div className="space-y-6">
            {/* Tabela de insumos aguardando classificação */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <InsumosSemClassificacao />
            </div>
          </div>
        )}

        {abaSelecionada === 'historico' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center gap-2 mb-4">
              <Clock className="w-5 h-5" />
              <h3 className="text-lg font-semibold">Histórico de Classificações</h3>
            </div>
            
            {historico.length > 0 ? (
              <div className="space-y-3">
                {historico.map((item, index) => (
                  <div key={index} className="border rounded-lg p-3 bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium">{item.termo_analisado}</p>
                        {item.taxonomia_sugerida && (
                          <p className="text-sm text-gray-600">
                            {item.taxonomia_sugerida.nome_completo}
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        {obterIconeStatus(item.status)}
                        <p className={`text-sm ${obterCorConfianca(item.confianca)}`}>
                          {(item.confianca * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                Nenhuma classificação realizada ainda
              </p>
            )}
          </div>
        )}

        {abaSelecionada === 'estatisticas' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Target className="w-5 h-5" />
                <h3 className="text-lg font-semibold">Performance Geral</h3>
              </div>
              
              {estatisticas ? (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">Taxa de Acerto</label>
                    <p className="text-2xl font-bold text-green-600">
                      {(estatisticas.taxa_acerto_geral * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Confiança Média</label>
                    <p className="text-2xl font-bold text-green-600">
                      {(estatisticas.confianca_media * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Total de Classificações</label>
                    <p className="text-2xl font-bold text-purple-600">
                      {estatisticas.total_classificacoes_realizadas}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-gray-500">Carregando estatísticas...</p>
              )}
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="w-5 h-5" />
                <h3 className="text-lg font-semibold">Base de Conhecimento</h3>
              </div>
              
              {estatisticas ? (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">Entradas na Base</label>
                    <p className="text-2xl font-bold text-indigo-600">
                      {estatisticas.total_entradas_conhecimento}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Confirmações</label>
                    <p className="text-2xl font-bold text-green-600">
                      {estatisticas.total_confirmacoes}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Correções</label>
                    <p className="text-2xl font-bold text-orange-600">
                      {estatisticas.total_correcoes}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-gray-500">Carregando estatísticas...</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
export default ClassificadorIA;