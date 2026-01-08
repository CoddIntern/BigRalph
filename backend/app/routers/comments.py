"""
Comments router for raffle discussions.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import Raffle, Comment
from ..schemas import CommentCreate, CommentOut

router = APIRouter(tags=["Comments"])


@router.get("/raffles/{raffle_id}/comments", response_model=list[CommentOut])
def get_comments(raffle_id: str, db: Session = Depends(get_db)):
    """
    Get all comments for a specific raffle.
    
    Returns 404 if raffle not found.
    Comments are returned in chronological order.
    """
    # Verify raffle exists
    raffle = db.query(Raffle).filter(Raffle.id == raffle_id).first()
    if not raffle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raffle not found"
        )
    
    comments = (
        db.query(Comment)
        .filter(Comment.raffle_id == raffle_id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    return comments


@router.post("/raffles/{raffle_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(raffle_id: str, data: CommentCreate, db: Session = Depends(get_db)):
    """
    Add a comment to a raffle.
    
    - Validates raffle exists
    - Supports is_admin flag for admin replies
    - Returns the created comment with timestamp
    """
    # Verify raffle exists
    raffle = db.query(Raffle).filter(Raffle.id == raffle_id).first()
    if not raffle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raffle not found"
        )
    
    comment = Comment(
        raffle_id=raffle_id,
        author=data.author,
        message=data.message,
        is_admin=data.is_admin
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return comment
