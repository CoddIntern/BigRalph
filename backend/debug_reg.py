
import sys
import os

# Add the parent directory to sys.path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, engine, Base
from app.models import User, Wallet
from app.auth import hash_password
from app.routers.auth import register
from app.schemas import UserRegister
from sqlalchemy.orm import Session

# Create tables if they don't exist (just in case)
Base.metadata.create_all(bind=engine)

def test_registration():
    db = SessionLocal()
    try:
        print("Attempting to register user...")
        email = "test_debug_user@example.com"
        password = "password123"
        
        # Cleanup existing user if any
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"Deleting existing user {existing.id}")
            db.delete(existing)
            db.commit()

        # Simulate the register function logic manually to see where it fails
        # Or we can just call the logic that is inside the function
        
        print("Hashing password...")
        hashed = hash_password(password)
        print(f"Password hashed: {hashed[:10]}...")

        print("Creating User object...")
        user = User(email=email, password_hash=hashed)
        db.add(user)
        print("Flushing to DB...")
        db.flush()
        print(f"User ID generated: {user.id}")

        print("Creating Wallet...")
        wallet = Wallet(user_id=user.id, balance=0)
        db.add(wallet)
        
        print("Committing transaction...")
        db.commit()
        print("Registration successful!")
        
    except Exception as e:
        print(f"CAUGHT EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_registration()
