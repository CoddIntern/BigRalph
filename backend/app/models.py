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

    # Transactions relationship
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")


# =============================================================================
# Transaction Ledger Model (replaces Wallet + WalletTransaction)
# =============================================================================

class Transaction(Base):
    """
    Transaction ledger model for all balance changes.
    
    Each row is an immutable ledger entry. balance_after is the authoritative
    running balance after this transaction.
    
    - amount: Positive for credit, negative for debit
    - type: "credit" or "debit"
    - balance_after: Running balance (must be updated atomically with user.balance)
    """
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)  # Positive=credit, Negative=debit (in Naira)
    type = Column(String, nullable=False)  # "credit" or "debit"
    description = Column(String, nullable=True)
    balance_after = Column(Integer, nullable=False)  # Running balance after this transaction (in Naira)
    reference = Column(String, nullable=True)  # Payment provider reference or raffle_id
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")

