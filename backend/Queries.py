#!/usr/bin/env python3
"""
Database Query Utility for BigRalph
Run this script to query the SQLite database interactively.
"""
import sqlite3
import os
from datetime import datetime

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "bigralph.db")

print(f"📁 Database path: {DB_PATH}")

# Connect to database
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row  # Enable column access by name
cursor = conn.cursor()


def show_tables():
    """List all tables in the database."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("\n📋 Tables in database:")
    for table in tables:
        print(f"   - {table['name']}")


def show_raffles():
    """Display all raffles with key info."""
    cursor.execute("""
        SELECT id, title, category, ticket_price, tickets_sold, total_tickets, is_ended, end_time
        FROM raffles
    """)
    raffles = cursor.fetchall()
    
    print("\n🎟️ Raffles:")
    print("-" * 130)
    print(f"{'ID':<25} {'Title':<25} {'Category':<12} {'Price':>10} {'Sold':>8} {'Total':>8} {'Progress':>10} {'End Date & Time'}")
    print("-" * 130)
    
    for r in raffles:
        progress = f"{(r['tickets_sold'] / r['total_tickets'] * 100):.1f}%"
        print(f"{r['id']:<25} {r['title']:<25} {r['category']:<12} ₦{r['ticket_price']:>8,} {r['tickets_sold']:>8,} {r['total_tickets']:>8,} {progress:>10} {r['end_time']}")


def show_comments():
    """Display all comments."""
    cursor.execute("""
        SELECT c.id, c.raffle_id, c.author, c.message, c.is_admin, c.created_at
        FROM comments c
        ORDER BY c.created_at DESC
    """)
    comments = cursor.fetchall()
    
    print("\n💬 Comments:")
    print("-" * 100)
    for c in comments:
        admin_badge = "[ADMIN]" if c['is_admin'] else ""
        print(f"  [{c['id']}] {c['author']} {admin_badge}")
        print(f"      Raffle: {c['raffle_id']}")
        print(f"      {c['message'][:80]}...")
        print()


def get_raffle_stats():
    """Show aggregate statistics."""
    cursor.execute("SELECT COUNT(*) as count FROM raffles")
    raffle_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT SUM(tickets_sold) as total FROM raffles")
    total_sold = cursor.fetchone()['total'] or 0
    
    cursor.execute("SELECT COUNT(*) as count FROM comments")
    comment_count = cursor.fetchone()['count']
    
    print("\n📊 Database Statistics:")
    print(f"   Total Raffles: {raffle_count}")
    print(f"   Total Tickets Sold: {total_sold:,}")
    print(f"   Total Comments: {comment_count}")


def custom_query(sql):
    """Run a custom SQL query."""
    try:
        cursor.execute(sql)

        # 🔥 IMPORTANT: commit changes
        conn.commit()

        # Try fetching results (safe for SELECTs)
        try:
            results = cursor.fetchall()
        except sqlite3.ProgrammingError:
            results = None

        if results:
            columns = results[0].keys()
            print("\n" + " | ".join(columns))
            print("-" * 80)
            for row in results:
                print(" | ".join(str(row[col]) for col in columns))
        else:
            print("✅ Query executed successfully.")

    except Exception as e:
        print(f"❌ Error: {e}")



# ============================================================================
# Run queries
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🎰 BigRalph Database Query Tool")
    print("=" * 60)
    
    # Show all info
    # show_tables()
    # show_raffles()
    # show_comments()
    # get_raffle_stats()
    
    # Example custom query - uncomment to use
    print("\n🔍 Custom Query:")
    # custom_query("SELECT * FROM transactions WHERE true ")
    ## custom_query("delete from transactions where id = 'efc922e8-d33e-40f0-ae6d-d3c7c6fcb89a';")

    # custom_query("UPDATE users SET balance = 5000 where email = 'oluwagbamzod@gmail.com';")
    custom_query("SELECT * FROM users WHERE true ")

    conn.close()
    print("\n✅ Done!")
