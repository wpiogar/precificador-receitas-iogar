# ============================================================================
# SERVICE - PROCESSAMENTO DE IMPORTAÇÃO DE INSUMOS
# ============================================================================
# Descrição: Serviço para processar arquivos Excel e importar insumos
# Data: 30/10/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

import openpyxl
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
import logging

from app.models.importacao_insumo import ImportacaoInsumo, StatusImportacao
from app.models.insumo import Insumo
from app.schemas.importacao_insumo import (
    PreviewImportacao,
    LogProcessamento,
    ItemLog
)

# Configurar logging
logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTES DE MAPEAMENTO
# ============================================================================

MAPEAMENTO_COLUNAS = {
    'CodigoProduto': 'codigo',
    'NomeProduto': 'nome',
    'PrecoCompra': 'preco_compra_real',
    'Unidade': 'unidade',
    'Fator': 'quantidade'
}

CONVERSAO_UNIDADES = {
    'LT': 'L',
    'UN': 'unidade',
    'KG': 'kg',
    'G': 'g',
    'ML': 'ml',
    'L': 'L'
}


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def converter_unidade(unidade_excel: str) -> str:
    """
    Converte unidade do Excel para o padrão do sistema.
    
    Args:
        unidade_excel: Unidade vinda do Excel (LT, UN, KG, etc.)
        
    Returns:
        str: Unidade no padrão do sistema
        
    Exemplos:
        LT -> L
        UN -> unidade
        KG -> kg
    """
    if not unidade_excel:
        return 'unidade'
    
    unidade_upper = str(unidade_excel).strip().upper()
    return CONVERSAO_UNIDADES.get(unidade_upper, unidade_excel.lower())


def encontrar_linha_cabecalho(worksheet) -> Optional[int]:
    """
    Encontra a linha do cabeçalho no Excel.
    Identifica o cabeçalho pela primeira linha que contém múltiplos valores não vazios
    e não é apenas numérica (indicando dados).
    
    Args:
        worksheet: Planilha do openpyxl
        
    Returns:
        int: Número da linha do cabeçalho (1-indexed) ou None se não encontrar
    """
    for row_num, row in enumerate(worksheet.iter_rows(min_row=1, max_row=20), start=1):
        valores = [str(cell.value).strip() if cell.value else '' for cell in row]
        
        # Contar quantos valores não vazios existem
        valores_preenchidos = [v for v in valores if v and v.lower() not in ['none', 'nan', '']]
        
        # Se tiver pelo menos 3 valores preenchidos, pode ser o cabeçalho
        if len(valores_preenchidos) >= 3:
            # Verificar se não é uma linha de dados (valores numéricos)
            # Cabeçalho geralmente tem pelo menos um texto
            tem_texto = any(
                not v.replace('.', '').replace(',', '').replace('-', '').isdigit() 
                for v in valores_preenchidos
            )
            
            if tem_texto:
                logger.info(f"Cabeçalho encontrado na linha {row_num}: {valores_preenchidos[:5]}")
                return row_num
    
    # Se não encontrou cabeçalho nas primeiras 20 linhas, assume linha 1
    logger.warning("Cabeçalho não identificado automaticamente, usando linha 1")
    return 1


