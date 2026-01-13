"""
Base payment provider interface.

All payment providers must implement this interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class PaymentStatus(Enum):
    """Payment status enum."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PaymentResult:
    """Result of a payment operation."""
    success: bool
    status: PaymentStatus
    reference: str
    amount: int  # Amount in Naira
    message: str
    authorization_url: Optional[str] = None  # For initialization
    provider_reference: Optional[str] = None  # Provider's transaction ID
    metadata: Optional[dict] = None


class PaymentProvider(ABC):
    """
    Abstract base class for payment providers.
    
    All payment providers must implement the initialize_payment and
    verify_payment methods for a consistent interface.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        pass
    
    @abstractmethod
    async def initialize_payment(
        self,
        amount: int,
        email: str,
        reference: str,
        callback_url: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> PaymentResult:
        """
        Initialize a payment transaction.
        
        Args:
            amount: Amount in Naira
            email: Customer email address
            reference: Unique transaction reference
            callback_url: URL to redirect after payment
            metadata: Additional transaction metadata
            
        Returns:
            PaymentResult with authorization_url for redirect
        """
        pass
    
    @abstractmethod
    async def verify_payment(self, reference: str) -> PaymentResult:
        """
        Verify a payment transaction.
        
        Args:
            reference: Transaction reference to verify
            
        Returns:
            PaymentResult with verification status
        """
        pass
    
    def get_webhook_secret(self) -> Optional[str]:
        """
        Get the webhook secret for signature verification.
        
        Override this in providers that support webhooks.
        """
        return None
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature.
        
        Override this in providers that support webhooks.
        """
        return False
