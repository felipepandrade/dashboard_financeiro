"""
database/crud.py
================
Operações CRUD (Create, Read, Update, Delete) para lançamentos realizados.

Este módulo fornece funções para:
- Criar, listar, atualizar e deletar lançamentos
- Consultar totais por centro de custo, conta contábil e mês
- Suporte a filtros e agregações

Autor: Sistema Orçamentário 2026
Data: Janeiro/2026
"""

from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from .models import LancamentoRealizado, get_session, init_db

# Garantir que o banco está inicializado
init_db()


# =============================================================================
# OPERAÇÕES DE CRIAÇÃO
# =============================================================================

def criar_lancamento(dados: dict, session: Session = None) -> Tuple[bool, int, str]:
    """
    Cria um novo lançamento no banco de dados.
    
    Args:
        dados: Dicionário com os dados do lançamento:
            - ano, mes (obrigatórios)
            - centro_gasto_codigo, centro_gasto_pai, centro_gasto_classe, etc.
            - conta_contabil_codigo, conta_contabil_descricao
            - fornecedor, descricao, valor
            - usuario, observacoes
        session: Sessão do banco (cria nova se não fornecida)
    
    Returns:
        Tuple (sucesso: bool, id: int, mensagem: str)
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True
    
    try:
        # Validar campos obrigatórios
        campos_obrigatorios = ['mes', 'centro_gasto_codigo', 'conta_contabil_codigo', 'valor']
        for campo in campos_obrigatorios:
            if campo not in dados or dados[campo] is None:
                return False, 0, f"Campo obrigatório não informado: {campo}"
        
        # Criar lançamento
        lancamento = LancamentoRealizado.from_dict(dados)
        lancamento.data_lancamento = datetime.now()
        
        session.add(lancamento)
        session.commit()
        
        return True, lancamento.id, f"Lançamento #{lancamento.id} criado com sucesso"
        
    except Exception as e:
        session.rollback()
        return False, 0, f"Erro ao criar lançamento: {str(e)}"
    
    finally:
        if close_session:
            session.close()


def criar_lancamentos_lote(lista_dados: List[dict], session: Session = None) -> Tuple[int, int, List[str]]:
    """
    Cria múltiplos lançamentos em lote.
    
    Args:
        lista_dados: Lista de dicionários com dados de lançamentos
        session: Sessão do banco
    
    Returns:
        Tuple (criados: int, erros: int, mensagens_erro: List[str])
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True
    
    criados = 0
    erros = 0
    mensagens_erro = []
    
    try:
        for i, dados in enumerate(lista_dados):
            try:
                lancamento = LancamentoRealizado.from_dict(dados)
                lancamento.data_lancamento = datetime.now()
                session.add(lancamento)
                criados += 1
            except Exception as e:
                erros += 1
                mensagens_erro.append(f"Linha {i+1}: {str(e)}")
        
        session.commit()
        return criados, erros, mensagens_erro
        
    except Exception as e:
        session.rollback()
        return 0, len(lista_dados), [f"Erro crítico: {str(e)}"]
    
    finally:
        if close_session:
            session.close()


# =============================================================================
# OPERAÇÕES DE LEITURA
# =============================================================================

