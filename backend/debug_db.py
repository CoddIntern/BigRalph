from app.database import SessionLocal, Base, engine
from app.models import User, Wallet, Raffle
from sqlalchemy import inspect
from app.auth import hash_password

def check_tables():
    inspector = inspect(engine)
    print("Tables:", inspector.get_tables())  # inspector.get_table_names() in newer sqlalchemy?
    # actually inspect(engine).get_table_names() is standard

def try_create_user():
    print("Checking tables...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Tables found:", tables)
    
    if "users" not in tables:
        print("Users table MISSING!")
    if "wallets" not in tables:
        print("Wallets table MISSING!")

    db = SessionLocal()
    try:
        # cleanup first
        existing = db.query(User).filter(User.email == "debug@example.com").first()
        if existing:
            db.delete(existing)
            db.commit()
            print("Cleaned up existing debug user.")

        user = User(email="debug@example.com", password_hash=hash_password("password"))
        db.add(user)
        db.flush()
        print(f"User created with ID: {user.id}")
        
        wallet = Wallet(user_id=user.id, balance=0)
        db.add(wallet)
        db.commit()
        print("Wallet created successfully.")
    except Exception as e:
        print(f"Error during creation: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    try_create_user()
