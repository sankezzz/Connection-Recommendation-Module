"""
seed.py — upsert lookup data (roles, commodities, interests).

The migration already inserts these rows, but running this script is
safe at any time — it skips rows that already exist.

Usage:
    python scripts/seed.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database.session import SessionLocal
from app.modules.profile.models import Commodity, Interest, Role

# Fixed IDs — must match what the app uses (1/2/3)
ROLES = [
    Role(id=1, name="Trader",   description="Trades commodities in domestic markets."),
    Role(id=2, name="Broker",   description="Connects buyers and sellers."),
    Role(id=3, name="Exporter", description="Supplies commodities to global markets."),
]

COMMODITIES = [
    Commodity(id=1, name="Rice"),
    Commodity(id=2, name="Cotton"),
    Commodity(id=3, name="Sugar"),
]

INTERESTS = [
    Interest(id=1, name="Connections"),
    Interest(id=2, name="Leads"),
    Interest(id=3, name="News"),
]


def seed():
    db = SessionLocal()
    try:
        existing_role_ids    = {r.id for r in db.query(Role.id).all()}
        existing_commodity_ids = {c.id for c in db.query(Commodity.id).all()}
        existing_interest_ids  = {i.id for i in db.query(Interest.id).all()}

        db.add_all([r for r in ROLES       if r.id not in existing_role_ids])
        db.add_all([c for c in COMMODITIES if c.id not in existing_commodity_ids])
        db.add_all([i for i in INTERESTS   if i.id not in existing_interest_ids])
        db.commit()

        print("\n=== Roles ===")
        for r in db.query(Role).order_by(Role.id).all():
            print(f"  {r.id}  {r.name:<12}  {r.description}")

        print("\n=== Commodities ===")
        for c in db.query(Commodity).order_by(Commodity.id).all():
            print(f"  {c.id}  {c.name}")

        print("\n=== Interests ===")
        for i in db.query(Interest).order_by(Interest.id).all():
            print(f"  {i.id}  {i.name}")

        print("\nSeeding complete.\n")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
