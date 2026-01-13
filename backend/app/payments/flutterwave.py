"""
Flutterwave payment provider implementation.

Test mode API documentation: https://developer.flutterwave.com/docs
"""
import os
import httpx
import hmac
import hashlib
from typing import Optional

from .base import PaymentProvider, PaymentResult, PaymentStatus


class FlutterwaveProvider(PaymentProvider):
    """Flutterwave payment provider for African payments."""
    
    BASE_URL = "https://api.flutterwave.com/v3"
    
    def __init__(self):
        self._secret_key = os.getenv("FLUTTERWAVE_SECRET_KEY")
        self._public_key = os.getenv("FLUTTERWAVE_PUBLIC_KEY")
        self._webhook_secret = os.getenv("FLUTTERWAVE_WEBHOOK_SECRET", "")
    
    @property
    def name(self) -> str:
        return "flutterwave"
    
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
        Initialize a Flutterwave transaction.
        """
        # Flutterwave expects amount in Naira
        payload = {
            "tx_ref": reference,
            "amount": amount,
            "currency": "NGN",
            "customer": {
                "email": email
            },
            "customizations": {
                "title": "BigRalph Wallet Funding"
            }
        }
        
        if callback_url:
            payload["redirect_url"] = callback_url
        
        if metadata:
            payload["meta"] = metadata
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/payments",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                
                data = response.json()
                
                if response.status_code == 200 and data.get("status") == "success":
                    return PaymentResult(
                        success=True,
                        status=PaymentStatus.PENDING,
                        reference=reference,
                        amount=amount,
                        message="Transaction initialized",
                        authorization_url=data["data"]["link"],
                        metadata=data.get("meta")
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
        """Verify a Flutterwave transaction by tx_ref."""
        try:
            async with httpx.AsyncClient() as client:
                # First get transaction by tx_ref
                response = await client.get(
                    f"{self.BASE_URL}/transactions",
                    headers=self._get_headers(),
                    params={"tx_ref": reference},
                    timeout=30.0
                )
                
                data = response.json()
                
                if response.status_code == 200 and data.get("status") == "success":
                    transactions = data.get("data", [])
                    
                    if not transactions:
                        return PaymentResult(
                            success=False,
                            status=PaymentStatus.PENDING,
                            reference=reference,
                            amount=0,
                            message="Transaction not found or still pending"
                        )
                    
                    tx = transactions[0]
                    
                    status_map = {
                        "successful": PaymentStatus.SUCCESS,
                        "failed": PaymentStatus.FAILED,
                        "pending": PaymentStatus.PENDING,
                    }
                    
                    status = status_map.get(tx["status"], PaymentStatus.PENDING)
                    # Flutterwave returns amount in Naira
                    amount_naira = tx["amount"]
                    
                    return PaymentResult(
                        success=status == PaymentStatus.SUCCESS,
                        status=status,
                        reference=reference,
                        amount=int(amount_naira),
                        message=tx.get("processor_response", "Verified"),
                        provider_reference=str(tx["id"]),
                        metadata=tx.get("meta")
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
        return self._webhook_secret if self._webhook_secret else None
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Flutterwave webhook using verif-hash header."""
        if not self._webhook_secret:
            return False
        return hmac.compare_digest(self._webhook_secret, signature)