def listar_lancamentos(
    ano: int = 2026,
    mes: str = None,
    centro_gasto_codigo: str = None,
    ativo: str = None,
    conta_contabil_codigo: str = None,
    apenas_cos: bool = None,
    limite: int = None,
    session: Session = None
) -> List[dict]:
    """
    Lista lançamentos com filtros opcionais.
    
    Args:
        ano: Ano dos lançamentos
        mes: Filtrar por mês específico (JAN, FEV, etc.)
        centro_gasto_codigo: Filtrar por centro de custo
        ativo: Filtrar por ativo (GASCOM, GASCAC, COS, etc.)
        conta_contabil_codigo: Filtrar por conta contábil
        apenas_cos: Se True, apenas COS; Se False, exclui COS; Se None, todos
        limite: Limitar número de resultados
        session: Sessão do banco
    
    Returns:
        Lista de dicionários com os lançamentos
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True
    
    try:
        query = session.query(LancamentoRealizado).filter(
            LancamentoRealizado.ano == ano
        )
        
        if mes:
            query = query.filter(func.upper(LancamentoRealizado.mes) == mes.upper())
        
        if centro_gasto_codigo:
            query = query.filter(LancamentoRealizado.centro_gasto_codigo == centro_gasto_codigo)
        
        if ativo:
            query = query.filter(LancamentoRealizado.ativo == ativo)
        
        if conta_contabil_codigo:
            query = query.filter(LancamentoRealizado.conta_contabil_codigo == conta_contabil_codigo)
        
        if apenas_cos is not None:
            query = query.filter(LancamentoRealizado.is_cos == apenas_cos)
        
        query = query.order_by(LancamentoRealizado.data_lancamento.desc())
        
        if limite:
            query = query.limit(limite)
        
        return [l.to_dict() for l in query.all()]
        
    finally:
        if close_session:
            session.close()


def obter_lancamento(id: int, session: Session = None) -> Optional[dict]:
    """
    Obtém um lançamento pelo ID.
    
    Args:
        id: ID do lançamento
        session: Sessão do banco
    
    Returns:
        Dicionário com o lançamento ou None se não encontrado
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True
    
    try:
        lancamento = session.query(LancamentoRealizado).filter(
            LancamentoRealizado.id == id
        ).first()
        
        return lancamento.to_dict() if lancamento else None
        
    finally:
        if close_session:
            session.close()


def listar_lancamentos_df(ano: int = 2026, mes: str = None, session: Session = None) -> pd.DataFrame:
    """
    Lista lançamentos como DataFrame pandas.
    
    Args:
        ano: Ano dos lançamentos
        mes: Filtrar por mês específico
        session: Sessão do banco
    
    Returns:
        DataFrame com os lançamentos
    """
    lancamentos = listar_lancamentos(ano=ano, mes=mes, session=session)
    return pd.DataFrame(lancamentos)


# =============================================================================
# OPERAÇÕES DE ATUALIZAÇÃO
# =============================================================================

def atualizar_lancamento(id: int, dados: dict, session: Session = None) -> Tuple[bool, str]:
    """
    Atualiza um lançamento existente.
    
    Args:
        id: ID do lançamento
        dados: Dicionário com os campos a atualizar
        session: Sessão do banco
    
    Returns:
        Tuple (sucesso: bool, mensagem: str)
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True
    
    try:
        lancamento = session.query(LancamentoRealizado).filter(
            LancamentoRealizado.id == id
        ).first()
        
        if not lancamento:
            return False, f"Lançamento #{id} não encontrado"
        
        # Atualizar campos permitidos
        campos_atualizaveis = [
            'mes', 'centro_gasto_codigo', 'centro_gasto_pai', 'centro_gasto_classe',
            'centro_gasto_classe_nome', 'centro_gasto_descricao', 'ativo', 'is_cos',
            'conta_contabil_codigo', 'conta_contabil_descricao', 'fornecedor',
            'descricao', 'valor', 'usuario', 'observacoes'
        ]
        
        for campo in campos_atualizaveis:
            if campo in dados:
                setattr(lancamento, campo, dados[campo])
        
        lancamento.data_atualizacao = datetime.now()
        session.commit()
        
        return True, f"Lançamento #{id} atualizado com sucesso"
        
    except Exception as e:
        session.rollback()
        return False, f"Erro ao atualizar lançamento: {str(e)}"
    
    finally:
        if close_session:
            session.close()


# =============================================================================
# OPERAÇÕES DE DELEÇÃO
# =============================================================================

def deletar_lancamento(id: int, session: Session = None) -> Tuple[bool, str]:
    """
    Deleta um lançamento.
    
    Args:
        id: ID do lançamento
        session: Sessão do banco
    
    Returns:
        Tuple (sucesso: bool, mensagem: str)
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True
    
    try:
        lancamento = session.query(LancamentoRealizado).filter(
            LancamentoRealizado.id == id
        ).first()
        
        if not lancamento:
            return False, f"Lançamento #{id} não encontrado"
        
        session.delete(lancamento)
        session.commit()
        
        return True, f"Lançamento #{id} deletado com sucesso"
        
    except Exception as e:
        session.rollback()
        return False, f"Erro ao deletar lançamento: {str(e)}"
    
    finally:
        if close_session:
            session.close()


