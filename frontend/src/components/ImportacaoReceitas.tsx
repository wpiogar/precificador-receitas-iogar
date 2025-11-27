// ============================================================================
// COMPONENTE - IMPORTAÇÃO DE RECEITAS VIA EXCEL
// ============================================================================
// Descrição: Interface para upload e importação de receitas via arquivo Excel
// Data: 25/11/2025
// Autor: Will - Empresa: IOGAR
// ============================================================================

import React, { useState, useCallback } from 'react';
import { Upload, FileSpreadsheet, X, CheckCircle, AlertCircle, Loader, AlertTriangle } from 'lucide-react';

// ============================================================================
// Importar configuração da API
// ============================================================================
import { API_BASE_URL } from '../config';

// ============================================================================
// INTERFACES E TIPOS
// ============================================================================

interface InsumoReceitaPreview {
  codigo: number | null;
  nome: string;
  quantidade: number;
  unidade: string;
  custo: number;
  valor: number;
  insumo_id_matched: number | null;
  tipo_match: string | null;
  score_similaridade: number;
  nome_insumo_sistema: string | null;
}

interface ReceitaPreview {
  codigo: number;
  nome: string;
  tipo: string;
  total_insumos: number;
  custo_total: number;
  valor_total: number;
  insumos: InsumoReceitaPreview[];
  insumos_nao_encontrados: number;
  pode_importar: boolean;
}

interface PreviewDados {
  nome_arquivo: string;
  total_receitas: number;
  estatisticas: {
    insumos_matched_exato: number;
    insumos_matched_fuzzy: number;
    insumos_nao_encontrados: number;
  };
  receitas_prontas: ReceitaPreview[];
  receitas_com_insumos_faltando: ReceitaPreview[];
  avisos: string[];
}

interface ResultadoImportacao {
  importacao_id: number;
  status: string;
  total_receitas_processadas: number;
  receitas_importadas_sucesso: number;
  receitas_com_erro: number;
  mensagem: string;
}

type EtapaImportacao = 'upload' | 'preview' | 'processando' | 'concluido';

interface ImportacaoReceitasProps {
  restauranteId: number;
  onClose: () => void;
  onSuccess?: () => void;
}

// ============================================================================
// COMPONENTE PRINCIPAL
// ============================================================================

