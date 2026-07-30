from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="TSX Paper Account")
    cash_balance = Column(Float, nullable=False, default=100000.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    positions = relationship("Position", back_populates="account", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="account", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="account", cascade="all, delete-orphan")

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    ticker = Column(String, nullable=False, index=True)
    quantity = Column(Float, nullable=False, default=0.0)
    average_buy_price = Column(Float, nullable=False, default=0.0)
    peak_price = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("Account", back_populates="positions")

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    ticker = Column(String, nullable=False, index=True)
    order_type = Column(String, nullable=False) # 'BUY' or 'SELL'
    quantity = Column(Float, nullable=False)
    execution_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    realized_pnl = Column(Float, default=0.0)
    executed_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="trades")

class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_equity = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    stock_value = Column(Float, nullable=False)
    total_pnl = Column(Float, nullable=False)
    realized_pnl = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, nullable=False)

    account = relationship("Account", back_populates="snapshots")
