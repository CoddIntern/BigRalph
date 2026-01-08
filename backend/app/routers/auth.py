"""
Authentication router for user registration and login.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_db, get_current_user
from ..models import User, Wallet
from ..schemas import UserRegister, UserLogin, UserOut, TokenResponse
from ..auth import hash_password, verify_password, create_access_token

router = APIRouter(tags=["Authentication"])


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - Creates user with hashed password
    - Automatically creates associated wallet with 0 balance
    - Returns user data (no password)
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with hashed password and profile info
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        picture=f"https://ui-avatars.com/api/?name={data.first_name}+{data.last_name}&background=random",
        balance=0
    )
    db.add(user)
    db.flush()  # Get user.id before creating wallet
    
    # Create wallet for user
    wallet = Wallet(user_id=user.id, balance=0)
    db.add(wallet)
    
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/auth/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    
    - Validates email and password
    - Returns access token on success
    """
    # Find user by email
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return TokenResponse(access_token=access_token)


@router.get("/auth/me", response_model=UserOut)
def get_current_user_info(user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    
    Requires valid JWT token in Authorization header.
    """
    return user
