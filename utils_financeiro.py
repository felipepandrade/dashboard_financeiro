"""
utils_financeiro.py
===================
Utilitários focados em análise financeira: ETL, validação, forecasting e IA.

Autor: Sistema de Análise Financeira
Versão: 2.0.0 (Standalone)
"""

# =============================================================================
# 1. IMPORTAÇÕES
# =============================================================================

# --- Padrão e Sistema ---
from typing import List, Tuple, Dict, Optional, Union
from datetime import datetime, timedelta
from io import BytesIO
import warnings
import os

import pandas as pd
import numpy as np
import streamlit as st

# --- Validação de Dados ---
import pandera as pa
from pandera import Column, Check, DataFrameSchema

# --- Análise de Série Temporal ---
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
import matplotlib.pyplot as plt

# --- Visualização ---
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- IA e ML ---
import google.generativeai as genai
from openai import OpenAI
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, mean_absolute_error
from sklearn.linear_model import LinearRegression

warnings.filterwarnings('ignore')

# =============================================================================
# 2. CONFIGURAÇÕES GLOBAIS
# =============================================================================

ABAS_PROCESSAR = [
    'ITABUNA', 'CAMAÇARI', 'CATU', 'ECOMP CATU', 'ATALAIA', 'PILAR'
]

MESES_ORDEM = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN',
               'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

MESES_NUM_MAP = {mes: i+1 for i, mes in enumerate(MESES_ORDEM)}

# =============================================================================
# 3. FUNÇÕES DE ETL FINANCEIRO
# =============================================================================

