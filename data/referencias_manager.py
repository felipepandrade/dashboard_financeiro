"""
referencias_manager.py
======================
Gerenciador das bases de referência permanentes do orçamento 2026.

Este módulo carrega e gerencia:
- Orçamento V1 2026 (317 itens orçados)
- Centros de Gasto (432 centros, com hierarquia pai-filho)
- Contas Contábeis (371 contas)

Autor: Sistema Orçamentário 2026
Data: Janeiro/2026
"""

import os
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# =============================================================================
# CONSTANTES
# =============================================================================

# Diretório base das referências
REFERENCIAS_DIR = Path(__file__).parent / "referencias"

# Mapeamento de classes de ativos (9º dígito do código)
MAPA_CLASSES = {
    '0': 'Instalação Principal',
    '1': 'Gasoduto',
    '2': 'Faixa',
    '3': 'Ramal',
    '4': 'Base',
    '5': 'ECOMP',
    '6': 'Ponto de Entrada',
    '7': 'Ponto de Saída',
    '8': 'ERP',
    '9': 'EDG'
}

# Ativos que NÃO seguem a lógica de hierarquia pai-filho
# COS = Custos Administrativos (50 centros)
# G&A = Custos de Suporte (29 centros)
ATIVOS_SEM_HIERARQUIA = ['COS', 'G&A']

# Ordem dos meses
MESES_ORDEM = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN',
               'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

MESES_NUM_MAP = {mes: i+1 for i, mes in enumerate(MESES_ORDEM)}

# Mapeamento de colunas de meses no orçamento 2026
COLUNAS_MESES_ORC_2026 = {
    'jan/26': 'JAN', 'fev/26': 'FEV', 'mar/26': 'MAR',
    'abr/26': 'ABR', 'mai/26': 'MAI', 'jun/26': 'JUN',
    'jul/26': 'JUL', 'ago/26': 'AGO', 'set/26': 'SET',
    'out/26': 'OUT', 'nov/26': 'NOV', 'dez/26': 'DEZ'
}


# =============================================================================
# FUNÇÕES DE CARREGAMENTO (COM CACHE)
# =============================================================================

