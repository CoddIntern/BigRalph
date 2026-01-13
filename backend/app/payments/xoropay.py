"""
XoroPay payment provider implementation.

XoroPay is Africa's Payment OS.
API Base URL: https://api.xoropay.com (assumed based on standard patterns)

Note: This implementation uses placeholder endpoints since the XoroPay
docs site is a SPA. Update endpoints based on actual API documentation.
"""
import os
import httpx
import hmac
import hashlib
from typing import Optional

from .base import PaymentProvider, PaymentResult, PaymentStatus


class XoroPayProvider(PaymentProvider):
    """XoroPay payment provider for African payments."""
    
    # Update this with actual XoroPay API URL from docs
    BASE_URL = os.getenv("XOROPAY_API_URL", "https://api.xoropay.com/v1")
    
    def __init__(self):
        self._secret_key = os.getenv("XOROPAY_SECRET_KEY")
        self._public_key = os.getenv("XOROPAY_PUBLIC_KEY")
        self._webhook_secret = os.getenv("XOROPAY_WEBHOOK_SECRET", "")
    
    @property
    def name(self) -> str:
        return "xoropay"
    
    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._secret_key}",
            "Content-Type": "application/json",
            "X-API-Key": self._public_key  # Some APIs use this pattern
        }
    
    async def initialize_payment(
        self,
        amount: int,
        email: str,
        reference: str,
        callback_url: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> PaymentResult:
        """
        Initialize a XoroPay transaction.
        """
        # Convert Naira to kobo for internal API if needed, 
        # or keep as Naira if XoroPay expects major unit.
        # Assuming standard smallest unit (kobo) for the outgoing request.
        payload = {
            "amount": int(amount * 100),
            "currency": "NGN",
            "email": email,
            "reference": reference,
            "description": "BigRalph Wallet Funding"
        }
        
        if callback_url:
            payload["callback_url"] = callback_url
            payload["redirect_url"] = callback_url
        
        if metadata:
            payload["metadata"] = metadata
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/transactions/initialize",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                
                data = response.json()
                
                # Adapt based on actual XoroPay response structure
                if response.status_code in [200, 201] and data.get("success", data.get("status") == "success"):
                    return PaymentResult(
                        success=True,
                        status=PaymentStatus.PENDING,
                        reference=reference,
                        amount=amount,
                        message="Transaction initialized",
                        authorization_url=data.get("data", {}).get("authorization_url") or data.get("payment_url"),
                        provider_reference=data.get("data", {}).get("id") or data.get("transaction_id")
                    )
                else:
                    return PaymentResult(
                        success=False,
                        status=PaymentStatus.FAILED,
                        reference=reference,
                        amount=amount,
                        message=data.get("message") or data.get("error", "Initialization failed")
                    )
                    
        except Exception as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                reference=reference,
                amount=amount,
                message=f"Request failed: {str(e)}"
            )
    
    async def verify_payment(self, reference: str) -> PaymentResult:
        """Verify a XoroPay transaction."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/transactions/verify/{reference}",
                    headers=self._get_headers(),
                    timeout=30.0
                )
                
                data = response.json()
                
                # Adapt based on actual XoroPay response structure
                if response.status_code == 200 and data.get("success", data.get("status") == "success"):
                    tx_data = data.get("data", data)
                    
                    tx_status = tx_data.get("status", "").lower()
                    status_map = {
                        "success": PaymentStatus.SUCCESS,
                        "successful": PaymentStatus.SUCCESS,
                        "completed": PaymentStatus.SUCCESS,
                        "failed": PaymentStatus.FAILED,
                        "cancelled": PaymentStatus.CANCELLED,
                        "abandoned": PaymentStatus.CANCELLED,
                    }
                    
                    status = status_map.get(tx_status, PaymentStatus.PENDING)
                    
                    return PaymentResult(
                        success=status == PaymentStatus.SUCCESS,
                        status=status,
                        reference=reference,
                        amount=tx_data.get("amount", 0),
                        message=tx_data.get("message", "Verified"),
                        provider_reference=str(tx_data.get("id", "")),
                        metadata=tx_data.get("metadata")
                    )
                else:
                    return PaymentResult(
                        success=False,
                        status=PaymentStatus.FAILED,
                        reference=reference,
                        amount=0,
                        message=data.get("message") or data.get("error", "Verification failed")
                    )
                    
        except Exception as e:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                reference=reference,
                amount=0,
                message=f"Verification failed: {str(e)}"
            )
    
    def get_webhook_secret(self) -> Optional[str]:
        return self._webhook_secret if self._webhook_secret else None
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify XoroPay webhook signature."""
        if not self._webhook_secret:
            return False
        
        # Standard HMAC SHA256 verification - update based on actual docs
        computed = hmac.new(
            self._webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(computed, signature)