def _standardize_string(text):
    """
    Normaliza uma string: converte para minúsculas, remove acentos,
    caracteres especiais e substitui espaços por underscores.
    """
    import unicodedata
    import re
    if pd.isna(text):
        return ""
    text_str = str(text)
    normalized_text = unicodedata.normalize('NFD', text_str).encode('ascii', 'ignore').decode('utf-8')
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', normalized_text.lower().strip())
    return re.sub(r'\s+', '_', clean_text)


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica padronização de strings a todos os nomes de colunas."""
    if df is None or df.empty:
        return df
    df.columns = [_standardize_string(col) for col in df.columns]
    return df


@st.cache_data(show_spinner="Processando P&L...")
def processar_pl_baseal(uploaded_file, ano: int = None) -> pd.DataFrame:
    """
    Processa a aba 'P&L BASEAL' do arquivo financeiro.
    
    Args:
        uploaded_file: Arquivo Excel carregado via Streamlit
        ano: Ano de referência dos dados (default: ano atual)
        
    Returns:
        DataFrame processado com colunas: 
        [data, ano, mes, mes_num, conta_contabil, tipo_valor, valor, 
         codigo_centro_gasto, centro_gasto_nome]
    """
    if not uploaded_file:
        return pd.DataFrame()
    
    # Definir ano padrão se não informado
    if ano is None:
        ano = datetime.now().year
    
    try:
        df = pd.read_excel(uploaded_file, sheet_name='P&L BASEAL', skiprows=15, header=0)
        df.fillna(0, inplace=True)
        
        # Renomear colunas iniciais
        df.rename(columns={
            df.columns[0]: 'codigo_centro_gasto', 
            df.columns[2]: 'conta_contabil'
        }, inplace=True)
        
        # Contas financeiras adicionais
        contas_financeiras = [
            "Gross Sales - Basic Services", "Gross Sales - Eventual Services",
            "Sales tax - Basic", "Sales tax - Eventual", "Net Revenue",
            "Gross profit", "Gross margin (%)", "Cost of Sales"
        ]
        
        # Separar custos e financeiro
        df_custos = df[df['codigo_centro_gasto'] != 0].copy()
        df_financeiro = df[
            (df['codigo_centro_gasto'] == 0) & 
            (df['conta_contabil'].isin(contas_financeiras))
        ].copy()
        
        # Padronizar código centro de custo
        df_custos['codigo_centro_gasto'] = (
            df_custos['codigo_centro_gasto']
            .astype(str)
            .str.replace(r'\.0$', '', regex=True)
            .apply(lambda x: '0' + x if len(x) == 10 else x)
        )
        
        # Mapeamento centro de custo
        mapa_centro_custo = {
            '01020504001': 'Gerência Regional BA',
            '1020504001': 'Gerência Regional BA',
            '01020504101': 'Coordenação Catu',
            '1020504101': 'Coordenação Catu',
            '01020504102': 'ECOMP CATU - BA',
            '1020504102': 'ECOMP CATU - BA',
            '01020504204': 'BASE CATU - BA',
            '1020504204': 'BASE CATU - BA',
            '01020504201': 'Coordenação Estacionário BA',
            '1020504201': 'Coordenação Estacionário BA',
            '01020504202': 'BASE CAMAÇARI - BA',
            '1020504202': 'BASE CAMAÇARI - BA',
            '01020504203': 'BASE ITABUNA - BA',
            '1020504203': 'BASE ITABUNA - BA',
            '01020505201': 'Coordenação Estacionar SE/AL',
            '1020505201': 'Coordenação Estacionar SE/AL',
            '01020505202': 'BASE ATALAIA - SE',
            '1020505202': 'BASE ATALAIA - SE',
            '01020505203': 'BASE PILAR - AL',
            '1020505203': 'BASE PILAR - AL'
        }
        
        df_custos['centro_gasto_nome'] = df_custos['codigo_centro_gasto'].map(mapa_centro_custo)
        
        # Concatenar custos e financeiro
        df_processado = pd.concat([df_custos, df_financeiro], ignore_index=True)
        
        # Colunas identificadoras
        colunas_identificadoras = ['codigo_centro_gasto', 'centro_gasto_nome', 'conta_contabil']
        
        # Mapeamento de colunas de mês
        mapa_colunas_mes = {
            'JAN': {3: 'Realizado', 4: 'Budget V1', 6: 'Budget V3', 7: 'LY - Actual'},
            'FEV': {8: 'Realizado', 9: 'Budget V1', 11: 'Budget V3', 12: 'LY - Actual'},
            'MAR': {13: 'Realizado', 14: 'Budget V1', 16: 'Budget V3', 17: 'LY - Actual'},
            'ABR': {18: 'Realizado', 19: 'Budget V1', 21: 'Budget V3', 22: 'LY - Actual'},
            'MAI': {23: 'Realizado', 24: 'Budget V1', 26: 'Budget V3', 27: 'LY - Actual'},
            'JUN': {28: 'Realizado', 29: 'Budget V1', 31: 'Budget V3', 32: 'LY - Actual'},
            'JUL': {33: 'Realizado', 34: 'Budget V1', 36: 'Budget V3', 37: 'LY - Actual'},
            'AGO': {38: 'Realizado', 39: 'Budget V1', 41: 'Budget V3', 42: 'LY - Actual'},
            'SET': {43: 'Realizado', 44: 'Budget V1', 46: 'Budget V3', 47: 'LY - Actual'},
            'OUT': {48: 'Realizado', 49: 'Budget V1', 51: 'Budget V3', 52: 'LY - Actual'},
            'NOV': {53: 'Realizado', 54: 'Budget V1', 56: 'Budget V3', 57: 'LY - Actual'},
            'DEZ': {58: 'Realizado', 59: 'Budget V1', 61: 'Budget V3', 62: 'LY - Actual'}
        }
        
        lista_dfs_meses = []
        
        for mes, mapa_indices in mapa_colunas_mes.items():
            cols_id_existentes = [col for col in colunas_identificadoras if col in df_processado.columns]
            cols_idx_existentes = [df_processado.columns[i] for i in mapa_indices.keys() if i < len(df_processado.columns)]
            
            df_mes_temp = df_processado[cols_id_existentes + cols_idx_existentes].copy()
            
            mapa_rename = {
                df_processado.columns[i]: nome_final 
                for i, nome_final in mapa_indices.items() 
                if i < len(df_processado.columns)
            }
            df_mes_temp.rename(columns=mapa_rename, inplace=True)
            df_mes_temp['mes'] = mes
            
            value_vars_existentes = [v for v in mapa_rename.values() if v in df_mes_temp.columns]
            id_vars_melt = cols_id_existentes + ['mes']
            
            df_melted = df_mes_temp.melt(
                id_vars=id_vars_melt,
                value_vars=value_vars_existentes,
                var_name='tipo_valor',
                value_name='valor'
            )
            lista_dfs_meses.append(df_melted)
        
        if not lista_dfs_meses:
            st.error("P&L: Nenhuma coluna de mês/valor encontrada.")
            return pd.DataFrame()
        
        df_final = pd.concat(lista_dfs_meses, ignore_index=True)
        df_final['mes_num'] = df_final['mes'].map(MESES_NUM_MAP)
        df_final['ano'] = ano
        df_final['data'] = pd.to_datetime(
            dict(year=df_final['ano'], month=df_final['mes_num'], day=1)
        )
        df_final['valor'] = pd.to_numeric(df_final['valor'], errors='coerce').fillna(0)
        
        return df_final
        
    except Exception as e:
        st.error(f"Erro ao processar P&L: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner="Processando Razão de Gastos...")
def processar_razao_gastos(uploaded_file) -> pd.DataFrame:
    """
    Processa a aba 'Razão_Gastos'
    (Versão completa do 'utils - old.py' fornecida pelo usuário)
    """
    if not uploaded_file:
        return pd.DataFrame()
    try:
        # Tenta ler a aba específica. Se não existir, retorna DF vazio.
        try:
            df = pd.read_excel(uploaded_file, sheet_name='Razão_Gastos', header=1)
        except ValueError:
            st.sidebar.warning("Aba 'Razão_Gastos' não encontrada no arquivo P&L.")
            return pd.DataFrame()
            
        df = _standardize_columns(df)
        
        RENAME_MAP = {
            'valor_credito': 'valor', # Padronizado de 'VALOR CRÉDITO'
            'nome_do_fornecedor': 'fornecedor' # Padronizado de 'Nome do Fornecedor'
            # Adicionar outros mapeamentos se necessário
        }
        df.rename(columns=RENAME_MAP, inplace=True)
        
        # Processa centro de gasto se a coluna existir (padronizado de 'CENTRO GASTO')
        if 'centro_gasto' in df.columns:
            df.rename(columns={'centro_gasto': 'codigo_centro_gasto'}, inplace=True)
            df['codigo_centro_gasto'] = df['codigo_centro_gasto'].astype(str).str.replace(r'\.0$', '', regex=True)
            df['codigo_centro_gasto'] = df['codigo_centro_gasto'].apply(lambda x: '0' + x if len(x) == 10 else x)
            
            # Mapa de centro de custo (o mesmo do P&L)
            mapa_centro_custo = {
                '01020504001': 'Gerência Regional BA', '1020504001': 'Gerência Regional BA',
                '01020504101': 'Coordenação Catu', '1020504101': 'Coordenação Catu',
                '01020504102': 'ECOMP CATU - BA', '1020504102': 'ECOMP CATU - BA',
                '01020504204': 'BASE CATU - BA', '1020504204': 'BASE CATU - BA',
                '01020504201': 'Coordenação Estacionário BA', '1020504201': 'Coordenação Estacionário BA',
                '01020504202': 'BASE CAMAÇARI - BA', '1020504202': 'BASE CAMAÇARI - BA',
                '01020504203': 'BASE ITABUNA - BA', '1020504203': 'BASE ITABUNA - BA',
                '01020505201': 'Coordenação Estacionar SE/AL', '1020505201': 'Coordenação Estacionar SE/AL',
                '01020505202': 'BASE ATALAIA - SE', '1020505202': 'BASE ATALAIA - SE',
                '01020505203': 'BASE PILAR - AL', '1020505203': 'BASE PILAR - AL'
            }
            df['centro_gasto_nome'] = df['codigo_centro_gasto'].map(mapa_centro_custo)
        else:
            st.warning("Razão: Coluna 'centro_gasto' não encontrada. Análise por centro de custo pode falhar.")
            df['centro_gasto_nome'] = 'N/A' # Cria coluna para evitar erros

        # Garante que a coluna 'valor' exista
        if 'valor' in df.columns:
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
        else:
            st.warning("Razão: Coluna 'valor' (de 'valor_credito') não encontrada. Gastos de fornecedores serão zero.")
            df['valor'] = 0 
            
        # Garante que a coluna 'fornecedor' exista
        if 'fornecedor' not in df.columns:
             st.warning("Razão: Coluna 'fornecedor' (de 'nome_do_fornecedor') não encontrada.")
             df['fornecedor'] = 'N/A'
             
        return df

    except Exception as e:
        st.error(f"Erro crítico ao processar a aba 'Razão_Gastos': {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner="Processando aba de orçamento...")
def processar_aba_orcamento(
    uploaded_file,
    sheet_name: str,
    ano_referencia: int = 2025
) -> pd.DataFrame:
    # ... código mantido, só para garantir integridade do replace ...
    # Mas como 'processar_pl_baseal' termina na 228, e eu estou substituindo até a 1323...
    # PERAÍ, EU NÃO POSSO SUBSTITUIR O ARQUIVO INTEIRO DE 88 A 1323. É MUITO CÓDIGO.
    # Vou fazer replaces menores.
    pass

# FIM DA TENTATIVA ERRADA. NÃO SUBMETER ISSO.



@st.cache_data(show_spinner="Processando Razão de Gastos...")
def processar_razao_gastos(uploaded_file) -> pd.DataFrame:
    """
    Processa a aba 'Razão_Gastos'
    (Versão completa do 'utils - old.py' fornecida pelo usuário)
    """
    if not uploaded_file:
        return pd.DataFrame()
    try:
        # Tenta ler a aba específica. Se não existir, retorna DF vazio.
        try:
            df = pd.read_excel(uploaded_file, sheet_name='Razão_Gastos', header=1)
        except ValueError:
            st.sidebar.warning("Aba 'Razão_Gastos' não encontrada no arquivo P&L.")
            return pd.DataFrame()
            
        df = _standardize_columns(df)
        
        RENAME_MAP = {
            'valor_credito': 'valor', # Padronizado de 'VALOR CRÉDITO'
            'nome_do_fornecedor': 'fornecedor' # Padronizado de 'Nome do Fornecedor'
            # Adicionar outros mapeamentos se necessário
        }
        df.rename(columns=RENAME_MAP, inplace=True)
        
        # Processa centro de gasto se a coluna existir (padronizado de 'CENTRO GASTO')
        if 'centro_gasto' in df.columns:
            df.rename(columns={'centro_gasto': 'codigo_centro_gasto'}, inplace=True)
            df['codigo_centro_gasto'] = df['codigo_centro_gasto'].astype(str).str.replace(r'\.0$', '', regex=True)
            df['codigo_centro_gasto'] = df['codigo_centro_gasto'].apply(lambda x: '0' + x if len(x) == 10 else x)
            
            # Mapa de centro de custo (o mesmo do P&L)
            mapa_centro_custo = {
                '01020504001': 'Gerência Regional BA', '1020504001': 'Gerência Regional BA',
                '01020504101': 'Coordenação Catu', '1020504101': 'Coordenação Catu',
                '01020504102': 'ECOMP CATU - BA', '1020504102': 'ECOMP CATU - BA',
                '01020504204': 'BASE CATU - BA', '1020504204': 'BASE CATU - BA',
                '01020504201': 'Coordenação Estacionário BA', '1020504201': 'Coordenação Estacionário BA',
                '01020504202': 'BASE CAMAÇARI - BA', '1020504202': 'BASE CAMAÇARI - BA',
                '01020504203': 'BASE ITABUNA - BA', '1020504203': 'BASE ITABUNA - BA',
                '01020505201': 'Coordenação Estacionar SE/AL', '1020505201': 'Coordenação Estacionar SE/AL',
                '01020505202': 'BASE ATALAIA - SE', '1020505202': 'BASE ATALAIA - SE',
                '01020505203': 'BASE PILAR - AL', '1020505203': 'BASE PILAR - AL'
            }
            df['centro_gasto_nome'] = df['codigo_centro_gasto'].map(mapa_centro_custo)
        else:
            st.warning("Razão: Coluna 'centro_gasto' não encontrada. Análise por centro de custo pode falhar.")
            df['centro_gasto_nome'] = 'N/A' # Cria coluna para evitar erros

        # Garante que a coluna 'valor' exista
        if 'valor' in df.columns:
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
        else:
            st.warning("Razão: Coluna 'valor' (de 'valor_credito') não encontrada. Gastos de fornecedores serão zero.")
            df['valor'] = 0 
            
        # Garante que a coluna 'fornecedor' exista
        if 'fornecedor' not in df.columns:
             st.warning("Razão: Coluna 'fornecedor' (de 'nome_do_fornecedor') não encontrada.")
             df['fornecedor'] = 'N/A'
             
        return df

    except Exception as e:
        st.error(f"Erro crítico ao processar a aba 'Razão_Gastos': {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner="Processando aba de orçamento...")
def processar_aba_orcamento(
    uploaded_file,
    sheet_name: str,
    ano_referencia: int = 2025
) -> pd.DataFrame:  
    try:
        # 1. Ler o arquivo com o cabeçalho na linha 2 (índice 1)
        if hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(0)
        
        df_raw = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=1) 

        # 2. Definir o mapeamento fixo de colunas (baseado no input do usuário)
        original_columns = df_raw.columns.tolist()

        # A=0, B=1, ..., F=5, G=6, ..., BB=53
        if len(original_columns) < 54:
            st.warning(f"Orçamento: Estrutura inesperada na aba {sheet_name}. Menos de 54 colunas (A-BB) encontradas. Pulando aba.")
            return pd.DataFrame()

        # Mapeamento dos metadados (A-F)
        col_map = {
            original_columns[0]: 'centro_gasto_descricao',
            original_columns[1]: 'servico_consumo',
            original_columns[2]: 'codigo_conta',
            original_columns[3]: 'descricao_conta',
            original_columns[4]: 'tipo_gasto',
            original_columns[5]: 'fornecedor',
        }
        
        # Mapeamento dos meses (G-BB)
        col_idx = 6
        for mes in MESES_ORDEM:
            if col_idx + 3 >= len(original_columns):
                break
            col_map[original_columns[col_idx]] = f"{mes}_PREVISTO"
            col_map[original_columns[col_idx+1]] = f"{mes}_REALIZADO"
            col_map[original_columns[col_idx+2]] = f"{mes}_DIFERENCA"
            col_map[original_columns[col_idx+3]] = f"{mes}_PERCENTUAL"
            col_idx += 4
        
        # 3. Selecionar apenas as colunas mapeadas e renomear
        df_renamed = df_raw[col_map.keys()].rename(columns=col_map)
        
        # 4. Filtrar linhas inválidas
        df_filtrado = df_renamed[
            df_renamed['fornecedor'].notna() & 
            (df_renamed['fornecedor'] != 'Fornecedor')
        ].copy()
        
        if df_filtrado.empty:
            st.warning(f"Orçamento: Nenhum dado válido após filtro na aba {sheet_name}.")
            return pd.DataFrame()
            
        df_filtrado['base_operacional'] = sheet_name
        df_filtrado['ano'] = ano_referencia
        
        linhas_long = []
        
        meta_cols = [
            'base_operacional', 'ano', 'centro_gasto_descricao', 'servico_consumo', 
            'codigo_conta', 'descricao_conta', 'tipo_gasto', 'fornecedor'
        ]
        
        # 5. Pivotar (wide para long)
        for _, row in df_filtrado.iterrows():
            for mes in MESES_ORDEM:
                col_prev = f"{mes}_PREVISTO"
                col_real = f"{mes}_REALIZADO"
                col_diff = f"{mes}_DIFERENCA"
                col_pct = f"{mes}_PERCENTUAL"

                try:
                    previsto = pd.to_numeric(row[col_prev], errors='coerce')
                    realizado = pd.to_numeric(row[col_real], errors='coerce')
                    diferenca = pd.to_numeric(row[col_diff], errors='coerce')
                    percentual = pd.to_numeric(row[col_pct], errors='coerce')

                    if pd.isna(previsto) and pd.isna(realizado):
                        continue

                    previsto = 0.0 if pd.isna(previsto) else float(previsto)
                    realizado = 0.0 if pd.isna(realizado) else float(realizado)
                    
                    if pd.isna(diferenca):
                        diferenca = realizado - previsto
                    else:
                        diferenca = float(diferenca)
                    
                    if pd.isna(percentual):
                        percentual = (diferenca / previsto * 100) if previsto != 0 else 0.0
                    else:
                        percentual = float(percentual)

                    nova_linha = {
                        'mes': mes,
                        'previsto': previsto,
                        'realizado': realizado,
                        'diferenca': diferenca,
                        'percentual_desvio': percentual
                    }
                    
                    for meta_col in meta_cols:
                        nova_linha[meta_col] = row.get(meta_col, 'N/A')

                    linhas_long.append(nova_linha)
                    
                except KeyError:
                    break
                except Exception as e_inner:
                    st.warning(f"Orçamento: Erro ao processar linha para mês {mes} na aba {sheet_name}: {e_inner}")
                    continue

        return pd.DataFrame(linhas_long)
    
    except Exception as e:
        st.error(f"Erro geral ao processar aba de orçamento '{sheet_name}': {str(e)}")
        return pd.DataFrame()


@st.cache_data(show_spinner="Processando Acompanhamento de Orçamento...")
def processar_acompanhamento_orcamento_completo(
    uploaded_file,
    ano_referencia: int = 2025
) -> pd.DataFrame:
    """
    Processa todas as abas do arquivo e consolida em um único DataFrame.
    """
    dfs_consolidados = []
    
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        abas_disponiveis = excel_file.sheet_names
        abas_a_processar = [aba for aba in ABAS_PROCESSAR if aba in abas_disponiveis]
    except Exception as e:
        st.error(f"Não foi possível ler as abas do arquivo Excel: {e}")
        return pd.DataFrame()

    if not abas_a_processar:
        st.error(f"Nenhuma das abas esperadas ({', '.join(ABAS_PROCESSAR)}) foi encontrada no arquivo.")
        return pd.DataFrame()

    st.info(f"📋 Processando {len(abas_a_processar)} abas encontradas...")
    progress_bar = st.progress(0)
    
    for idx, aba in enumerate(abas_a_processar):
        try:
            uploaded_file.seek(0)
            df_aba = processar_aba_orcamento(uploaded_file, aba, ano_referencia)
            
            if not df_aba.empty:
                dfs_consolidados.append(df_aba)
            else:
                st.warning(f"⚠️ {aba}: Nenhum dado válido encontrado após processamento")
        
        except Exception as e:
            st.error(f"❌ Erro na aba '{aba}': {str(e)}")
        
        progress_bar.progress((idx + 1) / len(abas_a_processar))
    
    if not dfs_consolidados:
        st.error("❌ Nenhuma aba foi processada com sucesso ou continha dados válidos.")
        return pd.DataFrame()
    
    df_final = pd.concat(dfs_consolidados, ignore_index=True)
    df_final = limpar_e_enriquecer_dados(df_final)
    
    st.success(f"✅ **Total consolidado (Orçamento): {len(df_final):,} registros de {len(dfs_consolidados)} bases**")
    
    return df_final


def limpar_e_enriquecer_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa, padroniza e adiciona métricas calculadas ao DataFrame de Orçamento."""
    df = df.copy()
    
    colunas_string = ['fornecedor', 'servico_consumo', 'descricao_conta', 
                      'tipo_gasto', 'centro_gasto_descricao']
    for col in colunas_string:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper().replace('NAN', 'N/A')
    
    if 'codigo_conta' in df.columns:
        df['codigo_centro_gasto'] = df['codigo_conta'].apply(
            lambda x: str(int(x)).zfill(11) if pd.notna(x) and isinstance(x, (int, float)) and x != 0 else 'N/A'
        )
    else:
        df['codigo_centro_gasto'] = 'N/A'

    df['aderencia_orcamento'] = np.where(
        df['previsto'] != 0,
        (df['realizado'] / df['previsto']) * 100,
        np.nan
    )
    
    def classificar_desvio(row):
        aderencia = row['aderencia_orcamento']
        if pd.isna(aderencia):
            if row['realizado'] == 0:
                return 'ZERO_PREV_REAL'
            else:
                return 'SEM_PREVISAO'
        
        if aderencia <= 90: return 'ABAIXO_10'
        elif 90 < aderencia <= 110: return 'DENTRO_META'
        elif 110 < aderencia <= 120: return 'ACIMA_10_20'
        else: return 'CRITICO_20'
    
    df['status_desvio'] = df.apply(classificar_desvio, axis=1)
    
    if 'ano' in df.columns and 'mes' in df.columns:
        df['mes_num'] = df['mes'].map(MESES_NUM_MAP)
        df_valid_dates = df.dropna(subset=['ano', 'mes_num'])
        df['data'] = pd.to_datetime(
            dict(year=df_valid_dates['ano'], month=df_valid_dates['mes_num'], day=1), errors='coerce'
        )
    else:
        st.warning("Orçamento: Colunas 'ano' ou 'mes' não encontradas para criar data.")
        df['data'] = pd.NaT

    df['desvio_significativo'] = (abs(df['diferenca']) > 5000)
    
    sort_cols = ['base_operacional', 'data', 'fornecedor']
    sort_cols_exist = [col for col in sort_cols if col in df.columns]
    if sort_cols_exist:
        df = df.sort_values(sort_cols_exist).reset_index(drop=True)
         
    required_final = ['base_operacional', 'fornecedor', 'servico_consumo', 'mes', 'ano', 'previsto', 'realizado', 'diferenca', 'status_desvio', 'data']
    for col in required_final:
        if col not in df.columns:
            st.error(f"Orçamento: Coluna essencial '{col}' não gerada na limpeza.")
            if col == 'data': df[col] = pd.NaT
            elif col in ['previsto', 'realizado', 'diferenca']: df[col] = 0.0
            else: df[col] = 'N/A'

    return df


