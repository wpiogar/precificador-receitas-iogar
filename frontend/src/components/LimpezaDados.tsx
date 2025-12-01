// ============================================================================
// COMPONENTE DE LIMPEZA DE DADOS - PAINEL ADMINISTRATIVO
// ============================================================================
// Descricao: Tela para limpeza seletiva de dados do sistema (apenas ADMIN)
// Acesso via Configuracoes > Limpeza de Dados
// Data: 24/10/2025
// Autor: Will - Empresa: IOGAR
// ============================================================================

import React, { useState, useEffect } from 'react';
import { 
  Trash2, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  RefreshCw,
  Database,
  Users,
  ShoppingCart,
  Package,
  Building,
  Tag
} from 'lucide-react';

import { apiService } from '../api-service';

// ============================================================================
// INTERFACES
// ============================================================================

interface Estatisticas {
  total_receitas: number;
  total_insumos: number;
  total_fornecedores: number;
  total_fornecedor_insumos: number;
  total_restaurantes: number;
  total_taxonomias: number;
  total_usuarios: number;
}

interface FiltroLimpeza {
  data_inicio?: string;
  data_fim?: string;
  restaurante_id?: number;
}

interface ResultadoLimpeza {
  secao: string;
  registros_removidos: number;
  sucesso: boolean;
  mensagem: string;
}

// ============================================================================
// PROPS DO COMPONENTE
// ============================================================================

interface LimpezaDadosProps {
  selectedRestaurante: {
    id: number;
    nome: string;
  } | null;
}

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================

