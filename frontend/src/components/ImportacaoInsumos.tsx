// ============================================================================
// COMPONENTE - IMPORTAÇÃO DE INSUMOS VIA EXCEL
// ============================================================================
// Descrição: Interface para upload e importação de insumos via arquivo Excel
// Data: 30/10/2025
// Autor: Will - Empresa: IOGAR
// ============================================================================

import React, { useState, useCallback, useEffect } from 'react';
import { Upload, FileSpreadsheet, X, CheckCircle, AlertCircle, Loader } from 'lucide-react';

// ============================================================================
// Importar configuração da API
// ============================================================================
import { API_BASE_URL } from '../config';

// ============================================================================
// INTERFACES E TIPOS
// ============================================================================

interface PreviewDados {
  nome_arquivo: string;
  total_linhas: number;
  colunas_detectadas: string[];
  primeiras_linhas: any[];
  mapeamento_colunas: Record<string, string>;
  avisos: string[];
}

interface ResultadoImportacao {
  importacao_id: number;
  status: string;
  total_linhas: number;
  linhas_processadas: number;
  linhas_com_erro: number;
  linhas_ignoradas: number;
}

type EtapaImportacao = 'upload' | 'preview' | 'mapeamento' | 'processando' | 'concluido';

interface ImportacaoInsumosProps {
  restauranteId: number;
  onClose: () => void;
  onSuccess?: () => void;
}

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================

