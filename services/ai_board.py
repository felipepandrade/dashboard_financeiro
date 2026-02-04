"""
services/ai_board.py
====================
Arquitetura Multi-Agente para Consultoria Financeira (Feature A - IA Board).
Implementa o padrão 'Board of Directors' onde diferentes personas analisam os dados.
"""

import pandas as pd
from typing import Dict, List
import json
from data.comparador import get_comparativo_mensal
from utils_financeiro import gerar_analise_ia, get_ai_chat_response

class AIBoard:
    def __init__(self, api_key: str, provider: str = "Gemini (Google)"):
        self.api_key = api_key
        self.provider = provider
        
    def _get_contexto_financeiro(self) -> str:
        """Coleta resumo dos dados financeiros atuais."""
        try:
            df = get_comparativo_mensal(2026)
            if df.empty:
                return "Dados financeiros não disponíveis."
                
            # Preparar resumo (com fallback seguro se tabulate falhar)
            grouped = df.groupby('mes')[['orcado', 'realizado']].sum()
            try:
                resumo = grouped.to_markdown()
            except Exception:
                # Fallback para string simples se tabulate não estiver instalado
                resumo = grouped.to_string()
                
            total_realizado = df['realizado'].sum()
            total_orcado = df['orcado'].sum()
            total_delta = total_realizado - total_orcado
            
            resumo_texto = f"Resumo YTD:\n{resumo}\n\nDesvio Total Acumulado: R$ {total_delta:,.2f}"
            
            # Smart Diagnostics: Detecta falta de carga de dados
            if total_realizado == 0 and total_orcado > 0:
                resumo_texto += "\n\n[SISTEMA NOTICE]: O Total Realizado é exatamente 0.00. Isso indica ALTA PROBABILIDADE de que os dados financeiros deste mês ainda NÃO foram carregados no sistema (Upload Pendente). NÃO assuma que a execução foi zero por incompetência ou falha de gestão. Informe ao usuário que os dados de realizado parecem estar pendentes de carga."
                
            return resumo_texto
        except Exception as e:
            return f"Erro ao ler dados: {str(e)}"

    def _consultar_especialista(self, persona: str, prompt_base: str, user_query: str) -> str:
        """Consulta um agente especialista específico."""
        
        system_prompts = {
            "CFO": """Você é o CFO Estratégico. Seu foco é macroeconomia, estratégia de alocação de capital e criação de valor a longo prazo.
                     Você usa termos sofisticados de finanças corporativas (CAPEX, OPEX, EBITDA Ajustado, Rolling Forecast).
                     Sua base teórica vem das melhores práticas de mercado e finanças corporativas.
                     Seja direto, executivo e focado em 'big picture'.""",
            
            "Controller": """Você é o Controller Operacional. Seu foco é detalhe, desvio orçamentário, centro de custo e conta contábil.
                            Você é cético, analítico e procura onde o dinheiro está vazando.
                            Você analisa 'Razão', 'Lançamentos' e 'Deltas'.""",
            
            "Auditor": """Você é o Auditor de Riscos e Compliance. Seu foco é governança, normas contábeis (IAS 37/CPC 25) e controle interno.
                         Você se preocupa com provisões não realizadas, riscos de passivos ocultos e justificativas de gastos (OBZ).
                         Seja formal e aponte riscos potenciais.""",
                         
            "Analyst": """Você é o Analista de Forecast. Seu foco é prever o futuro com base em tendências matemáticas.
                         Você fala sobre projeção linear, sazonalidade, intervalos de confiança e cenários.
                         Você olha para frente, não para trás."""
        }
        
        full_prompt = f"""
        [PERSONA: {persona.upper()}]
        {system_prompts.get(persona, "")}
        
        [DADOS FINANCEIROS ATUAIS]
        {self._get_contexto_financeiro()}
        
        [PERGUNTA DO USUÁRIO]
        {user_query}
        
        Responda como sua persona.
        """
        
        # Simula uma chamada isolada para essa persona
        # Em produção, isso poderia ser chamadas paralelas
        messages = [{"role": "user", "content": full_prompt}]
        
        # Estrategia Hibrida de Modelos (Gemini 3 Pro vs Flash)
        provider_for_call = self.provider
        
        # Personas operacionais usam Flash (mais rapido/eficiente)
        if persona in ["Controller", "Analyst"] and "Gemini" in self.provider:
            provider_for_call = self.provider + " Flash"
            
        return get_ai_chat_response(messages, self.api_key, provider_for_call)

    def realizar_reuniao_board(self, user_query: str) -> Dict[str, str]:
        """
        Realiza uma consulta 'Round Table' com todos os membros do board.
        Retorna as opiniões individuais e uma síntese.
        """
        # 1. Coleta opiniões (sequencial para MVP, idealmente paralelo)
        opinioes = {}
        
        # Decide quais agentes chamar baseado na query (pode ser otimizado)
        # Para MVP, chama todos ou os principais
        personas = ["CFO", "Controller", "Auditor"]
        
        for p in personas:
            opinioes[p] = self._consultar_especialista(p, "", user_query)
            
        # 2. Orquestrador Sintetiza
        sintese_prompt = f"""
        Você é o Presidente do Conselho (Chairman).
        Analise as opiniões dos seus diretores abaixo e forneça uma resposta conclusiva e integrada para o usuário.
        
        [PERGUNTA] {user_query}
        
        [OPINIÃO CFO] {opinioes.get('CFO')}
        [OPINIÃO CONTROLLER] {opinioes.get('Controller')}
        [OPINIÃO AUDITOR] {opinioes.get('Auditor')}
        
        Gere uma resposta final coesa em Markdown.
        """
        
        messages = [{"role": "user", "content": sintese_prompt}]
        sintese = get_ai_chat_response(messages, self.api_key, self.provider)
        
        return {
            "opinioes": opinioes,
            "sintese": sintese
        }