# =============================================================================
# 4. VALIDAÇÃO DE DADOS (PANDERA)
# =============================================================================

# Schema para P&L
SCHEMA_PL = DataFrameSchema(
    columns={
        'codigo_centro_gasto': Column(str, nullable=True, coerce=True),
        'centro_gasto_nome': Column(str, nullable=True, coerce=True),
        'conta_contabil': Column(str, nullable=False, coerce=True),
        'mes': Column(str, checks=[Check.isin(MESES_ORDEM)], nullable=False, coerce=True),
        'tipo_valor': Column(
            str, 
            checks=[Check.isin(['Realizado', 'Budget V1', 'Budget V3', 'LY - Actual'])], 
            nullable=False, 
            coerce=True
        ),
        'valor': Column(float, checks=[Check.greater_than_or_equal_to(0)], nullable=False, coerce=True),
        'ano': Column(int, checks=[Check.in_range(2000, datetime.now().year + 5)], nullable=False, coerce=True),
        'data': Column(pa.DateTime, nullable=False, coerce=True)
    },
    strict=False,
    coerce=True
)

# Schema para Orçamento
SCHEMA_ORCAMENTO = DataFrameSchema(
    columns={
        'base_operacional': Column(str, checks=[Check.isin(ABAS_PROCESSAR)], nullable=False, coerce=True),
        'fornecedor': Column(str, nullable=False, coerce=True),
        'servico_consumo': Column(str, nullable=False, coerce=True),
        'mes': Column(str, checks=[Check.isin(MESES_ORDEM)], nullable=False, coerce=True),
        'ano': Column(int, checks=[Check.in_range(2020, 2030)], nullable=False, coerce=True),
        'previsto': Column(float, checks=[Check.greater_than_or_equal_to(0)], nullable=False, coerce=True),
        'realizado': Column(float, checks=[Check.greater_than_or_equal_to(0)], nullable=False, coerce=True),
        'diferenca': Column(float, nullable=False, coerce=True),
        'data': Column(pa.DateTime, nullable=False, coerce=True)
    },
    strict=False,
    coerce=True
)