@st.cache_data(show_spinner="Carregando orçamento de referência 2026...")
def carregar_orcamento_v1_2026() -> pd.DataFrame:
    """
    Carrega o orçamento V1 2026 da base de referência permanente.
    
    Returns:
        DataFrame com 317 linhas contendo:
        - GERÊNCIA, ATIVO CONTRATUAL, CENTRO DE GASTO, DESCRIÇÃO CENTRO DE GASTO
        - CONTA P&L GERÊNCIAL, CÓDIGO CONTA CONTÁBIL, DESCRIÇÃO CONTA CONTÁBIL
        - ATIVIDADE, DESCRIÇÃO ATIVIDADE, FORNECEDOR, PREMISSA
        - Valores mensais: jan/26 a dez/26
    """
    caminho = REFERENCIAS_DIR / "orcamento_v1_2026.xlsx"
    
    if not caminho.exists():
        st.error(f"❌ Arquivo de orçamento não encontrado: {caminho}")
        return pd.DataFrame()
    
    try:
        df = pd.read_excel(caminho)
        
        # Padronizar código do centro de gasto
        if 'CENTRO DE GASTO' in df.columns:
            df['CENTRO DE GASTO'] = df['CENTRO DE GASTO'].astype(str).str.zfill(11)
        
        # Padronizar código da conta contábil
        if 'CÓDIGO CONTA CONTÁBIL' in df.columns:
            df['CÓDIGO CONTA CONTÁBIL'] = df['CÓDIGO CONTA CONTÁBIL'].astype(str)
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar orçamento: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner="Carregando centros de gasto...")
def carregar_centros_gasto() -> pd.DataFrame:
    """
    Carrega a base de centros de gasto (432 registros).
    
    Adiciona colunas derivadas:
    - codigo: Código padronizado com 11 dígitos
    - codigo_pai: Primeiros 8 dígitos (ativo pai)
    - classe: 9º dígito (classe do ativo)
    - classe_nome: Nome da classe
    - is_sem_hierarquia: True se for COS ou G&A (não seguem lógica pai-filho)
    - is_cos: True se for custo administrativo (COS)
    - is_ga: True se for custo de suporte (G&A)
    
    Returns:
        DataFrame enriquecido com hierarquia de centros de custo
    """
    caminho = REFERENCIAS_DIR / "centro_gasto.xlsx"
    
    if not caminho.exists():
        st.error(f"❌ Arquivo de centros de gasto não encontrado: {caminho}")
        return pd.DataFrame()
    
    try:
        df = pd.read_excel(caminho)
        
        # Padronizar código com 11 dígitos
        df['codigo'] = df['CENTRO DE GASTO'].astype(str).str.zfill(11)
        
        # Extrair hierarquia
        df['codigo_pai'] = df['codigo'].str[:8]
        df['classe'] = df['codigo'].str[8]
        df['classe_nome'] = df['classe'].map(MAPA_CLASSES).fillna('Desconhecido')
        
        # Identificar custos administrativos (COS) e custos de suporte (G&A)
        df['is_cos'] = df['ATIVO'] == 'COS'
        df['is_ga'] = df['ATIVO'] == 'G&A'
        
        # Identificar centros que NÃO seguem a lógica de hierarquia pai-filho
        df['is_sem_hierarquia'] = df['ATIVO'].isin(ATIVOS_SEM_HIERARQUIA)
        
        # Renomear colunas para padronização
        # Assumindo que o Excel novo tem colunas 'REGIONAL' e 'BASE'
        rename_map = {
            'DESCRIÇÃO CENTRO DE GASTO': 'descricao',
            'ATIVO': 'ativo',
            'REGIONAL': 'regional',
            'BASE': 'base'
        }
        df = df.rename(columns=rename_map)
        
        # Garantir que colunas existam mesmo se o Excel não tiver (fail-safe)
        if 'regional' not in df.columns: df['regional'] = None
        if 'base' not in df.columns: df['base'] = None
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar centros de gasto: {e}")
        return pd.DataFrame()


@st.cache_data(show_spinner="Carregando contas contábeis...")
def carregar_contas_contabeis() -> pd.DataFrame:
    """
    Carrega a base de contas contábeis (371 registros).
    
    Returns:
        DataFrame com código e descrição das contas
    """
    caminho = REFERENCIAS_DIR / "conta_contabil.xlsx"
    
    if not caminho.exists():
        st.error(f"❌ Arquivo de contas contábeis não encontrado: {caminho}")
        return pd.DataFrame()
    
    try:
        df = pd.read_excel(caminho)
        
        # Renomear colunas para padronização
        df = df.rename(columns={
            'CÓDIGO CONTA CONTÁBIL': 'codigo',
            'DESCRIÇÃO CONTA CONTÁBIL': 'descricao'
        })
        
        # Garantir que o código seja string
        df['codigo'] = df['codigo'].astype(str)
        
        return df
        
    except Exception as e:
        st.error(f"❌ Erro ao carregar contas contábeis: {e}")
        return pd.DataFrame()


# =============================================================================
# FUNÇÕES DE HIERARQUIA DE CENTROS DE CUSTO
# =============================================================================

def get_codigo_pai(codigo: str) -> str:
    """
    Extrai o código do ativo pai (primeiros 8 dígitos).
    
    Args:
        codigo: Código completo do centro de gasto (11 dígitos)
    
    Returns:
        Código do ativo pai (8 dígitos)
    """
    codigo_padronizado = str(codigo).zfill(11)
    return codigo_padronizado[:8]


