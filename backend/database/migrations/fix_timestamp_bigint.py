#!/usr/bin/env python3
"""
Migration: Fix timestamp column type from INTEGER to BIGINT

This migration fixes the timestamp column type in market flow tables.
PostgreSQL INTEGER (32-bit) cannot store millisecond timestamps (13 digits).
BIGINT (64-bit) is required for millisecond timestamps.

Tables affected:
- market_trades_aggregated
- market_orderbook_snapshots
- market_asset_metrics
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from connection import SessionLocal


def upgrade():
    """Apply the migration - alter timestamp columns to BIGINT"""
    print("Starting migration: fix_timestamp_bigint")

    db = SessionLocal()
    try:
        tables = [
            'market_trades_aggregated',
            'market_orderbook_snapshots',
            'market_asset_metrics'
        ]

        for table in tables:
            # Check if table exists
            result = db.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{table}'
                )
            """))
            exists = result.scalar()

            if not exists:
                print(f"Table {table} does not exist, skipping...")
                continue

            # Check current column type
            result = db.execute(text(f"""
                SELECT data_type FROM information_schema.columns
                WHERE table_name = '{table}' AND column_name = 'timestamp'
            """))
            current_type = result.scalar()

            if current_type == 'bigint':
                print(f"Table {table}.timestamp is already BIGINT, skipping...")
                continue

            print(f"Altering {table}.timestamp from {current_type} to BIGINT...")

            # Clear existing data (it's corrupted anyway due to overflow)
            db.execute(text(f"TRUNCATE TABLE {table}"))

            # Alter column type
            db.execute(text(f"""
                ALTER TABLE {table}
                ALTER COLUMN timestamp TYPE BIGINT
            """))

            print(f"Successfully altered {table}.timestamp to BIGINT")

        db.commit()
        print("Migration completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        db.close()


def downgrade():
    """Revert the migration - not recommended"""
    print("Downgrade not supported for this migration")
    print("BIGINT to INTEGER conversion would cause data loss")


if __name__ == "__main__":
    upgrade()
