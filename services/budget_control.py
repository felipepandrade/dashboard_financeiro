"""
services/budget_control.py
==========================
Serviço para controle orçamentário e remanejamentos (Features D & E).
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import Remanejamento, get_session

class BudgetControlService:
    def solicitar_remanejamento(self, dados: dict) -> Remanejamento:
        """Cria uma solicitação de remanejamento."""
        session = get_session()
        try:
            novo = Remanejamento(
                centro_origem_codigo=dados['centro_origem'],
                conta_origem_codigo=dados.get('conta_origem'),
                centro_destino_codigo=dados['centro_destino'],
                conta_destino_codigo=dados.get('conta_destino'),
                valor=float(dados['valor']),
                mes=dados['mes'],
                justificativa=dados['justificativa'],
                solicitante=dados.get('solicitante'),
                status='SOLICITADO'
            )
            session.add(novo)
            session.commit()
            return novo
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def listar_remanejamentos(self, status: str = None) -> List[dict]:
        """Lista remanejamentos."""
        session = get_session()
        try:
            query = session.query(Remanejamento)
            if status:
                query = query.filter(Remanejamento.status == status)
            return [r.to_dict() for r in query.order_by(Remanejamento.data_solicitacao.desc()).all()]
        finally:
            session.close()

    def aprovar_remanejamento(self, id_remanejamento: int, aprovador: str) -> bool:
        """Aprova uma transferência."""
        session = get_session()
        try:
            req = session.query(Remanejamento).get(id_remanejamento)
            if not req:
                raise ValueError("Solicitação não encontrada")
            
            req.status = 'APROVADO'
            req.aprovador = aprovador
            req.data_aprovacao = datetime.now()
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def rejeitar_remanejamento(self, id_remanejamento: int, motivo: str) -> bool:
        """Rejeita uma transferência."""
        session = get_session()
        try:
            req = session.query(Remanejamento).get(id_remanejamento)
            if not req:
                raise ValueError("Solicitação não encontrada")
            
            req.status = 'REJEITADO'
            req.justificativa += f" [REJEIÇÃO: {motivo}]"
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_ajustes_orcamentarios(self, centro_codigo: str, mes: str) -> float:
        """
        Calcula o impacto líquido dos remanejamentos aprovados para um centro/mês.
        Retorna: Valor (Positivo = Aumento de Budget, Negativo = Redução).
        """
        session = get_session()
        try:
            # Entradas (Destino)
            entradas = session.query(Remanejamento).filter(
                Remanejamento.centro_destino_codigo == centro_codigo,
                Remanejamento.mes == mes,
                Remanejamento.status == 'APROVADO'
            ).all()
            total_entradas = sum(r.valor for r in entradas)
            
            # Saídas (Origem)
            saidas = session.query(Remanejamento).filter(
                Remanejamento.centro_origem_codigo == centro_codigo,
                Remanejamento.mes == mes,
                Remanejamento.status == 'APROVADO'
            ).all()
            total_saidas = sum(r.valor for r in saidas)
            
            return total_entradas - total_saidas
        finally:
            session.close()