class ValidadorDados:
    """Validador de dados financeiros usando Pandera."""
    
    def __init__(self):
        self.schemas = {
            'pl': SCHEMA_PL,
            'orcamento': SCHEMA_ORCAMENTO
        }
    
    def _formatar_erros(self, schema_errors: pa.errors.SchemaErrors) -> List[Dict]:
        """Formata erros do Pandera para exibição."""
        erros_detalhados = []
        if schema_errors.failure_cases is not None and not schema_errors.failure_cases.empty:
            for erro in schema_errors.failure_cases.itertuples():
                erros_detalhados.append({
                    'coluna': getattr(erro, 'column', 'DataFrame'),
                    'check': getattr(erro, 'check', 'N/A'),
                    'index': getattr(erro, 'index', 'N/A'),
                    'valor_falha': getattr(erro, 'failure_case', 'N/A')
                })
        return erros_detalhados
    
    def validar_pl(self, df: pd.DataFrame, lazy: bool = True) -> Tuple[bool, Optional[pd.DataFrame], Dict]:
        """Valida DataFrame de P&L."""
        try:
            df_validado = self.schemas['pl'].validate(df, lazy=lazy)
            relatorio = {
                'status': 'SUCESSO',
                'total_linhas': len(df),
                'linhas_validas': len(df_validado),
                'erros': []
            }
            return True, df_validado, relatorio
        except pa.errors.SchemaErrors as e:
            erros_fmt = self._formatar_erros(e)
            relatorio = {
                'status': 'FALHA',
                'total_linhas': len(df),
                'linhas_com_erro': len(e.failure_cases) if e.failure_cases is not None else 1,
                'erros': erros_fmt
            }
            return False, None, relatorio
    
    def validar_orcamento(self, df: pd.DataFrame, lazy: bool = True) -> Tuple[bool, Optional[pd.DataFrame], Dict]:
        """Valida DataFrame de Orçamento."""
        try:
            if 'data' not in df.columns:
                if all(col in df.columns for col in ['ano', 'mes']):
                    df['mes_num'] = df['mes'].map(MESES_NUM_MAP)
                    df['data'] = pd.to_datetime(
                        dict(year=df['ano'], month=df['mes_num'], day=1),
                        errors='coerce'
                    )
                else:
                    raise ValueError("Colunas 'ano' e 'mes' necessárias para criar 'data'.")
            
            df_validado = self.schemas['orcamento'].validate(df, lazy=lazy)
            relatorio = {
                'status': 'SUCESSO',
                'total_linhas': len(df),
                'linhas_validas': len(df_validado),
                'erros': []
            }
            return True, df_validado, relatorio
        except (pa.errors.SchemaErrors, ValueError) as e:
            erros_fmt = self._formatar_erros(e) if isinstance(e, pa.errors.SchemaErrors) else [{'erro': str(e)}]
            relatorio = {
                'status': 'FALHA',
                'total_linhas': len(df),
                'linhas_com_erro': len(df),
                'erros': erros_fmt
            }
            return False, None, relatorio
    
    def gerar_relatorio_qualidade(self, df: pd.DataFrame) -> Dict:
        """Gera relatório de qualidade dos dados."""
        if df is None or df.empty:
            return {'colunas': {}}
        
        relatorio = {
            'timestamp': datetime.now().isoformat(),
            'total_linhas': len(df),
            'total_colunas': len(df.columns),
            'colunas': {}
        }
        
        for col in df.columns:
            stats_col = {
                'tipo': str(df[col].dtype),
                'valores_nulos': int(df[col].isna().sum()),
                'percentual_nulos': float(df[col].isna().sum() / len(df) * 100 if len(df) > 0 else 0),
                'valores_unicos': int(df[col].nunique())
            }
            
            if pd.api.types.is_numeric_dtype(df[col]):
                series_no_nan = df[col].dropna()
                stats_col.update({
                    'min': float(series_no_nan.min()) if not series_no_nan.empty else None,
                    'max': float(series_no_nan.max()) if not series_no_nan.empty else None,
                    'media': float(series_no_nan.mean()) if not series_no_nan.empty else None,
                    'mediana': float(series_no_nan.median()) if not series_no_nan.empty else None,
                    'desvio_padrao': float(series_no_nan.std()) if not series_no_nan.empty else None
                })
            
            relatorio['colunas'][col] = stats_col
        
        return relatorio


