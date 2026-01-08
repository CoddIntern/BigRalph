from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import uuid


# =============================================================================
# Raffle Models
# =============================================================================

class Raffle(Base):
    """
    Raffle model representing a giveaway item.
    
    Note: is_ended can be set manually or computed based on end_time in the API layer.
    """
    __tablename__ = "raffles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)  # Detailed description of the prize
    category = Column(String, nullable=False)  # Cars, Electronics, Gadgets, Land, Fashion
    ticket_price = Column(Integer, nullable=False)  # Price in Naira (₦)
    total_tickets = Column(Integer, nullable=False)
    tickets_sold = Column(Integer, default=0)
    item_value = Column(Integer, nullable=True)  # Prize value in Naira (₦)
    end_time = Column(DateTime, nullable=False)
    image = Column(String, nullable=True)
    is_ended = Column(Boolean, default=False)  # Manually set or computed from end_time

    comments = relationship("Comment", back_populates="raffle", cascade="all, delete-orphan")


class Comment(Base):
    """
    Comment model for raffle discussions.
    
    is_admin flag distinguishes admin replies from regular user comments.
    """
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    raffle_id = Column(String, ForeignKey("raffles.id"), nullable=False)
    author = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_admin = Column(Boolean, default=False)  # True for admin replies
    created_at = Column(DateTime, default=datetime.utcnow)

    raffle = relationship("Raffle", back_populates="comments")


# =============================================================================
# User & Authentication Models
# =============================================================================

class User(Base):
    """
    User model for authentication.
    
    Passwords are stored as bcrypt hashes, never plaintext.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False, default="User")
    last_name = Column(String, nullable=False, default="Name")
    picture = Column(String, nullable=True)
    balance = Column(Integer, default=0) # Read source for UI
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # One-to-one relationship with wallet
    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")


# =============================================================================
# Wallet Models
# =============================================================================

class Wallet(Base):
    """
    Wallet model for user funds.
    
    Balance is stored in kobo (1 Naira = 100 kobo) for precision.
    """
    __tablename__ = "wallets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    balance = Column(Integer, default=0)  # Balance in kobo
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="wallet")
    transactions = relationship("WalletTransaction", back_populates="wallet", cascade="all, delete-orphan")


class WalletTransaction(Base):
    """
    Audit log for all wallet balance changes.
    
    Every credit/debit is recorded for transparency and debugging.
    """
    __tablename__ = "wallet_transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    wallet_id = Column(String, ForeignKey("wallets.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # Amount in kobo (positive for credit, negative for debit)
    type = Column(String, nullable=False)  # "credit" or "debit"
    reference = Column(String, nullable=True)  # Optional reference (e.g., raffle_id for ticket purchase)
    description = Column(String, nullable=True)  # Human-readable description
    created_at = Column(DateTime, default=datetime.utcnow)

    wallet = relationship("Wallet", back_populates="transactions")
