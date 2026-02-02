"""
services/provisioning_service.py
================================
Serviço para gestão do ciclo de vida de provisões (Feature B).
"""

from typing import List, Optional, Tuple
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
                usuario=dados.get('usuario'),
                # Novos campos
                numero_contrato=dados.get('numero_contrato'),
                cadastrado_sistema=dados.get('cadastrado_sistema', False),
                numero_registro=dados.get('numero_registro')
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
                        
                    # Converter 'cadastrado_sistema' de string/excel para boolean
                    cadastrado = dados.get('cadastrado_sistema', False)
                    if isinstance(cadastrado, str):
                        cadastrado = cadastrado.lower() in ['sim', 's', 'true', '1']
                    
                    nova = Provisao(
                        descricao=desc,
                        valor_estimado=float(dados['valor_estimado']),
                        centro_gasto_codigo=str(dados['centro_gasto_codigo']),
                        conta_contabil_codigo=str(dados['conta_contabil_codigo']),
                        mes_competencia=dados['mes_competencia'],
                        justificativa_obz=dados.get('justificativa_obz'),
                        tipo_despesa=dados.get('tipo_despesa', 'Variavel'),
                        usuario=dados.get('usuario', 'Importação em Lote'),
                        # Novos campos
                        numero_contrato=str(dados.get('numero_contrato', '')) if dados.get('numero_contrato') else None,
                        cadastrado_sistema=bool(cadastrado),
                        numero_registro=str(dados.get('numero_registro', '')) if dados.get('numero_registro') else None
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
            session.close()

    def get_saldo_provisoes_por_mes(self) -> dict:
        """
        Retorna dicionário {mes: valor_total} de provisões PENDENTES.
        Útil para overlay em gráficos de forecast.
        """
        session = get_session()
        try:
            results = session.query(
                Provisao.mes_competencia, 
                Provisao.valor_estimado
            ).filter(Provisao.status == 'PENDENTE').all()
            
            saldo_mes = {}
            for mes, valor in results:
                saldo_mes[mes] = saldo_mes.get(mes, 0.0) + valor
                
            return saldo_mes
        finally:
            session.close()

    def atualizar_provisao(self, prov_id: int, novos_dados: dict) -> bool:
        """
        Atualiza uma provisão existente.
        Args:
            prov_id: ID da provisão
            novos_dados: Dict com campos a atualizar ('valor', 'status', 'numero_contrato', 'numero_registro')
        """
        session = get_session()
        try:
            provisao = session.query(Provisao).filter(Provisao.id == prov_id).first()
            if not provisao:
                return False
            
            # Atualizar campos se estiverem no dict
            if 'valor' in novos_dados:
                provisao.valor_estimado = float(novos_dados['valor'])
            if 'status' in novos_dados:
                provisao.status = novos_dados['status']
            if 'numero_contrato' in novos_dados:
                provisao.numero_contrato = novos_dados['numero_contrato']
            if 'numero_registro' in novos_dados:
                provisao.numero_registro = novos_dados['numero_registro']
                
            provisao.data_atualizacao = datetime.now()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Erro ao atualizar provisão: {e}")
            return False
        finally:
            session.close()