# =============================================================================
# 5. FUNÇÕES DE ESTATÍSTICAS E EXPORTAÇÃO
# =============================================================================

def gerar_estatisticas_orcamento(df: pd.DataFrame) -> Dict:
    """Gera estatísticas do orçamento."""
    stats = {
        'total_previsto': df['previsto'].sum(),
        'total_realizado': df['realizado'].sum(),
        'percentual_execucao': (df['realizado'].sum() / df['previsto'].sum() * 100) if df['previsto'].sum() > 0 else 0,
        'desvios_criticos': len(df[abs(df['diferenca']) > (df['previsto'] * 0.2)])
    }
    return stats


def exportar_orcamento_csv(df: pd.DataFrame) -> str:
    """Exporta orçamento para CSV."""
    return df.to_csv(index=False).encode('utf-8')


# =============================================================================
# 6. VISUALIZAÇÕES AVANÇADAS
# =============================================================================

def plot_heatmap_desvios(df: pd.DataFrame) -> go.Figure:
    """Gera heatmap de desvios orçamentários."""
    df_heatmap = df.pivot_table(
        values='diferenca',
        index='base_operacional',
        columns='mes',
        aggfunc='sum'
    )
    df_heatmap = df_heatmap.reindex(columns=MESES_ORDEM)
    
    fig = go.Figure(data=go.Heatmap(
        z=df_heatmap.values,
        x=df_heatmap.columns,
        y=df_heatmap.index,
        colorscale='RdYlGn',
        zmid=0,
        text=df_heatmap.values,
        texttemplate='R$ %{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="Desvio (R$)")
    ))
    
    fig.update_layout(
        title="Heatmap de Desvios Orçamentários por Base e Mês",
        xaxis_title="Mês",
        yaxis_title="Base Operacional",
        height=400
    )
    
    return fig


