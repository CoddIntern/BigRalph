"""
Wallet router for managing user funds.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from ..dependencies import get_db, get_current_user
from ..models import User, Wallet, WalletTransaction
from ..schemas import WalletOut, WalletFundRequest, WalletTransactionOut

router = APIRouter(tags=["Wallet"])


def wallet_to_response(wallet: Wallet) -> WalletOut:
    """Convert Wallet model to response schema with computed Naira balance."""
    return WalletOut(
        id=wallet.id,
        balance=wallet.balance,
        balance_naira=wallet.balance / 100,  # Convert kobo to Naira
        updated_at=wallet.updated_at or datetime.utcnow()
    )


@router.get("/wallet", response_model=WalletOut)
def get_wallet(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's wallet balance.
    
    Requires authentication.
    """
    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    
    if not wallet:
        # This shouldn't happen if registration works correctly, but handle it
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    return wallet_to_response(wallet)


@router.post("/wallet/fund", response_model=WalletOut)
def fund_wallet(
    data: WalletFundRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add funds to wallet (manual funding for now).
    
    In production, this would integrate with Paystack or similar.
    Amount is in kobo (100 kobo = 1 Naira).
    """
    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    # Update balance
    wallet.balance += data.amount
    wallet.updated_at = datetime.utcnow()
    
    # Sync user balance
    user.balance = wallet.balance
    user.updated_at = datetime.utcnow()
    
    # Create transaction record
    transaction = WalletTransaction(
        wallet_id=wallet.id,
        amount=data.amount,
        type="credit",
        reference=None,  # Would be payment reference in production
        description=f"Manual wallet funding: ₦{data.amount / 100:,.2f}"
    )
    db.add(transaction)
    
    db.commit()
    db.refresh(wallet)
    db.refresh(user)
    
    return wallet_to_response(wallet)


@router.get("/wallet/transactions", response_model=list[WalletTransactionOut])
def get_wallet_transactions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """
    Get wallet transaction history.
    
    Returns most recent transactions first.
    """
    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    transactions = (
        db.query(WalletTransaction)
        .filter(WalletTransaction.wallet_id == wallet.id)
        .order_by(WalletTransaction.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return transactions
