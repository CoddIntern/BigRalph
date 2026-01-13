"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional


# =============================================================================
# Raffle Schemas
# =============================================================================

class RaffleBase(BaseModel):
    """Base raffle fields shared across schemas."""
    title: str
    description: Optional[str] = None
    category: str
    ticket_price: int
    total_tickets: int
    item_value: Optional[int] = None
    image: Optional[str] = None


class RaffleOut(RaffleBase):
    """
    Response schema for raffle data.
    Includes computed fields for progress and ended status.
    """
    id: str
    tickets_sold: int
    end_time: datetime
    is_ended: bool
    progress_percent: float = Field(default=0.0, description="Percentage of tickets sold (0-100)")

    class Config:
        from_attributes = True

    @field_validator('progress_percent', mode='before')
    @classmethod
    def compute_progress(cls, v, info):
        """Progress is computed in the router, this is a fallback."""
        return v if v is not None else 0.0


# =============================================================================
# Ticket Schemas
# =============================================================================

class TicketPurchaseRequest(BaseModel):
    """Request schema for purchasing tickets."""
    quantity: int = Field(..., ge=1, description="Number of tickets to purchase (must be >= 1)")


class TicketPurchaseResponse(BaseModel):
    """Response after successful ticket purchase."""
    message: str
    tickets_purchased: int
    total_cost: int
    balance: int  # Remaining balance after purchase (in Naira)
    raffle: RaffleOut


# =============================================================================
# Comment Schemas
# =============================================================================

class CommentCreate(BaseModel):
    """Request schema for creating a comment."""
    author: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=2000)
    is_admin: bool = Field(default=False, description="Set to true for admin replies")


class CommentOut(BaseModel):
    """Response schema for comment data."""
    id: int
    author: str
    message: str
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Auth Schemas
# =============================================================================

class UserRegister(BaseModel):
    """Request schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)


class UserLogin(BaseModel):
    """Request schema for user login."""
    email: EmailStr
    password: str


class UserOut(BaseModel):
    """Response schema for user data (no password)."""
    id: str
    email: str
    first_name: str
    last_name: str
    picture: Optional[str] = None
    balance: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Response schema for login token."""
    access_token: str
    token_type: str = "bearer"


# =============================================================================
# Transaction Schemas (replaces Wallet schemas)
# =============================================================================

class TransactionOut(BaseModel):
    """Response schema for transaction data."""
    id: str
    amount: int  # In Naira (positive=credit, negative=debit)
    type: str  # "credit" or "debit"
    description: Optional[str]
    balance_after: int  # Running balance after this transaction
    reference: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FundRequest(BaseModel):
    """Request schema for funding account."""
    amount: int = Field(..., gt=0, description="Amount to add in Naira")


class BalanceOut(BaseModel):
    """Response schema for balance data."""
    balance: int  # Balance in Naira
    balance_naira: float  # Convenience field: balance in Naira


# =============================================================================
# Payment Schemas
# =============================================================================

class PaymentInitRequest(BaseModel):
    """Request schema for initializing a payment."""
    amount: int = Field(..., gt=0, description="Amount to fund in Naira")
    provider: str = Field(..., description="Payment provider: paystack, flutterwave, or xoropay")
    callback_url: Optional[str] = Field(None, description="URL to redirect after payment")


class PaymentInitResponse(BaseModel):
    """Response after initializing a payment."""
    success: bool
    reference: str
    authorization_url: Optional[str] = None
    message: str


class PaymentVerifyRequest(BaseModel):
    """Request schema for verifying a payment."""
    reference: str = Field(..., description="Transaction reference to verify")
    provider: str = Field(..., description="Payment provider used for the transaction")


class PaymentVerifyResponse(BaseModel):
    """Response after verifying a payment."""
    success: bool
    reference: str
    amount: int  # Amount in Naira
    balance: Optional[int] = None  # New balance after crediting (if successful)
    message: str