def get_classe(codigo: str) -> str:
    """
    Extrai a classe do ativo (9º dígito).
    
    Classes:
        0 = Instalação Principal (Pai)
        1 = Gasoduto
        2 = Faixa
        3 = Ramal
        4 = Base
        5 = ECOMP
        6 = Ponto de Entrada
        7 = Ponto de Saída
        8 = ERP
        9 = EDG
    
    Args:
        codigo: Código completo do centro de gasto
    
    Returns:
        Dígito da classe (0-9)
    """
    codigo_padronizado = str(codigo).zfill(11)
    return codigo_padronizado[8] if len(codigo_padronizado) > 8 else '0'


def get_nome_classe(codigo: str) -> str:
    """
    Retorna o nome da classe do ativo.
    
    Args:
        codigo: Código completo do centro de gasto
    
    Returns:
        Nome da classe (ex: 'Gasoduto', 'Base', etc.)
    """
    classe = get_classe(codigo)
    return MAPA_CLASSES.get(classe, 'Desconhecido')


def get_hierarquia_centro(codigo: str, df_centros: pd.DataFrame = None) -> Dict:
    """
    Retorna informações completas da hierarquia de um centro de custo.
    
    Nota: Centros COS (Custos Administrativos) e G&A (Custos de Suporte)
    NÃO seguem a lógica de hierarquia pai-filho.
    
    Args:
        codigo: Código do centro de gasto
        df_centros: DataFrame de centros (carrega automaticamente se não fornecido)
    
    Returns:
        Dict com: codigo, codigo_pai, classe, classe_nome, ativo, descricao, 
                  is_cos, is_ga, is_sem_hierarquia, pai_descricao, filhos_count
    """
    if df_centros is None:
        df_centros = carregar_centros_gasto()
    
    codigo_padronizado = str(codigo).zfill(11)
    
    # Buscar informações do centro
    centro = df_centros[df_centros['codigo'] == codigo_padronizado]
    
    if centro.empty:
        return {
            'codigo': codigo_padronizado,
            'encontrado': False,
            'erro': 'Centro de custo não encontrado na base de referência'
        }
    
    centro_info = centro.iloc[0]
    codigo_pai = centro_info['codigo_pai']
    is_sem_hierarquia = centro_info.get('is_sem_hierarquia', False)
    
    # Para centros sem hierarquia (COS, G&A), não buscar pai
    if is_sem_hierarquia:
        pai_descricao = 'N/A (Sem hierarquia)'
        filhos_count = 0
    else:
        # Buscar informações do pai
        pai = df_centros[df_centros['codigo'].str.startswith(codigo_pai) & 
                         (df_centros['classe'] == '0')]
        
        pai_descricao = pai.iloc[0]['descricao'] if not pai.empty else 'N/A'
        
        # Contar filhos do mesmo pai
        filhos = df_centros[(df_centros['codigo_pai'] == codigo_pai) & 
                            (df_centros['classe'] != '0')]
        filhos_count = len(filhos)
    
    return {
        'codigo': codigo_padronizado,
        'encontrado': True,
        'codigo_pai': codigo_pai,
        'classe': centro_info['classe'],
        'classe_nome': centro_info['classe_nome'],
        'ativo': centro_info['ativo'],
        'descricao': centro_info['descricao'],
        'is_cos': centro_info.get('is_cos', False),
        'is_ga': centro_info.get('is_ga', False),
        'is_sem_hierarquia': is_sem_hierarquia,
        'pai_descricao': pai_descricao,
        'filhos_count': filhos_count
    }


def get_filhos_por_classe(codigo_pai: str, classe: str = None, 
                          df_centros: pd.DataFrame = None) -> List[Dict]:
    """
    Retorna todos os centros filhos de um ativo pai, opcionalmente filtrado por classe.
    
    Args:
        codigo_pai: Primeiros 8 dígitos do código
        classe: Filtrar por classe específica (1-9) ou None para todos
        df_centros: DataFrame de centros
    
    Returns:
        Lista de dicts com informações dos centros filhos
    """
    if df_centros is None:
        df_centros = carregar_centros_gasto()
    
    # Filtrar por código pai
    filhos = df_centros[df_centros['codigo_pai'] == codigo_pai]
    
    # Filtrar por classe se especificado
    if classe is not None:
        filhos = filhos[filhos['classe'] == str(classe)]
    
    return filhos.to_dict('records')


