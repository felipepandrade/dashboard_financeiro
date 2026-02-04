"""
services/forecast_service.py
============================
Serviço para geração e gerenciamento de previsões orçamentárias (Feature A).
Integra modelos matemáticos (utils_financeiro) com persistência no banco de dados.
"""

import pandas as pd
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import ForecastCenario, ForecastEntry, get_session
from utils_financeiro import SimpleForecaster, MESES_ORDEM

class ForecastService:
    def __init__(self):
        self.forecaster = SimpleForecaster()

    def criar_cenario_automatico(self, 
                               df_historico: pd.DataFrame, 
                               nome: str = None, 
                               metodo: str = 'hybrid',
                               ano: int = 2026) -> int:
        """
        Gera um cenário automático baseado no histórico (Realizado + P&L Anterior).
        
        Args:
            df_historico: DataFrame com colunas ['mes', 'valor', 'conta_contabil', 'centro_gasto']
            nome: Nome do cenário (opcional)
            metodo: 'linear', 'sma', 'hybrid'
            
        Returns:
            ID do cenário criado
        """
        session = get_session()
        try:
            if not nome:
                nome = f"Forecast Automático ({metodo.upper()}) - {datetime.now().strftime('%d/%m %H:%M')}"
            
            # 1. Criar o Cenário
            cenario = ForecastCenario(
                nome=nome,
                descricao=f"Gerado automaticamente usando método {metodo}",
                tipo='AUTOMATICO',
                ano_referencia=ano
            )
            session.add(cenario)
            session.commit()
            
            # 2. Processar Previsão por Conta Contábil (Mais estável que centro)
            # Agrupar histórico por conta
            contas = df_historico['conta_contabil_codigo'].unique()
            
            entries = []
            
            for conta in contas:
                df_conta = df_historico[df_historico['conta_contabil_codigo'] == conta].copy()
                
                # Se tiver poucos dados, pular ou usar média simples
                if len(df_conta) < 3:
                    continue
                    
                # Treinar modelo
                self.forecaster.fit(
                    df_conta, 
                    date_col='data_ref',  # Precisa ter data datetime
                    value_col='valor',
                    method=metodo
                )
                
                # Prever até o fim do ano (12 meses)
                # O forecaster retorna 12 meses a frente
                df_pred = self.forecaster.predict(periods=12)
                
                # Filtrar apenas meses de 2026
                # Assumindo que o predict começa do mês seguinte ao último histórico
                
                # Converter para ForecastEntries
                for _, row in df_pred.iterrows():
                    mes_idx = row['data'].month - 1
                    if 0 <= mes_idx < 12:
                        mes_str = MESES_ORDEM[mes_idx]
                        
                        # Tenta manter o centro de custo se for único para a conta
                        # Caso contrário, usa um centro "DIVERSOS" ou o principal
                        centro = df_conta['centro_gasto_codigo'].mode().iloc[0] if not df_conta.empty else '00000000'
                        
                        entry = ForecastEntry(
                            cenario_id=cenario.id,
                            mes=mes_str,
                            centro_gasto_codigo=centro,
                            conta_contabil_codigo=conta,
                            valor_previsto=float(row['previsao']),
                            metodo_calculo=metodo
                        )
                        entries.append(entry)
            
            # Bulk Insert
            session.add_all(entries)
            session.commit()
            return cenario.id
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def listar_cenarios(self) -> List[dict]:
        """Lista todos os cenários disponíveis."""
        session = get_session()
        try:
            cenarios = session.query(ForecastCenario).order_by(ForecastCenario.data_criacao.desc()).all()
            return [c.to_dict() for c in cenarios]
        finally:
            session.close()

    def get_dados_cenario(self, cenario_id: int) -> pd.DataFrame:
        """Retorna os dados detalhados de um cenário."""
        session = get_session()
        try:
            entries = session.query(ForecastEntry).filter_by(cenario_id=cenario_id).all()
            data = [{
                'mes': e.mes,
                'conta_contabil': e.conta_contabil_codigo,
                'centro_custo': e.centro_gasto_codigo,
                'valor_previsto': e.valor_previsto
            } for e in entries]
            return pd.DataFrame(data)
        finally:
            session.close()
