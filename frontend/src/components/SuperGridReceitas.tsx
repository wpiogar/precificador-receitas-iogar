/*
 * ============================================================================
 * FOOD COST SYSTEM - Super Grid de Receitas
 * ============================================================================
 * Descrição: Um grid avançado que exibirá as receitas de forma organizada e funcional. 
 * O grid deve incluir:
 *  - Listagem paginada de receitas
 *  - Filtros por categoria, nome e status
 *  - Ações rápidas (editar, duplicar, excluir)
 *  - Visualização de métricas (CMV, margem, preço)
 *  - Interface responsiva e moderna
 * 
 * Data: 22/09/2025
 * Autor: Will - Empresa: IOGAR
 * ============================================================================
 */

import React, { useState, useMemo, useRef } from 'react';
import ReactDOM from 'react-dom';
import { 
  Search, X, Filter, MoreVertical, Edit3, Copy, Trash2, Eye, 
  ChefHat, TrendingUp, DollarSign, Clock, Users, 
  ChevronLeft, ChevronRight,  Grid  , List, SortAsc, SortDesc,
  Plus, ChevronDown, FileText, FileSpreadsheet, Download, Upload, Utensils, Package, CheckCircle
} from 'lucide-react';
import SkeletonLoader from './SkeletonLoader';
import EmptyState from './EmptyState';
import Tooltip from './Tooltip';
import { API_BASE_URL } from '../config';

// ===================================================================================================
// INTERFACES E TIPOS
// ===================================================================================================

interface Receita {
  id: number;
  codigo: string;
  nome: string;
  responsavel?: string;
  categoria: string;
  porcoes: number;
  tempo_preparo: number;
  cmv_real: number;
  preco_venda_sugerido: number;
  margem_percentual: number;
  status: 'ativo' | 'inativo' | 'processado';
  created_at: string;
  updated_at: string;
  restaurante_id: number;
  total_insumos: number;
  processada?: boolean;
  tem_insumos_sem_preco?: boolean;
  insumos_pendentes?: number[];
}

interface FiltroGrid {
  busca: string;
  categoria: string;
  status: string;
  ordenacao: 'nome' | 'categoria' | 'cmv' | 'margem' | 'created_at';
  direcao: 'asc' | 'desc';
  //===================================================================================================
  // FILTRO DE RECEITAS COM INSUMOS PENDENTES
  // ===================================================================================================
  mostrarApenasPendentes: boolean;
}

interface SuperGridReceitasProps {
  receitas: Receita[];
  loading: boolean;
  onEditReceita?: (receita: Receita) => void;
  onDuplicateReceita?: (receita: Receita) => void;
  onDeleteReceita?: (receita: Receita) => void;
  onViewReceita?: (receita: Receita) => void;
  onCreateReceita?: () => void;
  onImportar?: () => void;
}

// ===================================================================================================
// COMPONENTE AUXILIAR - DROPDOWN COM PORTAL
// ===================================================================================================
// Renderiza o dropdown fora da hierarquia do DOM para evitar problemas com overflow
const DropdownPortal: React.FC<{
  isOpen: boolean;
  position: { top?: number; bottom?: number; left: number; right?: number } | null;
  onClose: () => void;
  children: React.ReactNode;
}> = ({ isOpen, position, onClose, children }) => {
  if (!isOpen || !position) return null;

  return ReactDOM.createPortal(
    <>
      {/* Overlay invisível para fechar ao clicar fora */}
      <div 
        className="fixed inset-0 z-[9998]" 
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          onClose();
        }}
      />
      {/* Dropdown */}
      <div 
        className="fixed bg-white rounded-lg shadow-xl border border-gray-200 py-1 min-w-[150px] z-[9999]"
        style={{
          left: `${position.left}px`,
          top: position.top ? `${position.top}px` : undefined,
          bottom: position.bottom ? `${position.bottom}px` : undefined,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </>,
    document.body
  );
};

// ===================================================================================================
// COMPONENTE PRINCIPAL - SUPER GRID DE RECEITAS
// ===================================================================================================