def get_ativos_unicos(df_centros: pd.DataFrame = None) -> List[str]:
    """
    Retorna lista de ativos únicos (ex: GASCOM, GASCAC, COS).
    
    Args:
        df_centros: DataFrame de centros
    
    Returns:
        Lista ordenada de ativos únicos
    """
    if df_centros is None:
        df_centros = carregar_centros_gasto()
    
    return sorted(df_centros['ativo'].unique().tolist())


# =============================================================================
# FUNÇÕES DE VALIDAÇÃO
# =============================================================================

def validar_centro_gasto(codigo: str, df_centros: pd.DataFrame = None) -> Tuple[bool, str]:
    """
    Valida se um código de centro de gasto existe na base de referência.
    
    Args:
        codigo: Código do centro de gasto
        df_centros: DataFrame de centros
    
    Returns:
        Tuple (é_válido: bool, mensagem: str)
    """
    if df_centros is None:
        df_centros = carregar_centros_gasto()
    
    codigo_padronizado = str(codigo).zfill(11)
    
    if codigo_padronizado in df_centros['codigo'].values:
        centro = df_centros[df_centros['codigo'] == codigo_padronizado].iloc[0]
        return True, f"✅ {centro['descricao']} ({centro['ativo']})"
    else:
        return False, f"❌ Centro de gasto '{codigo}' não encontrado na base de referência"


def validar_conta_contabil(codigo: str, df_contas: pd.DataFrame = None) -> Tuple[bool, str]:
    """
    Valida se um código de conta contábil existe na base de referência.
    
    Args:
        codigo: Código da conta contábil
        df_contas: DataFrame de contas
    
    Returns:
        Tuple (é_válido: bool, mensagem: str)
    """
    if df_contas is None:
        df_contas = carregar_contas_contabeis()
    
    codigo_str = str(codigo)
    
    if codigo_str in df_contas['codigo'].values:
        conta = df_contas[df_contas['codigo'] == codigo_str].iloc[0]
        return True, f"✅ {conta['descricao']}"
    else:
        return False, f"❌ Conta contábil '{codigo}' não encontrada na base de referência"


# =============================================================================
# FUNÇÕES DE BUSCA (PARA DROPDOWNS)
# =============================================================================

def buscar_centros_gasto(termo: str = "", ativo: str = None, 
                         classe: str = None, excluir_cos: bool = False,
                         regional: str = None, base: str = None,
                         df_centros: pd.DataFrame = None) -> pd.DataFrame:
    """
    Busca centros de gasto com filtros opcionais.
    """
    if df_centros is None:
        df_centros = carregar_centros_gasto()
    
    resultado = df_centros.copy()
    
    # Filtrar por termo de busca
    if termo:
        termo_lower = termo.lower()
        resultado = resultado[
            resultado['codigo'].str.lower().str.contains(termo_lower) |
            resultado['descricao'].str.lower().str.contains(termo_lower, na=False)
        ]
    
    # Filtrar por ativo
    if ativo:
        resultado = resultado[resultado['ativo'] == ativo]
    
    # Filtrar por classe
    if classe:
        resultado = resultado[resultado['classe'] == str(classe)]

    # Filtrar por Regional
    if regional:
        resultado = resultado[resultado['regional'] == regional]

    # Filtrar por Base
    if base:
        resultado = resultado[resultado['base'] == base]
    
    # Excluir COS se solicitado
    if excluir_cos:
        resultado = resultado[~resultado['is_cos']]
    
    return resultado


