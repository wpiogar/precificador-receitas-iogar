// ===================================================================================================
// ARQUIVO: frontend/src/components/SuperPopupRelatorio.tsx
// DESCRIÇÃO: Super Popup de Relatório Detalhado para Receitas
// AUTOR: Claude - IOGAR
// DATA: Setembro 2025
// ===================================================================================================

import React, { useState, useEffect } from 'react';
import { 
  X, FileText, DollarSign, TrendingUp, Clock, Users, Package, 
  Calculator, BarChart3, PieChart, Target, AlertTriangle, CheckCircle,
  Download, Share2, Eye, Edit3, Copy,
  ChefHat, Scale, Percent, Calendar, Hash
} from 'lucide-react';
// Importar modal de selecao de relatorio
import ModalSelecaoRelatorio from './ModalSelecaoRelatorio';

// ===================================================================================================
// INTERFACES E TIPOS
// ===================================================================================================

interface ReceitaDetalhada {
  id: number;
  codigo: string;
  nome: string;
  descricao?: string;
  categoria: string;
  porcoes: number;
  rendimento_porcoes?: number;
  tempo_preparo: number;
  cmv_real: number;
  preco_venda_sugerido: number;
  margem_percentual: number;
  status: 'ativo' | 'inativo' | 'processado';
  created_at: string;
  updated_at: string;
  restaurante_id: number;
  total_insumos: number;
  insumos_processados?: number;
  // Campos calculados
  cmv_20_porcento?: number;
  cmv_25_porcento?: number;
  cmv_30_porcento?: number;
  receita_insumos?: any[];

  tem_insumos_sem_preco?: boolean;
  insumos_pendentes?: number[];
}

interface SuperPopupRelatorioProps {
  isVisible: boolean;
  receita: ReceitaDetalhada | null;
  onClose: () => void;
  onEdit?: (receita: ReceitaDetalhada) => void;
  onDuplicate?: (receita: ReceitaDetalhada) => void;
  onDelete?: (receita: ReceitaDetalhada) => void;
  // ===================================================================================================
  // CALLBACK PARA NAVEGAR PARA ABA INSUMOS COM FILTRO
  // ===================================================================================================
  onNavigateToInsumos?: (insumosPendentes: number[]) => void;
}

// ===================================================================================================
// COMPONENTE PRINCIPAL - SUPER POPUP DE RELATÓRIO
// ===================================================================================================

