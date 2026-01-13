#!/usr/bin/env python3
"""
Migration script to transition from Wallet/WalletTransaction to Transaction ledger.

This script:
1. Creates the new 'transactions' table
2. Migrates existing wallet_transactions data to transactions
3. Optionally drops the old wallets and wallet_transactions tables

Run from project root:
    python backend/migrate_to_transactions.py
"""
import sqlite3
import os
from datetime import datetime

# Database path - same as in database.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bigralph.db')


def get_connection():
    """Get database connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_transactions_table(cursor):
    """Create the new transactions table."""
    print("📦 Creating transactions table...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            amount INTEGER NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            balance_after INTEGER NOT NULL,
            reference TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create index for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_user_id 
        ON transactions(user_id)
    """)
    
    print("✅ transactions table created")


def migrate_wallet_transactions(cursor):
    """Migrate existing wallet_transactions to new transactions table."""
    print("🔄 Migrating wallet_transactions data...")
    
    # Check if wallet_transactions table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='wallet_transactions'
    """)
    if not cursor.fetchone():
        print("⚠️ wallet_transactions table does not exist, skipping migration")
        return
    
    # Get all wallet transactions with user info
    cursor.execute("""
        SELECT 
            wt.id,
            w.user_id,
            wt.amount,
            wt.type,
            wt.description,
            wt.reference,
            wt.created_at
        FROM wallet_transactions wt
        JOIN wallets w ON wt.wallet_id = w.id
        ORDER BY wt.created_at ASC
    """)
    
    transactions = cursor.fetchall()
    
    if not transactions:
        print("⚠️ No wallet_transactions to migrate")
        return
    
    # Get current user balances to calculate balance_after
    cursor.execute("SELECT id, balance FROM users")
    user_balances = {row['id']: row['balance'] for row in cursor.fetchall()}
    
    # Track running balance per user for migration
    running_balances = {}
    
    migrated_count = 0
    for tx in transactions:
        user_id = tx['user_id']
        amount = tx['amount']
        
        # Initialize running balance from 0 (we'll reconstruct)
        if user_id not in running_balances:
            running_balances[user_id] = 0
        
        # Update running balance
        running_balances[user_id] += amount
        
        # Insert into new transactions table
        cursor.execute("""
            INSERT OR IGNORE INTO transactions 
            (id, user_id, amount, type, description, balance_after, reference, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tx['id'],
            user_id,
            amount,
            tx['type'],
            tx['description'],
            running_balances[user_id],
            tx['reference'],
            tx['created_at']
        ))
        migrated_count += 1
    
    print(f"✅ Migrated {migrated_count} transactions")
    
    # Verify final balances match
    print("🔍 Verifying balance consistency...")
    for user_id, calculated_balance in running_balances.items():
        actual_balance = user_balances.get(user_id, 0)
        if calculated_balance != actual_balance:
            print(f"⚠️ Balance mismatch for user {user_id}: calculated={calculated_balance}, actual={actual_balance}")
        else:
            print(f"✓ User {user_id}: balance verified ({actual_balance} kobo)")


def drop_old_tables(cursor, force=False):
    """Drop the old wallets and wallet_transactions tables."""
    if not force:
        print("⏭️ Skipping table drop (use --force to drop old tables)")
        return
    
    print("🗑️ Dropping old tables...")
    
    cursor.execute("DROP TABLE IF EXISTS wallet_transactions")
    cursor.execute("DROP TABLE IF EXISTS wallets")
    
    print("✅ Old tables dropped")


def main():
    import sys
    
    force_drop = '--force' in sys.argv
    
    print(f"🚀 Starting migration...")
    print(f"📂 Database: {DB_PATH}")
    print()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Step 1: Create new transactions table
        create_transactions_table(cursor)
        
        # Step 2: Migrate existing data
        migrate_wallet_transactions(cursor)
        
        # Step 3: Optionally drop old tables
        drop_old_tables(cursor, force_drop)
        
        # Commit all changes
        conn.commit()
        
        print()
        print("✅ Migration completed successfully!")
        print()
        print("Next steps:")
        print("1. Restart the uvicorn server to load new models")
        print("2. Test the API endpoints")
        print("3. If everything works, run with --force to drop old tables")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