def plot_stl_decomposition(df: pd.DataFrame, date_col: str, value_col: str) -> go.Figure:
    """Decomposição STL de série temporal."""
    df_sorted = df.sort_values(date_col)
    df_sorted.set_index(date_col, inplace=True)
    
    # Agregar valores duplicados
    df_sorted = df_sorted.groupby(level=0)[value_col].sum()
    
    # Decomposição
    decomposition = seasonal_decompose(df_sorted, model='additive', period=12, extrapolate_trend='freq')
    
    # Criar subplots
    fig = make_subplots(
        rows=4, cols=1,
        subplot_titles=('Original', 'Tendência', 'Sazonalidade', 'Resíduos'),
        vertical_spacing=0.08
    )
    
    fig.add_trace(go.Scatter(x=df_sorted.index, y=df_sorted.values, mode='lines', name='Original'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_sorted.index, y=decomposition.trend, mode='lines', name='Tendência'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_sorted.index, y=decomposition.seasonal, mode='lines', name='Sazonalidade'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df_sorted.index, y=decomposition.resid, mode='lines', name='Resíduos'), row=4, col=1)
    
    fig.update_layout(height=800, title_text="Decomposição STL da Série Temporal", showlegend=False)
    
    return fig


# =============================================================================
# 7. INTEGRAÇÃO COM IA
# =============================================================================

def get_ai_chat_response(messages: List[Dict], api_key: str, provider: str) -> str:
    """
    Envia prompt para IA e retorna resposta.
    
    Args:
        messages: Lista de mensagens no formato [{"role": "user", "content": "..."}]
        api_key: Chave de API
        provider: "Gemini (Google)" ou "Copilot (OpenAI GPT-4)"
        
    Returns:
        Resposta da IA como string
    """
    try:
        if "Gemini" in provider:
            genai.configure(api_key=api_key)
            
            # Selecionar modelo (Padrão 3 Pro, fallback para 3 Flash se solicitado)
            model_name = 'gemini-3-pro-preview'
            if 'Flash' in provider:
                model_name = 'gemini-3-flash-preview'
            
            # print(f"[DEBUG] Usando Modelo: {model_name}")
            model = genai.GenerativeModel(model_name)
            
            # Concatenar mensagens
            prompt = "\n".join([msg["content"] for msg in messages if msg["role"] == "user"])
            response = model.generate_content(prompt)
            return response.text
        
        elif "OpenAI" in provider or "Copilot" in provider:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content
        
        else:
            return "Provedor de IA não reconhecido."
    
    except Exception as e:
        return f"Erro ao consultar IA: {e}"


def gerar_analise_ia(df: pd.DataFrame, api_key: str, provider: str, contexto: str = "") -> str:
    """Gera análise financeira usando IA."""
    
    # Preparar resumo dos dados
    resumo = df.describe().to_string()
    
    prompt = f"""
    Você é um analista financeiro sênior especializado em gestão de O&M de gasodutos.
    
    Contexto: {contexto}
    
    Analise os dados financeiros abaixo e forneça:
    1. **Resumo Executivo** da performance financeira
    2. **Principais Insights** (top 3)
    3. **Recomendações Estratégicas** (top 3)
    4. **Alertas e Riscos** identificados
    
    Dados:
    ```
    {resumo}
    ```
    
    Formate sua resposta em Markdown com emojis para melhor visualização.
    """
    
    messages = [
        {"role": "system", "content": "Você é um analista financeiro especialista em O&M de gasodutos."},
        {"role": "user", "content": prompt}
    ]
    
    return get_ai_chat_response(messages, api_key, provider)




# =============================================================================
# 8. FORECASTING MATEMÁTICO (STREAMLIT CLOUD COMPATIBLE)
# =============================================================================

