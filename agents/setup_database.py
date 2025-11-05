"""
Initialize SQLite database with chargeback management schema.
Run this script to create a clean database with all tables and indexes.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

# Database path - in agents directory
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "chargeback_system.db"


def init_database():
    """Create database and all tables with proper schema."""

    # Remove existing database for clean setup
    if DB_PATH.exists():
        print(f"🗑️  Removing existing database: {DB_PATH}")
        DB_PATH.unlink()

    # Connect to SQLite database (creates new file)
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    print(f"\n📦 Creating fresh database at: {DB_PATH}")

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # 1. CUSTOMERS TABLE
    print("   Creating customers table...")
    cursor.execute("""
        CREATE TABLE customers (
            customer_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            region VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_chargebacks INTEGER DEFAULT 0,
            total_refunds DECIMAL(10,2) DEFAULT 0.00
        )
    """)

    # 2. MERCHANTS TABLE
    print("   Creating merchants table...")
    cursor.execute("""
        CREATE TABLE merchants (
            merchant_id VARCHAR(50) PRIMARY KEY,
            merchant_name VARCHAR(255) NOT NULL,
            acquiring_bank VARCHAR(100),
            win_rate DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. TRANSACTIONS TABLE (with embedded risk data)
    print("   Creating transactions table...")
    cursor.execute("""
        CREATE TABLE transactions (
            transaction_id VARCHAR(50) PRIMARY KEY,
            customer_id VARCHAR(50) NOT NULL,
            merchant_id VARCHAR(50) NOT NULL,

            -- Transaction basics
            amount DECIMAL(10,2) NOT NULL,
            currency VARCHAR(3) DEFAULT 'USD',
            payment_method VARCHAR(50),
            card_last_4 VARCHAR(4),
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'completed',

            -- Gateway verification data
            avs_check VARCHAR(10),
            cvv_check VARCHAR(10),
            three_ds_used BOOLEAN DEFAULT 0,
            auth_code VARCHAR(20),

            -- Device/session data
            ip_address VARCHAR(45),
            device_fingerprint VARCHAR(255),

            -- Risk assessment data
            fraud_score DECIMAL(5,2),
            risk_level VARCHAR(20),
            velocity_flag BOOLEAN DEFAULT 0,
            velocity_data TEXT,
            risk_assessed_at TIMESTAMP,

            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
        )
    """)

    # 4. CHARGEBACKS TABLE
    print("   Creating chargebacks table...")
    cursor.execute("""
        CREATE TABLE chargebacks (
            chargeback_id VARCHAR(50) PRIMARY KEY,
            transaction_id VARCHAR(50) NOT NULL,

            -- Dispute details
            dispute_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason_code VARCHAR(10),
            dispute_type VARCHAR(50),
            issuing_bank VARCHAR(100),
            chargeback_amount DECIMAL(10,2) NOT NULL,

            -- Case management
            analyst_id VARCHAR(50),
            status VARCHAR(20) DEFAULT 'open',
            opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,
            outcome VARCHAR(20),

            -- Reference data
            retrieval_request_date TIMESTAMP,
            response_deadline TIMESTAMP,
            notes TEXT,

            FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
        )
    """)

    # 5. CASE_EVENTS TABLE (Activity log)
    print("   Creating case_events table...")
    cursor.execute("""
        CREATE TABLE case_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chargeback_id VARCHAR(50) NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            event_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_data TEXT,
            description TEXT,

            FOREIGN KEY (chargeback_id) REFERENCES chargebacks(chargeback_id)
        )
    """)

    # Create performance indexes
    print("\n📊 Creating indexes for query optimization...")

    indexes = [
        ("idx_transactions_customer", "transactions", "customer_id"),
        ("idx_transactions_merchant", "transactions", "merchant_id"),
        ("idx_transactions_date", "transactions", "transaction_date"),
        ("idx_transactions_risk_level", "transactions", "risk_level"),
        ("idx_transactions_status", "transactions", "status"),
        ("idx_chargebacks_transaction", "chargebacks", "transaction_id"),
        ("idx_chargebacks_status", "chargebacks", "status"),
        ("idx_chargebacks_opened", "chargebacks", "opened_at"),
        ("idx_chargebacks_outcome", "chargebacks", "outcome"),
        ("idx_case_events_chargeback", "case_events", "chargeback_id"),
        ("idx_case_events_type", "case_events", "event_type"),
        ("idx_case_events_date", "case_events", "event_date"),
    ]

    for idx_name, table, column in indexes:
        cursor.execute(f"""
            CREATE INDEX {idx_name} ON {table}({column})
        """)
        print(f"   ✓ {idx_name}")

    # Commit all changes
    conn.commit()

    # Verify database structure
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    print(f"\n✅ Database initialized successfully!")
    print(f"\n📋 Created {len(tables)} tables:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"   • {table[0]:<20} ({count} rows)")

    # Show database info
    cursor.execute("PRAGMA database_list")
    db_info = cursor.fetchone()

    conn.close()

    print(f"\n💾 Database location: {DB_PATH.absolute()}")
    print(f"📏 Database size: {DB_PATH.stat().st_size:,} bytes")
    print("\n🚀 Database is ready to use!")
    print("\nYou can now:")
    print("  • Import data into the tables")
    print("  • Query chargeback information")
    print("  • Track dispute cases and outcomes")


if __name__ == "__main__":
    try:
        init_database()
    except Exception as e:
        print(f"\n❌ Error during database initialization: {e}")
        raise
