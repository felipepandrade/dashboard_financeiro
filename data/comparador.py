"""
data/comparador.py
==================
Módulo de comparação entre orçamento previsto e valores realizados.

Fornece funções para:
- Comparativo mensal (orçado vs realizado)
- Comparativo por centro de custo
- Comparativo por conta contábil
- Drill-down por ativo (hierarquia pai-filho)
- Cálculo de desvios e KPIs

Autor: Sistema Orçamentário 2026
Data: Janeiro/2026
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import streamlit as st

from data.referencias_manager import (
    carregar_orcamento_v1_2026,
    carregar_centros_gasto,
    carregar_contas_contabeis,
    COLUNAS_MESES_ORC_2026,
    MESES_ORDEM,
    ATIVOS_SEM_HIERARQUIA
)

from database.crud import (
    listar_lancamentos,
    obter_estatisticas_gerais
)


# =============================================================================
# CONSTANTES
# =============================================================================

# Mapear meses para colunas do orçamento
MES_PARA_COLUNA_ORC = {
    'JAN': 'jan/26', 'FEV': 'fev/26', 'MAR': 'mar/26',
    'ABR': 'abr/26', 'MAI': 'mai/26', 'JUN': 'jun/26',
    'JUL': 'jul/26', 'AGO': 'ago/26', 'SET': 'set/26',
    'OUT': 'out/26', 'NOV': 'nov/26', 'DEZ': 'dez/26'
}


# =============================================================================
# FUNÇÕES DE AGREGAÇÃO DO ORÇAMENTO
# =============================================================================

@st.cache_data(ttl=900)
def get_orcamento_agregado_por_mes() -> pd.DataFrame:
    """
    Agrega o orçamento V1 2026 por mês.
    
    Returns:
        DataFrame com colunas: mes, valor_orcado
    """
    df_orc = carregar_orcamento_v1_2026()
    
    if df_orc.empty:
        return pd.DataFrame(columns=['mes', 'valor_orcado'])
    
    # Agregar por mês
    dados = []
    for mes, coluna in MES_PARA_COLUNA_ORC.items():
        if coluna in df_orc.columns:
            total = df_orc[coluna].sum()
            dados.append({'mes': mes, 'valor_orcado': total})
    
    return pd.DataFrame(dados)


@st.cache_data(ttl=900)
def get_orcamento_por_centro(mes: str = None) -> pd.DataFrame:
    """
    Agrega o orçamento por centro de custo.
    
    Args:
        mes: Mês específico (JAN, FEV, etc.) ou None para total do ano
    
    Returns:
        DataFrame com: centro_gasto_codigo, ativo, valor_orcado
    """
    df_orc = carregar_orcamento_v1_2026()
    
    if df_orc.empty:
        return pd.DataFrame()
    
    # Determinar colunas de valor
    if mes:
        coluna = MES_PARA_COLUNA_ORC.get(mes.upper())
        if coluna and coluna in df_orc.columns:
            colunas_valor = [coluna]
        else:
            return pd.DataFrame()
    else:
        # Somar todos os meses
        colunas_valor = [c for c in MES_PARA_COLUNA_ORC.values() if c in df_orc.columns]
    
    # Padronizar código do centro
    df_orc['centro_gasto_codigo'] = df_orc['CENTRO DE GASTO'].astype(str).str.zfill(11)
    
    # Calcular valor orçado
    df_orc['valor_orcado'] = df_orc[colunas_valor].sum(axis=1)
    
    # Agregar por centro
    df_agrupado = df_orc.groupby(['centro_gasto_codigo', 'ATIVO CONTRATUAL']).agg({
        'valor_orcado': 'sum'
    }).reset_index()
    
    df_agrupado = df_agrupado.rename(columns={'ATIVO CONTRATUAL': 'ativo'})
    
    return df_agrupado


@st.cache_data(ttl=900)
def get_orcamento_por_conta(mes: str = None) -> pd.DataFrame:
    """
    Agrega o orçamento por conta contábil.
    
    Args:
        mes: Mês específico ou None para total do ano
    
    Returns:
        DataFrame com: conta_contabil_codigo, descricao, valor_orcado
    """
    df_orc = carregar_orcamento_v1_2026()
    
    if df_orc.empty:
        return pd.DataFrame()
    
    # Determinar colunas de valor
    if mes:
        coluna = MES_PARA_COLUNA_ORC.get(mes.upper())
        if coluna and coluna in df_orc.columns:
            colunas_valor = [coluna]
        else:
            return pd.DataFrame()
    else:
        colunas_valor = [c for c in MES_PARA_COLUNA_ORC.values() if c in df_orc.columns]
    
    # Calcular valor orçado
    df_orc['valor_orcado'] = df_orc[colunas_valor].sum(axis=1)
    
    # Agregar por conta
    df_agrupado = df_orc.groupby(['CÓDIGO CONTA CONTÁBIL', 'DESCRIÇÃO CONTA CONTÁBIL']).agg({
        'valor_orcado': 'sum'
    }).reset_index()
    
    df_agrupado = df_agrupado.rename(columns={
        'CÓDIGO CONTA CONTÁBIL': 'conta_contabil_codigo',
        'DESCRIÇÃO CONTA CONTÁBIL': 'descricao'
    })
    
    df_agrupado['conta_contabil_codigo'] = df_agrupado['conta_contabil_codigo'].astype(str)
    
    return df_agrupado


# =============================================================================
# FUNÇÕES DE AGREGAÇÃO DO REALIZADO
# =============================================================================

@st.cache_data(ttl=900)
def get_realizado_agregado_por_mes(ano: int = 2026) -> pd.DataFrame:
    """
    Agrega os lançamentos realizados por mês.
    
    Returns:
        DataFrame com: mes, valor_realizado
    """
    dados = []
    
    for mes in MESES_ORDEM:
        lancamentos = listar_lancamentos(ano=ano, mes=mes)
        total = sum(l['valor'] for l in lancamentos) if lancamentos else 0
        dados.append({'mes': mes, 'valor_realizado': total})
    
    return pd.DataFrame(dados)


@st.cache_data(ttl=900)
def get_realizado_por_centro(mes: str = None, ano: int = 2026) -> pd.DataFrame:
    """
    Agrega lançamentos realizados por centro de custo.
    
    Args:
        mes: Mês específico ou None para todos
        ano: Ano de referência
    
    Returns:
        DataFrame com: centro_gasto_codigo, ativo, valor_realizado
    """
    lancamentos = listar_lancamentos(ano=ano, mes=mes)
    
    if not lancamentos:
        return pd.DataFrame(columns=['centro_gasto_codigo', 'ativo', 'valor_realizado'])
    
    df = pd.DataFrame(lancamentos)
    
    # Agregar por centro
    df_agrupado = df.groupby(['centro_gasto_codigo', 'ativo']).agg({
        'valor': 'sum'
    }).reset_index()
    
    df_agrupado = df_agrupado.rename(columns={'valor': 'valor_realizado'})
    
    return df_agrupado


@st.cache_data(ttl=900)
def get_realizado_por_conta(mes: str = None, ano: int = 2026) -> pd.DataFrame:
    """
    Agrega lançamentos realizados por conta contábil.
    
    Args:
        mes: Mês específico ou None para todos
        ano: Ano de referência
    
    Returns:
        DataFrame com: conta_contabil_codigo, valor_realizado
    """
    lancamentos = listar_lancamentos(ano=ano, mes=mes)
    
    if not lancamentos:
        return pd.DataFrame(columns=['conta_contabil_codigo', 'valor_realizado'])
    
    df = pd.DataFrame(lancamentos)
    
    # Agregar por conta
    df_agrupado = df.groupby(['conta_contabil_codigo']).agg({
        'valor': 'sum'
    }).reset_index()
    
    df_agrupado = df_agrupado.rename(columns={'valor': 'valor_realizado'})
    
    return df_agrupado


# =============================================================================
# FUNÇÕES DE COMPARAÇÃO
# =============================================================================

from services.provisioning_service import ProvisioningService

# ... CONSTANTES ...

def _get_provisoes_agregadas(agregacao: str = 'mes', ano: int = 2026) -> pd.DataFrame:
    """Retorna previsões PENDENTES agregadas."""
    try:
        ps = ProvisioningService()
        provs = ps.listar_provisoes(status='PENDENTE')
        if not provs:
            return pd.DataFrame()
        
        df = pd.DataFrame(provs)
        # Filtrar apenas para o ano corrente se houver campo ano, assumindo ano corrente da competencia
        # Como o modelo é simplificado, assumimos competencia do ano 2026
        
        if agregacao == 'mes':
            df_agg = df.groupby('mes_competencia').agg({'valor_estimado': 'sum'}).reset_index()
            df_agg.rename(columns={'mes_competencia': 'mes', 'valor_estimado': 'provisionado'}, inplace=True)
            return df_agg
            
        elif agregacao == 'centro':
            df_agg = df.groupby('centro_gasto_codigo').agg({'valor_estimado': 'sum'}).reset_index()
            df_agg.rename(columns={'valor_estimado': 'provisionado'}, inplace=True)
            return df_agg
            
        elif agregacao == 'conta':
            df_agg = df.groupby('conta_contabil_codigo').agg({'valor_estimado': 'sum'}).reset_index()
            df_agg.rename(columns={'valor_estimado': 'provisionado'}, inplace=True)
            return df_agg
            
    except Exception as e:
        print(f"Erro ao agregar provisões: {e}")
        return pd.DataFrame()
    return pd.DataFrame()


def get_comparativo_mensal(ano: int = 2026) -> pd.DataFrame:
    """
    Retorna comparativo orçado x realizado x provisionado por mês.
    
    Returns:
        DataFrame com: mes, orcado, realizado, provisionado, desvio, desvio_pct, status
    """
    # Obter dados
    df_orcado = get_orcamento_agregado_por_mes()
    df_realizado = get_realizado_agregado_por_mes(ano)
    df_prov = _get_provisoes_agregadas('mes', ano)
    
    # Merge Orcado + Realizado
    df = df_orcado.merge(df_realizado, on='mes', how='outer')
    
    # Merge Provisionado
    if not df_prov.empty:
        df = df.merge(df_prov, on='mes', how='left')
    else:
        df['provisionado'] = 0.0
    
    # Preencher valores nulos
    df['valor_orcado'] = df['valor_orcado'].fillna(0)
    df['valor_realizado'] = df['valor_realizado'].fillna(0)
    df['provisionado'] = df['provisionado'].fillna(0)
    
    # Calcular Total Executado (Realizado + Provisionado)
    df['total_executado'] = df['valor_realizado'] + df['provisionado']
    
    # Calcular desvios (Agora baseados no Executado Total)
    df['desvio'] = df['total_executado'] - df['valor_orcado']
    df['desvio_pct'] = np.where(
        df['valor_orcado'] != 0,
        (df['desvio'] / df['valor_orcado']) * 100,
        0
    )
    
    # Status
    df['status'] = df['desvio'].apply(
        lambda x: 'abaixo' if x < 0 else ('acima' if x > 0 else 'igual')
    )
    
    # Ordenar por mês
    df['mes_ordem'] = df['mes'].map({m: i for i, m in enumerate(MESES_ORDEM)})
    df = df.sort_values('mes_ordem').drop('mes_ordem', axis=1)
    
    # Renomear colunas para exibição
    df = df.rename(columns={
        'valor_orcado': 'orcado',
        'valor_realizado': 'realizado'
    })
    
    return df


def get_comparativo_por_centro(mes: str = None, ano: int = 2026) -> pd.DataFrame:
    """
    Retorna comparativo orçado x realizado x provisionado por centro de custo.
    """
    # Obter dados
    df_orcado = get_orcamento_por_centro(mes)
    df_realizado = get_realizado_por_centro(mes, ano)
    
    # Para provisões por centro, se tivermos filtro de mês, precisamos passar?
    # _get_provisoes_agregadas não aceita filtro mes ainda.
    # Vamos melhorar _get_provisoes_agregadas internamente ou filtrar depois?
    # Como _get_provisoes_agregadas faz 'groupby', se chamarmos sem filtro ela traz SUM de tudo.
    # PRECISAMOS FILTRAR AS PROVISÕES PELO MÊS.
    
    # FIX RÁPIDO: Trazer todas e filtrar aqui se 'mes' não for None?
    # Ou melhor: atualizar _get_provisoes_agregadas seria ideal, mas está acima.
    # Vou fazer inline aqui a busca corrigida.
    
    ps = ProvisioningService()
    provs = ps.listar_provisoes(status='PENDENTE', mes=mes) # LISTAR aceita mes
    
    df_prov = pd.DataFrame()
    if provs:
        df_p = pd.DataFrame(provs)
        df_prov = df_p.groupby('centro_gasto_codigo').agg({'valor_estimado': 'sum'}).reset_index()
        df_prov.rename(columns={'valor_estimado': 'provisionado'}, inplace=True)
    
    if df_orcado.empty and df_realizado.empty and df_prov.empty:
        return pd.DataFrame()
    
    # Merge Orcado + Realizado
    df = df_orcado.merge(
        df_realizado, 
        on=['centro_gasto_codigo', 'ativo'], 
        how='outer'
    )
    
    # Merge Provisionado
    if not df_prov.empty:
        df = df.merge(df_prov, on='centro_gasto_codigo', how='left')
    else:
        df['provisionado'] = 0.0
    
    # Preencher valores nulos
    df['valor_orcado'] = df['valor_orcado'].fillna(0)
    df['valor_realizado'] = df['valor_realizado'].fillna(0)
    df['provisionado'] = df['provisionado'].fillna(0)
    df['ativo'] = df['ativo'].fillna('Não Identificado') # Caso venha só de provisão e não tenha ativo mapeado?
    # Se vier só da provisão, 'ativo' vai ser NaN pois df_prov não tem 'ativo'. 
    # Precisamos pegar o ativo do df_centros
    
    if df['ativo'].isnull().any():
        df_centros = carregar_centros_gasto()
        # Map codigo -> ativo
        mapa = df_centros.set_index('codigo')['ativo'].to_dict()
        df['ativo'] = df['ativo'].fillna(df['centro_gasto_codigo'].map(mapa))

    
    df['total_executado'] = df['valor_realizado'] + df['provisionado']
    
    # Calcular desvios
    df['desvio'] = df['total_executado'] - df['valor_orcado']
    df['desvio_pct'] = np.where(
        df['valor_orcado'] != 0,
        (df['desvio'] / df['valor_orcado']) * 100,
        np.where(df['total_executado'] != 0, 100, 0)
    )
    
    # Renomear
    df = df.rename(columns={
        'valor_orcado': 'orcado',
        'valor_realizado': 'realizado'
    })
    
    # Ordenar por desvio absoluto (maiores primeiro)
    df = df.sort_values('desvio', key=abs, ascending=False)
    
    return df


def get_comparativo_por_conta(mes: str = None, ano: int = 2026) -> pd.DataFrame:
    """
    Retorna comparativo orçado x realizado por conta contábil.
    
    Args:
        mes: Mês específico ou None para total do ano
        ano: Ano de referência
    
    Returns:
        DataFrame com: conta_contabil_codigo, descricao, orcado, realizado, desvio, desvio_pct
    """
    # Obter dados
    df_orcado = get_orcamento_por_conta(mes)
    df_realizado = get_realizado_por_conta(mes, ano)
    
    if df_orcado.empty and df_realizado.empty:
        return pd.DataFrame()
    
    # Merge
    df = df_orcado.merge(
        df_realizado, 
        on='conta_contabil_codigo', 
        how='outer'
    )
    
    # Preencher valores nulos
    df['valor_orcado'] = df['valor_orcado'].fillna(0)
    df['valor_realizado'] = df['valor_realizado'].fillna(0)
    df['descricao'] = df['descricao'].fillna('Sem descrição')
    
    # Calcular desvios
    df['desvio'] = df['valor_realizado'] - df['valor_orcado']
    df['desvio_pct'] = np.where(
        df['valor_orcado'] != 0,
        (df['desvio'] / df['valor_orcado']) * 100,
        np.where(df['valor_realizado'] != 0, 100, 0)
    )
    
    # Renomear
    df = df.rename(columns={
        'valor_orcado': 'orcado',
        'valor_realizado': 'realizado'
    })
    
    # Ordenar por valor realizado (maiores primeiro)
    df = df.sort_values('realizado', ascending=False)
    
    return df


def get_drill_down_ativo(ativo: str, mes: str = None, ano: int = 2026) -> pd.DataFrame:
    """
    Retorna drill-down por ativo com hierarquia pai-filho.
    
    Args:
        ativo: Nome do ativo (GASCOM, GASCAC, etc.)
        mes: Mês específico ou None para todos
        ano: Ano de referência
    
    Returns:
        DataFrame com centros do ativo e seus totais
    """
    # Obter comparativo por centro
    df = get_comparativo_por_centro(mes, ano)
    
    if df.empty:
        return pd.DataFrame()
    
    # Filtrar por ativo
    df_ativo = df[df['ativo'] == ativo].copy()
    
    if df_ativo.empty:
        return pd.DataFrame()
    
    # Carregar informações dos centros
    df_centros = carregar_centros_gasto()
    
    # Adicionar informações de hierarquia
    df_ativo = df_ativo.merge(
        df_centros[['codigo', 'descricao', 'codigo_pai', 'classe', 'classe_nome', 'is_sem_hierarquia']],
        left_on='centro_gasto_codigo',
        right_on='codigo',
        how='left'
    )
    
    # Ordenar: primeiro pais (classe 0), depois filhos
    df_ativo['ordem'] = df_ativo['classe'].apply(lambda x: 0 if x == '0' else 1)
    df_ativo = df_ativo.sort_values(['codigo_pai', 'ordem', 'centro_gasto_codigo'])
    
    return df_ativo


# =============================================================================
# FUNÇÕES DE KPIs
# =============================================================================

def get_kpis_gerais(ano: int = 2026) -> Dict:
    """Calcula KPIs com base no total executado (Realizado + Provisionado)."""
    df = get_comparativo_mensal(ano)
    
    if df.empty:
        return {k: 0 for k in ['total_orcado', 'total_realizado', 'total_provisionado', 'desvio', 'desvio_pct', 'execucao_pct', 'meses_com_dados']} | {'status_geral': 'sem_dados'}
    
    total_orcado = df['orcado'].sum()
    total_realizado = df['realizado'].sum()
    total_provisionado = df['provisionado'].sum()
    total_executado = total_realizado + total_provisionado
    
    desvio = total_executado - total_orcado
    
    desvio_pct = (desvio / total_orcado * 100) if total_orcado != 0 else 0
    execucao_pct = (total_executado / total_orcado * 100) if total_orcado != 0 else 0
    
    meses_com_dados = ((df['realizado'] + df['provisionado']) != 0).sum()
    
    if abs(desvio_pct) <= 5:
        status_geral = 'normal'
    elif desvio_pct > 5:
        status_geral = 'acima'
    else:
        status_geral = 'abaixo'
    
    return {
        'total_orcado': total_orcado,
        'total_realizado': total_realizado,
        'total_provisionado': total_provisionado,
        'desvio': desvio,
        'desvio_pct': desvio_pct,
        'execucao_pct': execucao_pct,
        'meses_com_dados': meses_com_dados,
        'status_geral': status_geral
    }


def get_top_desvios(n: int = 10, mes: str = None, ano: int = 2026) -> pd.DataFrame:
    """
    Retorna os N maiores desvios por centro de custo.
    
    Args:
        n: Número de resultados
        mes: Mês específico ou None para todos
        ano: Ano de referência
    
    Returns:
        DataFrame com os maiores desvios
    """
    df = get_comparativo_por_centro(mes, ano)
    
    if df.empty:
        return pd.DataFrame()
    
    # Ordenar por desvio absoluto
    df['desvio_abs'] = df['desvio'].abs()
    df = df.nlargest(n, 'desvio_abs')
    df = df.drop('desvio_abs', axis=1)
    
    return df


def get_resumo_por_ativo(mes: str = None, ano: int = 2026) -> pd.DataFrame:
    """
    Retorna resumo agregado por ativo.
    
    Returns:
        DataFrame com: ativo, orcado, realizado, desvio, desvio_pct, qtd_centros
    """
    df = get_comparativo_por_centro(mes, ano)
    
    if df.empty:
        return pd.DataFrame()
    
    # Agregar por ativo
    df_agrupado = df.groupby('ativo').agg({
        'orcado': 'sum',
        'realizado': 'sum',
        'provisionado': 'sum',
        'centro_gasto_codigo': 'count'
    }).reset_index()
    
    df_agrupado = df_agrupado.rename(columns={'centro_gasto_codigo': 'qtd_centros'})
    
    # Calcular desvios (Total Executado)
    total_exec = df_agrupado['realizado'] + df_agrupado['provisionado']
    df_agrupado['desvio'] = total_exec - df_agrupado['orcado']
    
    df_agrupado['desvio_pct'] = np.where(
        df_agrupado['orcado'] != 0,
        (df_agrupado['desvio'] / df_agrupado['orcado']) * 100,
        0
    )
    
    # Marcar exceções de hierarquia
    df_agrupado['sem_hierarquia'] = df_agrupado['ativo'].isin(ATIVOS_SEM_HIERARQUIA)
    
    # Ordenar por valor orçado
    df_agrupado = df_agrupado.sort_values('orcado', ascending=False)
    
    return df_agrupado