const SuperPopupRelatorio: React.FC<SuperPopupRelatorioProps> = ({
  isVisible,
  receita,
  onClose,
  onEdit,
  onDuplicate,
  onDelete,
  // ===================================================================================================
  // CALLBACK PARA NAVEGAR PARA ABA INSUMOS
  // ===================================================================================================
  onNavigateToInsumos
}) => {
  // ===================================================================================================
  // BLOQUEAR SCROLL DO BODY QUANDO POPUP ESTÁ ABERTO
  // ===================================================================================================
  useEffect(() => {
    if (isVisible) {
      // Salvar posição atual do scroll
      const scrollY = window.scrollY;
      
      // Bloquear scroll
      document.body.style.position = 'fixed';
      document.body.style.top = `-${scrollY}px`;
      document.body.style.width = '100%';
      document.body.style.overflow = 'hidden';
      
      return () => {
        // Restaurar scroll ao fechar popup
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.width = '';
        document.body.style.overflow = '';
        window.scrollTo(0, scrollY);
      };
    }
  }, [isVisible]);

const calcularCustoPorPorcao = () => {
    if (!receita || receita.porcoes <= 0) return 0;
    return receita.cmv_real / receita.porcoes;
  };

  const calcularCMVPorPorcao = (precoVenda) => {
    if (!receita || receita.porcoes <= 0) return 0;
    return precoVenda / receita.porcoes;
  };

  const calcularLucroPorPorcao = (precoVenda) => {
    if (!receita || receita.porcoes <= 0) return 0;
    const custoPorPorcao = calcularCustoPorPorcao();
    const precoPorPorcao = precoVenda / receita.porcoes;
    return precoPorPorcao - custoPorPorcao;
  };

  // ===================================================================================================
  // DEBUG LOGS PARA DIAGNÓSTICO - ADICIONAR ESTAS LINHAS NO INÍCIO
  // ===================================================================================================
  console.log('🔍 SuperPopupRelatorio - Debug Props:', {
    isVisible,
    receita: receita ? {
      id: receita.id,
      nome: receita.nome,
      cmv_real: receita.cmv_real,
      preco_venda_sugerido: receita.preco_venda_sugerido
    } : null,
    hasOnClose: typeof onClose === 'function',
    hasOnEdit: typeof onEdit === 'function'
  });
  
  // Estados para controle do popup
  const [activeTab, setActiveTab] = useState<'geral' | 'insumos' | 'custos' | 'analise'>('geral');
  const [loading, setLoading] = useState(false);

  // Estado para controlar modal de selecao de relatorio
  const [showModalRelatorio, setShowModalRelatorio] = useState(false);

  // Resetar aba quando o popup abre
  useEffect(() => {
    if (isVisible && receita) {
      setActiveTab('geral');
    }
  }, [isVisible, receita]);

  // ===================================================================================================
  // CONDIÇÃO DE RETORNO ANTECIPADO - VERIFICAR SE DEVE RENDERIZAR
  // ===================================================================================================
  
  // Se não estiver visível, não renderizar nada
  if (!isVisible) {
    console.log('⏸️ SuperPopupRelatorio - Popup não está visível, não renderizando');
    return null;
  }

  // Se não há receita, mostrar mensagem de erro no popup
  if (!receita) {
    console.log('❌ SuperPopupRelatorio - Nenhuma receita fornecida');
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="bg-white rounded-xl p-6 max-w-md mx-4 shadow-xl">
          <h3 className="text-lg font-semibold text-red-600 mb-2">Erro no Relatório</h3>
          <p className="text-gray-600 mb-4">Nenhuma receita foi selecionada para exibição.</p>
          <button
            onClick={onClose}
            className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600"
          >
            Fechar
          </button>
        </div>
      </div>
    );
  }

  console.log('🎯 SuperPopupRelatorio - Renderizando popup completo para:', receita.nome);

  // ===================================================================================================
  // FUNÇÕES AUXILIARES
  // ===================================================================================================

  const formatarPreco = (valor: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(valor || 0);
  };

  const formatarData = (dataString: string) => {
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(dataString));
  };

  const calcularMargemLucro = (precoVenda: number, custoProducao: number) => {
    if (precoVenda === 0) return 0;
    return ((precoVenda - custoProducao) / precoVenda) * 100;
  };

  const getStatusBadge = (status: string) => {
    const configs = {
      ativo: { bg: 'bg-green-100', text: 'text-green-800', icon: CheckCircle, label: 'Ativo' },
      inativo: { bg: 'bg-gray-100', text: 'text-gray-800', icon: AlertTriangle, label: 'Inativo' },
      processado: { bg: 'bg-blue-100', text: 'text-blue-800', icon: Package, label: 'Processado' }
    };
    
    const config = configs[status] || configs.ativo;
    const IconComponent = config.icon;
    
    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.text}`}>
        <IconComponent className="w-4 h-4" />
        {config.label}
      </span>
    );
  };

  // ===================================================================================================
  // HANDLERS PARA AÇÕES
  // ===================================================================================================

  const handleEdit = () => {
    if (receita && onEdit) {
      onEdit(receita);
      onClose();
    }
  };

  const handleDuplicate = () => {
    if (receita && onDuplicate) {
      onDuplicate(receita);
      onClose();
    }
  };

  const handleDelete = () => {
    if (receita && onDelete) {
      if (confirm(`Tem certeza que deseja excluir a receita "${receita.nome}"?\n\nEsta ação não pode ser desfeita.`)) {
        onDelete(receita);
        onClose();
      }
    }
  };

  const handleExport = async () => {
    if (!receita) return;
    
    try {
      const API_URL = 'http://192.168.10.113:8000';
      
      const response = await fetch(`${API_URL}/api/v1/receitas/${receita.id}/pdf`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      // Fazer download do PDF
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `receita_${receita.codigo}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      console.log('✅ PDF exportado com sucesso:', receita.nome);
      
    } catch (error) {
      console.error('❌ Erro ao exportar PDF:', error);
      alert(`Erro ao gerar PDF: ${error.message}`);
    }
  };

  const handlePrint = () => {
    // Implementar impressão do relatório
    window.print();
  };

  // ===================================================================================================
  // COMPONENTES DAS ABAS
  // ===================================================================================================

  const TabGeral = () => {
    if (!receita) return null;

    return (
      <div className="space-y-6">
        
        {/* ===================================================================================================
            ALERTA DE INSUMOS SEM PRECO
            =================================================================================================== */}
        {receita.tem_insumos_sem_preco && receita.insumos_pendentes && receita.insumos_pendentes.length > 0 && (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 rounded-lg p-5">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <AlertTriangle className="w-6 h-6 text-yellow-600" />
              </div>
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-yellow-900 mb-2">
                  ⚠️ Atenção: Esta receita possui insumos sem preço cadastrado
                </h4>
                <p className="text-sm text-yellow-800 mb-3">
                  Os seguintes insumos não possuem preço cadastrado, o que impede o cálculo correto do custo da receita:
                </p>
                <ul className="space-y-2 mb-4">
                  {receita.receita_insumos
                    ?.filter(ri => receita.insumos_pendentes?.includes(ri.insumo?.id))
                    .map((ri, index) => (
                      <li key={index} className="flex items-center gap-2 text-sm text-yellow-900">
                        <span className="w-2 h-2 bg-yellow-600 rounded-full"></span>
                        <span className="font-medium">{ri.insumo?.nome || 'Insumo desconhecido'}</span>
                        <span className="text-yellow-700">(ID: {ri.insumo?.id})</span>
                      </li>
                    ))}
                </ul>
                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      // ===================================================================================================
                      // NAVEGAR PARA ABA INSUMOS COM FILTRO NOS INSUMOS PENDENTES
                      // ===================================================================================================
                      if (onNavigateToInsumos && receita.insumos_pendentes) {
                        console.log('🔄 Navegando para insumos pendentes:', receita.insumos_pendentes);
                        onNavigateToInsumos(receita.insumos_pendentes);
                        onClose(); // Fechar o popup
                      }
                    }}
                    className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors text-sm font-medium"
                  >
                    Cadastrar Preços
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ===================================================================================================
            ALERTA - RECEITA SEM INSUMOS
            =================================================================================================== */}
        {receita.total_insumos === 0 && (
          <div className="bg-orange-50 border-l-4 border-orange-400 rounded-lg p-5">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <AlertTriangle className="w-6 h-6 text-orange-600" />
              </div>
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-orange-900 mb-2">
                  ⚠️ Atenção: Esta receita não possui insumos cadastrados
                </h4>
                <p className="text-sm text-orange-800 mb-3">
                  Para calcular corretamente o custo desta receita, você precisa adicionar os insumos necessários.
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      if (onEdit) {
                        onEdit(receita);
                      }
                    }}
                    className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors flex items-center gap-2"
                  >
                    <Edit3 className="w-4 h-4" />
                    Adicionar Insumos
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Informações Básicas */}
        <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-xl p-6 border border-green-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-green-600" />
            Informações Gerais
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <Hash className="w-4 h-4 text-gray-500" />
                <span className="text-xs text-gray-500 font-medium">CÓDIGO</span>
              </div>
              <p className="font-bold text-gray-900">{receita.codigo}</p>
            </div>
            
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <ChefHat className="w-4 h-4 text-gray-500" />
                <span className="text-xs text-gray-500 font-medium">CATEGORIA</span>
              </div>
              <p className="font-bold text-gray-900">{receita.categoria}</p>
            </div>
            
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-4 h-4 text-gray-500" />
                <span className="text-xs text-gray-500 font-medium">RENDIMENTO</span>
              </div>
              <p className="font-bold text-gray-900">{receita.porcoes} {receita.porcoes === 1 ? 'unidade' : 'unidades'}</p>
            </div>
            
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-gray-500" />
                <span className="text-xs text-gray-500 font-medium">TEMPO PREPARO</span>
              </div>
              <p className="font-bold text-gray-900">{receita.tempo_preparo} min</p>
            </div>
            
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <Package className="w-4 h-4 text-gray-500" />
                <span className="text-xs text-gray-500 font-medium">INSUMOS</span>
              </div>
              <p className="font-bold text-gray-900">{receita.total_insumos} itens</p>
            </div>
            
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <span className="text-xs text-gray-500 font-medium">STATUS</span>
              </div>
              {getStatusBadge(receita.status)}
            </div>

            <div className="bg-white rounded-lg p-4 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span className="text-xs text-gray-500 font-medium">RESPONSÁVEL</span>
              </div>
              <p className="font-bold text-gray-900">{receita.responsavel || 'Não informado'}</p>
            </div>
          </div>
        </div>

        {/* Descrição se existir */}
        {receita.descricao && (
          <div className="bg-white rounded-xl p-6 border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Descrição</h3>
            <p className="text-gray-600 leading-relaxed">{receita.descricao}</p>
          </div>
        )}

        {/* ===================================================================================================
            MÉTRICAS PRINCIPAIS - 3 CARDS GRANDES
            Card Vermelho: Custo de Produção (mantido)
            Card Verde: Preço Sugerido pelo Restaurante + CMV Real (alterado)
            Card Azul: Preço Sugerido com Margem 25% (alterado)
            =================================================================================================== */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* ===================================================================================================
              CARD VERMELHO: CUSTO DE PRODUÇÃO
              Mantém o custo de produção por porção e custo total da receita
              =================================================================================================== */}
          <div className="bg-red-50 rounded-xl p-6 border border-red-100">
            <div className="flex items-center gap-3 mb-3">
              <div className="bg-red-100 p-2 rounded-lg">
                <Calculator className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h4 className="font-semibold text-red-800">Custo de Produção</h4>
                <p className="text-xs text-red-600">CMV por porção</p>
              </div>
            </div>
            <p className="text-2xl font-bold text-red-700">{formatarPreco(receita.cmv_real)}</p>
            <p className="text-sm text-red-600 mt-1">
              Por receita: {formatarPreco(receita.cmv_real * receita.porcoes)}
            </p>
          </div>

          {/* ===================================================================================================
              CARD VERDE: PREÇO SUGERIDO PELO RESTAURANTE + CMV REAL
              Alterado de "Preço Sugerido (Margem 25%)"
              Mostra o preço que o restaurante decidiu cobrar e o CMV Real deste preço
              =================================================================================================== */}
          {!receita.processada && (
            <div className="bg-green-50 rounded-xl p-6 border border-green-100">
              <div className="flex items-center gap-3 mb-3">
                <div className="bg-green-100 p-2 rounded-lg">
                  <DollarSign className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h4 className="font-semibold text-green-800">Preço Sugerido pelo Restaurante</h4>
                  <p className="text-xs text-green-600">Valor definido manualmente</p>
                </div>
              </div>
              <p className="text-2xl font-bold text-green-700">
                {formatarPreco(receita.sugestao_valor || 0)}
              </p>
              <p className="text-sm text-green-600 mt-1">
                CMV Real: {receita.sugestao_valor && receita.sugestao_valor > 0
                  ? ((receita.cmv_real / receita.sugestao_valor) * 100).toFixed(1)
                  : '0.0'}%
              </p>
            </div>
          )}

          {/* ===================================================================================================
              CARD AZUL: PREÇO SUGERIDO COM MARGEM 25%
              Alterado de "Lucro por Unidade"
              Mostra o preço calculado automaticamente pelo sistema com margem de 25%
              =================================================================================================== */}
          {!receita.processada && (
            <div className="bg-blue-50 rounded-xl p-6 border border-blue-100">
              <div className="flex items-center gap-3 mb-3">
                <div className="bg-blue-100 p-2 rounded-lg">
                  <TrendingUp className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h4 className="font-semibold text-blue-800">Preço Sugerido</h4>
                  <p className="text-xs text-blue-600">Margem 25%</p>
                </div>
              </div>
              <p className="text-2xl font-bold text-blue-700">{formatarPreco(receita.preco_venda_sugerido)}</p>
              <p className="text-sm text-blue-600 mt-1">
                Calculado automaticamente
              </p>
            </div>
          )}
        </div>

        {/* Dados de Criação e Atualização */}
        <div className="bg-gray-50 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Histórico</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Criado em</p>
              <p className="font-medium text-gray-900">{formatarData(receita.created_at)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Última atualização</p>
              <p className="font-medium text-gray-900">{formatarData(receita.updated_at)}</p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const TabInsumos = () => {
    if (!receita) return null;

    // ===================================================================================================
    // SEPARAR INSUMOS NORMAIS DE RECEITAS PROCESSADAS
    // ===================================================================================================
    const insumosNormais = receita.receita_insumos?.filter(ri => 
      ri.insumo && !ri.receita_processada_id
    ) || [];
    
    const receitasProcessadas = receita.receita_insumos?.filter(ri => 
      ri.receita_processada_id
    ) || [];

    // ===================================================================================================
    // DEBUG TEMPORÁRIO: Verificar estrutura dos dados
    // ===================================================================================================
    console.log('🔍 DEBUG TabInsumos:');
    console.log('📦 Total receita_insumos:', receita.receita_insumos?.length);
    console.log('📦 Insumos normais:', insumosNormais.length);
    console.log('🍳 Receitas processadas:', receitasProcessadas.length);
    console.log('📋 Estrutura completa:', receita.receita_insumos);
    console.log('📋 Estrutura completa:', receita.receita_insumos);
    console.log('🔍 TODOS receita_insumos:', receita.receita_insumos);
    console.log('🔍 Receitas processadas filtradas:', receitasProcessadas);
    // ===================================================================================================

    // ===================================================================================================
    // CALCULAR CUSTO TOTAL DOS INSUMOS NORMAIS + RECEITAS PROCESSADAS
    // ===================================================================================================
    const calcularCustoTotalInsumos = () => {
      let custoTotal = 0;
      
      // Somar custo dos insumos normais
      insumosNormais.forEach(insumo => {
        const custoInsumo = insumo.custo_calculado || 
          (insumo.quantidade_necessaria * (insumo.insumo?.preco_compra_real || 0));
        custoTotal += custoInsumo;
      });
      
      // Somar custo das receitas processadas
      receitasProcessadas.forEach(item => {
        // IMPORTANTE: O preco_compra_real está no campo 'insumo', não em 'receita_processada'
        const precoPorUnidade = item.insumo?.preco_compra_real || 
                                item.receita_processada?.preco_compra_real || 
                                0;
        const custoReceitaProcessada = (item.quantidade_necessaria || 0) * precoPorUnidade;
        custoTotal += custoReceitaProcessada;
      });
      
      return custoTotal;
    };
    
    const custoTotalCalculado = calcularCustoTotalInsumos();
    
    console.log('💰 Custo total calculado:', custoTotalCalculado);
    console.log('💰 CMV da receita:', receita.cmv_real);
    // ===================================================================================================

    return (
      <div className="space-y-6">
        {/* Seção de Insumos Normais */}
        {insumosNormais.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-100">
            <div className="p-6 border-b border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Package className="w-5 h-5 text-green-600" />
                Insumos ({insumosNormais.length} itens)
              </h3>
            </div>
            
            <div className="p-6">
              <div className="space-y-4">
                {insumosNormais.map((insumo, index) => (
                  <div key={index} className="bg-gray-50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">
                        {insumo.insumo?.nome || 'Insumo sem nome'}
                      </h4>
                      <span className="text-sm font-medium text-green-600">
                        {(() => {
                          // Calcular custo total do insumo (quantidade × preço unitário)
                          const custoInsumo = insumo.custo_calculado || 
                            (insumo.quantidade_necessaria * (insumo.insumo?.preco_compra_real || 0));
                          return formatarPreco(custoInsumo);
                        })()}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>
                        {(insumo.quantidade_necessaria || 0).toFixed(2)} {insumo.unidade_medida || 'un'}
                      </span>
                      <span>
                        {formatarPreco(insumo.insumo?.preco_compra_real || 0)} / {insumo.insumo?.unidade || 'un'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Seção de Receitas Processadas */}
        {receitasProcessadas.length > 0 && (
          <div className="bg-white rounded-xl border border-purple-100">
            <div className="p-6 border-b border-purple-100">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <ChefHat className="w-5 h-5 text-purple-600" />
                Receitas Processadas ({receitasProcessadas.length} itens)
              </h3>
            </div>
            
            <div className="p-6">
              <div className="space-y-4">
                {receitasProcessadas.map((item, index) => {
                // ===================================================================================================
                // CALCULAR CUSTO DA RECEITA PROCESSADA
                // ===================================================================================================
                const custoReceitaProcessada = (() => {
                  // IMPORTANTE: O preco_compra_real está no campo 'insumo', não em 'receita_processada'
                  const precoPorUnidade = item.insumo?.preco_compra_real || 
                                        item.receita_processada?.preco_compra_real || 
                                        0;
                  
                  // Calcular custo baseado na quantidade necessária
                  const custoTotal = (item.quantidade_necessaria || 0) * precoPorUnidade;
                  console.log('🔍 Cálculo receita processada:');
                  console.log('  - quantidade_necessaria:', item.quantidade_necessaria);
                  console.log('  - precoPorUnidade:', precoPorUnidade);
                  console.log('  - custoTotal:', custoTotal);
                  
                  return custoTotal;
                })();

                return (
                  <div key={index} className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">
                        {item.receita_processada?.nome || 'Receita Processada'}
                      </h4>
                      <span className="text-sm font-medium text-purple-600">
                        {formatarPreco(custoReceitaProcessada)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>
                        {(item.quantidade_necessaria || 0).toFixed(2)} {item.unidade_medida || 'un'}
                      </span>
                      <span>
                        {formatarPreco(item.insumo?.preco_compra_real || item.receita_processada?.preco_compra_real || 0)} / {item.insumo?.unidade || item.receita_processada?.unidade || 'un'}
                      </span>
                    </div>
                    <div className="mt-2 pt-2 border-t border-purple-200">
                      <div className="flex items-center gap-2">
                        <span className="text-purple-600">
                          Receita processada
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
              </div>
            </div>
          </div>
        )}

        {/* Mensagem quando não há nenhum insumo */}
        {insumosNormais.length === 0 && receitasProcessadas.length === 0 && (
          <div className="bg-white rounded-xl border border-gray-100 p-8 text-center">
            <Package className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">Nenhum insumo cadastrado nesta receita</p>
            <p className="text-sm text-gray-400 mt-2">Adicione insumos para calcular o custo automaticamente</p>
          </div>
        )}

        {/* Total Geral */}
        {(insumosNormais.length > 0 || receitasProcessadas.length > 0) && (
          <div className="bg-gradient-to-r from-green-50 to-purple-50 rounded-xl border border-gray-200 p-6">
            {/* ===================================================================================================
                USAR CUSTO TOTAL CALCULADO DOS INSUMOS
                =================================================================================================== */}
            {receita.processada && receita.rendimento_porcoes && receita.rendimento_porcoes !== 1 ? (
              <>
                {/* Para receita processada com rendimento diferente de 1: mostrar custo por rendimento primeiro */}
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-gray-900">Custo por Rendimento</span>
                  <span className="font-bold text-green-600 text-lg">
                    {formatarPreco(custoTotalCalculado / (receita.rendimento_porcoes || 1))}
                  </span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-sm text-gray-600">Custo total ({receita.rendimento_porcoes} {receita.unidade || 'un'})</span>
                  <span className="text-sm font-medium text-gray-900">
                    {formatarPreco(custoTotalCalculado)}
                  </span>
                </div>
              </>
            ) : receita.processada ? (
              <>
                {/* ===================================================================================================
                    RECEITA PROCESSADA - MOSTRAR CUSTO UNITARIO E CUSTO TOTAL
                    Linha principal: Custo por unidade (R$1,40 = R$2,80 ÷ 2kg)
                    Linha secundária: Custo total para o rendimento completo (R$2,80 para 2kg)
                    =================================================================================================== */}
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-gray-900">Custo por Rendimento</span>
                  <span className="font-bold text-green-600 text-lg">
                    {formatarPreco(custoTotalCalculado / (receita.porcoes || 1))}
                  </span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-sm text-gray-600">Rendimento: {receita.porcoes || 1} {receita.unidade || 'kg'}</span>
                  <span className="text-sm font-medium text-gray-900">
                    {formatarPreco(custoTotalCalculado)}
                  </span>
                </div>
              </>
            ) : (
              <>
                {/* Para receitas normais: usar custo total calculado */}
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-gray-900">Total da Receita</span>
                  <span className="font-bold text-green-600 text-lg">
                    {formatarPreco(custoTotalCalculado)}
                  </span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-sm text-gray-600">
                    Custo por rendimento
                    {receita.rendimento_porcoes && receita.rendimento_porcoes > 1 && 
                      ` (Rendimento: ${receita.rendimento_porcoes} ${receita.unidade || 'kg'})`
                    }
                  </span>
                  <span className="text-sm font-medium text-gray-900">
                    {/* ===================================================================================================
                        CUSTO POR UNIDADE DE RENDIMENTO - RECEITAS NORMAIS
                        Divide o custo total calculado pelo rendimento_porcoes (ou porcoes como fallback)
                        Exemplo: Custo total R$2,80 com rendimento 2kg = R$1,40 por kg
                        =================================================================================================== */}
                    {formatarPreco(custoTotalCalculado / (receita.rendimento_porcoes || receita.porcoes || 1))}
                  </span>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    );
  };

  const TabCustos = () => {
    if (!receita) return null;

    const cmv20 = receita.cmv_20_porcento || (receita.cmv_real * 5);
    const cmv25 = receita.cmv_25_porcento || (receita.cmv_real * 4);
    const cmv30 = receita.cmv_30_porcento || (receita.cmv_real * 3.33);

    // ===================================================================================================
    // VERIFICAR SE É RECEITA PROCESSADA COM RENDIMENTO DIFERENTE DE 1
    // ===================================================================================================
    const isReceitaProcessadaComRendimento = (
      receita.processada && 
      receita.rendimento_porcoes && 
      receita.rendimento_porcoes !== 1
    );

    return (
      <div className="space-y-6">
        
        {/* ===================================================================================================
            MOSTRAR APENAS CUSTO POR RENDIMENTO PARA RECEITAS PROCESSADAS
            =================================================================================================== */}
        {isReceitaProcessadaComRendimento ? (
          <div className="bg-white rounded-xl border border-gray-100 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
              <Calculator className="w-5 h-5 text-purple-600" />
              Custo de Produção - Receita Processada
            </h3>
            
            <div className="bg-purple-50 rounded-xl p-6 border-2 border-purple-200">
              <div className="text-center">
                <p className="text-sm text-purple-600 mb-2">Custo por Rendimento</p>
                <p className="text-4xl font-bold text-purple-600 mb-4">
                  {formatarPreco(receita.cmv_real)}
                </p>
                <p className="text-sm text-gray-600">
                  Rendimento: {receita.rendimento_porcoes} {receita.unidade || 'un'}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  Custo total: {formatarPreco(receita.cmv_real * receita.rendimento_porcoes)}
                </p>
              </div>
            </div>

            <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                <strong>Nota:</strong> Esta é uma receita processada utilizada como insumo em outras receitas. 
                O custo exibido é o custo de produção por unidade de rendimento.
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Análise da Sugestão Manual de Preço */}
            {receita.sugestao_valor && receita.sugestao_valor > 0 && (
              <div className="bg-purple-50 rounded-xl p-6 border border-purple-200">
                <h4 className="font-semibold text-purple-900 mb-4 flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  Análise da Sugestão Manual do Restaurante
                </h4>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-purple-700">Preço Sugerido pelo Restaurante:</span>
                    <span className="font-bold text-purple-900">{formatarPreco(receita.sugestao_valor)}</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-purple-700">Custo por Porção:</span>
                    <span className="font-medium text-purple-900">{formatarPreco(receita.cmv_real)}</span>
                  </div>
                  
                  <div className="flex items-center justify-between pt-2 border-t border-purple-200">
                    <span className="text-sm font-semibold text-purple-700">CMV deste Preço:</span>
                    <span className="text-lg font-bold text-purple-900">
                      {((receita.cmv_real / receita.sugestao_valor) * 100).toFixed(1)}%
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-purple-700">Lucro por rendimento:</span>
                    <span className="text-lg font-bold text-purple-900">
                      {formatarPreco(receita.sugestao_valor - receita.cmv_real)}
                    </span>
                  </div>
                  
                  {/* Feedback visual sobre a margem */}
                  {(() => {
                    const cmvPercent = (receita.cmv_real / receita.sugestao_valor) * 100;
                    if (cmvPercent > 35) {
                      return (
                        <div className="bg-red-100 border border-red-300 rounded-lg p-3 mt-2">
                          <p className="text-sm text-red-800">
                            <AlertTriangle className="w-4 h-4 inline mr-1" />
                            CMV muito alto! Recomenda-se aumentar o preço ou reduzir custos.
                          </p>
                        </div>
                      );
                    } else if (cmvPercent < 20) {
                      return (
                        <div className="bg-green-100 border border-green-300 rounded-lg p-3 mt-2">
                          <p className="text-sm text-green-800">
                            <CheckCircle className="w-4 h-4 inline mr-1" />
                            Excelente margem! Preço competitivo com boa rentabilidade.
                          </p>
                        </div>
                      );
                    } else {
                      return (
                        <div className="bg-blue-100 border border-blue-300 rounded-lg p-3 mt-2">
                          <p className="text-sm text-blue-800">
                            <CheckCircle className="w-4 h-4 inline mr-1" />
                            Margem adequada para operação sustentável.
                          </p>
                        </div>
                      );
                    }
                  })()}
                </div>
              </div>
            )}

            {/* Análise de Preços Sugeridos - APENAS PARA RECEITAS NÃO PROCESSADAS */}
            <div className="bg-white rounded-xl border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-green-600" />
            Análise de Preços Sugeridos
          </h3>

          <div className={`grid gap-6 ${receita.processada ? 'grid-cols-1 max-w-md mx-auto' : 'grid-cols-1 md:grid-cols-3'}`}>
            
            {/* CMV 20% */}
            <div className="bg-green-50 rounded-xl p-6 border-2 border-green-200">
              <div className="text-center mb-4">
                <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Percent className="w-8 h-8 text-green-600" />
                </div>
                <h4 className="font-bold text-green-800 text-lg">Margem 20%</h4>
                <p className="text-sm text-green-600">Conservadora</p>
              </div>
              
              <div className="space-y-3">
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-gray-500">Preço de Venda</p>
                  <p className="font-bold text-xl text-green-700">{formatarPreco(cmv20)}</p>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-gray-500">Lucro por Porção</p>
                  <p className="font-semibold text-green-600">{formatarPreco(cmv20 - receita.cmv_real)}</p>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-gray-500">Receita Total</p>
                  <p className="font-semibold text-green-600">{formatarPreco(cmv20 * receita.porcoes)}</p>
                </div>
              </div>
            </div>

            {/* CMV 25% */}
            <div className="bg-blue-50 rounded-xl p-6 border-2 border-blue-200">
              <div className="text-center mb-4">
                <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Target className="w-8 h-8 text-blue-600" />
                </div>
                <h4 className="font-bold text-blue-800 text-lg">Margem 25%</h4>
                <p className="text-sm text-blue-600">Recomendada</p>
              </div>
              
              <div className="space-y-3">
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-gray-500">Preço de Venda</p>
                  <p className="font-bold text-xl text-blue-700">{formatarPreco(cmv25)}</p>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-gray-500">Lucro por Porção</p>
                  <p className="font-semibold text-blue-600">{formatarPreco(cmv25 - receita.cmv_real)}</p>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-gray-500">Receita Total</p>
                  <p className="font-semibold text-blue-600">{formatarPreco(cmv25 * receita.porcoes)}</p>
                </div>
              </div>
            </div>

            {/* CMV 30% */}
            <div className="bg-purple-50 rounded-xl p-6 border-2 border-purple-200">
              <div className="text-center mb-4">
                <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3">
                  <TrendingUp className="w-8 h-8 text-purple-600" />
                </div>
                <h4 className="font-bold text-purple-800 text-lg">Margem 30%</h4>
                <p className="text-sm text-purple-600">Agressiva</p>
              </div>
              
              <div className="space-y-3">
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-gray-500">Preço de Venda</p>
                  <p className="font-bold text-xl text-purple-700">{formatarPreco(cmv30)}</p>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-gray-500">Lucro por Porção</p>
                  <p className="font-semibold text-purple-600">{formatarPreco(cmv30 - receita.cmv_real)}</p>
                </div>
                <div className="bg-white rounded-lg p-3">
                  <p className="text-xs text-gray-500">Receita Total</p>
                  <p className="font-semibold text-purple-600">{formatarPreco(cmv30 * receita.porcoes)}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ===================================================================================================
            VALORES POR RENDIMENTO - APENAS NA ABA ANÁLISE DE CUSTOS
            Movido do footer para dentro da aba de custos, posicionado antes da Análise Comparativa
            =================================================================================================== */}
        {!receita.processada && receita.porcoes > 1 && (
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <h4 className="font-semibold text-blue-900 mb-3">Valores por Rendimento</h4>
            <div className="grid grid-cols-2 gap-4">
              
              <div>
                <p className="text-sm text-blue-600 mb-1">Custo do Rendimento por unidade</p>
                <p className="text-lg font-bold text-blue-900">
                  {formatarPreco(receita.cmv_real)}
                </p>
              </div>

              <div>
                <p className="text-sm text-blue-600 mb-1">CMV 25% por Rendimento</p>
                <p className="text-lg font-bold text-blue-900">
                  {formatarPreco(receita.preco_venda_sugerido)}
                </p>
                <p className="text-xs text-blue-600">
                  Lucro: {formatarPreco(receita.preco_venda_sugerido - receita.cmv_real)}
                </p>
              </div>

            </div>
            
            <div className="mt-3 text-center">
              <p className="text-sm text-blue-600">
                Base: {receita.porcoes} {receita.porcoes === 1 ? 'porção' : 'porções'}
              </p>
            </div>
          </div>
        )}

        {/* Comparativo de Custos */}
        <div className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-xl p-6">
          <h4 className="font-semibold text-gray-900 mb-4">Análise Comparativa</h4>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">{formatarPreco(receita.cmv_real)}</p>
              <p className="text-sm text-gray-600">Custo por Rendimento</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{formatarPreco(cmv25)}</p>
              <p className="text-sm text-gray-600">Preço Sugerido</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{formatarPreco(cmv25 - receita.cmv_real)}</p>
              <p className="text-sm text-gray-600">Lucro por Rendimento</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">{receita.margem_percentual.toFixed(1)}%</p>
              <p className="text-sm text-gray-600">Margem Atual</p>
            </div>
          </div>
        </div>
        
          </>
        )}
      </div>
    );
  };

  const TabAnalise = () => {
    if (!receita) return null;

    // ===================================================================================================
    // DEBUG: Verificar se insumos_processados está sendo recebido
    // ===================================================================================================
    console.log('🔍 Debug Complexidade:', {
      total_insumos: receita.total_insumos,
      insumos_processados: receita.insumos_processados,
      receita_completa: receita
    });

    // ===================================================================================================
    // VERIFICAR SE É RECEITA PROCESSADA COM RENDIMENTO DIFERENTE DE 1
    // ===================================================================================================
    const isReceitaProcessadaComRendimento = (
      receita.processada && 
      receita.rendimento_porcoes && 
      receita.rendimento_porcoes !== 1
    );

    // Se for receita processada, mostrar apenas informações básicas
    if (isReceitaProcessadaComRendimento) {
      return (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-100 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Calculator className="w-5 h-5 text-purple-600" />
              Análise - Receita Processada
            </h3>
            
            <div className="bg-purple-50 rounded-lg p-6 border border-purple-200">
              <p className="text-sm text-gray-700 mb-4">
                Esta é uma receita processada utilizada como insumo em outras receitas. 
                As análises de margem e precificação não se aplicam, pois o foco é o custo de produção.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">Custo por Rendimento</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {formatarPreco(receita.cmv_real)}
                  </p>
                </div>
                
                <div className="bg-white rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">Rendimento Total</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {receita.rendimento_porcoes} {receita.unidade || 'un'}
                  </p>
                </div>
                
                <div className="bg-white rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">Custo Total de Produção</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {formatarPreco(receita.cmv_real * receita.rendimento_porcoes)}
                  </p>
                </div>
                
                <div className="bg-white rounded-lg p-4">
                  <p className="text-sm text-gray-600 mb-1">Total de Insumos</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {receita.total_insumos || 0}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        
        {/* Indicadores de Performance */}
        <div className="bg-white rounded-xl border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
            <PieChart className="w-5 h-5 text-green-600" />
            Análise de Performance
          </h3>

          {/* 
            ===================================================================================================
            GRID DE INDICADORES - AJUSTADO PARA 3 COLUNAS
            Removido "Potencial de Lucro" conforme solicitado
            =================================================================================================== 
          */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            
            {/* 
              ===================================================================================================
              EFICIÊNCIA DE CUSTO
              Calcula o CMV Real baseado no preço sugerido pelo restaurante
              Faixas: ótimo (≤20%), bom (≤25%), razoável (≤30%), atenção (≤35%), ruim (>40%)
              =================================================================================================== 
            */}
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Scale className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-green-800">Eficiência de Custo</span>
              </div>
              <p className="text-2xl font-bold text-green-700">
                {(() => {
                  if (!receita.sugestao_valor || receita.sugestao_valor === 0) return 'N/A';
                  const cmvReal = (receita.cmv_real / receita.sugestao_valor) * 100;
                  if (cmvReal <= 20) return 'Ótimo';
                  if (cmvReal <= 25) return 'Bom';
                  if (cmvReal <= 30) return 'Razoável';
                  if (cmvReal <= 35) return 'Atenção';
                  return 'Ruim';
                })()}
              </p>
              <p className="text-xs text-green-600 mt-1">
                CMV Real: {receita.sugestao_valor && receita.sugestao_valor > 0
                  ? ((receita.cmv_real / receita.sugestao_valor) * 100).toFixed(1)
                  : '0.0'}%
              </p>
            </div>

            {/* 
              ===================================================================================================
              COMPLEXIDADE
              Baseada na quantidade de receitas processadas:
              - 0 processados = Baixa
              - 1 processado = Moderada
              - 2 processados = Média
              - >2 processados = Alta
              =================================================================================================== 
            */}
            <div className="bg-yellow-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Package className="w-4 h-4 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-800">Complexidade</span>
              </div>
              <p className="text-2xl font-bold text-yellow-700">
                {(() => {
                  // Tentar pegar o valor de insumos_processados
                  const processados = receita.insumos_processados ?? 0;
                  
                  if (processados === 0) return 'Baixa';
                  if (processados === 1) return 'Moderada';
                  if (processados === 2) return 'Média';
                  return 'Alta';
                })()}
              </p>
              <p className="text-xs text-yellow-600 mt-1">
                {(() => {
                  const processados = receita.insumos_processados ?? 0;
                  return `${processados} ${processados === 1 ? 'processado' : 'processados'}`;
                })()}
              </p>
            </div>

            {/* Tempo de Preparo */}
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium text-purple-800">Agilidade</span>
              </div>
              <p className="text-2xl font-bold text-purple-700">
                {receita.tempo_preparo < 20 ? 'Rápida' : receita.tempo_preparo < 40 ? 'Média' : 'Lenta'}
              </p>
              <p className="text-xs text-purple-600 mt-1">
                {receita.tempo_preparo} minutos
              </p>
            </div>
          </div>
        </div>

        {/* Recomendações */}
        <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-xl p-6 border border-orange-100">
          <h4 className="font-semibold text-orange-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            Recomendações de Otimização
          </h4>
          
          <div className="space-y-4">
            
            {/* Recomendação baseada na margem */}
            {receita.margem_percentual < 20 && (
              <div className="bg-white rounded-lg p-4 border-l-4 border-red-500">
                <h5 className="font-medium text-red-800 mb-2">⚠️ Margem Baixa Detectada</h5>
                <p className="text-sm text-red-700">
                  A margem atual de {receita.margem_percentual.toFixed(1)}% está abaixo do recomendado (25%). 
                  Considere aumentar o preço ou otimizar os custos dos insumos.
                </p>
              </div>
            )}

            {/* Recomendação baseada no custo */}
            {receita.cmv_real > 15 && (
              <div className="bg-white rounded-lg p-4 border-l-4 border-yellow-500">
                <h5 className="font-medium text-yellow-800 mb-2">💡 Custo Alto por Rendimento</h5>
                <p className="text-sm text-yellow-700">
                  O custo de {formatarPreco(receita.cmv_real)} por rendimento está elevado. 
                  Analise fornecedores alternativos ou ajuste as quantidades dos insumos mais caros.
                </p>
              </div>
            )}

            {/* Recomendação baseada na complexidade */}
            {receita.total_insumos > 12 && (
              <div className="bg-white rounded-lg p-4 border-l-4 border-blue-500">
                <h5 className="font-medium text-blue-800 mb-2">🔧 Simplificação Possível</h5>
                <p className="text-sm text-blue-700">
                  Esta receita usa {receita.total_insumos} insumos. Considere consolidar ingredientes similares 
                  ou eliminar itens que agregam pouco valor ao produto final.
                </p>
              </div>
            )}

            {/* Recomendação baseada no tempo */}
            {receita.tempo_preparo > 60 && (
              <div className="bg-white rounded-lg p-4 border-l-4 border-purple-500">
                <h5 className="font-medium text-purple-800 mb-2">⏰ Otimização de Tempo</h5>
                <p className="text-sm text-purple-700">
                  O tempo de preparo de {receita.tempo_preparo} minutos pode impactar a eficiência operacional. 
                  Considere técnicas de pré-preparo ou otimização do processo.
                </p>
              </div>
            )}

            {/* Recomendação positiva */}
            {receita.margem_percentual >= 25 && receita.cmv_real <= 10 && (
              <div className="bg-white rounded-lg p-4 border-l-4 border-green-500">
                <h5 className="font-medium text-green-800 mb-2">✅ Receita Otimizada</h5>
                <p className="text-sm text-green-700">
                  Esta receita apresenta excelente equilíbrio entre custo e margem. 
                  Mantenha o padrão de qualidade e considere replicar esta estrutura em outras receitas.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Comparação com Benchmarks */}
        <div className="bg-white rounded-xl border border-gray-100 p-6">
          <h4 className="font-semibold text-gray-900 mb-4">Comparação com Padrões da Categoria</h4>
          
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              
              {/* Custo Médio da Categoria */}
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Custo Médio - {receita.categoria}</p>
                <p className="text-xl font-bold text-gray-900">R$ 8,50</p>
                <p className="text-xs text-gray-500">
                  Sua receita: {receita.cmv_real > 8.5 ? '↑' : '↓'} 
                  {Math.abs(((receita.cmv_real - 8.5) / 8.5) * 100).toFixed(0)}%
                </p>
              </div>

              {/* Margem Média da Categoria */}
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Margem Média - {receita.categoria}</p>
                <p className="text-xl font-bold text-gray-900">22%</p>
                <p className="text-xs text-gray-500">
                  Sua receita: {receita.margem_percentual > 22 ? '↑' : '↓'} 
                  {Math.abs(receita.margem_percentual - 22).toFixed(0)}%
                </p>
              </div>

              {/* Tempo Médio da Categoria */}
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Tempo Médio - {receita.categoria}</p>
                <p className="text-xl font-bold text-gray-900">25 min</p>
                <p className="text-xs text-gray-500">
                  Sua receita: {receita.tempo_preparo > 25 ? '↑' : '↓'} 
                  {Math.abs(receita.tempo_preparo - 25)} min
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // ===================================================================================================
  // RENDER DO COMPONENTE
  // ===================================================================================================

  if (!isVisible || !receita) return null;

  return (
  <div className="fixed inset-0 z-50">
    {/* Overlay escuro com backdrop blur */}
    <div 
      className="absolute inset-0 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    />
    
    {/* Modal do relatório */}
    <div className="absolute inset-0 flex items-center justify-center p-0 sm:p-4">
      <div 
        className="relative bg-white w-full h-full sm:h-auto sm:rounded-2xl sm:shadow-2xl sm:max-w-6xl sm:max-h-[90vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
        >
        
        {/* ===================================================================================================
            HEADER DO POPUP
            =================================================================================================== */}
        
        <div className="bg-gradient-to-r from-green-500 to-pink-500 p-6 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-white bg-opacity-20 p-3 rounded-lg">
                <FileText className="w-8 h-8" />
              </div>
              {/* Título e subtítulo da receita com indicador de processada */}
              <div>
                <h2 className="text-2xl font-bold">{receita.nome}</h2>
                <p className="text-white text-opacity-90">
                  {receita.codigo} • {receita.categoria}
                  {(() => {
                    console.log('🔍 DEBUG - Receita completa:', receita);
                    console.log('🔍 DEBUG - receita.processada:', receita.processada);
                    console.log('🔍 DEBUG - typeof:', typeof receita.processada);
                    return null;
                  })()}
                  {receita.processada && <> • Processada</>}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              
              {/* Ações do Header */}
              <button
                onClick={() => setShowModalRelatorio(true)}
                className="bg-white bg-opacity-20 hover:bg-opacity-30 p-2 rounded-lg transition-all"
                title="Exportar Relatório"
              >
                <Download className="w-5 h-5" />
              </button>
              
              <button
                onClick={handlePrint}
                className="bg-white bg-opacity-20 hover:bg-opacity-30 p-2 rounded-lg transition-all"
                title="Imprimir"
              >
                <FileText className="w-5 h-5" />
              </button>
              
              <button
                onClick={() => navigator.share && navigator.share({ title: receita.nome, text: `Relatório da receita ${receita.nome}` })}
                className="bg-white bg-opacity-20 hover:bg-opacity-30 p-2 rounded-lg transition-all"
                title="Compartilhar"
              >
                <Share2 className="w-5 h-5" />
              </button>
              
              <button
                onClick={onClose}
                className="bg-white bg-opacity-20 hover:bg-opacity-30 p-2 rounded-lg transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Métricas Rápidas no Header */}
          {/* ===================================================================================================
              PARA RECEITAS PROCESSADAS: MOSTRAR APENAS CUSTO POR RENDIMENTO
              =================================================================================================== */}
          {receita.processada ? (
            <div className="grid grid-cols-1 gap-4 mt-6">
              <div className="bg-white bg-opacity-20 rounded-lg p-4 text-center">
                {/* ===================================================================================================
                    LABEL DO CUSTO - Alterado para "Custo de 1" para maior clareza no card do topo
                    Representa o custo unitário da receita processada por unidade de rendimento
                    =================================================================================================== */}
                <p className="text-sm text-white text-opacity-80 mb-1">Custo de 1</p>
                <p className="text-3xl font-bold">{formatarPreco(receita.cmv_real)}</p>
                {receita.rendimento_porcoes && receita.rendimento_porcoes > 1 && (
                  <p className="text-sm text-white text-opacity-70 mt-2">
                    Rendimento: {receita.rendimento_porcoes} {receita.unidade || 'un'}
                  </p>
                )}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              {/* ===================================================================================================
                  CARD 1: CUSTO POR RENDIMENTO
                  Mantém o custo de produção por porção/rendimento
                  =================================================================================================== */}
              <div className="bg-white bg-opacity-20 rounded-lg p-3 text-center">
                <p className="text-sm text-white text-opacity-80">Custo por Rendimento</p>
                <p className="text-lg font-bold">{formatarPreco(receita.cmv_real)}</p>
              </div>
              
              {/* ===================================================================================================
                  CARD 2: PREÇO SUGERIDO PELO RESTAURANTE (alterado de "Preço Sugerido")
                  Exibe o valor que o restaurante pretende cobrar pela receita
                  =================================================================================================== */}
              <div className="bg-white bg-opacity-20 rounded-lg p-3 text-center">
                <p className="text-sm text-white text-opacity-80">Preço Sugerido pelo Restaurante</p>
                <p className="text-lg font-bold">{formatarPreco(receita.sugestao_valor || 0)}</p>
              </div>
              
              {/* ===================================================================================================
                  CARD 3: CMV REAL (alterado de "Margem")
                  Calcula o CMV percentual baseado no preço sugerido pelo restaurante
                  Fórmula: (Custo / Preço Sugerido) × 100
                  =================================================================================================== */}
              <div className="bg-white bg-opacity-20 rounded-lg p-3 text-center">
                <p className="text-sm text-white text-opacity-80">CMV Real</p>
                <p className="text-lg font-bold">
                  {receita.sugestao_valor && receita.sugestao_valor > 0
                    ? ((receita.cmv_real / receita.sugestao_valor) * 100).toFixed(1)
                    : '0.0'}%
                </p>
              </div>
              
              {/* ===================================================================================================
                  CARD 4: PREÇO SUGERIDO (alterado de "Lucro/Rendimento")
                  Exibe o preço sugerido calculado automaticamente com margem de 25%
                  Este é o valor recomendado pelo sistema baseado no custo e na margem padrão
                  =================================================================================================== */}
              <div className="bg-white bg-opacity-20 rounded-lg p-3 text-center">
                <p className="text-sm text-white text-opacity-80">Preço Sugerido</p>
                <p className="text-lg font-bold">{formatarPreco(receita.preco_venda_sugerido)}</p>
              </div>
            </div>
          )}
        </div>

        {/* ===================================================================================================
            NAVEGAÇÃO POR ABAS
            =================================================================================================== */}
        
        <div className="border-b border-gray-200 relative">
          {/* Container com scroll horizontal suave */}
          <nav className="flex overflow-x-auto scrollbar-hide scroll-smooth snap-x snap-mandatory">
            {[
              { key: 'geral', label: 'Visão Geral', icon: FileText },
              { key: 'insumos', label: 'Insumos', icon: Package },
              // Ocultar aba "Análise de Custos" para receitas processadas
              ...(!receita?.processada ? [{ key: 'custos', label: 'Análise de Custos', icon: Calculator }] : []),
              { key: 'analise', label: 'Performance', icon: BarChart3 }
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key as any)}
                className={`flex items-center gap-2 px-6 py-4 text-sm font-medium transition-all border-b-2 whitespace-nowrap flex-shrink-0 snap-start ${
                  activeTab === key
                    ? 'border-green-500 text-green-600 bg-green-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </nav>
          
          {/* Indicadores visuais de fade nas laterais (apenas desktop) */}
          <div className="hidden sm:block absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-white to-transparent pointer-events-none"></div>
          <div className="hidden sm:block absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-white to-transparent pointer-events-none"></div>
        </div>

        {/* Estilo para esconder scrollbar mas manter funcionalidade */}
        <style>{`
          .scrollbar-hide::-webkit-scrollbar {
            display: none;
          }
          .scrollbar-hide {
            -ms-overflow-style: none;
            scrollbar-width: none;
          }
        `}</style>

        {/* ===================================================================================================
            CONTEÚDO DAS ABAS
            =================================================================================================== */}
        
        <div className="flex-1 overflow-y-auto p-6" style={{ maxHeight: 'calc(90vh - 360px)' }}>
          {activeTab === 'geral' && <TabGeral />}
          {activeTab === 'insumos' && <TabInsumos />}
          {activeTab === 'custos' && <TabCustos />}
          {activeTab === 'analise' && <TabAnalise />}
        </div>
                
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 px-4 sm:px-6 py-3 sm:py-4 border-t border-gray-200">
  
          {/* LAYOUT MOBILE: Stack vertical / DESKTOP: Horizontal */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            
            {/* Info do Footer - Esconder em mobile, mostrar em desktop */}
            <div className="hidden sm:block text-xs text-gray-500">
              {new Date().toLocaleDateString('pt-BR')} • {new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
            </div>
            
            {/* Botões de Ação - Grid responsivo */}
            <div className="grid grid-cols-2 sm:flex sm:flex-row gap-2 sm:gap-3 w-full sm:w-auto">
              
              {/* Botão Editar - Tamanho completo em mobile */}
              <button
                onClick={handleEdit}
                className="flex items-center justify-center gap-2 px-4 py-3 sm:py-2 text-gray-700 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all font-medium shadow-sm"
              >
                <Edit3 className="w-5 h-5 sm:w-4 sm:h-4" />
                <span className="text-sm">Editar</span>
              </button>
              
              {/* Botão Duplicar */}
              <button
                onClick={handleDuplicate}
                className="flex items-center justify-center gap-2 px-4 py-3 sm:py-2 text-blue-700 bg-white border-2 border-blue-300 rounded-lg hover:bg-blue-50 hover:border-blue-400 transition-all font-medium shadow-sm"
              >
                <Copy className="w-5 h-5 sm:w-4 sm:h-4" />
                <span className="text-sm">Duplicar</span>
              </button>
              
              {/* Botão Excluir */}
              <button
                onClick={handleDelete}
                className="flex items-center justify-center gap-2 px-4 py-3 sm:py-2 text-red-700 bg-white border-2 border-red-300 rounded-lg hover:bg-red-50 hover:border-red-400 transition-all font-medium shadow-sm"
              >
                <AlertTriangle className="w-5 h-5 sm:w-4 sm:h-4" />
                <span className="text-sm">Excluir</span>
              </button>
              
              {/* Botão Fechar - Destaque com gradiente, ocupa 2 colunas em mobile */}
              <button
                onClick={onClose}
                className="col-span-2 sm:col-span-1 flex items-center justify-center gap-2 px-6 py-3 sm:py-2 bg-gradient-to-r from-green-500 to-pink-500 text-white rounded-lg hover:from-green-600 hover:to-pink-600 transition-all font-medium shadow-md"
              >
                <X className="w-5 h-5 sm:w-4 sm:h-4" />
                <span className="text-sm font-semibold">Fechar</span>
              </button>
              
            </div>
          </div>
          
        </div>
      </div>
    </div>
    {/* Modal de Selecao de Relatorio */}
      <ModalSelecaoRelatorio
        isVisible={showModalRelatorio}
        receitaId={receita.id}
        receitaNome={receita.nome}
        onClose={() => setShowModalRelatorio(false)}
      />
  </div>
);
};
export default SuperPopupRelatorio;