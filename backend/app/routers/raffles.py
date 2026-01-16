"""
Raffles router for listing and retrieving raffle information.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from ..dependencies import get_db
from ..models import Raffle
from ..schemas import RaffleOut

router = APIRouter(tags=["Raffles"])


def raffle_to_response(raffle: Raffle) -> RaffleOut:
    """
    Convert Raffle model to response schema with computed fields.
    
    - Computes progress_percent from tickets_sold / total_tickets
    - Determines is_ended from stored flag OR end_time comparison
    """
    progress = (raffle.tickets_sold / raffle.total_tickets * 100) if raffle.total_tickets > 0 else 0.0
    is_ended = raffle.is_ended or datetime.utcnow() > raffle.end_time
    
    return RaffleOut(
        id=raffle.id,
        uuid=raffle.uuid,
        serial_number=raffle.serial_number,
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


@router.get("/raffles", response_model=list[RaffleOut])
def list_raffles(
    category: Optional[str] = Query(None, description="Filter by category (e.g., Cars, Electronics)"),
    db: Session = Depends(get_db)
):
    """
    List all raffles, optionally filtered by category.
    
    Returns raffles with computed progress percentage and ended status.
    """
    query = db.query(Raffle)
    
    if category:
        # Case-insensitive category filter
        query = query.filter(Raffle.category.ilike(category))
    
    raffles = query.all()
    return [raffle_to_response(r) for r in raffles]


@router.get("/raffles/{raffle_id}", response_model=RaffleOut)
def get_raffle(raffle_id: str, db: Session = Depends(get_db)):
    """
    Get a single raffle by ID.
    
    Returns 404 if raffle not found.
    """
    raffle = db.query(Raffle).filter(Raffle.id == raffle_id).first()
    
    if not raffle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raffle not found"
        )
    
    return raffle_to_response(raffle)
