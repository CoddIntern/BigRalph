"""
Wallet router for managing user funds.

Refactored to use Transaction ledger instead of separate Wallet table.
User balance is stored directly on the User model.
Includes payment provider integration for Paystack, Flutterwave, XoroPay.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from ..dependencies import get_db, get_current_user
from ..models import User, Transaction
from ..schemas import (
    TransactionOut, FundRequest, BalanceOut,
    PaymentInitRequest, PaymentInitResponse,
    PaymentVerifyRequest, PaymentVerifyResponse
)
from ..payments import get_provider, PaymentStatus

router = APIRouter(tags=["Wallet"])


@router.get("/wallet", response_model=BalanceOut)
def get_balance(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's balance.
    
    Requires authentication.
    """
    return BalanceOut(
        balance=user.balance,
        balance_naira=float(user.balance)  # Already in Naira
    )


@router.post("/wallet/fund", response_model=BalanceOut)
def fund_account(
    data: FundRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add funds to account (manual funding for testing).
    
    For production, use /wallet/fund/initialize with a payment provider.
    Amount is in Naira.
    """
    try:
        # Calculate new balance
        new_balance = user.balance + data.amount
        
        # Update user balance atomically
        result = db.execute(
            text("""
                UPDATE users 
                SET balance = balance + :amount,
                    updated_at = :now
                WHERE id = :user_id
            """),
            {"amount": data.amount, "user_id": user.id, "now": datetime.utcnow()}
        )
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update balance"
            )
        
        # Create transaction record
        transaction = Transaction(
            user_id=user.id,
            amount=data.amount,
            type="credit",
            description=f"Manual wallet funding: ₦{data.amount:,}",
            balance_after=new_balance,
            reference=None
        )
        db.add(transaction)
        
        db.commit()
        db.refresh(user)
        
        return BalanceOut(
            balance=user.balance,
            balance_naira=float(user.balance)  # Already in Naira
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transaction failed. Please try again."
        )


@router.get("/wallet/transactions", response_model=list[TransactionOut])
def get_transactions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """
    Get transaction history.
    
    Returns most recent transactions first.
    """
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return transactions


# =============================================================================
# Payment Provider Endpoints
# =============================================================================

@router.post("/wallet/fund/initialize", response_model=PaymentInitResponse)
async def initialize_payment(
    data: PaymentInitRequest,
    user: User = Depends(get_current_user)
):
    """
    Initialize a payment with the specified provider.
    
    Supported providers: paystack, flutterwave, xoropay
    Returns an authorization URL to redirect the user for payment.
    """
    try:
        provider = get_provider(data.provider)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Generate unique reference
    reference = f"bigralph_{data.provider}_{uuid.uuid4().hex[:12]}"
    
    # Initialize payment with provider
    result = await provider.initialize_payment(
        amount=data.amount,
        email=user.email,
        reference=reference,
        callback_url=data.callback_url,
        metadata={"user_id": user.id}
    )
    
    return PaymentInitResponse(
        success=result.success,
        reference=reference,
        authorization_url=result.authorization_url,
        message=result.message
    )


@router.post("/wallet/fund/verify", response_model=PaymentVerifyResponse)
async def verify_payment(
    data: PaymentVerifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify a payment and credit user balance if successful.
    
    Call this after the user returns from the payment provider.
    """
    try:
        provider = get_provider(data.provider)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Verify with provider
    result = await provider.verify_payment(data.reference)
    
    if not result.success or result.status != PaymentStatus.SUCCESS:
        return PaymentVerifyResponse(
            success=False,
            reference=data.reference,
            amount=result.amount,
            message=result.message
        )
    
    # Check if this reference was already processed
    existing = db.query(Transaction).filter(
        Transaction.reference == data.reference
    ).first()
    
    if existing:
        return PaymentVerifyResponse(
            success=True,
            reference=data.reference,
            amount=result.amount,
            balance=user.balance,
            message="Payment already processed"
        )
    
    # Credit user balance
    try:
        new_balance = user.balance + result.amount
        
        db.execute(
            text("""
                UPDATE users 
                SET balance = balance + :amount,
                    updated_at = :now
                WHERE id = :user_id
            """),
            {"amount": result.amount, "user_id": user.id, "now": datetime.utcnow()}
        )
        
        # Create transaction record
        transaction = Transaction(
            user_id=user.id,
            amount=result.amount,
            type="credit",
            description=f"Wallet funding via {data.provider}: ₦{result.amount:,}",
            balance_after=new_balance,
            reference=data.reference
        )
        db.add(transaction)
        
        db.commit()
        db.refresh(user)
        
        return PaymentVerifyResponse(
            success=True,
            reference=data.reference,
            amount=result.amount,
            balance=user.balance,
            message="Payment verified and credited successfully"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to credit balance. Please contact support."
        )


@router.post("/wallet/webhook/{provider}")
async def handle_webhook(
    provider: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle payment provider webhooks.
    
    Providers send notifications for completed/failed payments.
    """
    try:
        payment_provider = get_provider(provider)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider: {provider}"
        )
    
    # Get raw body and signature
    body = await request.body()
    signature = request.headers.get("x-paystack-signature") or \
                request.headers.get("verif-hash") or \
                request.headers.get("x-xoropay-signature", "")
    
    # Verify signature
    if payment_provider.get_webhook_secret():
        if not payment_provider.verify_webhook_signature(body, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
    
    # Parse webhook data
    import json
    data = json.loads(body)
    
    # Extract reference and event type based on provider
    reference = None
    event_type = None
    
    if provider == "paystack":
        event_type = data.get("event")
        reference = data.get("data", {}).get("reference")
    elif provider == "flutterwave":
        event_type = data.get("event")
        reference = data.get("data", {}).get("tx_ref")
    elif provider == "xoropay":
        event_type = data.get("event") or data.get("type")
        reference = data.get("data", {}).get("reference") or data.get("reference")
    
    # Only process successful payment events
    success_events = ["charge.success", "charge.completed", "successful"]
    if event_type not in success_events:
        return {"status": "ignored", "event": event_type}
    
    if not reference:
        return {"status": "ignored", "reason": "no reference"}
    
    # Check if already processed
    existing = db.query(Transaction).filter(
        Transaction.reference == reference
    ).first()
    
    if existing:
        return {"status": "already_processed"}
    
    # Verify and credit (async)
    result = await payment_provider.verify_payment(reference)
    
    if result.success and result.status == PaymentStatus.SUCCESS:
        # Extract user_id from metadata
        user_id = result.metadata.get("user_id") if result.metadata else None
        
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                new_balance = user.balance + result.amount
                
                db.execute(
                    text("""
                        UPDATE users 
                        SET balance = balance + :amount,
                            updated_at = :now
                        WHERE id = :user_id
                    """),
                    {"amount": result.amount, "user_id": user_id, "now": datetime.utcnow()}
                )
                
                transaction = Transaction(
                    user_id=user_id,
                    amount=result.amount,
                    type="credit",
                    description=f"Webhook: Wallet funding via {provider}",
                    balance_after=new_balance,
                    reference=reference
                )
                db.add(transaction)
                db.commit()
                
                return {"status": "credited", "amount": result.amount}
    
    return {"status": "verification_failed", "message": result.message}
