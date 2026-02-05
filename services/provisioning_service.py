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
                numero_registro=dados.get('numero_registro'),
                regional=dados.get('regional'),
                base=dados.get('base')
            )
            session.add(nova)
            session.commit()
            return nova
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def listar_provisoes(self, status: str = None, mes: str = None, base: str = None) -> List[dict]:
        """Lista provisões com filtros."""
        session = get_session()
        try:
            query = session.query(Provisao)
            if status:
                query = query.filter(Provisao.status == status)
            if mes:
                query = query.filter(Provisao.mes_competencia == mes)
            if base:
                query = query.filter(Provisao.base == base)
                
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
                        numero_registro=str(dados.get('numero_registro', '')) if dados.get('numero_registro') else None,
                        regional=dados.get('regional'),
                        base=dados.get('base')
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

    def atualizar_provisoes_em_lote(self, lista_dados: List[dict]) -> Tuple[int, int, List[str]]:
        """
        Batch update provisions with optimistic locking.
        
        Args:
            lista_dados: List of dicts with keys:
                - id (required): Provision ID
                - valor_estimado (optional): New value
                - status (optional): New status (PENDENTE|REALIZADA|CANCELADA)
                - numero_registro (optional): Registration number
                - cadastrado_sistema (optional): Boolean or 'Sim'/'Não'
                - data_atualizacao (optional): Timestamp for conflict detection
        
        Returns:
            Tuple of (updated_count, conflict_count, errors_list)
        """
        session = get_session()
        updated_count = 0
        conflict_count = 0
        erros = []
        
        try:
            for idx, dados in enumerate(lista_dados):
                try:
                    prov_id = dados.get('id')
                    if not prov_id:
                        erros.append(f"Linha {idx+2}: ID não informado")
                        continue
                    
                    # Fetch existing provision
                    provisao = session.query(Provisao).filter(Provisao.id == int(prov_id)).first()
                    
                    if not provisao:
                        erros.append(f"Linha {idx+2}: ID {prov_id} não encontrado")
                        continue
                    
                    # Only allow updates to PENDENTE provisions
                    if provisao.status != 'PENDENTE':
                        erros.append(f"Linha {idx+2}: ID {prov_id} não está PENDENTE (status atual: {provisao.status})")
                        continue
                    
                    # Optimistic Locking: Check if record was modified since download
                    excel_timestamp = dados.get('data_atualizacao')
                    if excel_timestamp and provisao.data_atualizacao:
                        # Convert string to datetime if needed
                        if isinstance(excel_timestamp, str):
                            try:
                                from datetime import datetime as dt
                                excel_timestamp = dt.fromisoformat(excel_timestamp.replace('Z', '+00:00'))
                            except:
                                pass  # If parsing fails, skip conflict check
                        
                        # Compare timestamps (allow 1 second tolerance)
                        if hasattr(excel_timestamp, 'timestamp') and hasattr(provisao.data_atualizacao, 'timestamp'):
                            if abs(provisao.data_atualizacao.timestamp() - excel_timestamp.timestamp()) > 1:
                                conflict_count += 1
                                erros.append(f"Linha {idx+2}: CONFLITO - ID {prov_id} foi modificado por outro usuário")
                                continue
                    
                    # Apply updates
                    if 'valor_estimado' in dados and dados['valor_estimado'] is not None:
                        provisao.valor_estimado = float(dados['valor_estimado'])
                    
                    if 'status' in dados and dados['status']:
                        new_status = str(dados['status']).upper().strip()
                        if new_status in ['PENDENTE', 'REALIZADA', 'CANCELADA']:
                            provisao.status = new_status
                    
                    if 'numero_registro' in dados:
                        provisao.numero_registro = str(dados['numero_registro']) if dados['numero_registro'] else None
                    
                    if 'cadastrado_sistema' in dados:
                        val = dados['cadastrado_sistema']
                        if isinstance(val, str):
                            val = val.lower() in ['sim', 's', 'true', '1', 'verdadeiro']
                        provisao.cadastrado_sistema = bool(val)
                    
                    provisao.data_atualizacao = datetime.now()
                    updated_count += 1
                    
                except Exception as e:
                    erros.append(f"Linha {idx+2}: Erro - {str(e)}")
            
            if updated_count > 0:
                session.commit()
            
            return updated_count, conflict_count, erros
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