class SimpleForecaster:
    """Modelo de forecasting matemático usando extrapolação linear e médias móveis."""
    
    def __init__(self):
        self.model = None
        self.forecast = None
        self.method = None
        self.historical_data = None
        self.confidence_intervals = None
        
    def fit(self, df: pd.DataFrame, date_col: str, value_col: str, method='hybrid', **kwargs):
        """
        Treina o modelo de forecasting.
        
        Args:
            df: DataFrame com dados históricos
            date_col: Nome da coluna de data
            value_col: Nome da coluna de valores
            method: Método de forecasting ('linear', 'sma', 'ema', 'seasonal', 'hybrid')
            **kwargs: Parâmetros adicionais (window_size para médias móveis, etc.)
        """
        self.method = method
        self.date_col = date_col
        self.value_col = value_col
        
        # Ordenar por data
        df_sorted = df.sort_values(date_col).copy()
        self.historical_data = df_sorted
        
        # Armazenar série temporal
        self.dates = df_sorted[date_col].values
        self.values = df_sorted[value_col].values
        
        # Parâmetros do modelo
        self.window_size = kwargs.get('window_size', 3)
        self.alpha = kwargs.get('alpha', 0.3)  # Para EMA
        
    def _linear_trend(self, periods: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calcula tendência linear usando regressão."""
        X = np.arange(len(self.values)).reshape(-1, 1)
        y = self.values
        
        # Regressão linear
        model = LinearRegression()
        model.fit(X, y)
        
        # Previsões futuras
        future_X = np.arange(len(self.values), len(self.values) + periods).reshape(-1, 1)
        predictions = model.predict(future_X)
        
        # Intervalo de confiança baseado em desvio padrão dos resíduos
        residuals = y - model.predict(X)
        std_residuals = np.std(residuals)
        lower = predictions - 1.96 * std_residuals
        upper = predictions + 1.96 * std_residuals
        
        return predictions, lower, upper
    
    def _moving_average(self, periods: int, ma_type='sma') -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calcula médias móveis (Simple ou Exponential)."""
        if ma_type == 'sma':
            # Simple Moving Average
            last_values = self.values[-self.window_size:]
            prediction = np.mean(last_values)
            predictions = np.full(periods, prediction)
        else:
            # Exponential Moving Average
            ema = self.values[0]
            for val in self.values[1:]:
                ema = self.alpha * val + (1 - self.alpha) * ema
            predictions = np.full(periods, ema)
        
        # Intervalo de confiança baseado em desvio padrão
        std_values = np.std(self.values)
        lower = predictions - 1.96 * std_values
        upper = predictions + 1.96 * std_values
        
        return predictions, lower, upper
    
    def _seasonal_decompose(self, periods: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Decomposição sazonal + extrapolação de tendência."""
        # Preparar série temporal
        df_ts = self.historical_data.set_index(self.date_col)[self.value_col]
        
 # Decomposição
        try:
            decomposition = seasonal_decompose(df_ts, model='additive', period=min(12, len(df_ts)//2), extrapolate_trend='freq')
            
            # Extrair componentes
            trend = decomposition.trend.dropna()
            seasonal = decomposition.seasonal.dropna()
            
            # Extrapolar tendência linearmente
            X_trend = np.arange(len(trend)).reshape(-1, 1)
            model = LinearRegression()
            model.fit(X_trend, trend.values)
            
            future_X = np.arange(len(trend), len(trend) + periods).reshape(-1, 1)
            future_trend = model.predict(future_X)
            
            # Repetir padrão sazonal
            seasonal_pattern = seasonal.values[-12:] if len(seasonal) >= 12 else seasonal.values
            future_seasonal = np.tile(seasonal_pattern, (periods // len(seasonal_pattern) + 1))[:periods]
            
            # Combinar
            predictions = future_trend + future_seasonal
            
            # Intervalo de confiança
            residuals = decomposition.resid.dropna()
            std_residuals = np.std(residuals)
            lower = predictions - 1.96 * std_residuals
            upper = predictions + 1.96 * std_residuals
            
        except Exception as e:
            # Fallback para tendência linear simples
            predictions, lower, upper = self._linear_trend(periods)
        
        return predictions, lower, upper
    
    def _hybrid_forecast(self, periods: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Combina tendência linear com sazonalidade."""
        # Tendência linear
        linear_pred, _, _ = self._linear_trend(periods)
        
        # Componente sazonal
        try:
            df_ts = self.historical_data.set_index(self.date_col)[self.value_col]
            decomposition = seasonal_decompose(df_ts, model='additive', period=min(12, len(df_ts)//2), extrapolate_trend='freq')
            seasonal = decomposition.seasonal.dropna()
            
            # Repetir padrão sazonal
            seasonal_pattern = seasonal.values[-12:] if len(seasonal) >= 12 else seasonal.values
            future_seasonal = np.tile(seasonal_pattern, (periods // len(seasonal_pattern) + 1))[:periods]
            
            # Combinar
            predictions = linear_pred + future_seasonal
            
            # Intervalo de confiança
            residuals = decomposition.resid.dropna()
            std_residuals = np.std(residuals)
            lower = predictions - 1.96 * std_residuals
            upper = predictions + 1.96 * std_residuals
            
        except Exception:
            # Fallback para tendência linear
            predictions, lower, upper = self._linear_trend(periods)
        
        return predictions, lower, upper
    
    def predict(self, periods: int = 12) -> pd.DataFrame:
        """
        Gera previsões futuras.
        
        Args:
            periods: Número de períodos a prever
            
        Returns:
            DataFrame com previsões e intervalos de confiança
        """
        if self.method == 'linear':
            predictions, lower, upper = self._linear_trend(periods)
        elif self.method == 'sma':
            predictions, lower, upper = self._moving_average(periods, ma_type='sma')
        elif self.method == 'ema':
            predictions, lower, upper = self._moving_average(periods, ma_type='ema')
        elif self.method == 'seasonal':
            predictions, lower, upper = self._seasonal_decompose(periods)
        else:  # hybrid
            predictions, lower, upper = self._hybrid_forecast(periods)
        
        # Criar datas futuras
        last_date = pd.to_datetime(self.dates[-1])
        future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=periods, freq='MS')
        
        # DataFrame de resultados
        self.forecast = pd.DataFrame({
            'data': future_dates,
            'previsao': predictions,
            'limite_inferior': lower,
            'limite_superior': upper
        })
        
        return self.forecast
    
    def plot(self, df_hist: pd.DataFrame, date_col: str, value_col: str) -> go.Figure:
        """Plota histórico e previsões."""
        fig = go.Figure()
        
        # Histórico
        fig.add_trace(go.Scatter(
            x=df_hist[date_col],
            y=df_hist[value_col],
            mode='lines+markers',
            name='Histórico',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=4)
        ))
        
        if self.forecast is not None:
            # Previsão
            fig.add_trace(go.Scatter(
                x=self.forecast['data'],
                y=self.forecast['previsao'],
                mode='lines+markers',
                name='Previsão',
                line=dict(color='#d62728', width=2, dash='dash'),
                marker=dict(size=6)
            ))
            
            # Intervalo de confiança
            fig.add_trace(go.Scatter(
                x=self.forecast['data'],
                y=self.forecast['limite_superior'],
                mode='lines',
                name='IC Superior',
                line=dict(color='rgba(214, 39, 40, 0.3)', width=0),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=self.forecast['data'],
                y=self.forecast['limite_inferior'],
                mode='lines',
                name='IC Inferior',
                line=dict(color='rgba(214, 39, 40, 0.3)', width=0),
                fill='tonexty',
                fillcolor='rgba(214, 39, 40, 0.2)',
                showlegend=True
            ))
        
        # Layout
        method_names = {
            'linear': 'Tendência Linear',
            'sma': 'Média Móvel Simples',
            'ema': 'Média Móvel Exponencial',
            'seasonal': 'Decomposição Sazonal',
            'hybrid': 'Modelo Híbrido (Linear + Sazonal)'
        }
        
        fig.update_layout(
            title=f"Previsão Financeira - {method_names.get(self.method, 'Matemático')}",
            xaxis_title="Data",
            yaxis_title="Valor (R$)",
            hovermode='x unified',
            height=500,
            template='plotly_white'
        )
        
        return fig


# =============================================================================
# 9. INTERFACE DE FORECASTING (COMPONENTIZADA)
# =============================================================================

def criar_interface_forecasting_simples():
    """Interface Streamlit para Forecasting Matemático."""
    st.subheader("📈 Previsão Financeira (Modelo Matemático)")
    
    st.info("💡 **Modelo otimizado para Streamlit Cloud**: Utiliza extrapolação linear e médias móveis para previsões rápidas e interpretáveis.")
    
    if 'pl_df' not in st.session_state or st.session_state.pl_df is None:
        st.warning("⚠️ Carregue os dados de P&L primeiro.")
        return
    
    df = st.session_state.pl_df
    df_custos = df[df['codigo_centro_gasto'] != 0].copy()
    df_realizado = df_custos[df_custos['tipo_valor'] == 'Realizado'].groupby('data')['valor'].sum().reset_index()
    
    if len(df_realizado) < 3:
        st.error("❌ Dados insuficientes para previsão. Necessário pelo menos 3 períodos.")
        return
    
    # Configurações de previsão
    col1, col2, col3 = st.columns(3)
    
    with col1:
        method = st.selectbox(
            "Método de Previsão",
            options=['hybrid', 'linear', 'sma', 'ema', 'seasonal'],
            format_func=lambda x: {
                'linear': '📈 Tendência Linear',
                'sma': '📊 Média Móvel Simples',
                'ema': '📉 Média Móvel Exponencial',
                'seasonal': '🌊 Decomposição Sazonal',
                'hybrid': '🔮 Híbrido (Recomendado)'
            }[x],
            index=0
        )
    
    with col2:
        periods = st.number_input(
            "Períodos a Prever (meses)",
            min_value=1,
            max_value=24,
            value=12,
            help="Número de meses futuros para prever"
        )
    
    with col3:
        if method in ['sma', 'ema']:
            if method == 'sma':
                window_size = st.number_input(
                    "Janela da Média Móvel",
                    min_value=2,
                    max_value=12,
                    value=3,
                    help="Número de períodos para calcular a média"
                )
            else:
                alpha = st.slider(
                    "Alpha (EMA)",
                    min_value=0.1,
                    max_value=0.9,
                    value=0.3,
                    step=0.1,
                    help="Peso dos valores mais recentes"
                )
    
    # Botão de treinar
    if st.button("🚀 Gerar Previsão", type="primary"):
        with st.spinner("Gerando previsão..."):
            try:
                forecaster = SimpleForecaster()
                
                # Parâmetros
                kwargs = {}
                if method == 'sma':
                    kwargs['window_size'] = window_size
                elif method == 'ema':
                    kwargs['alpha'] = alpha
                
                # Treinar
                forecaster.fit(df_realizado, 'data', 'valor', method=method, **kwargs)
                forecast_df = forecaster.predict(periods=periods)
                
                # Salvar no session state
                st.session_state.simple_forecaster = forecaster
                st.session_state.simple_forecast = forecast_df
                
                st.success("✅ Previsão gerada com sucesso!")
                
            except Exception as e:
                st.error(f"❌ Erro ao gerar previsão: {e}")
                return
    
    # Exibir resultados
    if 'simple_forecast' in st.session_state:
        st.divider()
        st.subheader("📊 Resultados da Previsão")
        
        # Gráfico
        fig = st.session_state.simple_forecaster.plot(df_realizado, 'data', 'valor')
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela de previsões
        st.subheader("📋 Valores Previstos")
        
        df_display = st.session_state.simple_forecast.copy()
        df_display['data'] = df_display['data'].dt.strftime('%Y-%m')
        df_display['previsao'] = df_display['previsao'].apply(lambda x: f"R$ {x:,.2f}")
        df_display['limite_inferior'] = df_display['limite_inferior'].apply(lambda x: f"R$ {x:,.2f}")
        df_display['limite_superior'] = df_display['limite_superior'].apply(lambda x: f"R$ {x:,.2f}")
        
        df_display.columns = ['Mês', 'Previsão', 'Limite Inferior (95%)', 'Limite Superior (95%)']
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Estatísticas
        st.subheader("📈 Estatísticas")
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        previsao_media = st.session_state.simple_forecast['previsao'].mean()
        historico_media = df_realizado['valor'].mean()
        variacao = ((previsao_media - historico_media) / historico_media * 100) if historico_media != 0 else 0
        
        col_stat1.metric(
            "Média Prevista",
            f"R$ {previsao_media:,.2f}",
            delta=f"{variacao:+.1f}%"
        )
        col_stat2.metric(
            "Média Histórica",
            f"R$ {historico_media:,.2f}"
        )
        col_stat3.metric(
            "Total Previsto ({} meses)".format(periods),
            f"R$ {st.session_state.simple_forecast['previsao'].sum():,.2f}"
        )
        
        # Download
        st.divider()
        csv = st.session_state.simple_forecast.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Previsões (CSV)",
            data=csv,
            file_name=f"previsoes_{method}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )


# =============================================================================
# 10. INTEGRAÇÃO COM NOVA UI (HOME REFACTORED)
# =============================================================================

def verificar_status_dados() -> Dict:
    """Verifica status dos dados no session_state."""
    status = {
        'orcamento_ok': False,
        'orcamento_linhas': 0,
        'pl_ok': False,
        'pl_data': None,
        'mes_atual': datetime.now().strftime('%b/%Y').upper()
    }
    
    # Orçamento (Tenta carregar se não existir)
    if 'df_orc_proc' not in st.session_state:
        try:
            # Tentar carga automática default (opcional)
            pass
        except:
            pass

    if 'df_orc_proc' in st.session_state and not st.session_state['df_orc_proc'].empty:
        status['orcamento_ok'] = True
        status['orcamento_linhas'] = len(st.session_state['df_orc_proc'])
        
    if 'pl_df' in st.session_state and not st.session_state['pl_df'].empty:
        status['pl_ok'] = True
        try:
            max_date = st.session_state['pl_df']['data'].max()
            status['pl_data'] = max_date.strftime('%d/%m/%Y')
        except:
            status['pl_data'] = "Data Desconhecida"
            
    return status

def processar_upload_pl(uploaded_file, ano: int = None) -> Tuple[bool, str, Dict]:
    """
    Wrapper para processar upload de P&L com validação.
    Suporta múltiplos anos via merge no session_state.
    """
    if not uploaded_file:
        return False, "Nenhum arquivo enviado", {}
    
    if ano is None:
        ano = datetime.now().year
        
    try:
        # Processar com o ano informado
        df = processar_pl_baseal(uploaded_file, ano=ano)
        
        if not df.empty:
            # Lógica de Merge no Session State
            if 'pl_df' not in st.session_state or st.session_state['pl_df'] is None:
                st.session_state['pl_df'] = df
            else:
                # Remover dados existentes DESSE ano para evitar duplicação
                df_existente = st.session_state['pl_df']
                if 'ano' in df_existente.columns:
                    df_existente = df_existente[df_existente['ano'] != ano]
                
                # Concatenar
                st.session_state['pl_df'] = pd.concat([df_existente, df], ignore_index=True)
            
            # Gerar resumo acumulado
            df_atual = st.session_state['pl_df']
            anos_carregados = sorted(df_atual['ano'].unique().tolist()) if 'ano' in df_atual.columns else [ano]
            
            resumo = {
                'total_registros': len(df_atual),
                'anos': anos_carregados,
                'meses_por_ano': df_atual.groupby('ano')['mes'].nunique().to_dict(),
                'total_realizado': f"R$ {df_atual[df_atual['tipo_valor']=='Realizado']['valor'].sum():,.2f}"
            }
            st.session_state['pl_resumo_importacao'] = resumo
            
            return True, f"Importação de {ano} concluída. Anos carregados: {anos_carregados}", resumo
        else:
            return False, "Falha ao processar arquivo. Verifique o formato.", {}
    except Exception as e:
        return False, f"Erro ao processar: {e}", {}

def get_resumo_importacao():
    """Retorna resumo da última importação."""
    return st.session_state.get('pl_resumo_importacao', {})