def deletar_lancamentos_mes(ano: int, mes: str, session: Session = None) -> Tuple[bool, int, str]:
    """
    Deleta todos os lançamentos de um mês específico.
    
    Args:
        ano: Ano
        mes: Mês (JAN, FEV, etc.)
        session: Sessão do banco
    
    Returns:
        Tuple (sucesso: bool, quantidade: int, mensagem: str)
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True
    
    try:
        quantidade = session.query(LancamentoRealizado).filter(
            and_(
                LancamentoRealizado.ano == ano,
                LancamentoRealizado.mes == mes.upper()
            )
        ).delete()
        
        session.commit()
        
        return True, quantidade, f"{quantidade} lançamentos de {mes}/{ano} deletados"
        
    except Exception as e:
        session.rollback()
        return False, 0, f"Erro ao deletar lançamentos: {str(e)}"
    
    finally:
        if close_session:
            session.close()


# =============================================================================
# CONSULTAS DE AGREGAÇÃO
# =============================================================================

def obter_totais_por_centro(ano: int = 2026, mes: str = None, session: Session = None) -> pd.DataFrame:
    """
    Obtém totais de valores por centro de custo.
    
    Args:
        ano: Ano dos lançamentos
        mes: Filtrar por mês específico (ou None para todos)
        session: Sessão do banco
    
    Returns:
        DataFrame com: centro_gasto_codigo, ativo, classe_nome, total_valor, count
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True
    
    try:
        query = session.query(
            LancamentoRealizado.centro_gasto_codigo,
            LancamentoRealizado.centro_gasto_descricao,
            LancamentoRealizado.ativo,
            LancamentoRealizado.centro_gasto_classe_nome,
            func.sum(LancamentoRealizado.valor).label('total_valor'),
            func.count(LancamentoRealizado.id).label('count')
        ).filter(
            LancamentoRealizado.ano == ano
        )
        
        if mes:
            query = query.filter(LancamentoRealizado.mes == mes.upper())
        
        query = query.group_by(
            LancamentoRealizado.centro_gasto_codigo,
            LancamentoRealizado.centro_gasto_descricao,
            LancamentoRealizado.ativo,
            LancamentoRealizado.centro_gasto_classe_nome
        ).order_by(func.sum(LancamentoRealizado.valor))
        
        resultados = query.all()
        
        return pd.DataFrame([
            {
                'centro_gasto_codigo': r[0],
                'centro_gasto_descricao': r[1],
                'ativo': r[2],
                'classe_nome': r[3],
                'total_valor': r[4],
                'count': r[5]
            }
            for r in resultados
        ])
        
    finally:
        if close_session:
            session.close()


