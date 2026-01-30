"""
services/provisioning_service.py
================================
Serviço para gestão do ciclo de vida de provisões (Feature B).
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import Provisao, LancamentoRealizado, get_session

class ProvisioningService:
    def criar_provisao(self, dados: dict) -> Provisao:
        """Cria uma nova provisão."""
        session = get_session()
        try:
            nova = Provisao(
                descricao=dados['descricao'],
                valor_estimado=float(dados['valor_estimado']),
                centro_gasto_codigo=dados['centro_gasto_codigo'],
                conta_contabil_codigo=dados['conta_contabil_codigo'],
                mes_competencia=dados['mes_competencia'],
                justificativa_obz=dados.get('justificativa_obz'),
                tipo_despesa=dados.get('tipo_despesa', 'Variavel'),
                usuario=dados.get('usuario')
            )
            session.add(nova)
            session.commit()
            return nova
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def listar_provisoes(self, status: str = None, mes: str = None) -> List[dict]:
        """Lista provisões com filtros."""
        session = get_session()
        try:
            query = session.query(Provisao)
            if status:
                query = query.filter(Provisao.status == status)
            if mes:
                query = query.filter(Provisao.mes_competencia == mes)
                
            return [p.to_dict() for p in query.all()]
        finally:
            session.close()

    def conciliar_provisao(self, provisao_id: int, lancamento_id: int) -> bool:
        """
        Vincula uma provisão a um lançamento realizado (baixa).
        """
        session = get_session()
        try:
            provisao = session.query(Provisao).get(provisao_id)
            if not provisao:
                raise ValueError("Provisão não encontrada")
                
            lancamento = session.query(LancamentoRealizado).get(lancamento_id)
            if not lancamento:
                raise ValueError("Lançamento não encontrado")
                
            # Atualizar Provisão
            provisao.lancamento_realizado_id = lancamento_id
            provisao.status = 'REALIZADA'
            provisao.data_atualizacao = datetime.now()
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def criar_provisoes_em_lote(self, lista_dados: List[dict]) -> Tuple[int, List[str]]:
        """
        Cria múltiplas provisões em uma única transação.
        Retorna (sucesso_count, erros_list).
        """
        session = get_session()
        sucesso_count = 0
        erros = []
        
        try:
            for idx, dados in enumerate(lista_dados):
                try:
                    # Compilar descrição com fornecedor se existir
                    desc = dados.get('descricao')
                    fornecedor = dados.get('fornecedor')
                    if fornecedor:
                        desc = f"{desc} ({fornecedor})"
                        
                    nova = Provisao(
                        descricao=desc,
                        valor_estimado=float(dados['valor_estimado']),
                        centro_gasto_codigo=str(dados['centro_gasto_codigo']),
                        conta_contabil_codigo=str(dados['conta_contabil_codigo']),
                        mes_competencia=dados['mes_competencia'],
                        justificativa_obz=dados.get('justificativa_obz'),
                        tipo_despesa=dados.get('tipo_despesa', 'Variavel'),
                        usuario=dados.get('usuario', 'Importação em Lote')
                    )
                    session.add(nova)
                    sucesso_count += 1
                except Exception as e:
                    erros.append(f"Linha {idx+2}: {str(e)}") # +2 considerando header e 0-index
            
            if sucesso_count > 0:
                session.commit()
                
            return sucesso_count, erros
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def cancelar_provisao(self, provisao_id: int, motivo: str) -> bool:
        """Cancela (reverte) uma provisão."""
        session = get_session()
        try:
            provisao = session.query(Provisao).get(provisao_id)
            if not provisao:
                raise ValueError("Provisão não encontrada")
            
            provisao.status = 'CANCELADA'
            provisao.justificativa_obz = (provisao.justificativa_obz or "") + f" [CANCELADO: {motivo}]"
            provisao.data_atualizacao = datetime.now()
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
