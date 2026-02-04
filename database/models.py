"""
database/models.py
==================
Modelos SQLAlchemy para o banco de dados de lançamentos realizados.

Este módulo define:
- Tabela de lançamentos realizados mensais
- Configuração do engine SQLite
- Funções de inicialização do banco

Autor: Sistema Orçamentário 2026
Data: Janeiro/2026
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, 
    Boolean, DateTime, Text, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# =============================================================================
# CONFIGURAÇÃO DO BANCO
# =============================================================================

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente (.env) se existirem
load_dotenv()

# ... (imports anteriores se mantêm, mas vou substituir o bloco de config)

# Diretório do banco de dados (Fallback SQLite)
DATABASE_DIR = Path(__file__).parent.parent / "data" / "database"
DATABASE_PATH = DATABASE_DIR / "lancamentos_2026.db"

# Base declarativa
Base = declarative_base()


def get_engine():
    """
    Retorna o engine SQLAlchemy.
    Prioriza DATABASE_URL (Env ou Secrets).
    Caso contrário, usa SQLite local.
    """
    db_url = os.getenv("DATABASE_URL")
    
    # Tentativa de fallback para Streamlit Secrets (Cloud)
    if not db_url:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
                db_url = st.secrets["DATABASE_URL"]
        except Exception:
            pass # Ignora erros de importação ou contexto fora do Streamlit

    if db_url:
        # Configuração para Postgres (Neon/Production)
        # Substitui 'postgres://' por 'postgresql://' caso venha errado
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        return create_engine(
            db_url,
            echo=False,
            pool_pre_ping=True, # Evita desconexões silenciosas
            pool_recycle=300    # Renova conexões a cada 5 min
        )
    else:
        # Configuração para SQLite (Local/Fallback)
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        connection_string = f"sqlite:///{DATABASE_PATH}"
        
        return create_engine(
            connection_string,
            echo=False,
            connect_args={"check_same_thread": False}
        )


def get_session():
    """
    Retorna uma nova sessão do banco de dados.
    
    Returns:
        Session SQLAlchemy
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    """
    Inicializa o banco de dados, criando todas as tabelas.
    """
    engine = get_engine()
    Base.metadata.create_all(engine)


# =============================================================================
# MODELOS
# =============================================================================