def buscar_contas_contabeis(termo: str = "", 
                            df_contas: pd.DataFrame = None) -> pd.DataFrame:
    """
    Busca contas contábeis por termo.
    
    Args:
        termo: Termo para buscar no código ou descrição
        df_contas: DataFrame de contas
    
    Returns:
        DataFrame filtrado com contas contábeis
    """
    if df_contas is None:
        df_contas = carregar_contas_contabeis()
    
    if not termo:
        return df_contas
    
    termo_lower = termo.lower()
    return df_contas[
        df_contas['codigo'].str.lower().str.contains(termo_lower) |
        df_contas['descricao'].str.lower().str.contains(termo_lower, na=False)
    ]


# =============================================================================
# FUNÇÕES DE ORÇAMENTO
# =============================================================================

def get_orcamento_por_centro(codigo_centro: str, 
                             df_orcamento: pd.DataFrame = None) -> pd.DataFrame:
    """
    Retorna o orçamento previsto para um centro de gasto específico.
    
    Args:
        codigo_centro: Código do centro de gasto
        df_orcamento: DataFrame do orçamento
    
    Returns:
        DataFrame com linhas do orçamento para o centro
    """
    if df_orcamento is None:
        df_orcamento = carregar_orcamento_v1_2026()
    
    codigo_padronizado = str(codigo_centro).zfill(11)
    
    return df_orcamento[df_orcamento['CENTRO DE GASTO'] == codigo_padronizado]


def get_total_orcado_mes(mes: str, df_orcamento: pd.DataFrame = None) -> float:
    """
    Retorna o total orçado para um mês específico.
    
    Args:
        mes: Nome do mês (JAN, FEV, etc.) ou coluna (jan/26)
        df_orcamento: DataFrame do orçamento
    
    Returns:
        Total orçado para o mês
    """
    if df_orcamento is None:
        df_orcamento = carregar_orcamento_v1_2026()
    
    # Converter nome do mês para coluna se necessário
    if mes.upper() in MESES_ORDEM:
        coluna = [k for k, v in COLUNAS_MESES_ORC_2026.items() if v == mes.upper()]
        if coluna:
            mes = coluna[0]
    
    if mes in df_orcamento.columns:
        return df_orcamento[mes].sum()
    else:
        return 0.0


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def formatar_dropdown_centro(row: pd.Series) -> str:
    """
    Formata uma linha de centro de gasto para exibição em dropdown.
    
    Args:
        row: Série do pandas com dados do centro
    
    Returns:
        String formatada: "CÓDIGO - DESCRIÇÃO (ATIVO - CLASSE)"
    """
    return f"{row['codigo']} - {row['descricao']} ({row['ativo']} - {row['classe_nome']})"


def formatar_dropdown_conta(row: pd.Series) -> str:
    """
    Formata uma linha de conta contábil para exibição em dropdown.
    
    Args:
        row: Série do pandas com dados da conta
    
    Returns:
        String formatada: "CÓDIGO - DESCRIÇÃO"
    """
    return f"{row['codigo']} - {row['descricao']}"


def get_status_referencias() -> Dict:
    """
    Retorna o status de carregamento das bases de referência.
    
    Returns:
        Dict com: orcamento_ok, centros_ok, contas_ok, 
                  orcamento_count, centros_count, contas_count
    """
    status = {
        'orcamento_ok': False,
        'centros_ok': False,
        'contas_ok': False,
        'orcamento_count': 0,
        'centros_count': 0,
        'contas_count': 0
    }
    
    try:
        df_orc = carregar_orcamento_v1_2026()
        if not df_orc.empty:
            status['orcamento_ok'] = True
            status['orcamento_count'] = len(df_orc)
    except:
        pass
    
    try:
        df_centros = carregar_centros_gasto()
        if not df_centros.empty:
            status['centros_ok'] = True
            status['centros_count'] = len(df_centros)
    except:
        pass
    
    try:
        df_contas = carregar_contas_contabeis()
        if not df_contas.empty:
            status['contas_ok'] = True
            status['contas_count'] = len(df_contas)
    except:
        pass
    
    return status