const ImportacaoReceitas: React.FC<ImportacaoReceitasProps> = ({
  restauranteId,
  onClose,
  onSuccess
}) => {
  // Estados
  const [etapa, setEtapa] = useState<EtapaImportacao>('upload');
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [preview, setPreview] = useState<PreviewDados | null>(null);
  const [resultado, setResultado] = useState<ResultadoImportacao | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [receitasSelecionadas, setReceitasSelecionadas] = useState<number[]>([]);

  // ============================================================================
  // DEBUG: Log quando o componente renderiza
  // ============================================================================
  console.log('🔄 ImportacaoReceitas renderizado - Etapa:', etapa);

  // ========================================================================
  // HANDLERS DE DRAG AND DROP
  // ========================================================================

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleArquivoSelecionado(files[0]);
    }
  }, []);

  // ========================================================================
  // FUNÇÃO: VALIDAR E PROCESSAR ARQUIVO
  // ========================================================================

  const handleArquivoSelecionado = (file: File) => {
    // Validar tipo de arquivo
    if (!file.name.endsWith('.xlsx')) {
      setErro('Por favor, selecione um arquivo Excel (.xlsx)');
      return;
    }

    // Validar tamanho (máximo 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setErro('Arquivo muito grande. Tamanho máximo: 10MB');
      return;
    }

    setArquivo(file);
    setErro(null);
  };

  // ========================================================================
  // FUNÇÃO: UPLOAD E PREVIEW
  // ========================================================================

  const handleUpload = async () => {
    if (!arquivo) {
      setErro('Nenhum arquivo selecionado');
      return;
    }

    setEtapa('processando');
    setErro(null);

    try {
      const formData = new FormData();
      formData.append('file', arquivo);
      formData.append('restaurante_id', restauranteId.toString());

      const response = await fetch(`${API_BASE_URL}/api/v1/importacao-receitas/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao processar arquivo');
      }

      const data = await response.json();
      setPreview(data.preview);

      // Selecionar automaticamente todas as receitas prontas
      const receitasProntas = data.preview.receitas_prontas.map((r: ReceitaPreview) => r.codigo);
      setReceitasSelecionadas(receitasProntas);

      setEtapa('preview');

    } catch (error: any) {
      setErro(error.message || 'Erro ao processar arquivo');
      setEtapa('upload');
    }
  };

  // ========================================================================
  // FUNÇÃO: CONFIRMAR E PROCESSAR
  // ========================================================================

  const handleConfirmar = async () => {
    console.log('========================================');
    console.log('1. handleConfirmar CHAMADO');
    console.log('Preview:', preview);
    console.log('Arquivo:', arquivo);
    console.log('Receitas selecionadas:', receitasSelecionadas);
    console.log('========================================');
    
    if (!preview || !arquivo) {
        console.log('ERRO: Preview ou arquivo não existe');
        return;
    }

    setEtapa('processando');
    setErro(null);

    try {
      const formData = new FormData();
      formData.append('arquivo', arquivo);
      formData.append('restaurante_id', restauranteId.toString());

      console.log('🔍 Receitas a enviar:', receitasSelecionadas);
      console.log('🔍 JSON stringified:', JSON.stringify(receitasSelecionadas));
      
      // Enviar cada receita selecionada como item separado
      formData.append('receitas_selecionadas', JSON.stringify(receitasSelecionadas));

      console.log('========================================');
      console.log('2. FormData preparado');
      console.log('Enviando para:', `${API_BASE_URL}/api/v1/importacao-receitas/processar`);
      console.log('========================================');

      const response = await fetch(`${API_BASE_URL}/api/v1/importacao-receitas/processar`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erro ao processar importação');
      }

      const data = await response.json();
      console.log('========================================');
      console.log('RESPOSTA DO BACKEND:', data);
      console.log('========================================');
      setResultado(data);
      setEtapa('concluido');

      if (onSuccess) {
        onSuccess();
      }

    } catch (error: any) {
      console.error('Erro ao processar:', error);
      setErro(error.message || 'Erro ao processar importação');
      setEtapa('preview');
    }
  };

  // ========================================================================
  // FUNÇÃO: TOGGLE SELEÇÃO DE RECEITA
  // ========================================================================

  const toggleReceitaSelecionada = (codigo: number) => {
    setReceitasSelecionadas(prev => {
      if (prev.includes(codigo)) {
        return prev.filter(c => c !== codigo);
      } else {
        return [...prev, codigo];
      }
    });
  };

  // ========================================================================
  // RENDER: ETAPA UPLOAD
  // ========================================================================

  const renderUpload = () => (
    <div className="space-y-4">
      <div className="bg-gradient-to-r from-green-50 to-pink-50 border-2 border-green-200 rounded-xl p-4">
        <h3 className="font-semibold text-gray-900 mb-2">Formato esperado do arquivo</h3>
        <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
          <li>Arquivo Excel (.xlsx)</li>
          <li>Receitas começam com "Composto: CÓDIGO - NOME - TIPO"</li>
          <li>Insumos listados abaixo de cada receita com código, nome, quantidade e unidade</li>
          <li>Sistema fará matching automático dos insumos</li>
        </ul>
      </div>

      <div
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
          isDragging
            ? 'border-green-500 bg-green-50'
            : 'border-gray-300 hover:border-green-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <FileSpreadsheet className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-lg font-medium text-gray-700 mb-2">
          {arquivo ? arquivo.name : 'Arraste o arquivo aqui'}
        </p>
        <p className="text-sm text-gray-500 mb-4">
          ou clique para selecionar
        </p>
        <input
          type="file"
          accept=".xlsx"
          onChange={(e) => e.target.files && handleArquivoSelecionado(e.target.files[0])}
          className="hidden"
          id="file-input"
        />
        <label
          htmlFor="file-input"
          className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-green-500 to-pink-500 text-white rounded-lg cursor-pointer hover:from-green-600 hover:to-pink-600 transition-all"
        >
          <Upload className="mr-2 h-4 w-4" />
          Selecionar arquivo
        </label>
      </div>

      {arquivo && (
        <div className="flex justify-end space-x-3">
          <button
            onClick={() => setArquivo(null)}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleUpload}
            className="px-4 py-2 bg-gradient-to-r from-green-500 to-pink-500 text-white rounded-lg hover:from-green-600 hover:to-pink-600 transition-all"
          >
            Processar arquivo
          </button>
        </div>
      )}
    </div>
  );

  // ========================================================================
  // RENDER: ETAPA PREVIEW
  // ========================================================================

  const renderPreview = () => {
    if (!preview) return null;

    return (
      <div className="space-y-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-3">Resumo da Importação</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {preview.receitas_prontas.length}
              </div>
              <div className="text-sm text-gray-600">Receitas prontas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {preview.receitas_com_insumos_faltando.length}
              </div>
              <div className="text-sm text-gray-600">Com problemas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">
                {preview.total_receitas}
              </div>
              <div className="text-sm text-gray-600">Total</div>
            </div>
          </div>
        </div>

        {preview.avisos.length > 0 && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-start">
              <AlertTriangle className="h-5 w-5 text-orange-600 mr-2 mt-0.5" />
              <div className="flex-1">
                <h4 className="font-semibold text-orange-900 mb-2">Avisos</h4>
                <ul className="text-sm text-orange-800 space-y-1">
                  {preview.avisos.map((aviso, idx) => (
                    <li key={idx}>{aviso}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-4">
          <h4 className="font-semibold text-gray-900">Receitas que podem ser importadas</h4>
          {preview.receitas_prontas.map((receita) => (
            <div
              key={receita.codigo}
              className={`border rounded-lg p-4 cursor-pointer transition-all ${
                receitasSelecionadas.includes(receita.codigo)
                  ? 'border-green-500 bg-green-50'
                  : 'border-gray-200 hover:border-green-300'
              }`}
              onClick={() => toggleReceitaSelecionada(receita.codigo)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={receitasSelecionadas.includes(receita.codigo)}
                      onChange={() => toggleReceitaSelecionada(receita.codigo)}
                      className="h-4 w-4 text-green-600 rounded"
                    />
                    <h5 className="font-semibold text-gray-900">
                      {receita.codigo} - {receita.nome}
                    </h5>
                    <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">
                      {receita.tipo}
                    </span>
                  </div>
                  <div className="mt-2 text-sm text-gray-600">
                    {receita.total_insumos} insumos | Custo: R$ {receita.custo_total.toFixed(2)}
                  </div>
                </div>
                <CheckCircle className="h-5 w-5 text-green-600" />
              </div>
            </div>
          ))}
        </div>

        {preview.receitas_com_insumos_faltando.length > 0 && (
          <div className="space-y-4">
            <h4 className="font-semibold text-gray-900">Receitas com insumos faltando</h4>
            {preview.receitas_com_insumos_faltando.map((receita) => (
              <div
                key={receita.codigo}
                className="border border-orange-200 bg-orange-50 rounded-lg p-4"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="h-5 w-5 text-orange-600" />
                      <h5 className="font-semibold text-gray-900">
                        {receita.codigo} - {receita.nome}
                      </h5>
                    </div>
                    <div className="mt-2 text-sm text-orange-800">
                      {receita.insumos_nao_encontrados} insumo(s) não encontrado(s):
                      <ul className="mt-1 ml-4 list-disc">
                        {receita.insumos.map((insumo, idx) => (
                          <li key={idx}>
                            {insumo.nome} ({insumo.quantidade} {insumo.unidade})
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex justify-end space-x-3 pt-4">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleConfirmar}
            disabled={receitasSelecionadas.length === 0}
            className="px-4 py-2 bg-gradient-to-r from-green-500 to-pink-500 text-white rounded-lg hover:from-green-600 hover:to-pink-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Importar {receitasSelecionadas.length} receita(s)
          </button>
        </div>
      </div>
    );
  };

  // ========================================================================
  // RENDER: ETAPA PROCESSANDO
  // ========================================================================

  const renderProcessando = () => (
    <div className="flex flex-col items-center justify-center py-12">
      <Loader className="h-12 w-12 text-green-600 animate-spin mb-4" />
      <p className="text-lg font-medium text-gray-700">Processando importação...</p>
      <p className="text-sm text-gray-500 mt-2">Por favor, aguarde</p>
    </div>
  );

  // ========================================================================
  // RENDER: ETAPA CONCLUÍDO
  // ========================================================================

  const renderConcluido = () => {
    if (!resultado) return null;

    return (
      <div className="space-y-4">
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <CheckCircle className="mx-auto h-12 w-12 text-green-600 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Importação concluída com sucesso!
          </h3>
          <p className="text-gray-600">{resultado.mensagem}</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-green-600">
              {resultado.receitas_importadas_sucesso}
            </div>
            <div className="text-sm text-gray-600">Receitas importadas</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-red-600">
              {resultado.receitas_com_erro}
            </div>
            <div className="text-sm text-gray-600">Erros</div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gradient-to-r from-green-500 to-pink-500 text-white rounded-lg hover:from-green-600 hover:to-pink-600 transition-all"
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="bg-gradient-to-r from-green-500 to-pink-500 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Upload className="h-6 w-6 text-white" />
            <h2 className="text-xl font-bold text-white">Importar Receitas</h2>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {erro && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start">
                <AlertCircle className="h-5 w-5 text-red-600 mr-2 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-red-900">Erro</h4>
                  <p className="text-sm text-red-800 mt-1">{erro}</p>
                </div>
              </div>
            </div>
          )}

          {etapa === 'upload' && renderUpload()}
          {etapa === 'preview' && renderPreview()}
          {etapa === 'processando' && renderProcessando()}
          {etapa === 'concluido' && renderConcluido()}
        </div>
      </div>
    </div>
  );
};

export default ImportacaoReceitas;