class LancamentoRealizado(Base):
    """
    Modelo para lançamentos de valores realizados mensais.
    
    Esta tabela armazena os lançamentos de custos realizados ao longo do ano,
    permitindo comparação com o orçamento previsto (Orçamento V1 2026).
    """
    
    __tablename__ = 'lancamentos_realizados'
    
    # Identificador único
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Período
    ano = Column(Integer, nullable=False, default=2026, index=True)
    mes = Column(String(3), nullable=False, index=True)  # JAN, FEV, etc.
    
    # Centro de Custo (com hierarquia)
    centro_gasto_codigo = Column(String(11), nullable=False, index=True)
    centro_gasto_pai = Column(String(8), nullable=False, index=True)  # Primeiros 8 dígitos
    centro_gasto_classe = Column(String(1), nullable=False)  # 9º dígito (0-9)
    centro_gasto_classe_nome = Column(String(30))  # Nome da classe
    centro_gasto_descricao = Column(String(200))  # Descrição do centro
    ativo = Column(String(50), index=True)  # GASCOM, GASCAC, COS, G&A, etc.
    is_cos = Column(Boolean, default=False)  # True se custo administrativo (COS)
    is_ga = Column(Boolean, default=False)  # True se custo de suporte (G&A)
    is_sem_hierarquia = Column(Boolean, default=False)  # True se COS ou G&A (não segue hierarquia pai-filho)
    
    # Hierarquia Geográfica/Operacional (Adicionado Fev/2026)
    regional = Column(String(50), index=True, nullable=True)
    base = Column(String(50), index=True, nullable=True)
    
    # Conta Contábil
    conta_contabil_codigo = Column(String(15), nullable=False, index=True)
    conta_contabil_descricao = Column(String(200))
    
    # Detalhes do lançamento
    fornecedor = Column(String(200))
    descricao = Column(Text)
    valor = Column(Float, nullable=False)  # Negativo = custo
    
    # Metadados
    data_lancamento = Column(DateTime, default=datetime.now)
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    usuario = Column(String(100))
    observacoes = Column(Text)
    
    # Índices compostos para consultas frequentes
    __table_args__ = (
        Index('idx_periodo_centro', 'ano', 'mes', 'centro_gasto_codigo'),
        Index('idx_periodo_conta', 'ano', 'mes', 'conta_contabil_codigo'),
        Index('idx_ativo_mes', 'ativo', 'mes'),
    )
    
    def __repr__(self):
        return (
            f"<Lancamento(id={self.id}, mes={self.mes}/{self.ano}, "
            f"centro={self.centro_gasto_codigo}, valor={self.valor})>"
        )
    
    def to_dict(self) -> dict:
        """Converte o lançamento para dicionário."""
        return {
            'id': self.id,
            'ano': self.ano,
            'mes': self.mes,
            'centro_gasto_codigo': self.centro_gasto_codigo,
            'centro_gasto_pai': self.centro_gasto_pai,
            'centro_gasto_classe': self.centro_gasto_classe,
            'centro_gasto_classe_nome': self.centro_gasto_classe_nome,
            'centro_gasto_descricao': self.centro_gasto_descricao,
            'ativo': self.ativo,
            'is_cos': self.is_cos,
            'is_ga': self.is_ga,
            'is_sem_hierarquia': self.is_sem_hierarquia,
            'regional': self.regional,
            'base': self.base,
            'conta_contabil_codigo': self.conta_contabil_codigo,
            'conta_contabil_descricao': self.conta_contabil_descricao,
            'fornecedor': self.fornecedor,
            'descricao': self.descricao,
            'valor': self.valor,
            'data_lancamento': self.data_lancamento.isoformat() if self.data_lancamento else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'usuario': self.usuario,
            'observacoes': self.observacoes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LancamentoRealizado':
        """Cria uma instância a partir de um dicionário."""
        return cls(
            ano=data.get('ano', 2026),
            mes=data.get('mes', '').upper(),
            centro_gasto_codigo=data.get('centro_gasto_codigo', ''),
            centro_gasto_pai=data.get('centro_gasto_pai', ''),
            centro_gasto_classe=data.get('centro_gasto_classe', ''),
            centro_gasto_classe_nome=data.get('centro_gasto_classe_nome', ''),
            centro_gasto_descricao=data.get('centro_gasto_descricao', ''),
            ativo=data.get('ativo', ''),
            is_cos=data.get('is_cos', False),
            is_ga=data.get('is_ga', False),
            is_sem_hierarquia=data.get('is_sem_hierarquia', False),
            regional=data.get('regional', None),
            base=data.get('base', None),
            conta_contabil_codigo=data.get('conta_contabil_codigo', ''),
            conta_contabil_descricao=data.get('conta_contabil_descricao', ''),
            fornecedor=data.get('fornecedor', ''),
            descricao=data.get('descricao', ''),
            valor=float(data.get('valor', 0)),
            usuario=data.get('usuario', ''),
            observacoes=data.get('observacoes', '')
        )


class RazaoRealizado(Base):
    """
    Tabela para armazenar o Razão de Gastos (detalhado) vindo do P&L.
    Permite auditoria cruzada com Provisões.
    """
    __tablename__ = 'razao_realizados'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ano = Column(Integer, nullable=False, index=True)
    mes = Column(String(3), nullable=False, index=True)
    centro_gasto_codigo = Column(String(11), nullable=False, index=True)
    conta_contabil_codigo = Column(String(15), nullable=False, index=True)
    fornecedor = Column(String(200))
    descricao = Column(Text)
    valor = Column(Float, nullable=False)
    data_lancamento = Column(DateTime)
    numero_registro = Column(String(50))

    # Metadados de carga
    data_carga = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'ano': self.ano,
            'mes': self.mes,
            'centro': self.centro_gasto_codigo,
            'conta': self.conta_contabil_codigo,
            'fornecedor': self.fornecedor,
            'descricao': self.descricao,
            'valor': self.valor,
            'data_lancamento': self.data_lancamento.isoformat() if self.data_lancamento else None
        }


# =============================================================================
# NOVOS MODELOS (FASES 5-7)
# =============================================================================

class ForecastCenario(Base):
    """
    Representa um cenário de previsão (Fase 5 - Feature A).
    Ex: 'Cenário Otimista Jan/26', 'Forecast Automático V1'
    """
    __tablename__ = 'forecast_cenarios'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(200))
    tipo = Column(String(20), default='AUTOMATICO')  # AUTOMATICO, MANUAL
    data_criacao = Column(DateTime, default=datetime.now)
    usuario_criador = Column(String(100))
    ano_referencia = Column(Integer, default=2026)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'tipo': self.tipo,
            'data_criacao': self.data_criacao.isoformat(),
            'usuario_criador': self.usuario_criador
        }

class ForecastEntry(Base):
    """
    Entradas individuais de previsão vinculadas a um cenário.
    """
    __tablename__ = 'forecast_entries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cenario_id = Column(Integer, nullable=False, index=True) # FK lógica
    mes = Column(String(3), nullable=False, index=True)
    centro_gasto_codigo = Column(String(11), nullable=False, index=True)
    conta_contabil_codigo = Column(String(15), nullable=False)
    valor_previsto = Column(Float, nullable=False)
    metodo_calculo = Column(String(50)) # linear, media_movel, manual
    
    __table_args__ = (
        Index('idx_forecast_cenario_mes', 'cenario_id', 'mes'),
    )