const LimpezaDados: React.FC<LimpezaDadosProps> = ({ selectedRestaurante }) => {
  // Estados
  const [estatisticas, setEstatisticas] = useState<Estatisticas | null>(null);
  const [loading, setLoading] = useState(false);
  const [resultados, setResultados] = useState<ResultadoLimpeza[]>([]);
  const [mostrarConfirmacao, setMostrarConfirmacao] = useState(false);
  const [acaoSelecionada, setAcaoSelecionada] = useState<string>('');
  const [confirmacaoTexto, setConfirmacaoTexto] = useState('');

  // Estado para modal de erro customizado
  const [mostrarErro, setMostrarErro] = useState(false);
  const [erroTitulo, setErroTitulo] = useState('');
  const [erroMensagem, setErroMensagem] = useState('');
  
  // Filtros
  const [filtros, setFiltros] = useState<FiltroLimpeza>({});

  // Estados para modal de selecao de restaurante
  const [mostrarModalRestaurante, setMostrarModalRestaurante] = useState(false);
  const [restaurantes, setRestaurantes] = useState<Array<{ id: number; nome: string }>>([]);
  const [restauranteSelecionadoModal, setRestauranteSelecionadoModal] = useState<number | 'todos'>('todos');

  // ============================================================================
  // CARREGAR ESTATISTICAS
  // ============================================================================

  useEffect(() => {
    carregarEstatisticas();
  }, [selectedRestaurante]);

  const carregarEstatisticas = async () => {
    try {
      // Passar o ID do restaurante selecionado para filtrar as estatísticas
      const { data, error } = await apiService.getEstatisticasLimpeza(
        selectedRestaurante?.id
      );
      
      if (error) {
        console.error('Erro ao carregar estatisticas:', error);
        return;
      }
      
      if (data) {
        setEstatisticas(data);
      }
    } catch (error) {
      console.error('Erro ao carregar estatisticas:', error);
    }
  };

  // ============================================================================
  // CARREGAR LISTA DE RESTAURANTES
  // ============================================================================

  const carregarRestaurantes = async () => {
    try {
      // Usar apiService para manter consistência
      const response = await apiService.getRestaurantesGrid();
      
      if (response.data) {
        // Extrair apenas id e nome para o modal
        const restaurantesSimples = response.data.map((r: any) => ({
          id: r.id,
          nome: r.nome
        }));
        setRestaurantes(restaurantesSimples);
        console.log('✅ Restaurantes carregados:', restaurantesSimples);
      } else if (response.error) {
        console.error('Erro ao carregar restaurantes:', response.error);
        setRestaurantes([]);
      }
    } catch (error) {
      console.error('Erro ao carregar restaurantes:', error);
      setRestaurantes([]);
    }
  };

  // ============================================================================
  // FUNCOES DE LIMPEZA
  // ============================================================================

  const iniciarLimpeza = (secao: string) => {
    setAcaoSelecionada(secao);
    setResultados([]);
    
    // Se for limpeza de receitas, insumos ou restaurantes e NAO houver restaurante selecionado
    if ((secao === 'receitas' || secao === 'insumos' || secao === 'restaurantes') && !selectedRestaurante) {
      // Carregar lista de restaurantes e mostrar modal de selecao
      carregarRestaurantes();
      setMostrarModalRestaurante(true);
      setRestauranteSelecionadoModal('todos');
    } else {
      // Se houver restaurante selecionado ou for outra secao, ir direto para confirmacao
      setMostrarConfirmacao(true);
      setConfirmacaoTexto('');
    }
  };

  // ============================================================================
  // CONFIRMAR SELECAO DE RESTAURANTE NO MODAL
  // ============================================================================

  const confirmarSelecaoRestaurante = () => {
    // Fechar modal de selecao de restaurante
    setMostrarModalRestaurante(false);
    
    // Configurar filtros baseado na selecao
    if (restauranteSelecionadoModal !== 'todos') {
      setFiltros({ restaurante_id: restauranteSelecionadoModal as number });
    } else {
      setFiltros({});
    }
    
    // Mostrar modal de confirmacao
    setMostrarConfirmacao(true);
    setConfirmacaoTexto('');
  };

  const confirmarLimpeza = async () => {
    // Validar confirmacao para limpeza total APENAS se NAO houver restaurante selecionado
    if (acaoSelecionada === 'limpar-tudo' && !selectedRestaurante && confirmacaoTexto !== 'CONFIRMAR LIMPEZA TOTAL') {
      setErroTitulo('Confirmação Incorreta');
      setErroMensagem('Digite exatamente: CONFIRMAR LIMPEZA TOTAL');
      setMostrarErro(true);
      return;
    }

    setLoading(true);
    setMostrarConfirmacao(false);

    try {
      let response;
      
      // Preparar filtros com base no restaurante selecionado
      let filtrosParaEnviar = { ...filtros };
      
      // Se houver restaurante selecionado no menu, adicionar ao filtro
      if (selectedRestaurante && (acaoSelecionada === 'receitas' || acaoSelecionada === 'insumos' || acaoSelecionada === 'restaurantes')) {
        filtrosParaEnviar.restaurante_id = selectedRestaurante.id;
      }
      
      // Executar ação conforme seleção
      switch (acaoSelecionada) {
        case 'receitas':
          response = await apiService.limparReceitas(Object.keys(filtrosParaEnviar).length > 0 ? filtrosParaEnviar : undefined);
          break;
        case 'insumos':
          response = await apiService.limparInsumos(Object.keys(filtrosParaEnviar).length > 0 ? filtrosParaEnviar : undefined);
          break;
        case 'fornecedores':
          response = await apiService.limparFornecedores();
          break;
        case 'restaurantes':
          // Se houver filtro de restaurante, enviar; senão, manter ID 1
          if (Object.keys(filtrosParaEnviar).length > 0 && filtrosParaEnviar.restaurante_id) {
            response = await apiService.limparRestaurantes(false, filtrosParaEnviar.restaurante_id);
          } else {
            response = await apiService.limparRestaurantes(true);
          }
          break;
        case 'limpar-tudo':
          // Se houver restaurante selecionado, limpar apenas dados desse restaurante
          if (selectedRestaurante) {
            // Limpar em sequência: receitas, insumos e o restaurante
            const resultadosLimpezaRestaurante: ResultadoLimpeza[] = [];
            
            // 1. Limpar receitas do restaurante
            const resReceitas = await apiService.limparReceitas({ restaurante_id: selectedRestaurante.id });
            if (resReceitas.data) resultadosLimpezaRestaurante.push(resReceitas.data);
            
            // 2. Limpar insumos do restaurante
            const resInsumos = await apiService.limparInsumos({ restaurante_id: selectedRestaurante.id });
            if (resInsumos.data) resultadosLimpezaRestaurante.push(resInsumos.data);
            
            // 3. Limpar o restaurante
            const resRestaurante = await apiService.limparRestaurantes(false, selectedRestaurante.id);
            if (resRestaurante.data) resultadosLimpezaRestaurante.push(resRestaurante.data);
            
            // Criar resposta consolidada
            response = { data: resultadosLimpezaRestaurante, error: null };
          } else {
            // Limpeza total do sistema
            response = await apiService.limparTudo('CONFIRMAR LIMPEZA TOTAL');
          }
          break;
        default:
          throw new Error('Ação inválida');
      }

      if (response.error) {
        setErroTitulo('Erro na Limpeza');
        setErroMensagem(response.error);
        setMostrarErro(true);
        return;
      }

      if (response.data) {
        // Se for array de resultados (limpar tudo) ou resultado único
        const resultadosArray = Array.isArray(response.data) ? response.data : [response.data];
        setResultados(resultadosArray);
        
        // Recarregar estatísticas
        await carregarEstatisticas();
      }
    } catch (error: any) {
      console.error('Erro ao executar limpeza:', error);
      setErroTitulo('Erro de Conexão');
      setErroMensagem(error.message || 'Erro ao executar limpeza. Verifique sua conexão com o servidor.');
      setMostrarErro(true);
    } finally {
      setLoading(false);
    }
  };

  const cancelarLimpeza = () => {
    setMostrarConfirmacao(false);
    setMostrarModalRestaurante(false);
    setAcaoSelecionada('');
    setConfirmacaoTexto('');
    setFiltros({});
    setRestauranteSelecionadoModal('todos');
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Database className="w-8 h-8 text-red-600" />
          <h1 className="text-3xl font-bold text-gray-900">Limpeza de Dados</h1>
        </div>
        <p className="text-gray-600">
          Gerencie e limpe dados do sistema de forma seletiva ou total
        </p>
        <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-yellow-800">
            <strong>ATENÇÃO:</strong> Todas as operações de limpeza são IRREVERSÍVEIS. 
            Certifique-se de ter backup dos dados antes de prosseguir.
          </div>
        </div>
      </div>

      {/* Estatisticas */}
      {estatisticas && (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            icon={ShoppingCart}
            label="Receitas"
            valor={estatisticas.total_receitas}
            cor="blue"
          />
          <StatCard
            icon={Package}
            label="Insumos"
            valor={estatisticas.total_insumos}
            cor="green"
          />
          <StatCard
            icon={Users}
            label="Fornecedores"
            valor={estatisticas.total_fornecedores}
            cor="purple"
          />
          <StatCard
            icon={Building}
            label="Restaurantes"
            valor={estatisticas.total_restaurantes}
            cor="orange"
          />
          <StatCard
            icon={Tag}
            label="Taxonomias"
            valor={estatisticas.total_taxonomias}
            cor="pink"
          />
          <StatCard
            icon={Users}
            label="Usuários"
            valor={estatisticas.total_usuarios}
            cor="indigo"
          />
        </div>
      )}

      {/* Secoes de Limpeza */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Receitas */}
        <SecaoLimpeza
          titulo="Receitas"
          descricao={
            selectedRestaurante 
              ? `Remove receitas de: ${selectedRestaurante.nome}`
              : "Remove receitas e seus vínculos com insumos"
          }
          icone={ShoppingCart}
          cor="blue"
          onLimpar={() => iniciarLimpeza('receitas')}
          total={estatisticas?.total_receitas || 0}
          restauranteInfo={selectedRestaurante ? selectedRestaurante.nome : null}
        />

        {/* Insumos */}
        <SecaoLimpeza
          titulo="Insumos"
          descricao={
            selectedRestaurante 
              ? `Remove insumos de: ${selectedRestaurante.nome}`
              : "Remove insumos do sistema"
          }
          icone={Package}
          cor="green"
          onLimpar={() => iniciarLimpeza('insumos')}
          total={estatisticas?.total_insumos || 0}
          restauranteInfo={selectedRestaurante ? selectedRestaurante.nome : null}
        />

        {/* Fornecedores */}
        <SecaoLimpeza
          titulo="Fornecedores"
          descricao="Remove fornecedores e catálogo de insumos"
          icone={Users}
          cor="purple"
          onLimpar={() => iniciarLimpeza('fornecedores')}
          total={estatisticas?.total_fornecedores || 0}
        />

        {/* Restaurantes */}
        <SecaoLimpeza
          titulo="Restaurantes"
          descricao={
            selectedRestaurante 
              ? `Remove restaurante: ${selectedRestaurante.nome}`
              : "Remove restaurantes (mantém ID 1)"
          }
          icone={Building}
          cor="orange"
          onLimpar={() => iniciarLimpeza('restaurantes')}
          total={estatisticas?.total_restaurantes || 0}
          restauranteInfo={selectedRestaurante ? selectedRestaurante.nome : null}
        />
      </div>

      {/* Limpeza Total do Sistema ou Limpeza do Restaurante */}
      <div className={`border-2 rounded-xl p-6 ${
        selectedRestaurante 
          ? 'bg-orange-50 border-orange-300' 
          : 'bg-red-50 border-red-300'
      }`}>
        <div className="flex items-start gap-4">
          <AlertTriangle className={`w-8 h-8 flex-shrink-0 ${
            selectedRestaurante ? 'text-orange-600' : 'text-red-600'
          }`} />
          <div className="flex-1">
            {selectedRestaurante ? (
              <>
                <h3 className="text-xl font-bold text-orange-900 mb-2">
                  Limpeza Total do Restaurante: {selectedRestaurante.nome}
                </h3>
                <p className="text-orange-700 mb-4">
                  Remove TODOS os dados deste restaurante (receitas, insumos e o próprio restaurante). 
                  Esta ação é IRREVERSÍVEL!
                </p>
                <button
                  onClick={() => iniciarLimpeza('limpar-tudo')}
                  disabled={loading}
                  className="px-6 py-3 bg-orange-600 text-white font-semibold rounded-lg 
                           hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed
                           transition-colors flex items-center gap-2"
                >
                  <Trash2 className="w-5 h-5" />
                  Limpar Restaurante Completo
                </button>
              </>
            ) : (
              <>
                <h3 className="text-xl font-bold text-red-900 mb-2">
                  Limpeza Total do Sistema
                </h3>
                <p className="text-red-700 mb-4">
                  Remove TODOS os dados do sistema (receitas, insumos, fornecedores, restaurantes, 
                  taxonomias e usuários). Apenas o usuário ADMIN atual e o restaurante ID 1 serão mantidos.
                </p>
                <button
                  onClick={() => iniciarLimpeza('limpar-tudo')}
                  disabled={loading}
                  className="px-6 py-3 bg-red-600 text-white font-semibold rounded-lg 
                           hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed
                           transition-colors flex items-center gap-2"
                >
                  <Trash2 className="w-5 h-5" />
                  Limpar Tudo
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Resultados */}
      {resultados.length > 0 && (
        <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <CheckCircle className="w-6 h-6 text-green-600" />
            Resultados da Limpeza
          </h3>
          <div className="space-y-3">
            {resultados.map((resultado, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border ${
                  resultado.sucesso
                    ? 'bg-green-50 border-green-200'
                    : 'bg-red-50 border-red-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {resultado.sucesso ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-600" />
                    )}
                    <div>
                      <p className="font-semibold text-gray-900 capitalize">
                        {resultado.secao}
                      </p>
                      <p className="text-sm text-gray-600">{resultado.mensagem}</p>
                    </div>
                  </div>
                  <span className="text-2xl font-bold text-gray-700">
                    {resultado.registros_removidos}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={carregarEstatisticas}
            className="mt-4 px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-lg
                     transition-colors flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Atualizar Estatísticas
          </button>
        </div>
      )}

      {/* Modal de Confirmacao */}
      {mostrarConfirmacao && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
            <div className="flex items-start gap-4 mb-6">
              <AlertTriangle className="w-8 h-8 text-red-600 flex-shrink-0" />
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  Confirmar Limpeza
                </h3>
                <p className="text-gray-600">
                  {acaoSelecionada === 'limpar-tudo' && selectedRestaurante
                    ? `Você está prestes a APAGAR TODOS OS DADOS do restaurante "${selectedRestaurante.nome}". Esta ação é IRREVERSÍVEL!`
                    : acaoSelecionada === 'limpar-tudo'
                    ? 'Você está prestes a APAGAR TODOS OS DADOS do sistema. Esta ação é IRREVERSÍVEL!'
                    : `Você está prestes a remover dados de: ${acaoSelecionada}. Esta ação é IRREVERSÍVEL!`}
                </p>
                
                {/* Mostrar informacao do restaurante se houver filtro ou restaurante selecionado */}
                {(selectedRestaurante || filtros.restaurante_id) && (acaoSelecionada === 'receitas' || acaoSelecionada === 'insumos' || acaoSelecionada === 'restaurantes') && (
                  <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Restaurante:</strong>{' '}
                      {selectedRestaurante 
                        ? selectedRestaurante.nome 
                        : restaurantes.find(r => r.id === filtros.restaurante_id)?.nome || 'Selecionado'}
                    </p>
                    <p className="text-xs text-blue-600 mt-1">
                      Apenas os dados deste restaurante serão removidos
                    </p>
                  </div>
                )}
                
                {/* Mostrar aviso se for limpar TODOS os restaurantes */}
                {!selectedRestaurante && !filtros.restaurante_id && (acaoSelecionada === 'receitas' || acaoSelecionada === 'insumos') && (
                  <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                    <p className="text-sm text-orange-800 font-semibold">
                      Atenção: Dados de TODOS os restaurantes serão removidos
                    </p>
                  </div>
                )}
              </div>
            </div>

            {acaoSelecionada === 'limpar-tudo' && !selectedRestaurante && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Digite: <span className="font-mono text-red-600">CONFIRMAR LIMPEZA TOTAL</span>
                </label>
                <input
                  type="text"
                  value={confirmacaoTexto}
                  onChange={(e) => setConfirmacaoTexto(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg 
                           focus:outline-none focus:ring-2 focus:ring-red-500"
                  placeholder="Digite a confirmação"
                />
              </div>
            )}

            <div className="flex gap-3 justify-end">
              <button
                onClick={cancelarLimpeza}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg
                         transition-colors font-medium"
              >
                Cancelar
              </button>
              <button
                onClick={confirmarLimpeza}
                disabled={loading}
                className="px-4 py-2 bg-red-600 text-white font-semibold rounded-lg
                         hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed
                         transition-colors flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Executando...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    Confirmar Limpeza
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Modal de Erro Customizado */}
      {mostrarErro && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-[70] p-4">
          <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-2xl">
            {/* Header com gradiente IOGAR */}
            <div className="flex items-center gap-3 mb-4 pb-4 border-b border-gray-100">
              <div className="bg-gradient-to-r from-red-500 to-orange-500 p-2 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-bold text-gray-800">{erroTitulo}</h3>
            </div>
            
            {/* Conteúdo */}
            <div className="mb-6">
              <p className="text-gray-600 whitespace-pre-line">
                {erroMensagem}
              </p>
            </div>
            
            {/* Botão */}
            <div className="flex justify-end">
              <button
                onClick={() => setMostrarErro(false)}
                className="px-6 py-2 bg-gradient-to-r from-red-600 to-orange-600 text-white rounded-lg hover:shadow-lg transition-all font-medium"
              >
                Entendi
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Selecao de Restaurante */}
      {mostrarModalRestaurante && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full p-6">
            {/* Header */}
            <div className="flex items-start gap-4 mb-6">
              <div className="bg-gradient-to-r from-green-500 to-pink-500 p-3 rounded-lg">
                <Building className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  Selecione o Restaurante
                </h3>
                <p className="text-gray-600 text-sm">
                  Escolha de qual restaurante deseja limpar os dados, ou selecione "Todos" para limpar de todos os restaurantes.
                </p>
              </div>
            </div>

            {/* Selecao de Restaurante */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Restaurante:
              </label>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {/* Opcao: Todos */}
                <label className="flex items-center gap-3 p-4 border-2 rounded-lg cursor-pointer transition-all hover:bg-gray-50">
                  <input
                    type="radio"
                    name="restaurante"
                    value="todos"
                    checked={restauranteSelecionadoModal === 'todos'}
                    onChange={() => setRestauranteSelecionadoModal('todos')}
                    className="w-5 h-5 text-blue-600"
                  />
                  <div className="flex-1">
                    <span className="font-semibold text-gray-900">Todos os Restaurantes</span>
                    <p className="text-xs text-gray-500 mt-1">
                      Limpar dados de todos os restaurantes do sistema
                    </p>
                  </div>
                </label>

                {/* Mensagem se não houver restaurantes */}
                {restaurantes.length === 0 && (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <p className="text-sm text-yellow-800">
                      Nenhum restaurante cadastrado no sistema
                    </p>
                  </div>
                )}

                {/* Lista de Restaurantes */}
                {restaurantes.map((rest) => (
                  <label
                    key={rest.id}
                    className="flex items-center gap-3 p-4 border-2 rounded-lg cursor-pointer transition-all hover:bg-gray-50"
                  >
                    <input
                      type="radio"
                      name="restaurante"
                      value={rest.id}
                      checked={restauranteSelecionadoModal === rest.id}
                      onChange={() => setRestauranteSelecionadoModal(rest.id)}
                      className="w-5 h-5 text-blue-600"
                    />
                    <div className="flex-1">
                      <span className="font-semibold text-gray-900">{rest.nome}</span>
                      <p className="text-xs text-gray-500 mt-1">
                        Limpar apenas dados deste restaurante
                      </p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Botoes */}
            <div className="flex gap-3 justify-end">
              <button
                onClick={cancelarLimpeza}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg
                         hover:bg-gray-50 transition-colors font-medium"
              >
                Cancelar
              </button>
              <button
                onClick={confirmarSelecaoRestaurante}
                className="px-6 py-2 bg-gradient-to-r from-green-600 to-pink-600 text-white 
                         rounded-lg hover:shadow-lg transition-all font-medium"
              >
                Continuar
              </button>
            </div>
          </div>
        </div>
      )}

    </div>             /* ← Fecha o container principal do componente */
  );
};

// ============================================================================
// COMPONENTES AUXILIARES
// ============================================================================

interface StatCardProps {
  icon: React.ElementType;
  label: string;
  valor: number;
  cor: string;
}

const StatCard: React.FC<StatCardProps> = ({ icon: Icon, label, valor, cor }) => {
  const cores = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    green: 'bg-green-50 text-green-600 border-green-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    orange: 'bg-orange-50 text-orange-600 border-orange-200',
    pink: 'bg-pink-50 text-pink-600 border-pink-200',
    indigo: 'bg-indigo-50 text-indigo-600 border-indigo-200',
  };

  return (
    <div className={`p-4 rounded-xl border ${cores[cor]} transition-all hover:shadow-md`}>
      <div className="flex items-center justify-between mb-2">
        <Icon className="w-6 h-6" />
        <span className="text-2xl font-bold">{valor}</span>
      </div>
      <p className="text-sm font-medium opacity-80">{label}</p>
    </div>
  );
};

interface SecaoLimpezaProps {
  titulo: string;
  descricao: string;
  icone: React.ElementType;
  cor: string;
  onLimpar: () => void;
  total: number;
  restauranteInfo?: string | null;
}

const SecaoLimpeza: React.FC<SecaoLimpezaProps> = ({
  titulo,
  descricao,
  icone: Icon,
  cor,
  onLimpar,
  total,
  restauranteInfo,
}) => {
  const cores = {
    blue: 'border-blue-200 hover:border-blue-300',
    green: 'border-green-200 hover:border-green-300',
    purple: 'border-purple-200 hover:border-purple-300',
    orange: 'border-orange-200 hover:border-orange-300',
  };

  return (
    <div className={`bg-white rounded-xl shadow-sm border-2 ${cores[cor]} p-6 transition-all`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3 flex-1">
          <Icon className="w-6 h-6 text-gray-700" />
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-lg font-bold text-gray-900">{titulo}</h3>
              {restauranteInfo && (
                <span className="px-3 py-1 bg-gradient-to-r from-green-500 to-pink-500 text-white text-xs font-semibold rounded-full">
                  {restauranteInfo}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-600 mt-1">{descricao}</p>
          </div>
        </div>
        <span className="text-xl font-bold text-gray-700">{total}</span>
      </div>
      <button
        onClick={onLimpar}
        disabled={total === 0}
        className="w-full px-4 py-2 bg-red-600 text-white font-semibold rounded-lg
                 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed
                 transition-colors flex items-center justify-center gap-2"
      >
        <Trash2 className="w-4 h-4" />
        Limpar {titulo}
      </button>
    </div>
  );
};

export default LimpezaDados;