const SuperGridReceitas: React.FC<SuperGridReceitasProps> = ({
  receitas,
  loading = false,
  onEditReceita,
  onDuplicateReceita,
  onDeleteReceita,
  onViewReceita,
  onCreateReceita,
  onImportar
}) => {

  // ===================================================================================================
  // DEBUG: Verificar estrutura das receitas recebidas
  // ===================================================================================================
  console.log('🔍 RECEITAS RECEBIDAS NO GRID:', receitas);
  console.log('🔍 PRIMEIRA RECEITA:', receitas[0]);
  console.log('🔍 Campos da primeira receita:', {
    total_insumos: receitas[0]?.total_insumos,
    tem_insumos_sem_preco: receitas[0]?.tem_insumos_sem_preco,
    status: receitas[0]?.status
  });

  // TESTE - verificar dados
  console.log('RECEITAS:', receitas);
  
  
  const [dropdownPosition, setDropdownPosition] = useState<{ 
    top?: number; 
    bottom?: number; 
    left: number;
  } | null>(null);
  
  // Estados para controle do grid
  const [filtros, setFiltros] = useState<FiltroGrid>({
    busca: '',
    categoria: '',
    status: '',
    ordenacao: 'nome',
    direcao: 'asc',
    // ===================================================================================================
    // FILTRO DE RECEITAS COM INSUMOS PENDENTES - INICIADO COMO FALSE
    // ===================================================================================================
    mostrarApenasPendentes: false
  });
  
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [paginaAtual, setPaginaAtual] = useState(1);
  const [itensPorPagina] = useState(12);
  const [receitaSelecionada, setReceitaSelecionada] = useState<number | null>(null);
  const [showDropdown, setShowDropdown] = useState<number | null>(null);
  // Estado para controlar dropdown de exportação
  const [showExportDropdown, setShowExportDropdown] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  // Estado para controlar modal de exportacao PDF
  const [showModalExportacaoPDF, setShowModalExportacaoPDF] = useState(false);
  // Ref para posicionar dropdown de exportação
  const exportButtonRef = useRef<HTMLButtonElement>(null);
  
  // ===================================================================================================
  // IMPORTAR CONFIGURACAO CENTRALIZADA DA API
  // ===================================================================================================
  // Usar API_BASE_URL do config.ts que detecta automaticamente o ambiente
  const API_URL = API_BASE_URL

  // ===================================================================================================
  // LÓGICA DE FILTRAGEM E ORDENAÇÃO
  // ===================================================================================================

  const receitasFiltradas = useMemo(() => {
    let resultado = [...receitas];

    // Filtro por busca (nome ou código)
    if (filtros.busca) {
      const termoBusca = filtros.busca.toLowerCase();
      resultado = resultado.filter(receita => 
        receita.nome.toLowerCase().includes(termoBusca) ||
        receita.codigo.toLowerCase().includes(termoBusca)
      );
    }

    // Filtro por categoria
    if (filtros.categoria) {
      resultado = resultado.filter(receita => receita.categoria === filtros.categoria);
    }

    // Filtro por status
    if (filtros.status) {
      resultado = resultado.filter(receita => receita.status === filtros.status);
    }

    // ===================================================================================================
    // FILTRO POR RECEITAS COM INSUMOS PENDENTES
    // ===================================================================================================
    if (filtros.mostrarApenasPendentes) {
      resultado = resultado.filter(receita => receita.tem_insumos_sem_preco === true);
    }

    // Ordenação
    resultado.sort((a, b) => {
      let valorA: any = a[filtros.ordenacao];
      let valorB: any = b[filtros.ordenacao];

      // Tratamento especial para strings
      if (typeof valorA === 'string') {
        valorA = valorA.toLowerCase();
        valorB = valorB.toLowerCase();
      }

      if (filtros.direcao === 'asc') {
        return valorA < valorB ? -1 : valorA > valorB ? 1 : 0;
      } else {
        return valorA > valorB ? -1 : valorA < valorB ? 1 : 0;
      }
    });

    return resultado;
  }, [receitas, filtros]);

  // Cálculo da paginação
  const totalPaginas = Math.ceil(receitasFiltradas.length / itensPorPagina);
  const indiceInicial = (paginaAtual - 1) * itensPorPagina;
  const receitasPaginadas = receitasFiltradas.slice(indiceInicial, indiceInicial + itensPorPagina);

  // Obter categorias únicas para filtro
  const categoriasUnicas = useMemo(() => {
    const categorias = receitas.map(r => r.categoria);
    return Array.from(new Set(categorias)).sort();
  }, [receitas]);

  // ===================================================================================================
  // FUNÇÕES AUXILIARES
  // ===================================================================================================

  const handleOrdenacao = (campo: string) => {
    setFiltros(prev => ({
      ...prev,
      ordenacao: campo as any,
      direcao: prev.ordenacao === campo && prev.direcao === 'asc' ? 'desc' : 'asc'
    }));
  };

  const formatarPreco = (valor: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(valor);
  };


  const getStatusBadge = (status: string, temInsumosSemPreco?: boolean, totalInsumos?: number) => {
    // ===================================================================================================
    // LÓGICA DE STATUS PENDENTE
    // Descrição: Determina o status final baseado em:
    // 1. Se receita existe (não undefined/null) E tem 0 insumos → PENDENTE
    // 2. Se receita tem insumos sem preço → PENDENTE
    // 3. Caso contrário → status original (ativo/inativo/processado)
    // ===================================================================================================
    console.log('🐛 getStatusBadge chamado:', { status, temInsumosSemPreco, totalInsumos });

    let statusFinal = status;
    
    // Verificação 1: Receita sem insumos (totalInsumos definido e igual a 0)
    if (totalInsumos !== undefined && totalInsumos === 0) {
      statusFinal = 'pendente';
      console.log('→ Marcado como PENDENTE: receita sem insumos');
    }
    // Verificação 2: Receita com insumos sem preço
    else if (temInsumosSemPreco === true) {
      statusFinal = 'pendente';
      console.log('→ Marcado como PENDENTE: insumos sem preço');
    }
    // Caso contrário: manter status original
    else {
      console.log('→ Status mantido:', status);
    }
    
    const configs = {
      ativo: { bg: 'bg-green-100', text: 'text-green-800', label: 'Ativo', icon: '✓' },
      inativo: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Inativo', icon: '○' },
      processado: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Processado', icon: '⚙' },
      pendente: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Pendente', icon: '⚠' }
    };
    
    const config = configs[statusFinal] || configs.ativo;
      
    return (
      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        <span>{config.icon}</span>
        {config.label}
      </span>
    );
  };

  // ===================================================================================================
  // COMPONENTE DE CARD PARA VIEW GRID
  // ===================================================================================================

  const ReceitaCard = ({ receita }: { receita: Receita }) => {
    // ===================================================================================================
    // DEBUG: Verificar dados da receita para status
    // ===================================================================================================
    console.log('=====================================');
    console.log('📊 RECEITA:', receita.nome);
    console.log('📊 status:', receita.status);
    console.log('📊 tem_insumos_sem_preco:', receita.tem_insumos_sem_preco);
    console.log('📊 total_insumos:', receita.total_insumos);
    console.log('📊 tipo total_insumos:', typeof receita.total_insumos);
    console.log('=====================================');

    return (
      <div
        className={`relative bg-white rounded-xl border-2 transition-all duration-300 hover:shadow-lg cursor-pointer overflow-hidden transform hover:-translate-y-1 ease-in-out active:scale-98 ${
          receitaSelecionada === receita.id
            ? 'border-green-500 shadow-lg'
            : 'border-gray-100 hover:border-green-300'
        }`}
        role="article"
        aria-label={`Receita ${receita.nome}`}
        onClick={() => {
          if (onViewReceita) {
            onViewReceita(receita);
          }
        }}
      >
      {/* Checkbox de seleção - canto superior esquerdo */}
      <div className="absolute top-3 left-3 z-10">
        <input
          type="checkbox"
          checked={receitaSelecionada === receita.id}
          onChange={(e) => {
            e.stopPropagation();
            setReceitaSelecionada(receitaSelecionada === receita.id ? null : receita.id);
          }}
          className="w-5 h-5 text-green-600 border-gray-300 rounded focus:ring-green-500 cursor-pointer shadow-lg"
          onClick={(e) => e.stopPropagation()}
        />
      </div>
      {/* Marca d'água de fundo */}
      <div 
        className="absolute inset-0 flex items-center justify-center pointer-events-none"
        style={{ 
          opacity: 0.05,
          zIndex: 0
        }}
      >
        <img 
          src="/src/image/food_receita.svg" 
          alt="" 
          className="w-full h-full object-contain"
        />
      </div>
      {/* Header do card */}
      <div className="p-4 border-b border-gray-50">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
            {receita.codigo}
          </span>
          <div className="relative">
            <button
              ref={(el) => {
                if (el && showDropdown === receita.id && !dropdownPosition) {
                  const rect = el.getBoundingClientRect();
                  const spaceBelow = window.innerHeight - rect.bottom;
                  const spaceAbove = rect.top;
                  
                  // Calcular posição absoluta em relação à viewport
                  const left = rect.right - 150; // 150px é a largura do dropdown
                  
                  if (spaceBelow < 200 && spaceAbove > spaceBelow) {
                    // Abrir para cima
                    setDropdownPosition({ 
                      bottom: window.innerHeight - rect.top + 5,
                      left: left 
                    });
                  } else {
                    // Abrir para baixo
                    setDropdownPosition({ 
                      top: rect.bottom + 5,
                      left: left 
                    });
                  }
                }
              }}
              onClick={(e) => {
                e.stopPropagation();
                setDropdownPosition(null); // Reset position
                setShowDropdown(showDropdown === receita.id ? null : receita.id);
              }}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <MoreVertical className="w-4 h-4 text-gray-400" />
            </button>
            
            {/* Dropdown de ações com Portal */}
            <DropdownPortal
              isOpen={showDropdown === receita.id}
              position={dropdownPosition}
              onClose={() => setShowDropdown(null)}
            >
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onViewReceita?.(receita);
                  setShowDropdown(null);
                }}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                <Eye className="w-4 h-4" />
                Visualizar
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onEditReceita?.(receita);
                  setShowDropdown(null);
                }}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                <Edit3 className="w-4 h-4" />
                Editar
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDuplicateReceita?.(receita);
                  setShowDropdown(null);
                }}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                <Copy className="w-4 h-4" />
                Duplicar
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteReceita?.(receita);
                  setShowDropdown(null);
                }}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                <Trash2 className="w-4 h-4" />
                Excluir
              </button>
            </DropdownPortal>
          </div>
        </div>
        
        <h3 className="font-semibold text-gray-900 mb-1 line-clamp-2">{receita.nome}</h3>
        
        {/* ===================================================================================================
            BADGE DE ALERTA - INSUMOS SEM PRECO
            =================================================================================================== */}
        {receita.tem_insumos_sem_preco && receita.insumos_pendentes && receita.insumos_pendentes.length > 0 && (
          <div className="flex items-center gap-1.5 bg-yellow-50 border border-yellow-200 rounded-lg px-2 py-1 mb-2">
            <span className="text-yellow-600 text-base">⚠️</span>
            <span className="text-xs font-medium text-yellow-700">
              {receita.insumos_pendentes.length} {receita.insumos_pendentes.length === 1 ? 'insumo pendente' : 'insumos pendentes'}
            </span>
          </div>
        )}
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">{receita.categoria}</span>
          {getStatusBadge(receita.status, receita.tem_insumos_sem_preco, receita.total_insumos)}
        </div>

        {/* Informacao do responsavel pela receita */}
        {receita.responsavel && (
          <div className="flex items-center gap-1.5 mt-2 text-xs text-gray-600">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <span>{receita.responsavel}</span>
          </div>
        )}
      </div>

      {/* Métricas principais */}
      <div className="p-4 space-y-3">
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            {/* ===================================================================================================
                CUSTO DO PRATO - Preco sugerido pelo restaurante
                =================================================================================================== */}
            <div className="flex items-center justify-center gap-1 mb-1">
              <Utensils className="w-4 h-4 text-green-500" />
              <span className="text-xs text-gray-500">Custo do Prato</span>
            </div>
            <p className="font-semibold text-green-600">
              {receita.sugestao_valor && receita.sugestao_valor > 0 
                ? formatarPreco(receita.sugestao_valor)
                : formatarPreco(receita.cmv_real)
              }
            </p>
          </div>
          
          <div className="text-center">
            {/* ===================================================================================================
                CMV % - Percentual de custo sobre preco sugerido com cores dinamicas
                Verde: ate 20% | Azul: 20-30% | Roxo: 30%+
                =================================================================================================== */}
            <div className="flex items-center justify-center gap-1 mb-1">
              {(() => {
                if (!receita.sugestao_valor || receita.sugestao_valor <= 0) {
                  return (
                    <>
                      <TrendingUp className="w-4 h-4 text-gray-400" />
                      <span className="text-xs text-gray-500">CMV %</span>
                    </>
                  );
                }
                
                const cmvPercentual = (receita.cmv_real / receita.sugestao_valor) * 100;
                let corIcone = 'text-blue-500';
                
                if (cmvPercentual <= 20) {
                  corIcone = 'text-green-500';
                } else if (cmvPercentual <= 30) {
                  corIcone = 'text-blue-500';
                } else {
                  corIcone = 'text-purple-500';
                }
                
                return (
                  <>
                    <TrendingUp className={`w-4 h-4 ${corIcone}`} />
                    <span className="text-xs text-gray-500">CMV %</span>
                  </>
                );
              })()}
            </div>
            <p className={`font-semibold ${(() => {
              if (!receita.sugestao_valor || receita.sugestao_valor <= 0) return 'text-gray-400';
              const cmvPercentual = (receita.cmv_real / receita.sugestao_valor) * 100;
              if (cmvPercentual <= 20) return 'text-green-600';
              if (cmvPercentual <= 30) return 'text-blue-600';
              return 'text-purple-600';
            })()}`}>
              {receita.sugestao_valor && receita.sugestao_valor > 0 
                ? `${((receita.cmv_real / receita.sugestao_valor) * 100).toFixed(1)}%`
                : '-'
              }
            </p>
          </div>
        </div>

        <div className="space-y-2 pt-2 border-t border-gray-50">
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-1">
              <Users className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-600">{receita.porcoes} porções</span>
            </div>
            
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-600">{receita.tempo_preparo}min</span>
            </div>
          </div>
          
          {/* ===================================================================================================
              CONTADORES DE INSUMOS - Calcular separacao dinamicamente
              Conta quantos itens tem receita_processada_id para determinar processados
              =================================================================================================== */}
          {(() => {
            const totalInsumos = receita.total_insumos || 0;
            
            // Calcular quantos sao processados verificando receita_processada_id
            const insumosProcessados = receita.receita_insumos?.filter(
              ri => ri.receita_processada_id !== null && ri.receita_processada_id !== undefined
            ).length || 0;
            
            const insumosNormais = totalInsumos - insumosProcessados;
            
            return (
              <div className="flex items-center justify-center gap-3 text-xs text-gray-500 pt-2">
                <div className="flex items-center gap-1">
                  <Package className="w-3.5 h-3.5" />
                  <span>{insumosNormais} insumos</span>
                </div>
                <div className="flex items-center gap-1">
                  <ChefHat className="w-3.5 h-3.5" />
                  <span>{insumosProcessados} processados</span>
                </div>
              </div>
            );
          })()}
        </div>

        {/* Preço sugerido */}
        <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-3 text-center">
          <span className="text-xs text-gray-500">Preço Sugerido</span>
          <p className="font-bold text-lg text-gray-900">{formatarPreco(receita.preco_venda_sugerido)}</p>
        </div>
      </div>
    </div>
  );
};
  // ===================================================================================================
  // COMPONENTE DE LINHA PARA VIEW LIST
  // ===================================================================================================

  const ReceitaRow = ({ receita }: { receita: Receita }) => {
  // ===================================================================================================
  // DEBUG: Verificar dados da receita para status (VIEW LIST)
  // ===================================================================================================
  console.log('📋 LISTA - Receita:', receita.nome, 'total_insumos:', receita.total_insumos);

  return (
    <tr
      className={`hover:bg-gray-50 cursor-pointer transition-colors duration-200 ${
        receitaSelecionada === receita.id ? 'bg-green-50' : ''
      }`}
      onClick={() => {
        if (onViewReceita) {
          onViewReceita(receita);
        }
      }}
    >
      <td className="px-6 py-4 w-12">
        <input
          type="checkbox"
          checked={receitaSelecionada === receita.id}
          onChange={(e) => {
            e.stopPropagation();
            setReceitaSelecionada(receitaSelecionada === receita.id ? null : receita.id);
          }}
          className="w-5 h-5 text-green-600 border-gray-300 rounded focus:ring-green-500 cursor-pointer"
          onClick={(e) => e.stopPropagation()}
        />
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <div>
          <div className="text-sm font-medium text-gray-900">{receita.nome}</div>
          <div className="text-sm text-gray-500">{receita.codigo}</div>
        </div>
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap">
        <span className="text-sm text-gray-900">{receita.categoria}</span>
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <span className="text-sm text-gray-600">{receita.responsavel || '-'}</span>
        </div>
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap">
        {getStatusBadge(receita.status, receita.tem_insumos_sem_preco, receita.total_insumos)}
      </td>
      
     <td className="px-6 py-4 whitespace-nowrap">
        {/* ===================================================================================================
            CUSTO DO PRATO - Preco sugerido pelo restaurante (sugestao_valor)
            Exibe o valor manual cadastrado pelo restaurante ao inves do CMV real
            =================================================================================================== */}
        <div className="flex items-center gap-2">
          <Utensils className="w-4 h-4 text-green-500" />
          <span className="text-sm font-semibold text-green-600">
            {receita.sugestao_valor && receita.sugestao_valor > 0 
              ? formatarPreco(receita.sugestao_valor)
              : formatarPreco(receita.cmv_real)
            }
          </span>
        </div>
      </td>

    <td className="px-6 py-4 whitespace-nowrap">
      {/* ===================================================================================================
          CALCULO DO CMV % BASEADO NO PRECO SUGERIDO PELO RESTAURANTE
          Formula: (custo_prato / preco_sugerido) * 100
          Exemplo: R$2,88 / R$7,80 = 36,9%
          
          Cores dinamicas baseadas no CMV:
          - Verde: ate 20% (otimo)
          - Azul: 20% a 30% (bom)
          - Roxo: 30% ou mais (atencao)
          =================================================================================================== */}
      {(() => {
        if (!receita.sugestao_valor || receita.sugestao_valor <= 0) {
          return (
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-400">-</span>
            </div>
          );
        }
        
        const cmvPercentual = (receita.cmv_real / receita.sugestao_valor) * 100;
        
        let corIcone = 'text-blue-500';
        let corTexto = 'text-gray-900';
        
        if (cmvPercentual <= 20) {
          corIcone = 'text-green-500';
          corTexto = 'text-green-600';
        } else if (cmvPercentual <= 30) {
          corIcone = 'text-blue-500';
          corTexto = 'text-blue-600';
        } else {
          corIcone = 'text-purple-500';
          corTexto = 'text-purple-600';
        }
        
        return (
          <div className="flex items-center gap-2">
            <TrendingUp className={`w-4 h-4 ${corIcone}`} />
            <span className={`text-sm font-medium ${corTexto}`}>
              {cmvPercentual.toFixed(1)}%
            </span>
          </div>
        );
      })()}
    </td>
      
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
        {formatarPreco(receita.preco_venda_sugerido)}
      </td>
      
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {receita.porcoes} | {receita.tempo_preparo}min
      </td>
      
      <td className="px-6 py-4 text-center">
        {receita.processada ? (
          <div className="flex items-center justify-center">
            <div className="flex items-center gap-2 px-3 py-1 bg-purple-50 border border-purple-200 rounded-full">
              <CheckCircle className="w-4 h-4 text-purple-600" />
              <span className="text-xs font-medium text-purple-700">Sim</span>
            </div>
          </div>
        ) : (
          <span className="text-gray-300">—</span>
        )}
      </td>

      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <div className="relative">
          <button
            ref={(el) => {
              if (el && showDropdown === receita.id && !dropdownPosition) {
                const rect = el.getBoundingClientRect();
                const spaceBelow = window.innerHeight - rect.bottom;
                const spaceAbove = rect.top;
                
                // Calcular posição absoluta em relação à viewport
                const left = rect.right - 150; // 150px é a largura do dropdown
                
                if (spaceBelow < 200 && spaceAbove > spaceBelow) {
                  // Abrir para cima
                  setDropdownPosition({ 
                    bottom: window.innerHeight - rect.top + 5,
                    left: left 
                  });
                } else {
                  // Abrir para baixo
                  setDropdownPosition({ 
                    top: rect.bottom + 5,
                    left: left 
                  });
                }
              }
            }}
            onClick={(e) => {
              e.stopPropagation();
              setDropdownPosition(null);
              setShowDropdown(showDropdown === receita.id ? null : receita.id);
            }}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <MoreVertical className="w-4 h-4 text-gray-400" />
          </button>
          
          {/* Dropdown de ações com Portal */}
          <DropdownPortal
            isOpen={showDropdown === receita.id}
            position={dropdownPosition}
            onClose={() => setShowDropdown(null)}
          >
            <button
              onClick={(e) => {
                e.stopPropagation();
                onViewReceita?.(receita);
                setShowDropdown(null);
              }}
              className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              <Eye className="w-4 h-4" />
              Visualizar
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onEditReceita?.(receita);
                setShowDropdown(null);
              }}
              className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              <Edit3 className="w-4 h-4" />
              Editar
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDuplicateReceita?.(receita);
                setShowDropdown(null);
              }}
              className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              <Copy className="w-4 h-4" />
              Duplicar
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDeleteReceita?.(receita);
                setShowDropdown(null);
              }}
              className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50"
            >
              <Trash2 className="w-4 h-4" />
              Excluir
            </button>
          </DropdownPortal>
        </div>
      </td>
    </tr>
  );
};

  // ===================================================================================================
  // FUNCOES DE EXPORTACAO
  // ===================================================================================================

  const handleExportarPDF = () => {
    // Abrir modal de opcoes de exportacao PDF
    setShowModalExportacaoPDF(true);
  };

  const handleExportarExcel = () => {
    // TODO: Implementar exportacao para Excel
    console.log('Exportar para Excel');
    alert('Funcionalidade de exportação para Excel será implementada em breve!');
  };

  const handleExportarCSV = () => {
    // TODO: Implementar exportacao para CSV
    console.log('Exportar para CSV');
    alert('Funcionalidade de exportação para CSV será implementada em breve!');
  };

  const exportarReceitaPDF = async (receitaId: number) => {
    try {
      setIsExporting(true);
      
      const response = await fetch(`${API_URL}/api/v1/receitas/${receitaId}/pdf`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Erro ao gerar PDF');
      }

      // Fazer download do PDF
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `receita_${receitaId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (error) {
      console.error('Erro ao exportar PDF:', error);
      alert('Erro ao gerar PDF. Tente novamente.');
    } finally {
      setIsExporting(false);
    }
  };

  const exportarReceitasLotePDF = async (receitaIds: number[]) => {
    try {
      setIsExporting(true);
      
      const response = await fetch(`${API_URL}/api/v1/receitas/pdf/lote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ receita_ids: receitaIds }),
      });

      if (!response.ok) {
        throw new Error('Erro ao gerar PDFs');
      }

      // Fazer download do ZIP
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Obter nome do arquivo do header ou usar padrao
      const contentDisposition = response.headers.get('content-disposition');
      const filename = contentDisposition 
        ? contentDisposition.split('filename=')[1].replace(/"/g, '')
        : `receitas_${new Date().getTime()}.zip`;
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      // Mostrar resumo
      const totalGerado = response.headers.get('x-total-generated');
      const totalSolicitado = response.headers.get('x-total-requested');
      
      if (totalGerado && totalSolicitado) {
        alert(`PDFs gerados com sucesso!\n${totalGerado} de ${totalSolicitado} receitas exportadas.`);
      }
      
    } catch (error) {
      console.error('Erro ao exportar PDFs em lote:', error);
      alert('Erro ao gerar PDFs. Tente novamente.');
    } finally {
      setIsExporting(false);
    }
  };

  const handleConfirmarExportacaoPDF = async (opcao: 'individual' | 'filtradas' | 'todas') => {
    let receitasParaExportar: number[] = [];
    
    switch (opcao) {
      case 'individual':
        // Se há receita selecionada explicitamente, exportar ela
        if (receitaSelecionada) {
          await exportarReceitaPDF(receitaSelecionada);
        } 
        // Caso contrário, mostrar aviso
        else {
          alert('Por favor, selecione uma receita clicando no checkbox ao lado do nome da receita.');
          return;
        }
        break;
        
      case 'filtradas':
        // Exportar receitas filtradas
        receitasParaExportar = receitasFiltradas.map(r => r.id);
        if (receitasParaExportar.length === 0) {
          alert('Nenhuma receita encontrada com os filtros aplicados.');
          return;
        }
        if (receitasParaExportar.length > 50) {
          alert('Máximo de 50 receitas por exportação. Por favor, aplique filtros para reduzir a quantidade.');
          return;
        }
        await exportarReceitasLotePDF(receitasParaExportar);
        break;
        
      case 'todas':
        // Exportar todas as receitas
        receitasParaExportar = receitas.map(r => r.id);
        if (receitasParaExportar.length === 0) {
          alert('Nenhuma receita cadastrada no sistema.');
          return;
        }
        if (receitasParaExportar.length > 50) {
          alert('Máximo de 50 receitas por exportação. Use os filtros para exportar em lotes menores.');
          return;
        }
        await exportarReceitasLotePDF(receitasParaExportar);
        break;
    }
    
    setShowModalExportacaoPDF(false);
  };

  // ===================================================================================================
  // RENDER PRINCIPAL
  // ===================================================================================================

  return (
    <div className="space-y-6">
      
      {/* ===================================================================================================
          HEADER COM ESTATÍSTICAS E AÇÕES PRINCIPAIS
          =================================================================================================== */}
      
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="flex flex-col gap-4">
          
          {/* Título e estatísticas */}
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Gestão de Receitas</h2>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <Tooltip content="Total de receitas cadastradas no sistema">
                <span className="flex items-center gap-1 cursor-help">
                  <ChefHat className="w-4 h-4" />
                  {receitas.length} receitas
                </span>
              </Tooltip>
              
              <Tooltip content="Receitas exibidas após aplicar filtros de busca">
                <span className="flex items-center gap-1 cursor-help">
                  <TrendingUp className="w-4 h-4" />
                  {receitasFiltradas.length} filtradas
                </span>
              </Tooltip>
              
              <Tooltip content="Custo Médio de Venda calculado a partir de todas as receitas">
                <span className="flex items-center gap-1 cursor-help">
                  <DollarSign className="w-4 h-4" />
                  CMV médio: {formatarPreco(receitas.reduce((acc, r) => acc + r.cmv_real, 0) / receitas.length || 0)}
                </span>
              </Tooltip>
            </div>
          </div>
          
          {/* Ações principais */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            {/* Grupo de botões Exportar e Importar */}
            <div className="flex items-center gap-3">
              {/* Dropdown de Exportação */}
              <div className="relative">
                <Tooltip content="Exportar receitas em diferentes formatos">
                  <button
                    ref={exportButtonRef}
                    onClick={() => setShowExportDropdown(!showExportDropdown)}
                    className="flex items-center justify-center gap-2 px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 hover:shadow-sm transition-all duration-200 flex-1 sm:flex-initial active:scale-95"
                  >
                    <Download className="w-4 h-4" />
                    Exportar
                    <ChevronDown className={`w-4 h-4 transition-transform ${showExportDropdown ? 'rotate-180' : ''}`} />
                  </button>
                </Tooltip>
              </div>

              {/* Dropdown renderizado com position fixed - fora do container */}
              {showExportDropdown && (
                <>
                  {/* Overlay para fechar ao clicar fora */}
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={() => setShowExportDropdown(false)}
                  />
                  
                  {/* Dropdown com posição fixed */}
                  <div 
                    className="fixed bg-white rounded-lg shadow-xl border border-gray-200 z-50 min-w-[220px]"
                    style={{
                      top: exportButtonRef.current 
                        ? `${exportButtonRef.current.getBoundingClientRect().bottom + 8}px`
                        : 'auto',
                      right: exportButtonRef.current
                        ? `${window.innerWidth - exportButtonRef.current.getBoundingClientRect().right}px`
                        : 'auto'
                    }}
                  >
                    <div className="py-1">
                      <button
                        onClick={() => {
                          handleExportarPDF();
                          setShowExportDropdown(false);
                        }}
                        className="flex items-center gap-3 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                      >
                        <FileText className="w-4 h-4 text-red-500" />
                        <span>Exportar para PDF</span>
                      </button>
                      <button
                        onClick={() => {
                          handleExportarExcel();
                          setShowExportDropdown(false);
                        }}
                        className="flex items-center gap-3 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                      >
                        <FileSpreadsheet className="w-4 h-4 text-green-500" />
                        <span>Exportar para Excel</span>
                      </button>
                      <button
                        onClick={() => {
                          handleExportarCSV();
                          setShowExportDropdown(false);
                        }}
                        className="flex items-center gap-3 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                      >
                        <FileSpreadsheet className="w-4 h-4 text-blue-500" />
                        <span>Exportar para CSV</span>
                      </button>
                    </div>
                  </div>
                </>
              )}
              
              <Tooltip content="Importar receitas a partir de arquivo Excel ou CSV">
                <button 
                  onClick={onImportar}
                  className="flex items-center justify-center gap-2 px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 hover:shadow-sm transition-all duration-200 flex-1 sm:flex-initial active:scale-95"
                >
                  <Upload className="w-4 h-4" />
                  Importar
                </button>
              </Tooltip>
            </div>
            
            {/* Botão Nova Receita - abaixo no mobile, ao lado no desktop */}
            <button
              onClick={onCreateReceita}
              className="flex items-center justify-center gap-2 px-6 py-2 bg-gradient-to-r from-green-500 to-pink-500 text-white rounded-lg hover:from-green-600 hover:to-pink-600 hover:shadow-lg transition-all duration-200 w-full sm:w-auto active:scale-95"
              aria-label="Criar nova receita"
            >
              <Plus className="w-4 h-4" aria-hidden="true" />
              Nova Receita
            </button>
          </div>
        </div>
      </div>

      {/* ===================================================================================================
          BARRA DE FILTROS E CONTROLES
          =================================================================================================== */}
      
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="flex flex-col lg:flex-row gap-4">
          
          {/* Campo de busca */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-green-500 w-5 h-5" />
            <input
              type="text"
              placeholder="Buscar por nome ou código da receita..."
              value={filtros.busca}
              onChange={(e) => setFiltros(prev => ({ ...prev, busca: e.target.value }))}
              className="w-full pl-10 pr-4 py-2 bg-white border-2 border-green-500 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-600 placeholder:text-gray-400"
            />
          </div>
          
          {/* Filtros */}
          <div className="flex flex-wrap lg:flex-nowrap gap-3">
            
            {/* Filtro por categoria */}
            <select
              value={filtros.categoria}
              onChange={(e) => setFiltros(prev => ({ ...prev, categoria: e.target.value }))}
              className="px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white"
              aria-label="Filtrar por categoria"
            >
              <option value="">Todas as categorias</option>
              {categoriasUnicas.map(categoria => (
                <option key={categoria} value={categoria}>{categoria}</option>
              ))}
            </select>
            
            {/* Filtro por status */}
            <select
              value={filtros.status}
              onChange={(e) => setFiltros(prev => ({ ...prev, status: e.target.value }))}
              className="px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-white"
              aria-label="Filtrar por status"
            >
              <option value="">Todos os status</option>
              <option value="ativo">Ativo</option>
              <option value="inativo">Inativo</option>
              <option value="processado">Processado</option>
            </select>
            
            {/* ===================================================================================================
                CHECKBOX - MOSTRAR APENAS RECEITAS COM INSUMOS PENDENTES
                =================================================================================================== */}
            <label className="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-lg bg-white hover:bg-gray-50 cursor-pointer transition-colors">
              <input
                type="checkbox"
                checked={filtros.mostrarApenasPendentes}
                onChange={(e) => setFiltros(prev => ({ ...prev, mostrarApenasPendentes: e.target.checked }))}
                className="w-4 h-4 text-yellow-600 border-gray-300 rounded focus:ring-yellow-500"
                aria-label="Mostrar apenas receitas com insumos pendentes"
              />
              <span className="text-sm text-gray-700 whitespace-nowrap">
                Apenas Pendentes
              </span>
            </label>
            
            {/* Toggle de visualização */}
            <div className="flex rounded-lg border border-gray-200 p-1" role="group" aria-label="Modo de visualização">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded ${viewMode === 'grid' ? 'bg-green-100 text-green-600' : 'text-gray-400 hover:text-gray-600'}`}
                aria-label="Visualizar em grade"
                aria-pressed={viewMode === 'grid'}
              >
                <Grid className="w-4 h-4" aria-hidden="true" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded ${viewMode === 'list' ? 'bg-green-100 text-green-600' : 'text-gray-400 hover:text-gray-600'}`}
                aria-label="Visualizar em lista"
                aria-pressed={viewMode === 'list'}
              >
                <List className="w-4 h-4" aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ===================================================================================================
          CONTEÚDO PRINCIPAL - GRID OU LISTA
          =================================================================================================== */}

      {/* ===================================================================================================
          PAGINAÇÃO NO TOPO
          =================================================================================================== */}
      
      {totalPaginas > 1 && (
        <div className="mb-4 flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3 sm:px-6 rounded-lg">
          {/* Mobile - Botões Anterior/Próxima */}
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

          {/* Desktop - Paginação Completa */}
          <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Mostrando 
                <span className="font-medium"> {indiceInicial + 1}</span> a{' '}
                <span className="font-medium">
                  {Math.min(indiceInicial + itensPorPagina, receitasFiltradas.length)}
                </span>{' '}
                de <span className="font-medium">{receitasFiltradas.length}</span> receitas
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
      
      {loading ? (
        <div className="space-y-4">
          {/* Skeleton loader baseado no modo de visualização atual */}
          {viewMode === 'grid' ? (
            <SkeletonLoader variant="grid" />
          ) : (
            <SkeletonLoader variant="table" />
          )}
        </div>
      ) : receitasFiltradas.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <EmptyState
            icon={ChefHat}
            title={filtros.busca || filtros.categoria || filtros.status !== 'todos' 
              ? "Nenhuma receita encontrada" 
              : "Nenhuma receita cadastrada"}
            description={filtros.busca || filtros.categoria || filtros.status !== 'todos'
              ? "Não encontramos receitas com os filtros aplicados. Tente ajustar os critérios de busca."
              : "Comece criando sua primeira receita para gerenciar custos e calcular preços de venda."}
            actionLabel="Nova Receita"
            onAction={onCreateReceita}
            secondaryActionLabel={filtros.busca || filtros.categoria || filtros.status !== 'todos' 
              ? "Limpar Filtros" 
              : ""}
            onSecondaryAction={filtros.busca || filtros.categoria || filtros.status !== 'todos' 
              ? () => {
                  setFiltros({
                    busca: '',
                    categoria: '',
                    status: 'todos',
                    ordenacao: 'nome',
                    direcao: 'asc',
                    // ===================================================================================================
                    // LIMPAR FILTRO DE PENDENTES TAMBEM
                    // ===================================================================================================
                    mostrarApenasPendentes: false
                  });
                }
              : undefined}
          />
        </div>
      ) : (
        <>
          {/* View em Grid */}
          {viewMode === 'grid' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {receitasPaginadas.map(receita => (
                <ReceitaCard key={receita.id} receita={receita} />
              ))}
            </div>
          )}

          {/* View em Lista */}
          {viewMode === 'list' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 w-12">
                        {/* Espaço para checkbox de seleção */}
                      </th>
                      <th 
                        onClick={() => handleOrdenacao('nome')}
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      >
                        <div className="flex items-center gap-1">
                          Nome
                          {filtros.ordenacao === 'nome' && (
                            filtros.direcao === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />
                          )}
                        </div>
                      </th>
                      
                      <th 
                        onClick={() => handleOrdenacao('categoria')}
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      >
                        <div className="flex items-center gap-1">
                          Categoria
                          {filtros.ordenacao === 'categoria' && (
                            filtros.direcao === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />
                          )}
                        </div>
                      </th>

                      {/* ADICIONAR ESTA NOVA COLUNA */}
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Responsável
                      </th>
                      
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      
                      <th 
                        onClick={() => handleOrdenacao('cmv')}
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      >
                        {/* ===================================================================================================
                            HEADER DA COLUNA - Alterado de CMV para Custo do Prato
                            Representa o custo real de producao da receita
                            =================================================================================================== */}
                        <div className="flex items-center gap-1">
                          Custo do Prato
                          {filtros.ordenacao === 'cmv' && (
                            filtros.direcao === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />
                          )}
                        </div>
                      </th>
                      
                      <th 
                        onClick={() => handleOrdenacao('margem')}
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      >
                        {/* ===================================================================================================
                            HEADER DA COLUNA - Alterado de Margem para CMV %
                            Mostra o percentual de CMV baseado no preco sugerido pelo restaurante
                            =================================================================================================== */}
                        <div className="flex items-center gap-1">
                          CMV %
                          {filtros.ordenacao === 'margem' && (
                            filtros.direcao === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />
                          )}
                        </div>
                      </th>
                      
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Preço Sugerido
                      </th>
                      
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Porções | Tempo
                      </th>

                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Processada
                      </th>
                      
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ações
                      </th>
                    </tr>
                  </thead>
                  
                  <tbody className="bg-white divide-y divide-gray-200">
                    {receitasPaginadas.map(receita => (
                      <ReceitaRow key={receita.id} receita={receita} />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ===================================================================================================
                  PAGINAÇÃO NO RODAPÉ
                  =================================================================================================== */}
          
          {totalPaginas > 1 && (
            <div className="mt-6 flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6 rounded-lg">
              {/* Mobile - Botões Anterior/Próxima */}
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

              {/* Desktop - Paginação Completa */}
              <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Mostrando 
                    <span className="font-medium"> {indiceInicial + 1}</span> a{' '}
                    <span className="font-medium">
                      {Math.min(indiceInicial + itensPorPagina, receitasFiltradas.length)}
                    </span>{' '}
                    de <span className="font-medium">{receitasFiltradas.length}</span> receitas
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
        </>
      )}
    {/* Overlay para fechar dropdown */}
    {showDropdown && (
        <div 
          className="fixed inset-0 z-5" 
          onClick={() => setShowDropdown(null)}
        />
      )}

      {/* Modal de Exportacao PDF */}
      {showModalExportacaoPDF && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full mx-4">
            {/* Header do Modal */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex items-center gap-3">
                <FileText className="w-6 h-6 text-red-500" />
                <h3 className="text-xl font-bold text-gray-900">Exportar para PDF</h3>
              </div>
              <button
                onClick={() => setShowModalExportacaoPDF(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Conteudo do Modal */}
            <div className="p-6 space-y-4">
              <p className="text-sm text-gray-600">
                Escolha quais receitas você deseja exportar:
              </p>

              {/* Opcoes de exportacao */}
              <div className="space-y-3">
                {/* Opcao 1: Receita Individual */}
                <button
                  onClick={() => handleConfirmarExportacaoPDF('individual')}
                  disabled={!receitaSelecionada || isExporting}
                  className={`w-full flex items-start gap-4 p-4 rounded-lg border-2 transition-all ${
                    receitaSelecionada && !isExporting
                      ? 'border-gray-200 hover:border-red-500 hover:bg-red-50'
                      : 'border-gray-100 bg-gray-50 cursor-not-allowed opacity-50'
                  }`}
                >
                  <div className="flex-shrink-0 mt-1">
                    <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                      <FileText className="w-5 h-5 text-red-600" />
                    </div>
                  </div>
                  <div className="flex-1 text-left">
                    <h4 className="font-semibold text-gray-900 mb-1">Receita Individual</h4>
                    <p className="text-sm text-gray-600">
                      Exportar apenas a receita selecionada
                    </p>
                  </div>
                </button>

                {/* Opcao 2: Receitas Filtradas */}
                <button
                  onClick={() => handleConfirmarExportacaoPDF('filtradas')}
                  disabled={receitasFiltradas.length === 0 || isExporting}
                  className={`w-full flex items-start gap-4 p-4 rounded-lg border-2 transition-all ${
                    receitasFiltradas.length > 0 && !isExporting
                      ? 'border-gray-200 hover:border-green-500 hover:bg-green-50'
                      : 'border-gray-100 bg-gray-50 cursor-not-allowed opacity-50'
                  }`}
                >
                  <div className="flex-shrink-0 mt-1">
                    <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                      <Filter className="w-5 h-5 text-green-600" />
                    </div>
                  </div>
                  <div className="flex-1 text-left">
                    <h4 className="font-semibold text-gray-900 mb-1">Receitas Filtradas</h4>
                    <p className="text-sm text-gray-600">
                      Exportar {receitasFiltradas.length} receita(s) visível(is) após aplicar filtros
                    </p>
                  </div>
                </button>

                {/* Opcao 3: Todas as Receitas */}
                <button
                  onClick={() => handleConfirmarExportacaoPDF('todas')}
                  disabled={receitas.length === 0 || isExporting}
                  className={`w-full flex items-start gap-4 p-4 rounded-lg border-2 transition-all ${
                    receitas.length > 0 && !isExporting
                      ? 'border-gray-200 hover:border-blue-500 hover:bg-blue-50'
                      : 'border-gray-100 bg-gray-50 cursor-not-allowed opacity-50'
                  }`}
                >
                  <div className="flex-shrink-0 mt-1">
                    <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                      <List className="w-5 h-5 text-blue-600" />
                    </div>
                  </div>
                  <div className="flex-1 text-left">
                    <h4 className="font-semibold text-gray-900 mb-1">Todas as Receitas</h4>
                    <p className="text-sm text-gray-600">
                      Exportar todas as {receitas.length} receita(s) do sistema
                    </p>
                    {receitas.length > 50 && (
                      <p className="text-xs text-orange-600 mt-1">
                        ⚠️ Máximo de 50 receitas por exportação
                      </p>
                    )}
                  </div>
                </button>
              </div>

              {/* Loading durante exportacao */}
              {isExporting && (
                <div className="flex items-center justify-center gap-3 py-4">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-red-500"></div>
                  <span className="text-sm text-gray-600">Gerando PDF(s)...</span>
                </div>
              )}

              {/* Informacao adicional */}
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-xs text-blue-800">
                  <strong>Nota:</strong> Os PDFs incluem todas as informações da receita: ingredientes, custos, precificação e dados complementares.
                </p>
              </div>
            </div>

            {/* Footer do Modal */}
            <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
              <button
                onClick={() => setShowModalExportacaoPDF(false)}
                disabled={isExporting}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


export default SuperGridReceitas;