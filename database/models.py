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

# Diretório do banco de dados
DATABASE_DIR = Path(__file__).parent.parent / "data" / "database"
DATABASE_PATH = DATABASE_DIR / "lancamentos_2026.db"

# Base declarativa
Base = declarative_base()


def get_engine():
    """
    Retorna o engine SQLAlchemy para o banco SQLite.
    
    Returns:
        Engine SQLAlchemy configurado
    """
    # Garantir que o diretório existe
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Conexão SQLite
    connection_string = f"sqlite:///{DATABASE_PATH}"
    
    return create_engine(
        connection_string,
        echo=False,  # Mudar para True para debug de SQL
        connect_args={"check_same_thread": False}  # Necessário para SQLite + Streamlit
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
            conta_contabil_codigo=data.get('conta_contabil_codigo', ''),
            conta_contabil_descricao=data.get('conta_contabil_descricao', ''),
            fornecedor=data.get('fornecedor', ''),
            descricao=data.get('descricao', ''),
            valor=float(data.get('valor', 0)),
            usuario=data.get('usuario', ''),
            observacoes=data.get('observacoes', '')
        )

