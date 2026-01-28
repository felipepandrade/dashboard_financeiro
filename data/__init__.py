"""
data/__init__.py
=================
Inicialização do módulo de dados.
"""

from .referencias_manager import (
    # Constantes
    MAPA_CLASSES,
    MESES_ORDEM,
    MESES_NUM_MAP,
    COLUNAS_MESES_ORC_2026,
    
    # Carregamento
    carregar_orcamento_v1_2026,
    carregar_centros_gasto,
    carregar_contas_contabeis,
    
    # Hierarquia
    get_codigo_pai,
    get_classe,
    get_nome_classe,
    get_hierarquia_centro,
    get_filhos_por_classe,
    get_ativos_unicos,
    
    # Validação
    validar_centro_gasto,
    validar_conta_contabil,
    
    # Busca
    buscar_centros_gasto,
    buscar_contas_contabeis,
    
    # Orçamento
    get_orcamento_por_centro,
    get_total_orcado_mes,
    
    # Utilitários
    formatar_dropdown_centro,
    formatar_dropdown_conta,
    get_status_referencias
)

__all__ = [
    'MAPA_CLASSES',
    'MESES_ORDEM',
    'MESES_NUM_MAP',
    'COLUNAS_MESES_ORC_2026',
    'carregar_orcamento_v1_2026',
    'carregar_centros_gasto',
    'carregar_contas_contabeis',
    'get_codigo_pai',
    'get_classe',
    'get_nome_classe',
    'get_hierarquia_centro',
    'get_filhos_por_classe',
    'get_ativos_unicos',
    'validar_centro_gasto',
    'validar_conta_contabil',
    'buscar_centros_gasto',
    'buscar_contas_contabeis',
    'get_orcamento_por_centro',
    'get_total_orcado_mes',
    'formatar_dropdown_centro',
    'formatar_dropdown_conta',
    'get_status_referencias'
]