class Provisao(Base):
    """
    Gestão de provisões e passivos (Fase 6 - Feature B).
    """
    __tablename__ = 'provisoes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    descricao = Column(String(200), nullable=False)
    valor_estimado = Column(Float, nullable=False)
    centro_gasto_codigo = Column(String(11), nullable=False, index=True)
    conta_contabil_codigo = Column(String(15), nullable=False)
    mes_competencia = Column(String(3), nullable=False) # Mês a que se refere
    
    # Ciclo de vida: PENDENTE -> REALIZADA (Consumida) -> CANCELADA (Revertida)
    status = Column(String(20), default='PENDENTE', index=True) 
    
    # Justificativa Base Zero (Feature E)
    justificativa_obz = Column(Text)
    tipo_despesa = Column(String(20), default='Variavel') # Core, Nice-to-have, etc.
    
    # Hierarquia Geográfica (Adicionado Fev/2026)
    regional = Column(String(50), nullable=True)
    base = Column(String(50), nullable=True)
    
    # Novos Campos (Fase 8.3)
    numero_contrato = Column(String(50), nullable=True)
    cadastrado_sistema = Column(Boolean, default=False)
    numero_registro = Column(String(50), nullable=True) # SE, Fusion, RC
    
    # Vínculo com lançamento real (quando a provisão se concretiza)
    lancamento_realizado_id = Column(Integer, nullable=True) # FK lógica
    
    data_criacao = Column(DateTime, default=datetime.now)
    data_atualizacao = Column(DateTime, onupdate=datetime.now)
    usuario = Column(String(100))

    def to_dict(self):
        return {
            'id': self.id,
            'descricao': self.descricao,
            'valor_estimado': self.valor_estimado,
            'centro_gasto_codigo': self.centro_gasto_codigo,
            'conta_contabil_codigo': self.conta_contabil_codigo,
            'mes_competencia': self.mes_competencia,
            'status': self.status,
            'justificativa_obz': self.justificativa_obz,
            'numero_contrato': self.numero_contrato,
            'cadastrado_sistema': self.cadastrado_sistema,
            'numero_contrato': self.numero_contrato,
            'cadastrado_sistema': self.cadastrado_sistema,
            'numero_registro': self.numero_registro,
            'regional': self.regional,
            'base': self.base
        }

class Remanejamento(Base):
    """
    Transferências de orçamento entre centros (Fase 7 - Feature D).
    """
    __tablename__ = 'remanejamentos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Origem
    centro_origem_codigo = Column(String(11), nullable=False)
    conta_origem_codigo = Column(String(15)) # Opcional se for remanejamento global do centro
    
    # Destino
    centro_destino_codigo = Column(String(11), nullable=False)
    conta_destino_codigo = Column(String(15))
    
    valor = Column(Float, nullable=False)
    mes = Column(String(3), nullable=False)
    
    justificativa = Column(Text, nullable=False)
    
    # Workflow
    status = Column(String(20), default='SOLICITADO') # SOLICITADO, APROVADO, REJEITADO
    solicitante = Column(String(100))
    aprovador = Column(String(100))
    data_aprovacao = Column(DateTime)
    
    data_solicitacao = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'origem': self.centro_origem_codigo,
            'destino': self.centro_destino_codigo,
            'valor': self.valor,
            'status': self.status,
            'justificativa': self.justificativa
        }

class JustificativaOBZ(Base):
    """
    Justificativas de pacotes de gastos para o Orçamento Base Zero (Feature E).
    """
    __tablename__ = 'obz_justificativas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    centro_gasto_codigo = Column(String(11), nullable=False, index=True)
    pacote = Column(String(100), nullable=False) # Ex: Viagens, TI, Consultoria
    descricao = Column(Text, nullable=False)
    valor_orcado = Column(Float, nullable=False)
    classificacao = Column(String(20), nullable=False) # Necessário, Estratégico, etc.
    usuario_responsavel = Column(String(100))
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'centro_gasto_codigo': self.centro_gasto_codigo,
            'pacote': self.pacote,
            'descricao': self.descricao,
            'valor_orcado': self.valor_orcado,
            'classificacao': self.classificacao,
            'usuario_responsavel': self.usuario_responsavel,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

# =============================================================================
# MODELO DE AUTENTICAÇÃO (Fase Segurança)
# =============================================================================

class User(Base):
    """
    Tabela de Usuários para controle de acesso (RBAC).
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100))
    # RBAC Granular: JSON as String (Ex: '{"financeiro": "editor", "admin": "viewer"}')
    permissions = Column(Text, default='{}') 
    
    role = Column(String(20), default='viewer', nullable=False) # admin, editor, viewer
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'role': self.role,
            'permissions': self.permissions,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
