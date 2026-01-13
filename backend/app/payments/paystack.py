"""
Paystack payment provider implementation.

Test mode API documentation: https://paystack.com/docs/api/
"""
import os
import httpx
import hmac
import hashlib
from typing import Optional

from .base import PaymentProvider, PaymentResult, PaymentStatus


class PaystackProvider(PaymentProvider):
    """Paystack payment provider for Nigerian payments."""
    
    BASE_URL = "https://api.paystack.co"
    
    def __init__(self):
        self._secret_key = os.getenv("PAYSTACK_SECRET_KEY")
        self._public_key = os.getenv("PAYSTACK_PUBLIC_KEY")
    
    @property
    def name(self) -> str:
        return "paystack"
    
    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._secret_key}",
            "Content-Type": "application/json"
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
        Initialize a Paystack transaction.
        
        Amount is in Naira (internally converted to kobo for Paystack API).
        """
        paystack_amount = int(amount * 100)
        payload = {
            "amount": paystack_amount,
            "email": email,
            "reference": reference,
            "currency": "NGN",
        }
        
        if callback_url:
            payload["callback_url"] = callback_url
        
        if metadata:
            payload["metadata"] = metadata
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/transaction/initialize",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                
                data = response.json()
                
                if response.status_code == 200 and data.get("status"):
                    return PaymentResult(
                        success=True,
                        status=PaymentStatus.PENDING,
                        reference=reference,
                        amount=amount,
                        message="Transaction initialized",
                        authorization_url=data["data"]["authorization_url"],
                        provider_reference=data["data"]["reference"]
                    )
                else:
                    return PaymentResult(
                        success=False,
                        status=PaymentStatus.FAILED,
                        reference=reference,
                        amount=amount,
                        message=data.get("message", "Initialization failed")
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
        """Verify a Paystack transaction."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/transaction/verify/{reference}",
                    headers=self._get_headers(),
                    timeout=30.0
                )
                
                data = response.json()
                
                if response.status_code == 200 and data.get("status"):
                    tx_data = data["data"]
                    
                    status_map = {
                        "success": PaymentStatus.SUCCESS,
                        "failed": PaymentStatus.FAILED,
                        "abandoned": PaymentStatus.CANCELLED,
                    }
                    
                    status = status_map.get(tx_data["status"], PaymentStatus.PENDING)
                    
                    return PaymentResult(
                        success=status == PaymentStatus.SUCCESS,
                        status=status,
                        reference=reference,
                        amount=int(tx_data["amount"] / 100),  # Convert kobo back to Naira
                        message=tx_data.get("gateway_response", "Verified"),
                        provider_reference=str(tx_data["id"]),
                        metadata=tx_data.get("metadata")
                    )
                else:
                    return PaymentResult(
                        success=False,
                        status=PaymentStatus.FAILED,
                        reference=reference,
                        amount=0,
                        message=data.get("message", "Verification failed")
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
        return self._secret_key
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Paystack webhook signature using HMAC SHA512."""
        computed = hmac.new(
            self._secret_key.encode(),
            payload,
            hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(computed, signature)