def extrair_dados_linha(row, colunas_mapeadas: Dict[str, int]) -> Dict[str, Any]:
    """
    Extrai dados de uma linha do Excel usando o mapeamento de colunas.
    
    Args:
        row: Linha do Excel (tupla de células)
        colunas_mapeadas: Dicionário {nome_campo: índice_coluna}
        
    Returns:
        Dict com os dados extraídos e convertidos
    """
    dados = {}
    
    # Converter row em lista se for iterator
    if not isinstance(row, (list, tuple)):
        row = list(row)
    
    # Extrair código
    if 'codigo' in colunas_mapeadas:
        idx = colunas_mapeadas['codigo']
        if idx < len(row):
            codigo_cell = row[idx]
            valor = codigo_cell.value if hasattr(codigo_cell, 'value') else codigo_cell
            dados['codigo'] = str(valor).strip() if valor else None
    
    # Extrair nome
    if 'nome' in colunas_mapeadas:
        idx = colunas_mapeadas['nome']
        if idx < len(row):
            nome_cell = row[idx]
            valor = nome_cell.value if hasattr(nome_cell, 'value') else nome_cell
            dados['nome'] = str(valor).strip() if valor else None
    
    # Extrair preço - verificar preco_unitario E preco_compra_real
    preco_key = None
    if 'preco_unitario' in colunas_mapeadas:
        preco_key = 'preco_unitario'
    elif 'preco_compra_real' in colunas_mapeadas:
        preco_key = 'preco_compra_real'
    
    if preco_key:
        idx = colunas_mapeadas[preco_key]
        if idx < len(row):
            preco_cell = row[idx]
            valor = preco_cell.value if hasattr(preco_cell, 'value') else preco_cell
            try:
                preco = float(valor) if valor else 0.0
                dados['preco_compra_real'] = preco
            except (ValueError, TypeError):
                dados['preco_compra_real'] = 0.0
    
    # Extrair unidade
    if 'unidade' in colunas_mapeadas:
        idx = colunas_mapeadas['unidade']
        if idx < len(row):
            unidade_cell = row[idx]
            valor = unidade_cell.value if hasattr(unidade_cell, 'value') else unidade_cell
            unidade_raw = str(valor).strip() if valor else 'unidade'
            dados['unidade'] = converter_unidade(unidade_raw)
    
    # Extrair quantidade (se mapeado)
    if 'quantidade' in colunas_mapeadas:
        idx = colunas_mapeadas['quantidade']
        if idx < len(row):
            qtd_cell = row[idx]
            valor = qtd_cell.value if hasattr(qtd_cell, 'value') else qtd_cell
            try:
                dados['quantidade'] = float(valor) if valor else 1.0
            except (ValueError, TypeError):
                dados['quantidade'] = 1.0
    
    # Extrair grupo/categoria (se mapeado)
    if 'grupo' in colunas_mapeadas:
        idx = colunas_mapeadas['grupo']
        if idx < len(row):
            grupo_cell = row[idx]
            valor = grupo_cell.value if hasattr(grupo_cell, 'value') else grupo_cell
            dados['grupo'] = str(valor).strip() if valor else None
    
    return dados


def validar_dados_linha(dados: Dict[str, Any], linha_num: int) -> Tuple[bool, Optional[str]]:
    """
    Valida se os dados extraídos estão corretos.
    
    Args:
        dados: Dicionário com dados extraídos
        linha_num: Número da linha (para mensagem de erro)
        
    Returns:
        Tuple[bool, Optional[str]]: (válido, mensagem_erro)
    """
    # Validar código (obrigatório na importação)
    codigo = dados.get('codigo')
    if not codigo or str(codigo).strip() == '' or str(codigo).lower() in ['none', 'nan']:
        return False, f"Linha {linha_num}: Código do produto está vazio ou inválido"
    
    # Validar nome (obrigatório)
    nome = dados.get('nome')
    if not nome or str(nome).strip() == '' or str(nome).lower() in ['none', 'nan']:
        return False, f"Linha {linha_num}: Nome do produto está vazio"
    
    # Unidade - se não tiver, usar padrão
    if not dados.get('unidade'):
        dados['unidade'] = 'unidade'
    
    # Preço - se não tiver, usar 0
    if 'preco_compra_real' not in dados or dados['preco_compra_real'] is None:
        dados['preco_compra_real'] = 0.0
    
    return True, None


# ============================================================================
# CLASSE PRINCIPAL DO SERVICE
# ============================================================================

