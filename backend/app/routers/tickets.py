"""
Tickets router for purchasing raffle tickets.
Handles race-condition safe atomic ticket purchases with transaction ledger.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from ..dependencies import get_db, get_current_user
from ..models import Raffle, User, Transaction
from ..schemas import TicketPurchaseRequest, TicketPurchaseResponse, RaffleOut

router = APIRouter(tags=["Tickets"])


def raffle_to_response(raffle: Raffle) -> RaffleOut:
    """Convert Raffle model to response schema with computed fields."""
    progress = (raffle.tickets_sold / raffle.total_tickets * 100) if raffle.total_tickets > 0 else 0.0
    is_ended = raffle.is_ended or datetime.utcnow() > raffle.end_time
    
    return RaffleOut(
        id=raffle.id,
        title=raffle.title,
        description=raffle.description,
        category=raffle.category,
        ticket_price=raffle.ticket_price,
        total_tickets=raffle.total_tickets,
        tickets_sold=raffle.tickets_sold,
        item_value=raffle.item_value,
        end_time=raffle.end_time,
        image=raffle.image,
        is_ended=is_ended,
        progress_percent=round(progress, 2)
    )


@router.post("/raffles/{raffle_id}/tickets", response_model=TicketPurchaseResponse)
def purchase_tickets(
    raffle_id: str,
    request: TicketPurchaseRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Purchase tickets for a raffle using account balance.
    
    - Requires authentication
    - Validates raffle exists and is active
    - Enforces max 10 tickets per purchase (via Pydantic)
    - Deducts cost from balance atomically
    - Uses atomic UPDATE to prevent race conditions and overselling
    - Returns updated raffle stats and balance after purchase
    """
    print(f"🚨 BUY ENDPOINT HIT: Raffle={raffle_id}, Qty={request.quantity}, User={user.email if user else 'None'}")
    
    # Fetch the raffle
    raffle = db.query(Raffle).filter(Raffle.id == raffle_id).first()
    if not raffle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raffle not found"
        )
    
    # Check if raffle has ended
    if raffle.is_ended or datetime.utcnow() > raffle.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This raffle has ended"
        )
    
    # Check ticket availability before atomic update
    available_tickets = raffle.total_tickets - raffle.tickets_sold
    if available_tickets <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tickets available - raffle is sold out"
        )
    
    if request.quantity > available_tickets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {available_tickets} tickets remaining"
        )
    
    # Calculate total cost in Naira (all values are in Naira)
    total_cost = raffle.ticket_price * request.quantity
    
    print(f"💰 User balance: ₦{user.balance:,}, Required: ₦{total_cost:,}")

    # Check balance
    if user.balance < total_cost:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient balance. Required: ₦{total_cost:,}, Available: ₦{user.balance:,}"
        )
    
    # === Begin atomic transaction ===
    try:
        # Calculate new balance
        new_balance = user.balance - total_cost
        
        # 1. Deduct from user balance atomically
        balance_result = db.execute(
            text("""
                UPDATE users 
                SET balance = balance - :amount,
                    updated_at = :now
                WHERE id = :user_id 
                AND balance >= :amount
            """),
            {"amount": total_cost, "user_id": user.id, "now": datetime.utcnow()}
        )
        
        if balance_result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient balance (concurrent transaction)"
            )
        
        # 2. Update raffle tickets atomically
        raffle_result = db.execute(
            text("""
                UPDATE raffles 
                SET tickets_sold = tickets_sold + :quantity
                WHERE id = :raffle_id 
                AND (total_tickets - tickets_sold) >= :quantity
            """),
            {"quantity": request.quantity, "raffle_id": raffle_id}
        )
        
        if raffle_result.rowcount == 0:
            # Rollback will happen automatically on exception
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Could not complete purchase - tickets may have been sold to another buyer"
            )
        
        # 3. Create transaction record
        transaction = Transaction(
            user_id=user.id,
            amount=-total_cost,  # Negative for debit (in Naira)
            type="debit",
            description=f"Purchased {request.quantity} ticket(s) for {raffle.title}",
            balance_after=new_balance,
            reference=raffle_id
        )
        db.add(transaction)
        
        # Commit all changes
        db.commit()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Transaction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transaction failed. Please try again."
        )
    
    # Refresh models to get updated values
    db.refresh(raffle)
    db.refresh(user)
    
    return TicketPurchaseResponse(
        message=f"Successfully purchased {request.quantity} ticket(s)",
        tickets_purchased=request.quantity,
        total_cost=total_cost,  # In Naira
        balance=user.balance,  # Remaining balance in Naira
        raffle=raffle_to_response(raffle)
    )
