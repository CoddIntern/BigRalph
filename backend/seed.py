#!/usr/bin/env python3
"""
Seed script to populate the database with sample raffles matching the frontend content.

Run with: python seed.py

This script is SAFE to run multiple times.
It will NOT reseed if data already exists.
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.models import Raffle, Comment

# Create tables (safe: does nothing if tables exist)
Base.metadata.create_all(bind=engine)


def seed_database():
    """Populate the database with sample data only if empty."""
    db = SessionLocal()

    try:
        # 🔒 SAFETY CHECK — DO NOT SEED IF DATA EXISTS
        existing_raffles = db.query(Raffle).count()
        if existing_raffles > 0:
            print("ℹ️ Database already contains data.")
            print(f"   - Found {existing_raffles} raffles")
            print("   - Skipping seeding to avoid data loss.")
            return

        print("🚀 Seeding database with initial data...")

        now = datetime.utcnow()

        raffles = [
            Raffle(
                id="raffle-toyota-camry",
                title="2023 Toyota Camry",
                description="""Brand new 2023 Toyota Camry XSE with all premium features including:
• 3.5L V6 Engine with 301 HP
• Leather-trimmed seats with heating and ventilation
• 9-inch touchscreen with Apple CarPlay and Android Auto
• JBL premium audio system
• Panoramic moonroof
• Advanced safety features including adaptive cruise control

Color: Midnight Black Metallic""",
                category="Cars",
                ticket_price=7500,
                total_tickets=4000,
                tickets_sold=1234,
                item_value=15000000,
                end_time=now + timedelta(days=365),
                image="http://static.photos/automotive/640x360/1",
                is_ended=False
            ),
            Raffle(
                id="raffle-iphone-15",
                title="iPhone 15 Pro Max",
                description="Latest Apple smartphone with 256GB storage. Features include Dynamic Island, 48MP camera system, A17 Pro chip, and titanium design.",
                category="Gadgets",
                ticket_price=2500,
                total_tickets=1500,
                tickets_sold=876,
                item_value=1800000,
                end_time=now + timedelta(days=314),
                image="http://static.photos/technology/640x360/187",
                is_ended=False
            ),
            Raffle(
                id="raffle-airpods-pro",
                title="AirPods Pro 2",
                description="Premium wireless earbuds with active noise cancellation, adaptive transparency, and personalized spatial audio.",
                category="Gadgets",
                ticket_price=1000,
                total_tickets=800,
                tickets_sold=800,
                item_value=150000,
                end_time=now + timedelta(days=298),
                image="http://static.photos/technology/640x360/193",
                is_ended=False
            ),
            Raffle(
                id="raffle-lekki-land",
                title="500sqm Plot in Lekki",
                description="Prime residential land in highbrow Lekki area. Fully documented with C of O. Perfect for building your dream home or investment.",
                category="Land",
                ticket_price=10000,
                total_tickets=3000,
                tickets_sold=1876,
                item_value=75000000,
                end_time=now + timedelta(days=344),
                image="http://static.photos/estate/640x360/4",
                is_ended=False
            ),
            Raffle(
                id="raffle-gaming-monitor",
                title='32" 4K Gaming Monitor',
                description="144Hz refresh rate, 1ms response time. Features include HDR1000, NVIDIA G-SYNC compatibility, and USB-C power delivery.",
                category="Electronics",
                ticket_price=3000,
                total_tickets=1500,
                tickets_sold=1500,
                item_value=650000,
                end_time=now + timedelta(days=319),
                image="http://static.photos/technology/640x360/5",
                is_ended=False
            ),
            Raffle(
                id="raffle-yamaha-r1",
                title="2023 Yamaha R1",
                description="1000cc sports bike with racing features. Includes crossplane crankshaft engine, traction control, slide control, and wheelie control.",
                category="Cars",
                ticket_price=7500,
                total_tickets=2500,
                tickets_sold=1543,
                item_value=12000000,
                end_time=now + timedelta(days=339),
                image="http://static.photos/automotive/640x360/6",
                is_ended=False
            ),
        ]

        db.add_all(raffles)
        db.commit()

        comments = [
            Comment(
                raffle_id="raffle-toyota-camry",
                author="Emeka C.",
                message="This is an amazing car! I've bought 5 tickets already. Good luck to everyone!",
                is_admin=False
            ),
            Comment(
                raffle_id="raffle-toyota-camry",
                author="Amina B.",
                message="Does this come with a warranty? And is there an option for a different color?",
                is_admin=False
            ),
            Comment(
                raffle_id="raffle-toyota-camry",
                author="BigRalph Admin",
                message="Yes, it comes with full manufacturer warranty. Color options are limited to what's in stock.",
                is_admin=True
            ),
            Comment(
                raffle_id="raffle-toyota-camry",
                author="Chinedu O.",
                message="I won a phone from BigRalph last month. The process was smooth and delivery was fast. Hoping to win this car too!",
                is_admin=False
            ),
        ]

        db.add_all(comments)
        db.commit()

        print("✅ Database seeded successfully!")
        print(f"   - Created {len(raffles)} raffles")
        print(f"   - Created {len(comments)} comments")

        print("\n📋 Raffles created:")
        for raffle in raffles:
            progress = (raffle.tickets_sold / raffle.total_tickets) * 100
            status = "SOLD OUT" if raffle.tickets_sold >= raffle.total_tickets else f"{progress:.1f}%"
            print(f"   [{raffle.category}] {raffle.title} - {status}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
