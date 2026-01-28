"""
database/__init__.py
=====================
Inicialização do módulo de banco de dados.
"""

from .models import Base, LancamentoRealizado, get_engine, get_session, init_db
from .crud import (
    criar_lancamento,
    listar_lancamentos,
    obter_lancamento,
    atualizar_lancamento,
    deletar_lancamento,
    obter_totais_por_centro,
    obter_totais_por_conta,
    obter_totais_por_mes
)

__all__ = [
    'Base',
    'LancamentoRealizado',
    'get_engine',
    'get_session',
    'init_db',
    'criar_lancamento',
    'listar_lancamentos',
    'obter_lancamento',
    'atualizar_lancamento',
    'deletar_lancamento',
    'obter_totais_por_centro',
    'obter_totais_por_conta',
    'obter_totais_por_mes'
]