const ImportacaoInsumos: React.FC<ImportacaoInsumosProps> = ({
  restauranteId,
  onClose,
  onSuccess
}) => {
  // Estados
  const [etapa, setEtapa] = useState<EtapaImportacao>('upload');
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [importacaoId, setImportacaoId] = useState<number | null>(null);
  const [preview, setPreview] = useState<PreviewDados | null>(null);
  const [resultado, setResultado] = useState<ResultadoImportacao | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [contador, setContador] = useState<number>(60);
  const [intervaloId, setIntervaloId] = useState<NodeJS.Timeout | null>(null);
  const [mostrarDetalhesErros, setMostrarDetalhesErros] = useState(false);
  const [mostrarDetalhesIgnorados, setMostrarDetalhesIgnorados] = useState(false);
  const [logProcessamento, setLogProcessamento] = useState<any>(null);

  // Estado para mapeamento de colunas
  const [mapeamento, setMapeamento] = useState<{
    [colunaExcel: string]: {
      selecionada: boolean;
      campoDestino: string;
    }
  }>({});

  // Campos disponíveis no sistema
  const camposDisponiveis = [
    { value: 'nome', label: 'Nome do Insumo' },
    { value: 'unidade', label: 'Unidade de Medida' },
    { value: 'quantidade', label: 'Quantidade' },
    { value: 'fator', label: 'Fator (Multiplicador)' },
    { value: 'preco_unitario', label: 'Último Preço Praticado' },
    { value: 'codigo', label: 'Código (Opcional)' },
    { value: 'grupo', label: 'Categoria/Grupo (Opcional)' }
  ];

// Limpar intervalo ao desmontar componente
useEffect(() => {
return () => {
    if (intervaloId) {
    clearInterval(intervaloId);
    }
};
}, [intervaloId]);

  // ========================================================================
  // FUNÇÃO: HANDLE DRAG & DROP
  // ========================================================================

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      validarESetarArquivo(files[0]);
    }
  }, []);

  // ========================================================================
  // FUNÇÃO: VALIDAR E SETAR ARQUIVO
  // ========================================================================

  const validarESetarArquivo = (file: File) => {
    // Validar extensão
    if (!file.name.endsWith('.xlsx')) {
      setErro('Apenas arquivos .xlsx são aceitos');
      return;
    }

    // Validar tamanho (máx 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setErro('Arquivo muito grande. Tamanho máximo: 10MB');
      return;
    }

    setArquivo(file);
    setErro(null);
  };

  // ========================================================================
  // FUNÇÃO: HANDLE FILE INPUT
  // ========================================================================

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      validarESetarArquivo(files[0]);
    }
  };

  // ========================================================================
  // FUNÇÃO: UPLOAD E PREVIEW
  // ========================================================================

  const handleUpload = async () => {
    if (!arquivo) return;

    setEtapa('processando');
    setErro(null);

    try {
      const formData = new FormData();
      formData.append('file', arquivo);
      formData.append('restaurante_id', restauranteId.toString());

      const response = await fetch(`${API_BASE_URL}/api/v1/importacoes/upload`, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      console.log('Status da resposta:', response.status);
      console.log('Headers:', response.headers);

      const contentType = response.headers.get('content-type');

      if (!response.ok) {
        if (contentType && contentType.includes('application/json')) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Erro ao fazer upload');
        } else {
          const textError = await response.text();
          console.error('Erro não-JSON:', textError);
          throw new Error(`Erro ${response.status}: ${response.statusText}`);
        }
      }

      if (!contentType || !contentType.includes('application/json')) {
        const textResponse = await response.text();
        console.error('Resposta não é JSON:', textResponse);
        throw new Error('Servidor retornou resposta inválida. Verifique os logs do backend.');
      }

      const data = await response.json();
      setImportacaoId(data.importacao_id);
      setPreview(data.preview);

      // Inicializar mapeamento automático
      const mapeamentoInicial: typeof mapeamento = {};
      data.preview.colunas_detectadas.forEach((coluna: string) => {
        const colunaLower = coluna.toLowerCase();
        let campoAuto = '';
        
        // Detectar campo automaticamente
        if (colunaLower.includes('nome') || colunaLower.includes('produto') || colunaLower.includes('descri')) {
          campoAuto = 'nome';
        } else if (colunaLower.includes('unid')) {
          campoAuto = 'unidade';
        } else if (colunaLower.includes('qtd') || colunaLower.includes('quantidade') || colunaLower.includes('estoque')) {
          campoAuto = 'quantidade';
        } else if (colunaLower.includes('prec') || colunaLower.includes('valor') || colunaLower.includes('custo')) {
          campoAuto = 'preco_unitario';
        } else if (colunaLower.includes('cod') || colunaLower.includes('ean')) {
          campoAuto = 'codigo';
        } else if (colunaLower.includes('categ') || colunaLower.includes('grupo') || colunaLower.includes('tipo')) {
          campoAuto = 'grupo';
        }
        
        mapeamentoInicial[coluna] = {
          selecionada: campoAuto !== '',
          campoDestino: campoAuto
        };
      });

      setMapeamento(mapeamentoInicial);
      setEtapa('mapeamento');

    } catch (error: any) {
      setErro(error.message || 'Erro ao processar arquivo');
      setEtapa('upload');
    }
  };

  // ========================================================================
  // FUNÇÃO: CONFIRMAR E PROCESSAR
  // ========================================================================

  const handleConfirmar = async () => {
    if (!importacaoId) return;

    setEtapa('processando');
    setErro(null);

    try {
        // DEBUG: Mostrar TODOS os mapeamentos antes de filtrar
        console.log('🔍 DEBUG - MAPEAMENTO COMPLETO:', mapeamento);
        console.log('🔍 DEBUG - TOTAL DE COLUNAS:', Object.keys(mapeamento).length);
        
        // Verificar especificamente a coluna Código
        const colunaCodigo = Object.entries(mapeamento).find(([col, config]) => 
          col.toLowerCase().includes('código') || col.toLowerCase().includes('codigo')
        );
        console.log('🔍 DEBUG - COLUNA CÓDIGO:', colunaCodigo);
        
        // Preparar mapeamento apenas das colunas selecionadas
        const mapeamentoParaEnviar: Record<string, string> = {};
        Object.entries(mapeamento).forEach(([colunaExcel, config]) => {
          console.log(`🔍 DEBUG - Processando: ${colunaExcel}`, {
            selecionada: config.selecionada,
            campoDestino: config.campoDestino
          });
          
          if (config.selecionada && config.campoDestino) {
            mapeamentoParaEnviar[colunaExcel] = config.campoDestino;
          }
        });

        console.log('📤 DEBUG - MAPEAMENTO FINAL A ENVIAR:', mapeamentoParaEnviar);
        console.log('📤 DEBUG - TEM CÓDIGO?:', 'Código' in mapeamentoParaEnviar || 'codigo' in mapeamentoParaEnviar);

        const response = await fetch(`${API_BASE_URL}/api/v1/importacoes/processar`, {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
              importacao_id: importacaoId,
              confirmar: true,
              mapeamento_colunas: mapeamentoParaEnviar
          })
        });


      console.log('Status da resposta (processar):', response.status);
      console.log('Headers:', response.headers);

      // ============================================================================
      // Verificar se a resposta é JSON antes de tentar parsear
      // ============================================================================
      const contentType = response.headers.get('content-type');

      if (!response.ok) {
          if (contentType && contentType.includes('application/json')) {
              const errorData = await response.json();
              throw new Error(errorData.detail || 'Erro ao processar importação');
          } else {
              const textError = await response.text();
              console.error('Erro não-JSON:', textError);
              throw new Error(`Erro ${response.status}: ${response.statusText}`);
          }
      }

      // Verificar se resposta é JSON válido
      if (!contentType || !contentType.includes('application/json')) {
          const textResponse = await response.text();
          console.error('Resposta não é JSON:', textResponse);
          throw new Error('Servidor retornou resposta inválida. Verifique os logs do backend.');
      }

      const data = await response.json();
      console.log('🔍 DEBUG - Resposta completa:', data);
      console.log('🔍 DEBUG - log_processamento:', data.log_processamento);

      setResultado(data);

      // Carregar log de processamento se disponível
      if (data.log_processamento) {
          try {
              const log = typeof data.log_processamento === 'string' 
                  ? JSON.parse(data.log_processamento)
                  : data.log_processamento;
              console.log('🔍 DEBUG - Log parseado:', log);
              console.log('🔍 DEBUG - Ignorados no log:', log.ignorados);
              console.log('🔍 DEBUG - ERROS no log:', log.erros);
              console.log('🔍 DEBUG - Quantidade de erros:', log.erros?.length);
              setLogProcessamento(log);
          } catch (e) {
              console.error('❌ Erro ao parsear log:', e);
          }
      } else {
          console.log('⚠️ Não há log_processamento na resposta');
      }

      setEtapa('concluido');

      } catch (error: any) {
          setErro(error.message || 'Erro ao processar arquivo');
          setEtapa('upload');
      }
  };

  // ========================================================================
  // FUNÇÃO: CANCELAR
  // ========================================================================

  const handleCancelar = () => {
    setArquivo(null);
    setImportacaoId(null);
    setPreview(null);
    setResultado(null);
    setErro(null);
    setEtapa('upload');
  };

  // ========================================================================
  // RENDER: ETAPA UPLOAD
  // ========================================================================

  const renderUpload = () => (
    <div className="space-y-6">
      {/* Area de Drag & Drop */}
      <div
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center
          transition-all duration-200
          ${isDragging 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
        `}
      >
        <div className="flex flex-col items-center space-y-4">
          <div className={`
            p-4 rounded-full
            ${isDragging ? 'bg-blue-100' : 'bg-gray-100'}
          `}>
            <FileSpreadsheet 
              className={`w-12 h-12 ${isDragging ? 'text-blue-500' : 'text-gray-400'}`}
            />
          </div>

          {arquivo ? (
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-900">
                {arquivo.name}
              </p>
              <p className="text-xs text-gray-500">
                {(arquivo.size / 1024).toFixed(2)} KB
              </p>
              <button
                onClick={() => setArquivo(null)}
                className="text-sm text-red-600 hover:text-red-700"
              >
                Remover arquivo
              </button>
            </div>
          ) : (
            <>
              <div>
                <p className="text-base font-medium text-gray-900">
                  Arraste o arquivo Excel aqui
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  ou clique para selecionar
                </p>
              </div>

              <label className="cursor-pointer">
                <span className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                  <Upload className="w-4 h-4 mr-2" />
                  Selecionar Arquivo
                </span>
                <input
                  type="file"
                  accept=".xlsx"
                  onChange={handleFileInput}
                  className="hidden"
                />
              </label>
            </>
          )}

          <p className="text-xs text-gray-500">
            Formato aceito: .xlsx | Tamanho máximo: 10MB
          </p>
        </div>
      </div>

      {/* Mensagem de Erro */}
      {erro && (
        <div className="flex items-start space-x-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800">Erro</p>
            <p className="text-sm text-red-700 mt-1">{erro}</p>
          </div>
        </div>
      )}

      {/* Botões */}
      <div className="flex justify-end space-x-3">
        <button
          onClick={onClose}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancelar
        </button>
        <button
          onClick={handleUpload}
          disabled={!arquivo}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Continuar
        </button>
      </div>
    </div>
  );

  // ========================================================================
  // RENDER: ETAPA PREVIEW
  // ========================================================================

  // ========================================================================
  // RENDER: ETAPA MAPEAMENTO DE COLUNAS
  // ========================================================================

  const renderMapeamento = () => {
    if (!preview) return null;

    // Verificar se pelo menos uma coluna está selecionada e mapeada
    const temMapeamentoValido = Object.values(mapeamento).some(
      m => m.selecionada && m.campoDestino
    );

    // Verificar se tem campo "nome" mapeado (obrigatório)
    const temNomeMapeado = Object.values(mapeamento).some(
      m => m.selecionada && m.campoDestino === 'nome'
    );

    return (
      <div className="space-y-6">
        {/* Informações do arquivo */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 mb-2">Arquivo: {preview.nome_arquivo}</h4>
          <p className="text-sm text-blue-800">
            {preview.colunas_detectadas.length} colunas detectadas | {preview.total_linhas} linhas para importar
          </p>
        </div>

        {/* Instruções */}
        <div className="bg-gradient-to-r from-green-50 to-pink-50 border-2 border-green-200 rounded-xl p-4">
          <h3 className="font-semibold text-gray-900 mb-2">Como funciona o mapeamento?</h3>
          <ol className="text-sm text-gray-700 space-y-1 list-decimal list-inside">
            <li>Marque as colunas da planilha que você deseja importar</li>
            <li>Para cada coluna marcada, escolha em qual campo do sistema ela será inserida</li>
            <li>O campo <strong>"Nome do Insumo"</strong> é obrigatório</li>
            <li>O sistema tentou fazer o mapeamento automático - revise e ajuste conforme necessário</li>
          </ol>
        </div>

        {/* Tabela de Mapeamento */}
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase w-12">
                  Importar
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Coluna na Planilha
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Exemplo de Valor
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Campo no Sistema
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {preview.colunas_detectadas.map((coluna, index) => (
                <tr key={coluna} className={mapeamento[coluna]?.selecionada ? 'bg-green-50' : ''}>
                  {/* Checkbox */}
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={mapeamento[coluna]?.selecionada || false}
                      onChange={(e) => {
                        setMapeamento(prev => ({
                          ...prev,
                          [coluna]: {
                            ...prev[coluna],
                            selecionada: e.target.checked
                          }
                        }));
                      }}
                      className="w-5 h-5 text-green-600 border-gray-300 rounded focus:ring-green-500"
                    />
                  </td>

                  {/* Nome da coluna */}
                  <td className="px-4 py-3">
                    <span className="text-sm font-medium text-gray-900">{coluna}</span>
                  </td>

                  {/* Exemplo de valor */}
                  <td className="px-4 py-3">
                    <span className="text-sm text-gray-600">
                      {preview.primeiras_linhas[0]?.[coluna] || '-'}
                    </span>
                  </td>

                  {/* Select de campo destino */}
                  <td className="px-4 py-3">
                    <select
                      value={mapeamento[coluna]?.campoDestino || ''}
                      onChange={(e) => {
                        setMapeamento(prev => ({
                          ...prev,
                          [coluna]: {
                            selecionada: e.target.value !== '' ? true : prev[coluna]?.selecionada,
                            campoDestino: e.target.value
                          }
                        }));
                      }}
                      disabled={!mapeamento[coluna]?.selecionada}
                      className={`w-full px-3 py-2 bg-white border-2 rounded-lg transition-all ${
                        mapeamento[coluna]?.selecionada
                          ? 'border-green-500 focus:ring-2 focus:ring-green-500'
                          : 'border-gray-200 bg-gray-50 cursor-not-allowed'
                      }`}
                    >
                      <option value="">Selecione um campo...</option>
                      {camposDisponiveis.map(campo => (
                        <option key={campo.value} value={campo.value}>
                          {campo.label}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Avisos */}
        {!temNomeMapeado && (
          <div className="flex items-start gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-red-900">Campo obrigatório faltando</p>
              <p className="text-sm text-red-800">
                Você precisa mapear pelo menos uma coluna para o campo <strong>"Nome do Insumo"</strong>
              </p>
            </div>
          </div>
        )}

        {/* Botões */}
        <div className="flex justify-between pt-4">
          <button
            onClick={() => setEtapa('upload')}
            className="px-6 py-3 text-gray-700 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
          >
            Voltar
          </button>
          <button
            onClick={() => {
              if (temNomeMapeado) {
                setEtapa('preview');
              }
            }}
            disabled={!temNomeMapeado}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              temNomeMapeado
                ? 'bg-gradient-to-r from-green-500 to-pink-500 text-white hover:from-green-600 hover:to-pink-600 shadow-md hover:shadow-lg'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            Continuar para Preview
          </button>
        </div>
      </div>
    );
  };

  const renderPreview = () => {
    if (!preview) return null;

    return (
      <div className="space-y-6">
        {/* Informações do Arquivo */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-900 mb-3">
            Informações do Arquivo
          </h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Nome:</span>
              <span className="ml-2 font-medium">{preview.nome_arquivo}</span>
            </div>
            <div>
              <span className="text-gray-600">Total de linhas:</span>
              <span className="ml-2 font-medium">{preview.total_linhas}</span>
            </div>
          </div>
        </div>

        {/* Avisos */}
        {preview.avisos.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-yellow-900 mb-2">
              Avisos
            </h3>
            <ul className="space-y-1">
              {preview.avisos.map((aviso, index) => (
                <li key={index} className="text-sm text-yellow-800">
                  {aviso}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Preview dos Dados */}
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">
            Preview dos Dados (primeiras 5 linhas)
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 border">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Código</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Nome</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Quantidade</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Fator</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Preço</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Unidade</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {preview.primeiras_linhas.map((linha, index) => (
                  <tr key={index}>
                    <td className="px-4 py-2 text-sm text-gray-900">{linha.codigo}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{linha.nome}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{linha.quantidade || 1}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">{linha.fator || 1.0}</td>
                    <td className="px-4 py-2 text-sm text-gray-900">
                      R$ {linha.preco_compra_real?.toFixed(2)}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-900">{linha.unidade}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Botões */}
        <div className="flex justify-end space-x-3">
          <button
            onClick={handleCancelar}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onClick={handleConfirmar}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
          >
            Confirmar e Importar
          </button>
        </div>
      </div>
    );
  };

  // ========================================================================
  // RENDER: ETAPA PROCESSANDO
  // ========================================================================

  const renderProcessando = () => (
    <div className="flex flex-col items-center justify-center py-12 space-y-4">
      <Loader className="w-12 h-12 text-blue-600 animate-spin" />
      <p className="text-lg font-medium text-gray-900">
        Processando importação...
      </p>
      <p className="text-sm text-gray-600">
        Isso pode levar alguns instantes
      </p>
    </div>
  );

  // ========================================================================
  // RENDER: ETAPA CONCLUÍDO
  // ========================================================================

  const renderConcluido = () => {
    if (!resultado) return null;

    const sucesso = resultado.linhas_com_erro === 0;
    const taxaSucesso = resultado.total_linhas > 0 
        ? Math.round((resultado.linhas_processadas / resultado.total_linhas) * 100)
        : 0;

    return (
        <div className="space-y-6">
        {/* Header com gradiente IOGAR */}
        <div className={`
            rounded-xl p-6 
            ${sucesso 
            ? 'bg-gradient-to-r from-green-500 to-green-600' 
            : 'bg-gradient-to-r from-yellow-500 to-orange-500'
            }
        `}>
            <div className="flex items-center space-x-4 text-white">
            {sucesso ? (
                <div className="bg-white/20 p-3 rounded-full">
                <CheckCircle className="w-8 h-8" />
                </div>
            ) : (
                <div className="bg-white/20 p-3 rounded-full">
                <AlertCircle className="w-8 h-8" />
                </div>
            )}
            <div className="flex-1">
                <h3 className="text-2xl font-bold">
                {sucesso ? 'Importação Concluída com Sucesso!' : 'Importação Concluída com Avisos'}
                </h3>
                <p className="text-white/90 mt-1">
                {resultado.linhas_processadas} de {resultado.total_linhas} insumos importados ({taxaSucesso}%)
                </p>
            </div>
            </div>
        </div>

        {/* Cards de estatísticas com estilo IOGAR */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Total */}
            <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-600">Total</span>
                <div className="bg-gray-200 p-1.5 rounded">
                📊
                </div>
            </div>
            <p className="text-2xl font-bold text-gray-900">
                {resultado.total_linhas}
            </p>
            <p className="text-xs text-gray-500 mt-1">linhas processadas</p>
            </div>

            {/* Sucesso */}
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
            <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-green-700">Importados</span>
                <div className="bg-green-200 p-1.5 rounded">
                ✅
                </div>
            </div>
            <p className="text-2xl font-bold text-green-900">
                {resultado.linhas_processadas}
            </p>
            <p className="text-xs text-green-600 mt-1">com sucesso</p>
            </div>

            {/* Erros */}
            <div 
                className="bg-gradient-to-br from-red-50 to-red-100 rounded-lg p-4 border border-red-200 cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => setMostrarDetalhesErros(!mostrarDetalhesErros)}
                title="Clique para ver detalhes"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-red-700">Erros</span>
                <div className="bg-red-200 p-1.5 rounded">
                ❌
                </div>
              </div>
              <p className="text-2xl font-bold text-red-900">
                {resultado.linhas_com_erro}
              </p>
              <p className="text-xs text-red-600 mt-1">
                {resultado.linhas_com_erro > 0 ? 'clique para ver detalhes' : 'sem erros'}
              </p>
            </div>

            {/* Ignorados */}
            <div 
                className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg p-4 border border-yellow-200 cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => setMostrarDetalhesIgnorados(!mostrarDetalhesIgnorados)}
                title="Clique para ver detalhes dos códigos duplicados"
            >
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-yellow-700">Duplicados</span>
                    <div className="bg-yellow-200 p-1.5 rounded">
                    ⏭️
                    </div>
                </div>
                <p className="text-2xl font-bold text-yellow-900">
                    {resultado.linhas_ignoradas}
                </p>
                <p className="text-xs text-yellow-600 mt-1">
                    {resultado.linhas_ignoradas > 0 ? 'já cadastrados' : 'nenhum duplicado'}
                </p>
            </div>
        </div>

        {/* Seção de detalhes dos ignorados (CÓDIGOS DUPLICADOS) */}
        {mostrarDetalhesIgnorados && resultado.linhas_ignoradas > 0 && logProcessamento && (
            <div className="bg-yellow-50 border-2 border-yellow-300 rounded-xl p-6 shadow-lg">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h4 className="font-semibold text-yellow-900 text-lg flex items-center gap-2">
                            ⏭️ Códigos Duplicados (Não Importados)
                        </h4>
                        <p className="text-sm text-yellow-700 mt-1">
                            Os seguintes insumos <strong>não foram importados</strong> pois já existem neste restaurante
                        </p>
                    </div>
                    <button
                        onClick={() => setMostrarDetalhesIgnorados(false)}
                        className="text-yellow-600 hover:text-yellow-800 p-2 hover:bg-yellow-100 rounded-lg transition-colors"
                        title="Fechar"
                    >
                        ✕
                    </button>
                </div>

                {/* Explicação adicional */}
                <div className="bg-white border border-yellow-200 rounded-lg p-4 mb-4">
                    <div className="flex items-start gap-3">
                        <div className="text-2xl">💡</div>
                        <div className="flex-1 text-sm text-gray-700">
                            <p className="font-medium text-gray-900 mb-2">Por que foram ignorados?</p>
                            <ul className="list-disc list-inside space-y-1 text-gray-600">
                                <li>Estes códigos <strong>já estão cadastrados</strong> neste restaurante</li>
                                <li>O sistema não permite códigos duplicados no mesmo restaurante</li>
                                <li>Para atualizar estes insumos, edite-os manualmente na lista de insumos</li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Lista de duplicados */}
                <div className="space-y-2 max-h-96 overflow-y-auto">
                    {logProcessamento.ignorados && logProcessamento.ignorados.length > 0 ? (
                        logProcessamento.ignorados.map((item: any, index: number) => (
                            <div 
                                key={index}
                                className="bg-white border-2 border-yellow-200 rounded-lg p-4 hover:border-yellow-300 transition-colors"
                            >
                                <div className="flex items-start space-x-3">
                                    <div className="bg-yellow-100 px-3 py-2 rounded-lg flex-shrink-0">
                                        <span className="text-yellow-900 font-bold text-sm">
                                            Linha {item.linha}
                                        </span>
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-gray-900 mb-1">
                                            {item.mensagem}
                                        </p>
                                        {item.dados && (item.dados.codigo || item.dados.nome) && (
                                            <div className="flex items-center gap-4 text-xs text-gray-600 bg-gray-50 rounded px-3 py-2">
                                                {item.dados.codigo && (
                                                    <span className="font-mono">
                                                        <strong>Código:</strong> {item.dados.codigo}
                                                    </span>
                                                )}
                                                {item.dados.nome && (
                                                    <span>
                                                        <strong>Nome na planilha:</strong> {item.dados.nome}
                                                    </span>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))
                    ) : (
                        <p className="text-center text-gray-500 py-4">
                            Nenhum detalhe disponível
                        </p>
                    )}
                </div>
            </div>
        )}

        {/* Seção de detalhes dos erros */}
        {mostrarDetalhesErros && resultado.linhas_com_erro > 0 && logProcessamento && (
            <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                    <h4 className="font-semibold text-red-900 text-lg">
                        ❌ Detalhes dos Erros
                    </h4>
                    <button
                        onClick={() => setMostrarDetalhesErros(false)}
                        className="text-red-600 hover:text-red-800"
                    >
                        ✕
                    </button>
                </div>

                <div className="space-y-2 max-h-96 overflow-y-auto">
                    {logProcessamento.erros && logProcessamento.erros.length > 0 ? (
                        logProcessamento.erros.map((item: any, index: number) => (
                            <div 
                                key={index}
                                className="bg-white border border-red-200 rounded-lg p-4"
                            >
                                <div className="flex items-start space-x-3">
                                    <div className="bg-red-100 p-2 rounded-full flex-shrink-0">
                                        <span className="text-red-700 font-bold">
                                            {item.linha}
                                        </span>
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-red-900">
                                            {item.mensagem}
                                        </p>
                                        {item.dados && (item.dados.codigo || item.dados.nome) && (
                                            <p className="text-xs text-gray-600 mt-1">
                                                {item.dados.codigo && `Código: ${item.dados.codigo}`}
                                                {item.dados.codigo && item.dados.nome && ' | '}
                                                {item.dados.nome && `Nome: ${item.dados.nome}`}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))
                    ) : (
                        <p className="text-center text-gray-500 py-4">
                            Nenhum detalhe disponível
                        </p>
                    )}
                </div>
            </div>
        )}

        {/* Mensagem de sucesso com animação */}
        {sucesso && (
            <div className="bg-gradient-to-r from-green-50 to-green-100 border-2 border-green-500 rounded-xl p-6">
            <div className="flex items-start space-x-4">
                <div className="bg-green-500 p-2 rounded-full animate-pulse">
                <CheckCircle className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                <h4 className="font-semibold text-green-900 text-lg mb-2">
                    🎉 Insumos importados com sucesso!
                </h4>
                <p className="text-green-800 text-sm">
                    Todos os {resultado.linhas_processadas} insumos foram adicionados ao sistema e já estão disponíveis para uso.
                </p>
                </div>
            </div>
            </div>
        )}

        {/* Botão de fechar */}
        <div className="flex justify-end">
            <button
                onClick={() => {
                    if (onSuccess) {
                        onSuccess();
                    }
                    onClose();
                }}
                className="px-6 py-3 bg-gradient-to-r from-green-500 to-pink-500 text-white rounded-lg hover:from-green-600 hover:to-pink-600 transition-all shadow-md hover:shadow-lg font-medium"
            >
                Fechar
            </button>
        </div>
        </div>
    );
    };

  // ========================================================================
  // RENDER PRINCIPAL
  // ========================================================================

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            Importar Insumos via Excel
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {etapa === 'upload' && renderUpload()}
          {etapa === 'mapeamento' && renderMapeamento()}
          {etapa === 'preview' && renderPreview()}
          {etapa === 'processando' && renderProcessando()}
          {etapa === 'concluido' && renderConcluido()}
        </div>
      </div>
    </div>
  );
};

export default ImportacaoInsumos;