def obter_totais_por_conta(ano: int = 2026, mes: str = None, session: Session = None) -> pd.DataFrame:
    """
    Obtém totais de valores por conta contábil.
    
    Args:
        ano: Ano dos lançamentos
        mes: Filtrar por mês específico (ou None para todos)
        session: Sessão do banco
    
    Returns:
        DataFrame com: conta_contabil_codigo, descricao, total_valor, count
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True
    
    try:
        query = session.query(
            LancamentoRealizado.conta_contabil_codigo,
            LancamentoRealizado.conta_contabil_descricao,
            func.sum(LancamentoRealizado.valor).label('total_valor'),
            func.count(LancamentoRealizado.id).label('count')
        ).filter(
            LancamentoRealizado.ano == ano
        )
        
        if mes:
            query = query.filter(LancamentoRealizado.mes == mes.upper())
        
        query = query.group_by(
            LancamentoRealizado.conta_contabil_codigo,
            LancamentoRealizado.conta_contabil_descricao
        ).order_by(func.sum(LancamentoRealizado.valor))
        
        resultados = query.all()
        
        return pd.DataFrame([
            {
                'conta_contabil_codigo': r[0],
                'conta_contabil_descricao': r[1],
                'total_valor': r[2],
                'count': r[3]
            }
            for r in resultados
        ])
        
    finally:
        if close_session:
            session.close()


def obter_totais_por_mes(ano: int = 2026, session: Session = None) -> pd.DataFrame:
    """
    Obtém totais de valores por mês.
    
    Args:
        ano: Ano dos lançamentos
        session: Sessão do banco
    
    Returns:
        DataFrame com: mes, total_valor, count
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True
    
    try:
        query = session.query(
            LancamentoRealizado.mes,
            func.sum(LancamentoRealizado.valor).label('total_valor'),
            func.count(LancamentoRealizado.id).label('count')
        ).filter(
            LancamentoRealizado.ano == ano
        ).group_by(
            LancamentoRealizado.mes
        )
        
        resultados = query.all()
        
        return pd.DataFrame([
            {
                'mes': r[0],
                'total_valor': r[1],
                'count': r[2]
            }
            for r in resultados
        ])
        
    finally:
        if close_session:
            session.close()


def obter_totais_por_ativo(ano: int = 2026, mes: str = None, session: Session = None) -> pd.DataFrame:
    """
    Obtém totais de valores por ativo.
    
    Args:
        ano: Ano dos lançamentos
        mes: Filtrar por mês específico
        session: Sessão do banco
    
    Returns:
        DataFrame com: ativo, total_valor, count
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True
    
    try:
        query = session.query(
            LancamentoRealizado.ativo,
            func.sum(LancamentoRealizado.valor).label('total_valor'),
            func.count(LancamentoRealizado.id).label('count')
        ).filter(
            LancamentoRealizado.ano == ano
        )
        
        if mes:
            query = query.filter(LancamentoRealizado.mes == mes.upper())
        
        query = query.group_by(
            LancamentoRealizado.ativo
        ).order_by(func.sum(LancamentoRealizado.valor))
        
        resultados = query.all()
        
        return pd.DataFrame([
            {
                'ativo': r[0],
                'total_valor': r[1],
                'count': r[2]
            }
            for r in resultados
        ])
        
    finally:
        if close_session:
            session.close()


# =============================================================================
# ESTATÍSTICAS
# =============================================================================

def obter_estatisticas_gerais(ano: int = 2026, session: Session = None) -> dict:
    """
    Obtém estatísticas gerais dos lançamentos.
    
    Args:
        ano: Ano dos lançamentos
        session: Sessão do banco
    
    Returns:
        Dict com: total_lancamentos, total_valor, meses_com_dados, 
                  centros_utilizados, contas_utilizadas
    """
    close_session = False
    if session is None:
        session = get_session()
        close_session = True
    
    try:
        # Total de lançamentos e valor
        totais = session.query(
            func.count(LancamentoRealizado.id),
            func.sum(LancamentoRealizado.valor)
        ).filter(
            LancamentoRealizado.ano == ano
        ).first()
        
        # Meses com dados
        meses = session.query(
            func.distinct(LancamentoRealizado.mes)
        ).filter(
            LancamentoRealizado.ano == ano
        ).count()
        
        # Centros utilizados
        centros = session.query(
            func.distinct(LancamentoRealizado.centro_gasto_codigo)
        ).filter(
            LancamentoRealizado.ano == ano
        ).count()
        
        # Contas utilizadas
        contas = session.query(
            func.distinct(LancamentoRealizado.conta_contabil_codigo)
        ).filter(
            LancamentoRealizado.ano == ano
        ).count()
        
        return {
            'ano': ano,
            'total_lancamentos': totais[0] or 0,
            'total_valor': totais[1] or 0.0,
            'meses_com_dados': meses,
            'centros_utilizados': centros,
            'contas_utilizadas': contas
        }
        
    finally:
        if close_session:
            session.close()
