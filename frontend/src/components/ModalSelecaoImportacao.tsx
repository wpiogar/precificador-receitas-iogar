/*
 * ============================================================================
 * MODAL DE SELEÇÃO DE TIPO DE IMPORTAÇÃO
 * ============================================================================
 * Descrição: Modal intermediário que permite ao usuário escolher se vai
 *           importar Insumos ou Receitas antes de abrir o modal específico.
 * 
 * Data: 15/11/2025
 * Autor: Will - Empresa: IOGAR
 * ============================================================================
 */

import React, { useState } from 'react';
import { X, Package, ChefHat, Store, AlertCircle, Loader } from 'lucide-react';

// ============================================================================
// INTERFACES
// ============================================================================

interface ModalSelecaoImportacaoProps {
  onClose: () => void;
  onSelectInsumos: (restauranteId: number | null, isGlobal: boolean) => void;
  onSelectReceitas: (restauranteId: number) => void;
  restauranteSelecionado: { id: number; nome: string } | null;
  restaurantesDisponiveis: Array<{ id: number; nome: string }>;
  userRole: string;
  tipoFixo?: 'insumos' | 'receitas' | null;
}

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================

const ModalSelecaoImportacao: React.FC<ModalSelecaoImportacaoProps> = ({
  onClose,
  onSelectInsumos,
  onSelectReceitas,
  restauranteSelecionado,
  restaurantesDisponiveis,
  userRole,
  tipoFixo = null
}) => {
  // Estados locais
  const [tipoSelecionado, setTipoSelecionado] = useState<'insumos' | 'receitas' | null>(tipoFixo);
  const [insumoGlobal, setInsumoGlobal] = useState(false);
  const [restauranteEscolhido, setRestauranteEscolhido] = useState<number | null>(null);
  const [processando, setProcessando] = useState(false);

  // ============================================================================
  // FUNÇÃO: CONFIRMAR SELEÇÃO
  // ============================================================================
  const handleConfirmar = () => {
    if (!tipoSelecionado) return;

    setProcessando(true);

    setTimeout(() => {
      if (tipoSelecionado === 'insumos') {
        onSelectInsumos(
          insumoGlobal ? null : (restauranteEscolhido || restauranteSelecionado?.id || null),
          insumoGlobal
        );
      } else {
        // Receitas: usar restaurante selecionado automaticamente
        const restauranteId = restauranteSelecionado?.id || restauranteEscolhido;
        if (restauranteId) {
          onSelectReceitas(restauranteId);
        }
      }
      setProcessando(false);
    }, 300);
  };

  // ============================================================================
  // VERIFICAR SE PODE CONFIRMAR
  // ============================================================================
  const podeConfirmar = () => {
    if (!tipoSelecionado) return false;

    if (tipoSelecionado === 'insumos') {
      // Insumos: precisa de restaurante OU ser global
      return restauranteSelecionado || insumoGlobal || restauranteEscolhido;
    }

    if (tipoSelecionado === 'receitas') {
      // Receitas: SEMPRE precisa de restaurante
      return restauranteSelecionado || restauranteEscolhido;
    }

    return false;
  };

  // ============================================================================
  // RENDER: TELA DE PROCESSAMENTO
  // ============================================================================
  if (processando) {
    return (
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-white rounded-xl shadow-2xl p-8 max-w-md w-full mx-4">
          <div className="flex flex-col items-center justify-center space-y-4">
            {/* Spinner do Flowbite */}
            <div role="status">
              <svg 
                aria-hidden="true" 
                className="w-16 h-16 text-gray-200 animate-spin fill-green-600"
                viewBox="0 0 100 101" 
                fill="none" 
                xmlns="http://www.w3.org/2000/svg"
              >
                <path 
                  d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" 
                  fill="currentColor"
                />
                <path 
                  d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" 
                  fill="currentFill"
                />
              </svg>
              <span className="sr-only">Carregando...</span>
            </div>
            <p className="text-lg font-semibold text-gray-900">Preparando importação...</p>
            <p className="text-sm text-gray-600">Aguarde um momento</p>
          </div>
        </div>
      </div>
    );
  }

  // ============================================================================
  // RENDER PRINCIPAL
  // ============================================================================
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-pink-500 rounded-lg flex items-center justify-center">
              {tipoFixo === 'receitas' ? (
                <ChefHat className="w-5 h-5 text-white" />
              ) : tipoFixo === 'insumos' ? (
                <Package className="w-5 h-5 text-white" />
              ) : (
                <Package className="w-5 h-5 text-white" />
              )}
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                {tipoFixo === 'receitas' ? 'Importar Receitas' : tipoFixo === 'insumos' ? 'Importar Insumos' : 'Importar Dados'}
              </h2>
              <p className="text-sm text-gray-500">
                {tipoFixo ? 'Configure as opções de importação' : 'Escolha o tipo de dados que deseja importar'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Conteúdo */}
        <div className="p-6 space-y-6">
          
          {/* Opções de Tipo - Apenas se não for tipo fixo */}
          {!tipoFixo && (
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-gray-900 mb-3">
                O que você deseja importar?
              </label>

              {/* Opção: Insumos */}
              <button
                onClick={() => setTipoSelecionado('insumos')}
              className={`w-full flex items-start gap-4 p-4 rounded-xl border-2 transition-all ${
                tipoSelecionado === 'insumos'
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:border-green-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex-shrink-0">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                  tipoSelecionado === 'insumos' ? 'bg-green-500' : 'bg-gray-100'
                }`}>
                  <Package className={`w-6 h-6 ${
                    tipoSelecionado === 'insumos' ? 'text-white' : 'text-gray-400'
                  }`} />
                </div>
              </div>
              <div className="flex-1 text-left">
                <h3 className="font-semibold text-gray-900 mb-1">Insumos (Ingredientes)</h3>
                <p className="text-sm text-gray-600">
                  Importar lista de ingredientes com preços, unidades e fornecedores
                </p>
              </div>
            </button>

            {/* Opção: Receitas */}
            <button
              onClick={() => setTipoSelecionado('receitas')}
              className={`w-full flex items-start gap-4 p-4 rounded-xl border-2 transition-all ${
                tipoSelecionado === 'receitas'
                  ? 'border-pink-500 bg-pink-50'
                  : 'border-gray-200 hover:border-pink-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex-shrink-0">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                  tipoSelecionado === 'receitas' ? 'bg-pink-500' : 'bg-gray-100'
                }`}>
                  <ChefHat className={`w-6 h-6 ${
                    tipoSelecionado === 'receitas' ? 'text-white' : 'text-gray-400'
                  }`} />
                </div>
              </div>
              <div className="flex-1 text-left">
                <h3 className="font-semibold text-gray-900 mb-1">Receitas</h3>
                <p className="text-sm text-gray-600">
                  Importar fichas técnicas com insumos, quantidades e modo de preparo
                </p>
              </div>
            </button>
          </div>
          )}
          {/* Configurações adicionais - Apenas se tipo selecionado */}
          {tipoSelecionado && (
            <div className="space-y-4 pt-4 border-t border-gray-200">
              
              {/* Se tem restaurante selecionado no menu */}
              {restauranteSelecionado && (
                <div className={`rounded-xl p-4 ${
                  tipoSelecionado === 'receitas' 
                    ? 'bg-green-50 border-2 border-green-500' 
                    : 'bg-blue-50 border-2 border-blue-200'
                }`}>
                  <div className="flex items-start gap-3">
                    <Store className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                      tipoSelecionado === 'receitas' ? 'text-green-600' : 'text-blue-600'
                    }`} />
                    <div className="flex-1">
                      <h4 className={`font-semibold mb-1 ${
                        tipoSelecionado === 'receitas' ? 'text-green-900' : 'text-blue-900'
                      }`}>
                        {tipoSelecionado === 'receitas' ? '✓ Pronto para Importar' : 'Restaurante Selecionado'}
                      </h4>
                      <p className={`text-sm ${
                        tipoSelecionado === 'receitas' ? 'text-green-800' : 'text-blue-800'
                      }`}>
                        {tipoSelecionado === 'receitas' 
                          ? `As receitas serão importadas para: ${restauranteSelecionado.nome}`
                          : `Os dados serão importados para: ${restauranteSelecionado.nome}`
                        }
                      </p>
                      {tipoSelecionado === 'receitas' && (
                        <p className="text-xs text-green-700 mt-2 font-medium">
                          Clique em "Continuar" para selecionar o arquivo Excel
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Se NÃO tem restaurante selecionado - Mostrar opções */}
              {!restauranteSelecionado && (
                <div className="space-y-4">
                  
                  {/* Para INSUMOS - opção de global */}
                  {tipoSelecionado === 'insumos' && ['ADMIN', 'CONSULTANT'].includes(userRole) && (
                    <div className="flex items-start gap-3 p-4 bg-purple-50 border-2 border-purple-200 rounded-xl hover:bg-purple-100 transition-all cursor-pointer"
                      onClick={() => setInsumoGlobal(!insumoGlobal)}
                    >
                      <input
                        type="checkbox"
                        checked={insumoGlobal}
                        onChange={(e) => {
                          setInsumoGlobal(e.target.checked);
                          if (e.target.checked) {
                            setRestauranteEscolhido(null);
                          }
                        }}
                        className="w-5 h-5 text-purple-600 border-gray-300 rounded focus:ring-purple-500 mt-0.5"
                      />
                      <div className="flex-1">
                        <label className="font-semibold text-purple-900 cursor-pointer">
                          Importar como Insumos Globais
                        </label>
                        <p className="text-sm text-purple-800 mt-1">
                          Os insumos ficarão disponíveis para todos os restaurantes do sistema
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Seleção de Restaurante - se não for global */}
                  {(!insumoGlobal || tipoSelecionado === 'receitas') && (
                    <div className="space-y-3">
                      <label className="block text-sm font-semibold text-gray-900">
                        Selecione o Restaurante {tipoSelecionado === 'receitas' && '*'}
                      </label>
                      <select
                        value={restauranteEscolhido || ''}
                        onChange={(e) => setRestauranteEscolhido(e.target.value ? Number(e.target.value) : null)}
                        className="w-full px-4 py-3 bg-white border-2 border-green-500 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-600 transition-all"
                      >
                        <option value="">Escolha um restaurante...</option>
                        {restaurantesDisponiveis.map(rest => (
                          <option key={rest.id} value={rest.id}>
                            {rest.nome}
                          </option>
                        ))}
                      </select>

                      {/* Alerta se não selecionou */}
                      {tipoSelecionado === 'receitas' && !restauranteEscolhido && (
                        <div className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                          <p className="text-sm text-yellow-800">
                            <strong>Atenção:</strong> Receitas precisam estar vinculadas a um restaurante específico.
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer com botões */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-6 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleConfirmar}
            disabled={!podeConfirmar()}
            className={`px-6 py-2 rounded-lg font-medium transition-all ${
              podeConfirmar()
                ? 'bg-gradient-to-r from-green-500 to-pink-500 text-white hover:from-green-600 hover:to-pink-600 shadow-md hover:shadow-lg'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            {tipoSelecionado === 'receitas' && restauranteSelecionado 
              ? 'Continuar para Importação' 
              : 'Continuar'
            }
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModalSelecaoImportacao;