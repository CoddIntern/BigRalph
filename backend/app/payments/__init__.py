"""
Payment providers module.

Provides a provider-agnostic interface for payment processing.
Supports Paystack, Flutterwave, and XoroPay.
"""

from .base import PaymentProvider, PaymentResult, PaymentStatus
from .paystack import PaystackProvider
from .flutterwave import FlutterwaveProvider
from .xoropay import XoroPayProvider

__all__ = [
    'PaymentProvider',
    'PaymentResult',
    'PaymentStatus',
    'PaystackProvider',
    'FlutterwaveProvider',
    'XoroPayProvider',
]


def get_provider(name: str) -> PaymentProvider:
    """
    Get a payment provider instance by name.
    
    Args:
        name: Provider name ('paystack', 'flutterwave', 'xoropay')
        
    Returns:
        PaymentProvider instance
        
    Raises:
        ValueError: If provider name is unknown
    """
    providers = {
        'paystack': PaystackProvider,
        'flutterwave': FlutterwaveProvider,
        'xoropay': XoroPayProvider,
    }
    
    provider_class = providers.get(name.lower())
    if not provider_class:
        raise ValueError(f"Unknown payment provider: {name}")
    
    return provider_class()