class ImportacaoService:
    """
    Service para processamento de importação de insumos via Excel.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o service com a sessão do banco de dados.
        
        Args:
            db: Sessão do SQLAlchemy
        """
        self.db = db
    
    # ========================================================================
    # MÉTODO: GERAR PREVIEW
    # ========================================================================
    
    def gerar_preview(
        self,
        caminho_arquivo: str,
        nome_arquivo: str
    ) -> PreviewImportacao:
        """
        Gera preview dos dados que serão importados.
        
        Args:
            caminho_arquivo: Caminho do arquivo Excel no servidor
            nome_arquivo: Nome original do arquivo
            
        Returns:
            PreviewImportacao: Schema com preview dos dados
            
        Raises:
            ValueError: Se arquivo inválido ou não puder ser lido
        """
        try:
            # Abrir arquivo Excel
            wb = openpyxl.load_workbook(caminho_arquivo, data_only=True)
            ws = wb.active
            
            # Encontrar linha do cabeçalho
            linha_cabecalho = encontrar_linha_cabecalho(ws)
            if not linha_cabecalho:
                raise ValueError("Não foi possível encontrar o cabeçalho no arquivo Excel")
            
            # Extrair colunas do cabeçalho - TODAS AS COLUNAS (mesmo com vazias no meio)
            header_row = list(ws.iter_rows(min_row=linha_cabecalho, max_row=linha_cabecalho))[0]
            colunas_detectadas = []

            # Detectar até onde tem dados (última coluna com conteúdo)
            ultima_coluna_com_dado = 0
            for i, cell in enumerate(header_row):
                if cell.value is not None and str(cell.value).strip() != '':
                    ultima_coluna_com_dado = i

            # Extrair até a última coluna que tem dado
            for i in range(ultima_coluna_com_dado + 1):
                cell = header_row[i]
                valor = cell.value
                if valor is None or str(valor).strip() == '':
                    # Coluna vazia - dar nome genérico
                    colunas_detectadas.append(f"Coluna_{i+1}")
                else:
                    colunas_detectadas.append(str(valor).strip())

            logger.info(f"📋 Colunas detectadas no preview ({len(colunas_detectadas)}): {colunas_detectadas}")
            
            # Mapear colunas
            colunas_mapeadas = {}
            for i, col in enumerate(colunas_detectadas):
                campo_sistema = MAPEAMENTO_COLUNAS.get(col)
                if campo_sistema:
                    colunas_mapeadas[campo_sistema] = i
            
            # Extrair primeiras 5 linhas de dados
            primeiras_linhas = []
            linha_dados_inicial = linha_cabecalho + 1
            
            for row in ws.iter_rows(min_row=linha_dados_inicial, max_row=linha_dados_inicial + 4):
                dados = extrair_dados_linha(row, colunas_mapeadas)
                if dados.get('codigo') and dados.get('nome'):
                    primeiras_linhas.append(dados)
            
            # Contar total de linhas
            total_linhas = ws.max_row - linha_cabecalho
            
            # Gerar avisos
            avisos = []
            if 'codigo' not in colunas_mapeadas:
                avisos.append("⚠️ Coluna 'CodigoProduto' não encontrada")
            if 'nome' not in colunas_mapeadas:
                avisos.append("⚠️ Coluna 'NomeProduto' não encontrada")
            if 'preco_compra_real' not in colunas_mapeadas:
                avisos.append("⚠️ Coluna 'PrecoCompra' não encontrada")
            if 'unidade' not in colunas_mapeadas:
                avisos.append("⚠️ Coluna 'Unidade' não encontrada")
            
            # ================================================================
            # Informar sobre coluna Fator (opcional)
            # ================================================================
            # HISTÓRICO: Aviso adicionado em 19/11/2025
            if 'quantidade' in colunas_mapeadas:
                avisos.append("ℹ️ Coluna 'Fator' detectada - valores serão importados como Quantidade")
            
            wb.close()
            
            return PreviewImportacao(
                nome_arquivo=nome_arquivo,
                total_linhas=total_linhas,
                colunas_detectadas=colunas_detectadas,
                primeiras_linhas=primeiras_linhas,
                mapeamento_colunas={
                    k: v for k, v in MAPEAMENTO_COLUNAS.items()
                },
                avisos=avisos
            )
            
        except Exception as e:
            logger.error(f"Erro ao gerar preview: {e}")
            raise ValueError(f"Erro ao processar arquivo: {str(e)}")
    
    # ========================================================================
    # MÉTODO: PROCESSAR IMPORTAÇÃO
    # ========================================================================
    
    def processar_importacao(
        self,
        importacao_id: int,
        restaurante_id: int,
        mapeamento_customizado: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, str]:
        """
        Processa a importação e cria os insumos no banco de dados.
        
        Args:
            importacao_id: ID da importação a processar
            restaurante_id: ID do restaurante
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        # Buscar importação
        importacao = self.db.query(ImportacaoInsumo).filter(
            ImportacaoInsumo.id == importacao_id
        ).first()
        
        if not importacao:
            return False, "Importação não encontrada"
        
        # Atualizar status para processando
        importacao.status = StatusImportacao.PROCESSANDO
        importacao.data_inicio_processamento = datetime.now()
        self.db.commit()
        
        # Inicializar log
        log = LogProcessamento()
        
        try:
            # Abrir arquivo Excel
            wb = openpyxl.load_workbook(importacao.caminho_arquivo, data_only=True)
            ws = wb.active
            
            # Encontrar cabeçalho
            linha_cabecalho = encontrar_linha_cabecalho(ws)
            if not linha_cabecalho:
                raise ValueError("Cabeçalho não encontrado")
            
            # Mapear colunas
            header_row = list(ws.iter_rows(min_row=linha_cabecalho, max_row=linha_cabecalho))[0]
            colunas_mapeadas = {}

            # Se recebeu mapeamento customizado do frontend, usar ele
            if mapeamento_customizado:
                logger.info(f"Usando mapeamento customizado: {mapeamento_customizado}")
                for i, cell in enumerate(header_row):
                    col_name_excel = str(cell.value).strip() if cell.value else ''
                    # Verificar se esta coluna está no mapeamento customizado
                    if col_name_excel in mapeamento_customizado:
                        campo_sistema = mapeamento_customizado[col_name_excel]
                        colunas_mapeadas[campo_sistema] = i
                        logger.info(f"Mapeado: '{col_name_excel}' -> '{campo_sistema}' (coluna {i})")
            else:
                # Usar mapeamento padrão (TOTVS)
                logger.info("Usando mapeamento padrão TOTVS")
                for i, cell in enumerate(header_row):
                    col_name = str(cell.value).strip() if cell.value else ''
                    campo_sistema = MAPEAMENTO_COLUNAS.get(col_name)
                    if campo_sistema:
                        colunas_mapeadas[campo_sistema] = i

            # ADICIONAR ESTAS 2 LINHAS AQUI
            logger.info(f"📊 Colunas mapeadas final: {colunas_mapeadas}")
            logger.info(f"📋 Total de colunas no header: {len(header_row)}")            
            
            # Processar linhas
            linha_dados_inicial = linha_cabecalho + 1
            total_linhas = ws.max_row - linha_cabecalho

            for row_num, row in enumerate(
                ws.iter_rows(min_row=linha_dados_inicial),
                start=linha_dados_inicial
            ):
                # Extrair dados
                dados = extrair_dados_linha(row, colunas_mapeadas)
                
                # ========================================================================
                # VERIFICAÇÃO 1: Ignorar linhas de cabeçalho de grupo (ex: "Grupo: DP")
                # ========================================================================
                codigo_valor = dados.get('codigo', '')
                if codigo_valor and str(codigo_valor).strip().upper().startswith('GRUPO'):
                    log.ignorados.append(ItemLog(
                        linha=row_num,
                        tipo="ignorado",
                        mensagem="Linha de cabeçalho de grupo",
                        dados={'codigo': codigo_valor}
                    ))
                    continue
                
                # ========================================================================
                # VERIFICAÇÃO 2: Ignorar linhas completamente vazias
                # ========================================================================
                tem_algum_valor = any(
                    dados.get(campo) and str(dados.get(campo)).strip() not in ['', 'None', 'none']
                    for campo in ['codigo', 'nome']
                )
                if not tem_algum_valor:
                    log.ignorados.append(ItemLog(
                        linha=row_num,
                        tipo="ignorado",
                        mensagem="Linha vazia",
                        dados={}
                    ))
                    continue
                
                # ========================================================================
                # VERIFICAÇÃO 3: Se não tem código mas tem nome, gerar código automático
                # ========================================================================
                # Se não tem código mas tem nome, gerar código automático
                if (not dados.get('codigo') or str(dados.get('codigo')).strip() in ['', 'None', 'none']) and dados.get('nome'):
                    # Gerar código baseado no nome + timestamp para garantir unicidade
                    nome_limpo = ''.join(c for c in str(dados['nome'])[:12].upper() if c.isalnum())
                    
                    # Usar número da linha como diferenciador
                    codigo_final = f"AUTO_{nome_limpo}_{row_num}"
                    
                    # Garantir que não existe (extra segurança)
                    contador = 1
                    while self.db.query(Insumo).filter(
                        Insumo.codigo == codigo_final,
                        Insumo.restaurante_id == restaurante_id
                    ).first():
                        codigo_final = f"AUTO_{nome_limpo}_{row_num}_{contador}"
                        contador += 1
                    
                    dados['codigo'] = codigo_final
                    logger.info(f"Linha {row_num}: Código gerado automaticamente: {codigo_final}")
                
                # ========================================================================
                # FILTRO: Apenas códigos entre 5000 e 5999
                # ========================================================================
                try:
                    codigo_str = str(dados.get('codigo', '')).strip()
                    # Se começar com AUTO_, permitir (código gerado automaticamente)
                    if not codigo_str.startswith('AUTO_'):
                        codigo_numero = int(codigo_str)
                        if codigo_numero < 5000 or codigo_numero > 5999:
                            log.ignorados.append(ItemLog(
                                linha=row_num,
                                tipo="ignorado",
                                mensagem=f"Código {dados['codigo']} fora da faixa permitida (5000-5999)",
                                dados=dados
                            ))
                            continue
                except (ValueError, TypeError):
                    # Se não conseguir converter para int e não for AUTO_, é erro
                    if not str(dados.get('codigo', '')).startswith('AUTO_'):
                        log.erros.append(ItemLog(
                            linha=row_num,
                            tipo="erro",
                            mensagem=f"Código inválido: {dados.get('codigo')}",
                            dados=dados
                        ))
                        continue
                
                # Validar dados
                valido, erro = validar_dados_linha(dados, row_num)
                
                if not valido:
                    log.erros.append(ItemLog(
                        linha=row_num,
                        tipo="erro",
                        mensagem=erro,
                        dados=dados
                    ))
                    continue
                
                # Verificar se insumo já existe
                insumo_existente = self.db.query(Insumo).filter(
                    Insumo.restaurante_id == restaurante_id,
                    Insumo.codigo == dados['codigo']
                ).first()
                
                if insumo_existente:
                    log.ignorados.append(ItemLog(
                        linha=row_num,
                        tipo="ignorado",
                        mensagem=f"Insumo com código {dados['codigo']} já existe",
                        dados=dados
                    ))
                    continue
                
                # Criar insumo
                try:
                    novo_insumo = Insumo(
                        restaurante_id=restaurante_id,
                        importacao_id=importacao_id,
                        codigo=dados['codigo'],
                        nome=dados['nome'],
                        quantidade=dados.get('quantidade', 1),
                        unidade=dados['unidade'],
                        preco_compra=int(dados.get('preco_compra_real', 0) * 100),
                        grupo=dados.get('grupo', ''),
                        subgrupo='',
                        eh_fornecedor_anonimo=True,
                        aguardando_classificacao=False
                    )
                    
                    self.db.add(novo_insumo)
                    
                    log.sucessos.append(ItemLog(
                        linha=row_num,
                        tipo="sucesso",
                        mensagem=f"Insumo '{dados['nome']}' importado com sucesso",
                        dados=dados
                    ))
                    
                except Exception as e:
                    log.erros.append(ItemLog(
                        linha=row_num,
                        tipo="erro",
                        mensagem=f"Erro ao criar insumo: {str(e)}",
                        dados=dados
                    ))
                
                except Exception as e:
                    log.erros.append(ItemLog(
                        linha=row_num,
                        tipo="erro",
                        mensagem=f"Erro ao criar insumo: {str(e)}",
                        dados=dados
                    ))

            # ADICIONAR AQUI: Commit a cada 100 linhas para não perder tudo
            if len(log.sucessos) % 100 == 0 and len(log.sucessos) > 0:
                try:
                    self.db.commit()
                    logger.info(f"✓ Commit parcial: {len(log.sucessos)} insumos salvos")
                except Exception as e:
                    logger.error(f"Erro no commit parcial: {e}")
                    self.db.rollback()

            wb.close()

            # Atualizar estatísticas da importação
            importacao.total_linhas = total_linhas
            importacao.linhas_processadas = len(log.sucessos)
            importacao.linhas_com_erro = len(log.erros)
            importacao.linhas_ignoradas = len(log.ignorados)
            importacao.log_processamento = log.model_dump_json()
            importacao.data_fim_processamento = datetime.now()

            # Definir status final
            if len(log.erros) == 0 and len(log.sucessos) > 0:
                importacao.status = StatusImportacao.SUCESSO
            elif len(log.sucessos) > 0 and len(log.erros) > 0:
                importacao.status = StatusImportacao.SUCESSO_PARCIAL
            else:
                importacao.status = StatusImportacao.ERRO
                importacao.mensagem_erro = "Nenhum insumo foi importado com sucesso"

            self.db.commit()

            return True, f"Importação concluída: {len(log.sucessos)} sucessos, {len(log.erros)} erros"
        
        except Exception as e:
            logger.error(f"Erro ao processar importação: {e}")
            importacao.status = StatusImportacao.ERRO
            importacao.mensagem_erro = str(e)
            importacao.data_fim_processamento = datetime.now()
            self.db.commit()
            return False, f"Erro ao processar: {str(e)}"