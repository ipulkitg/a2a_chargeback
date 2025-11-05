"""
View data from the chargeback system database.
Shows all tables with formatted output.
"""

import sqlite3
from pathlib import Path
from tabulate import tabulate
import json

# Database path
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "chargeback_system.db"


def view_database():
    """Display all data from the database in a formatted way."""
    
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("Please run setup_database.py first!")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    print("=" * 80)
    print("📊 CHARGEBACK SYSTEM DATABASE OVERVIEW")
    print("=" * 80)
    
    # 1. Database Summary
    print("\n📋 Database Summary:")
    print(f"   Location: {DB_PATH.absolute()}")
    print(f"   Size: {DB_PATH.stat().st_size:,} bytes")
    
    # Get table counts
    tables = ['customers', 'merchants', 'transactions', 'chargebacks', 'case_events']
    print("\n   Table Counts:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"      • {table:<20} {count:>4} rows")
    
    # 2. Customers
    print("\n" + "=" * 80)
    print("👥 CUSTOMERS")
    print("=" * 80)
    cursor.execute("""
        SELECT customer_id, name, email, region, total_chargebacks, 
               created_at
        FROM customers
        ORDER BY customer_id
    """)
    customers = cursor.fetchall()
    if customers:
        headers = ["ID", "Name", "Email", "Region", "Total CBs", "Created"]
        print(tabulate(customers, headers=headers, tablefmt="grid"))
    else:
        print("   No customers found.")
    
    # 3. Merchants
    print("\n" + "=" * 80)
    print("🏪 MERCHANTS")
    print("=" * 80)
    cursor.execute("""
        SELECT merchant_id, merchant_name, acquiring_bank, win_rate, created_at
        FROM merchants
        ORDER BY merchant_id
    """)
    merchants = cursor.fetchall()
    if merchants:
        headers = ["ID", "Name", "Acquiring Bank", "Win Rate %", "Created"]
        print(tabulate(merchants, headers=headers, tablefmt="grid"))
    else:
        print("   No merchants found.")
    
    # 4. Transactions Summary
    print("\n" + "=" * 80)
    print("💳 TRANSACTIONS SUMMARY")
    print("=" * 80)
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT customer_id) as unique_customers,
            COUNT(DISTINCT merchant_id) as unique_merchants,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount,
            MIN(amount) as min_amount,
            MAX(amount) as max_amount
        FROM transactions
    """)
    stats = cursor.fetchone()
    print(f"   Total Transactions: {stats[0]}")
    print(f"   Unique Customers: {stats[1]}")
    print(f"   Unique Merchants: {stats[2]}")
    print(f"   Total Amount: ${stats[3]:,.2f}")
    print(f"   Average Amount: ${stats[4]:,.2f}")
    print(f"   Min Amount: ${stats[5]:,.2f}")
    print(f"   Max Amount: ${stats[6]:,.2f}")
    
    # Show sample transactions
    print("\n   Sample Transactions (first 10):")
    cursor.execute("""
        SELECT 
            t.transaction_id,
            t.customer_id,
            t.merchant_id,
            t.amount,
            t.currency,
            t.payment_method,
            t.transaction_date,
            t.status,
            t.risk_level,
            t.fraud_score
        FROM transactions t
        ORDER BY t.transaction_date DESC
        LIMIT 10
    """)
    transactions = cursor.fetchall()
    if transactions:
        headers = ["Transaction ID", "Customer", "Merchant", "Amount", "Currency", 
                  "Payment Method", "Date", "Status", "Risk Level", "Fraud Score"]
        print(tabulate(transactions, headers=headers, tablefmt="grid"))
    
    # 5. Chargebacks
    print("\n" + "=" * 80)
    print("🚨 CHARGEBACKS")
    print("=" * 80)
    
    # Chargeback summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'open' THEN 1 END) as open,
            COUNT(CASE WHEN status = 'under_review' THEN 1 END) as under_review,
            COUNT(CASE WHEN status = 'won' THEN 1 END) as won,
            COUNT(CASE WHEN status = 'lost' THEN 1 END) as lost,
            SUM(chargeback_amount) as total_amount
        FROM chargebacks
    """)
    cb_stats = cursor.fetchone()
    print(f"   Total Chargebacks: {cb_stats[0]}")
    print(f"   Open: {cb_stats[1]}")
    print(f"   Under Review: {cb_stats[2]}")
    print(f"   Won: {cb_stats[3]}")
    print(f"   Lost: {cb_stats[4]}")
    print(f"   Total Amount: ${cb_stats[5]:,.2f}")
    
    # Show all chargebacks with details
    print("\n   All Chargebacks:")
    cursor.execute("""
        SELECT 
            c.chargeback_id,
            c.transaction_id,
            c.dispute_date,
            c.reason_code,
            c.dispute_type,
            c.chargeback_amount,
            c.status,
            c.outcome,
            c.issuing_bank,
            t.amount as transaction_amount,
            cust.name as customer_name,
            m.merchant_name
        FROM chargebacks c
        JOIN transactions t ON c.transaction_id = t.transaction_id
        JOIN customers cust ON t.customer_id = cust.customer_id
        JOIN merchants m ON t.merchant_id = m.merchant_id
        ORDER BY c.dispute_date DESC
    """)
    chargebacks = cursor.fetchall()
    if chargebacks:
        headers = ["Chargeback ID", "Transaction ID", "Dispute Date", "Reason Code", 
                  "Type", "CB Amount", "Status", "Outcome", "Issuing Bank", 
                  "Tx Amount", "Customer", "Merchant"]
        print(tabulate(chargebacks, headers=headers, tablefmt="grid"))
    else:
        print("   No chargebacks found.")
    
    # 6. Case Events Summary
    print("\n" + "=" * 80)
    print("📝 CASE EVENTS")
    print("=" * 80)
    cursor.execute("""
        SELECT 
            event_type,
            COUNT(*) as count
        FROM case_events
        GROUP BY event_type
        ORDER BY count DESC
    """)
    events = cursor.fetchall()
    if events:
        headers = ["Event Type", "Count"]
        print(tabulate(events, headers=headers, tablefmt="grid"))
        
        # Show sample events
        print("\n   Sample Events (last 10):")
        cursor.execute("""
            SELECT 
                ce.event_id,
                ce.chargeback_id,
                ce.event_type,
                ce.event_date,
                ce.description
            FROM case_events ce
            ORDER BY ce.event_date DESC
            LIMIT 10
        """)
        sample_events = cursor.fetchall()
        if sample_events:
            headers = ["Event ID", "Chargeback ID", "Type", "Date", "Description"]
            print(tabulate(sample_events, headers=headers, tablefmt="grid"))
    else:
        print("   No case events found.")
    
    # 7. Risk Analysis
    print("\n" + "=" * 80)
    print("🔍 RISK ANALYSIS")
    print("=" * 80)
    cursor.execute("""
        SELECT 
            risk_level,
            COUNT(*) as count,
            AVG(fraud_score) as avg_fraud_score,
            SUM(amount) as total_amount
        FROM transactions
        WHERE risk_level IS NOT NULL
        GROUP BY risk_level
        ORDER BY avg_fraud_score DESC
    """)
    risk_stats = cursor.fetchall()
    if risk_stats:
        headers = ["Risk Level", "Count", "Avg Fraud Score", "Total Amount"]
        print(tabulate(risk_stats, headers=headers, tablefmt="grid"))
    
    print("\n" + "=" * 80)
    print("✅ Database view complete!")
    print("=" * 80)
    
    conn.close()


if __name__ == "__main__":
    try:
        view_database()
    except Exception as e:
        print(f"\n❌ Error viewing database: {e}")
        raise


