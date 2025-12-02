# ============================================================================
# SERVICE - IMPORTAÇÃO DE RECEITAS VIA EXCEL
# ============================================================================
# Descrição: Serviço para processar importação de receitas do Excel
# Data: 25/11/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

import pandas as pd
import re
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from difflib import SequenceMatcher

from app.models.receita import Receita, ReceitaInsumo
from app.models.insumo import Insumo


# ============================================================================
# CLASSES DE DADOS
# ============================================================================

class InsumoReceita:
    """Representa um insumo dentro de uma receita"""
    def __init__(self, codigo: Optional[int], nome: str, quantidade: float, 
                 unidade: str, custo: float, valor: float):
        self.codigo = codigo
        self.nome = nome
        self.quantidade = quantidade
        self.unidade = unidade
        self.custo = custo
        self.valor = valor
        self.insumo_id_matched = None
        self.tipo_match = None  # EXATO, FUZZY, NAO_ENCONTRADO
        self.score_similaridade = 0.0


class ReceitaImportacao:
    """Representa uma receita completa a ser importada"""
    def __init__(self, codigo: int, nome: str, tipo: str):
        self.codigo = codigo
        self.nome = nome
        self.tipo = tipo  # Composto ou Processado
        self.insumos: List[InsumoReceita] = []
        self.custo_total = 0.0
        self.valor_total = 0.0
        self.sucesso = False
        self.mensagem_erro = None


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class ReceitaImportService:
    """
    Serviço para processar importação de receitas via Excel.
    Identifica receitas (linhas cinzas) e seus ingredientes.
    """
    
    def __init__(self, db: Session, restaurante_id: int):
        self.db = db
        self.restaurante_id = restaurante_id
        self.receitas_processadas: List[ReceitaImportacao] = []
        self.receitas_com_erro: List[ReceitaImportacao] = []
        
    # ========================================================================
    # MÉTODO PRINCIPAL - PROCESSAR ARQUIVO
    # ========================================================================
    
    def processar_arquivo(self, caminho_arquivo: str) -> Dict:
        """
        Processa o arquivo Excel e extrai as receitas.
        
        Args:
            caminho_arquivo: Caminho do arquivo Excel
            
        Returns:
            Dict com estatísticas e resultados
        """
        try:
            # Ler arquivo Excel sem cabeçalho
            df = pd.read_excel(caminho_arquivo, header=None)
            
            # Processar linhas e identificar receitas
            receitas = self._identificar_receitas(df)
            
            # Fazer matching de insumos
            self._processar_matching_insumos(receitas)
            
            # Preparar resultado
            resultado = {
                "total_receitas": len(receitas),
                "receitas_prontas": [],
                "receitas_com_insumos_faltando": [],
                "estatisticas": {
                    "insumos_matched_exato": 0,
                    "insumos_matched_fuzzy": 0,
                    "insumos_nao_encontrados": 0
                }
            }
            
            # Classificar receitas
            # Alteração: TODAS as receitas vão para "receitas_prontas" 
            # (mesmo com insumos faltando, pois podem ser importadas como "pendentes")
            for receita in receitas:
                insumos_faltando = [
                    ins for ins in receita.insumos 
                    if ins.tipo_match == "NAO_ENCONTRADO"
                ]
                
                # Todas as receitas são adicionadas a receitas_prontas
                resultado["receitas_prontas"].append({
                    "codigo": receita.codigo,
                    "nome": receita.nome,
                    "tipo": receita.tipo,
                    "total_insumos": len(receita.insumos),
                    "custo_total": receita.custo_total,
                    "valor_total": receita.valor_total,
                    "insumos_nao_encontrados": len(insumos_faltando),
                    "insumos": [
                        {
                            "insumo_id": ins.insumo_id_matched,
                            "nome": ins.nome,
                            "quantidade": ins.quantidade,
                            "unidade": ins.unidade,
                            "custo": ins.custo,
                            "valor": ins.valor,
                            "tipo_match": ins.tipo_match
                        }
                        for ins in receita.insumos
                    ]
                })
                
                # Se tiver insumos faltando, adicionar TAMBÉM na lista de problemas
                # (para exibir aviso ao usuário, mas não impede importação)
                if len(insumos_faltando) > 0:
                    resultado["receitas_com_insumos_faltando"].append({
                        "codigo": receita.codigo,
                        "nome": receita.nome,
                        "tipo": receita.tipo,
                        "total_insumos": len(receita.insumos),
                        "custo_total": receita.custo_total,
                        "valor_total": receita.valor_total,
                        "insumos_nao_encontrados": len(insumos_faltando),
                        "insumos_faltando": [
                            {
                                "nome": ins.nome,
                                "quantidade": ins.quantidade,
                                "unidade": ins.unidade
                            }
                            for ins in insumos_faltando
                        ]
                    })
                
                # Contar estatísticas
                for ins in receita.insumos:
                    if ins.tipo_match == "EXATO":
                        resultado["estatisticas"]["insumos_matched_exato"] += 1
                    elif ins.tipo_match == "FUZZY":
                        resultado["estatisticas"]["insumos_matched_fuzzy"] += 1
                    elif ins.tipo_match == "NAO_ENCONTRADO":
                        resultado["estatisticas"]["insumos_nao_encontrados"] += 1
            
            return resultado
            
        except Exception as e:
            raise ValueError(f"Erro ao processar arquivo: {str(e)}")
    
    # ========================================================================
    # IDENTIFICAR RECEITAS NO DATAFRAME
    # ========================================================================
    
    def _identificar_receitas(self, df: pd.DataFrame) -> List[ReceitaImportacao]:
        """
        Identifica as receitas e seus insumos no DataFrame.
        Receitas começam com 'Composto:' ou 'Processado:'.
        
        Args:
            df: DataFrame do pandas com os dados
            
        Returns:
            Lista de ReceitaImportacao
        """
        receitas = []
        receita_atual = None
        
        for idx, row in df.iterrows():
            # Pegar primeira coluna
            primeira_coluna = str(row[0]) if pd.notna(row[0]) else ""
            
            # Verificar se é linha de receita (qualquer linha que comece com "Composto:" seguido de número)
            if primeira_coluna.startswith("Composto:"):
                # Salvar receita anterior se existir
                if receita_atual is not None:
                    receitas.append(receita_atual)
                
                # Extrair código e nome da receita
                # Padrão: "Composto: CODIGO - NOME" (com ou sem tipo no final)
                # Regex simplificado: pega código e todo o resto como nome
                match = re.search(r'Composto:\s*(\d+)\s*-\s*(.+)', primeira_coluna, re.IGNORECASE)
                
                if match:
                    codigo = int(match.group(1))  # Código da receita
                    nome_completo = match.group(2).strip()  # Nome pode incluir tipo no final
                    
                    # Remover tipo do nome se existir (PROCESSADO ou COMPOSTO no final)
                    # Exemplo: "TEMPERO SHARI - PROCESSADO" vira "TEMPERO SHARI"
                    nome = re.sub(r'\s*-\s*(PROCESSADO|COMPOSTO)\s*$', '', nome_completo, flags=re.IGNORECASE).strip()
                    
                    # Detectar tipo se existir, senão usar "COMPOSTO" como padrão
                    if re.search(r'PROCESSADO', nome_completo, re.IGNORECASE):
                        tipo = "PROCESSADO"
                    else:
                        tipo = "COMPOSTO"
                    
                    receita_atual = ReceitaImportacao(codigo, nome, tipo)
            
            # Verificar se é linha de insumo (tem código na coluna 1)
            elif receita_atual is not None and pd.notna(row[1]):
                try:
                    codigo_insumo = int(row[1])
                    nome_insumo = str(row[2]) if pd.notna(row[2]) else ""
                    quantidade = float(row[3]) if pd.notna(row[3]) else 0.0
                    
                    # Processar custo e valor (podem estar com R$)
                    custo = self._limpar_valor_moeda(row[4])
                    valor = self._limpar_valor_moeda(row[5])
                    unidade = str(row[6]).strip() if pd.notna(row[6]) else ""
                    
                    # Criar insumo
                    insumo = InsumoReceita(
                        codigo=codigo_insumo,
                        nome=nome_insumo,
                        quantidade=quantidade,
                        unidade=unidade,
                        custo=custo,
                        valor=valor
                    )
                    
                    receita_atual.insumos.append(insumo)
                    
                except (ValueError, TypeError):
                    # Linha não é insumo válido, continuar
                    pass
            
            # Verificar se é linha de totais (custo e valor total da receita)
            elif receita_atual is not None and pd.notna(row[4]) and pd.notna(row[5]):
                custo_str = str(row[4])
                valor_str = str(row[5])
                
                if custo_str.startswith("R$") and valor_str.startswith("R$"):
                    receita_atual.custo_total = self._limpar_valor_moeda(row[4])
                    receita_atual.valor_total = self._limpar_valor_moeda(row[5])
        
        # Adicionar última receita
        if receita_atual is not None:
            receitas.append(receita_atual)
        
        return receitas
    
    # ========================================================================
    # MATCHING DE INSUMOS
    # ========================================================================
    
    def _processar_matching_insumos(self, receitas: List[ReceitaImportacao]):
        """
        Processa matching de todos os insumos de todas as receitas.
        
        Args:
            receitas: Lista de receitas a processar
        """
        for receita in receitas:
            for insumo in receita.insumos:
                # Buscar insumo no banco
                self._fazer_matching_insumo(insumo)
    
    def _fazer_matching_insumo(self, insumo: InsumoReceita):
        """
        Faz matching de um insumo com o banco de dados.
        Tenta: 1) Match exato, 2) Match por código, 3) Match fuzzy.
        
        Args:
            insumo: Insumo a fazer matching
        """
        # ETAPA 1: Tentar match por código
        if insumo.codigo:
            # Converter código para string pois a coluna é VARCHAR
            insumo_db = self.db.query(Insumo).filter(
                Insumo.restaurante_id == self.restaurante_id,
                Insumo.codigo == str(insumo.codigo)
            ).first()
            
            if insumo_db:
                insumo.insumo_id_matched = insumo_db.id
                insumo.tipo_match = "EXATO"
                insumo.score_similaridade = 100.0
                return
        
        # ETAPA 2: Tentar match exato por nome (normalizado)
        nome_normalizado = self._normalizar_nome(insumo.nome)
        
        # Buscar todos insumos do restaurante e comparar nome normalizado
        todos_insumos = self.db.query(Insumo).filter(
            Insumo.restaurante_id == self.restaurante_id
        ).all()

        insumo_db = None
        for insumo_candidato in todos_insumos:
            if self._normalizar_nome(insumo_candidato.nome) == nome_normalizado:
                insumo_db = insumo_candidato
                break
        
        if insumo_db:
            insumo.insumo_id_matched = insumo_db.id
            insumo.tipo_match = "EXATO"
            insumo.score_similaridade = 100.0
            return
        
        # ETAPA 3: Tentar match fuzzy (similaridade >= 85%)
        todos_insumos = self.db.query(Insumo).filter(
            Insumo.restaurante_id == self.restaurante_id
        ).all()
        
        melhor_match = None
        melhor_score = 0.0
        
        for insumo_db in todos_insumos:
            score = self._calcular_similaridade(
                nome_normalizado, 
                self._normalizar_nome(insumo_db.nome)
            )
            
            if score > melhor_score:
                melhor_score = score
                melhor_match = insumo_db
        
        # Se encontrou match com score >= 85%
        if melhor_score >= 85.0:
            insumo.insumo_id_matched = melhor_match.id
            insumo.tipo_match = "FUZZY"
            insumo.score_similaridade = melhor_score
        else:
            # Não encontrou match
            insumo.tipo_match = "NAO_ENCONTRADO"
            insumo.score_similaridade = melhor_score
    
    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================
    
    def _normalizar_nome(self, nome: str) -> str:
        """
        Normaliza nome para comparação.
        Remove espaços extras, lowercase, acentos.
        """
        if not nome:
            return ""
        
        # Lowercase e remover espaços extras
        nome = nome.lower().strip()
        nome = re.sub(r'\s+', ' ', nome)
        
        # Remover acentos
        nome = (nome
                .replace('á', 'a').replace('à', 'a').replace('ã', 'a')
                .replace('é', 'e').replace('ê', 'e')
                .replace('í', 'i')
                .replace('ó', 'o').replace('ô', 'o').replace('õ', 'o')
                .replace('ú', 'u').replace('ü', 'u')
                .replace('ç', 'c'))
        
        return nome
    
    def _calcular_similaridade(self, texto1: str, texto2: str) -> float:
        """
        Calcula similaridade entre dois textos usando SequenceMatcher.
        
        Returns:
            Score de 0 a 100
        """
        ratio = SequenceMatcher(None, texto1, texto2).ratio()
        return round(ratio * 100, 2)
    
    def _limpar_valor_moeda(self, valor) -> float:
        """
        Remove formatação de moeda e converte para float.
        Ex: 'R$ 145,50' -> 145.50
        """
        if pd.isna(valor):
            return 0.0
        
        valor_str = str(valor)
        
        # Remover R$, espaços
        valor_str = valor_str.replace('R$', '').strip()
        
        # Remover pontos de milhar e trocar vírgula por ponto
        valor_str = valor_str.replace('.', '').replace(',', '.')
        
        try:
            return float(valor_str)
        except ValueError:
            return 0.0