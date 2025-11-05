"""
Seed database with synthetic chargeback data.
Creates realistic scenarios for true fraud, friendly fraud, merchant error, and not guilty cases.
"""

import sqlite3
import random
import json
from datetime import datetime, timedelta
from pathlib import Path

# Database path
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "chargeback_system.db"


def random_date(start_days_ago=365, end_days_ago=1):
    """Generate random date between start and end days ago."""
    days_ago = random.randint(end_days_ago, start_days_ago)
    return (datetime.now() - timedelta(days=days_ago)).isoformat()


def generate_id(prefix: str, num: int) -> str:
    """Generate ID with prefix and number."""
    return f"{prefix}_{num:04d}"


def seed_database():
    """Populate database with synthetic chargeback data."""

    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        print("Please run setup_database.py first!")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    print("🌱 Seeding database with synthetic data...")

    # Clear existing data for fresh start
    print("   Clearing existing data...")
    cursor.execute("DELETE FROM case_events")
    cursor.execute("DELETE FROM chargebacks")
    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM customers")
    cursor.execute("DELETE FROM merchants")
    conn.commit()

    # 1. Create Merchants
    print("📦 Creating merchants...")
    merchants = [
        ("merch_001", "TechStore Pro", "Chase Bank", 72.5),
        ("merch_002", "FashionHub", "Bank of America", 68.3),
        ("merch_003", "Electronics Plus", "Wells Fargo", 75.1),
        ("merch_004", "Home Essentials", "Citi Bank", 70.8),
    ]

    for merchant_id, name, bank, win_rate in merchants:
        cursor.execute(
            """INSERT INTO merchants
               (merchant_id, merchant_name, acquiring_bank, win_rate, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (merchant_id, name, bank, win_rate, random_date(730))
        )

    # 2. Create Customers
    print("👥 Creating customers and transactions...")

    customers_data = [
        ("cust_001", "Sarah Johnson", "sarah.j@email.com", "US"),
        ("cust_002", "Michael Chen", "m.chen@email.com", "US"),
        ("cust_003", "Emma Williams", "emma.w@email.com", "US"),
        ("cust_004", "David Rodriguez", "d.rodriguez@email.com", "US"),
        ("cust_005", "Lisa Anderson", "lisa.a@email.com", "US"),
        ("cust_006", "James Taylor", "j.taylor@email.com", "US"),
        ("cust_007", "Maria Garcia", "maria.g@email.com", "US"),
    ]

    for customer_id, name, email, region in customers_data:
        cursor.execute(
            """INSERT INTO customers
               (customer_id, name, email, region, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (customer_id, name, email, region, random_date(730))
        )

    # 3. Create normal transactions for each customer
    transaction_counter = 1

    for customer_id, _, _, _ in customers_data:
        num_transactions = random.randint(5, 10)
        for _ in range(num_transactions):
            tx_id = generate_id("txn", transaction_counter)
            merchant_id = random.choice(["merch_001", "merch_002", "merch_003", "merch_004"])
            amount = round(random.uniform(25.0, 850.0), 2)
            tx_date = random_date(180, 10)

            # Risk data (low risk for normal transactions)
            fraud_score = round(random.uniform(5.0, 25.0), 2)
            velocity_data = json.dumps({
                "cards_last_24h": 0,
                "same_ip_count": 1,
                "transactions_last_week": random.randint(1, 3)
            })

            cursor.execute(
                """INSERT INTO transactions
                   (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
                    card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
                    auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
                    velocity_flag, velocity_data, risk_assessed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (tx_id, customer_id, merchant_id, amount, "USD",
                 random.choice(["visa", "mastercard", "amex"]),
                 f"{random.randint(1000, 9999)}", tx_date, "completed",
                 random.choice(["Y", "N", "Z"]), random.choice(["Y", "N"]),
                 random.choice([0, 1]), f"AUTH{random.randint(10000, 99999)}",
                 f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                 f"DEV{random.randint(100000, 999999)}",
                 fraud_score, "low", 0, velocity_data, tx_date)
            )
            transaction_counter += 1

    # 4. Create Chargeback Cases
    print("🚨 Creating chargeback cases...")

    chargeback_cases = []

    # ========== TRUE FRAUD CASES (2 cases) ==========

    # Case 1: Stolen Card
    cb1_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb1_tx_id, "cust_001", "merch_001", 1249.99, "USD", "visa", "4521",
         random_date(30, 25), "disputed", "N", "N", 0, "AUTH12345",
         "185.220.101.45", "DEV999001", 95.5, "high", 1,
         json.dumps({"cards_last_24h": 8, "same_ip_count": 0, "transactions_last_week": 12}),
         random_date(30, 25))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_001",
        "transaction_id": cb1_tx_id,
        "dispute_date": random_date(25, 20),
        "reason_code": "4855",
        "dispute_type": "fraud",
        "issuing_bank": "Chase Bank",
        "chargeback_amount": 1249.99,
        "analyst_id": "analyst_001",
        "status": "open",
        "opened_at": random_date(20, 18),
        "closed_at": None,
        "outcome": None,
        "notes": "Cardholder reports card stolen. Transaction from unusual location. Multiple high-value transactions in 24h.",
        "fraud_type": "true_fraud"
    })

    # Case 2: Account Takeover
    cb2_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb2_tx_id, "cust_002", "merch_002", 899.50, "USD", "mastercard", "5432",
         random_date(28, 23), "disputed", "Z", "N", 0, "AUTH67890",
         "203.0.113.22", "DEV999002", 88.2, "high", 1,
         json.dumps({"cards_last_24h": 5, "same_ip_count": 0, "transactions_last_week": 7}),
         random_date(28, 23))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_002",
        "transaction_id": cb2_tx_id,
        "dispute_date": random_date(23, 18),
        "reason_code": "4853",
        "dispute_type": "fraud",
        "issuing_bank": "Bank of America",
        "chargeback_amount": 899.50,
        "analyst_id": "analyst_002",
        "status": "open",
        "opened_at": random_date(18, 16),
        "closed_at": None,
        "outcome": None,
        "notes": "Account takeover suspected. Login from new device and location. Customer denies all transactions.",
        "fraud_type": "true_fraud"
    })

    # ========== FRIENDLY FRAUD CASES (4 cases) ==========

    # Case 3: Item Not Received
    cb3_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb3_tx_id, "cust_003", "merch_001", 299.99, "USD", "visa", "1234",
         random_date(45, 40), "disputed", "Y", "Y", 1, "AUTH11111",
         "192.168.1.100", "DEV123456", 15.0, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 5, "transactions_last_week": 2}),
         random_date(45, 40))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_003",
        "transaction_id": cb3_tx_id,
        "dispute_date": random_date(35, 30),
        "reason_code": "4855",
        "dispute_type": "service_not_provided",
        "issuing_bank": "Wells Fargo",
        "chargeback_amount": 299.99,
        "analyst_id": "analyst_003",
        "status": "open",
        "opened_at": random_date(30, 28),
        "closed_at": None,
        "outcome": None,
        "notes": "Customer claims item never received. Tracking shows delivered. Customer has history of similar claims.",
        "fraud_type": "friendly_fraud"
    })

    # Case 4: Product Quality Issue
    cb4_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb4_tx_id, "cust_004", "merch_003", 549.99, "USD", "amex", "5678",
         random_date(60, 55), "disputed", "Y", "Y", 1, "AUTH22222",
         "192.168.1.101", "DEV123457", 12.5, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 8, "transactions_last_week": 3}),
         random_date(60, 55))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_004",
        "transaction_id": cb4_tx_id,
        "dispute_date": random_date(50, 45),
        "reason_code": "4855",
        "dispute_type": "service_not_provided",
        "issuing_bank": "Citi Bank",
        "chargeback_amount": 549.99,
        "analyst_id": "analyst_004",
        "status": "open",
        "opened_at": random_date(45, 43),
        "closed_at": None,
        "outcome": None,
        "notes": "Customer claims product defective. Merchant provided refund but customer filed chargeback anyway.",
        "fraud_type": "friendly_fraud"
    })

    # Case 5: Subscription Cancellation
    cb5_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb5_tx_id, "cust_005", "merch_002", 79.99, "USD", "visa", "9012",
         random_date(90, 85), "disputed", "Y", "Y", 1, "AUTH33333",
         "192.168.1.102", "DEV123458", 10.0, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 12, "transactions_last_week": 1}),
         random_date(90, 85))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_005",
        "transaction_id": cb5_tx_id,
        "dispute_date": random_date(80, 75),
        "reason_code": "4855",
        "dispute_type": "service_not_provided",
        "issuing_bank": "Chase Bank",
        "chargeback_amount": 79.99,
        "analyst_id": "analyst_005",
        "status": "open",
        "opened_at": random_date(75, 73),
        "closed_at": None,
        "outcome": None,
        "notes": "Customer cancelled subscription but was charged. Claims cancellation before billing cycle.",
        "fraud_type": "friendly_fraud"
    })

    # Case 6: Unauthorized Family Member
    cb6_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb6_tx_id, "cust_006", "merch_004", 199.99, "USD", "mastercard", "3456",
         random_date(40, 35), "disputed", "Y", "Y", 1, "AUTH44444",
         "192.168.1.103", "DEV123459", 18.0, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 6, "transactions_last_week": 4}),
         random_date(40, 35))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_006",
        "transaction_id": cb6_tx_id,
        "dispute_date": random_date(30, 25),
        "reason_code": "4855",
        "dispute_type": "fraud",
        "issuing_bank": "Bank of America",
        "chargeback_amount": 199.99,
        "analyst_id": "analyst_006",
        "status": "open",
        "opened_at": random_date(25, 23),
        "closed_at": None,
        "outcome": None,
        "notes": "Customer claims unauthorized transaction. Same IP, device, and shipping address. Likely family member.",
        "fraud_type": "friendly_fraud"
    })

    # ========== MERCHANT ERROR CASES (2 cases) ==========

    # Case 7: Duplicate Charge
    cb7_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb7_tx_id, "cust_001", "merch_003", 149.99, "USD", "visa", "4521",
         random_date(20, 18), "disputed", "Y", "Y", 1, "AUTH66666",
         "192.168.1.100", "DEV123456", 5.0, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 5, "transactions_last_week": 2}),
         random_date(20, 18))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_007",
        "transaction_id": cb7_tx_id,
        "dispute_date": random_date(15, 12),
        "reason_code": "4837",
        "dispute_type": "duplicate",
        "issuing_bank": "Chase Bank",
        "chargeback_amount": 149.99,
        "analyst_id": "analyst_007",
        "status": "open",
        "opened_at": random_date(12, 10),
        "closed_at": None,
        "outcome": None,
        "notes": "Customer charged twice for same purchase. Merchant confirmed duplicate. Refund processed.",
        "fraud_type": "merchant_error"
    })

    # Case 8: Wrong Amount
    cb8_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb8_tx_id, "cust_002", "merch_002", 249.99, "USD", "mastercard", "5432",
         random_date(25, 22), "disputed", "Y", "Y", 1, "AUTH77777",
         "192.168.1.101", "DEV123457", 8.0, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 8, "transactions_last_week": 3}),
         random_date(25, 22))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_008",
        "transaction_id": cb8_tx_id,
        "dispute_date": random_date(18, 15),
        "reason_code": "4837",
        "dispute_type": "duplicate",
        "issuing_bank": "Bank of America",
        "chargeback_amount": 249.99,
        "analyst_id": "analyst_008",
        "status": "open",
        "opened_at": random_date(15, 13),
        "closed_at": None,
        "outcome": None,
        "notes": "Customer ordered for $99.99 but charged $249.99. Merchant pricing error. Partial refund issued.",
        "fraud_type": "merchant_error"
    })

    # ========== NOT GUILTY CASES (5 cases - Merchant Won) ==========

    # Case 9: Legitimate Purchase - Customer Confusion
    cb9_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb9_tx_id, "cust_003", "merch_001", 179.99, "USD", "visa", "1234",
         random_date(70, 65), "disputed", "Y", "Y", 1, "AUTH88888",
         "192.168.1.100", "DEV123456", 12.0, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 5, "transactions_last_week": 2}),
         random_date(70, 65))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_009",
        "transaction_id": cb9_tx_id,
        "dispute_date": random_date(60, 55),
        "reason_code": "4855",
        "dispute_type": "fraud",
        "issuing_bank": "Wells Fargo",
        "chargeback_amount": 179.99,
        "analyst_id": "analyst_009",
        "status": "won",
        "opened_at": random_date(55, 53),
        "closed_at": random_date(40, 38),
        "outcome": "won",
        "notes": "Customer claimed unauthorized. Merchant provided proof: same IP, device, shipping address, email confirmation. Chargeback reversed.",
        "fraud_type": "not_guilty"
    })

    # Case 10: Subscription Renewal - Customer Forgot
    cb10_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb10_tx_id, "cust_004", "merch_002", 49.99, "USD", "amex", "5678",
         random_date(85, 80), "disputed", "Y", "Y", 1, "AUTH99999",
         "192.168.1.101", "DEV123457", 10.0, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 8, "transactions_last_week": 3}),
         random_date(85, 80))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_010",
        "transaction_id": cb10_tx_id,
        "dispute_date": random_date(75, 70),
        "reason_code": "4855",
        "dispute_type": "service_not_provided",
        "issuing_bank": "Citi Bank",
        "chargeback_amount": 49.99,
        "analyst_id": "analyst_010",
        "status": "won",
        "opened_at": random_date(70, 68),
        "closed_at": random_date(55, 53),
        "outcome": "won",
        "notes": "Customer claimed unauthorized subscription. Merchant provided signed TOS, agreement, 6 months usage logs. Chargeback reversed.",
        "fraud_type": "not_guilty"
    })

    # Case 11: Digital Goods Delivered
    cb11_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb11_tx_id, "cust_005", "merch_003", 89.99, "USD", "visa", "9012",
         random_date(50, 45), "disputed", "Y", "Y", 1, "AUTH10101",
         "192.168.1.102", "DEV123458", 8.0, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 12, "transactions_last_week": 1}),
         random_date(50, 45))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_011",
        "transaction_id": cb11_tx_id,
        "dispute_date": random_date(40, 35),
        "reason_code": "4855",
        "dispute_type": "service_not_provided",
        "issuing_bank": "Chase Bank",
        "chargeback_amount": 89.99,
        "analyst_id": "analyst_011",
        "status": "won",
        "opened_at": random_date(35, 33),
        "closed_at": random_date(20, 18),
        "outcome": "won",
        "notes": "Customer claimed digital product not received. Merchant provided delivery confirmation, download logs, IP match, usage analytics. Chargeback reversed.",
        "fraud_type": "not_guilty"
    })

    # Case 12: Return Policy Violation
    cb12_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb12_tx_id, "cust_006", "merch_004", 299.99, "USD", "mastercard", "3456",
         random_date(65, 60), "disputed", "Y", "Y", 1, "AUTH20202",
         "192.168.1.103", "DEV123459", 15.0, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 6, "transactions_last_week": 4}),
         random_date(65, 60))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_012",
        "transaction_id": cb12_tx_id,
        "dispute_date": random_date(55, 50),
        "reason_code": "4855",
        "dispute_type": "service_not_provided",
        "issuing_bank": "Bank of America",
        "chargeback_amount": 299.99,
        "analyst_id": "analyst_012",
        "status": "won",
        "opened_at": random_date(50, 48),
        "closed_at": random_date(35, 33),
        "outcome": "won",
        "notes": "Customer claimed defective. Merchant provided return policy, photos of used item, expired return window (45 vs 30 days). Chargeback reversed.",
        "fraud_type": "not_guilty"
    })

    # Case 13: Item Delivered - Customer Dishonest
    cb13_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb13_tx_id, "cust_007", "merch_001", 399.99, "USD", "visa", "7890",
         random_date(55, 50), "disputed", "Y", "Y", 1, "AUTH30303",
         "192.168.1.104", "DEV123460", 11.0, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 10, "transactions_last_week": 2}),
         random_date(55, 50))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_013",
        "transaction_id": cb13_tx_id,
        "dispute_date": random_date(45, 40),
        "reason_code": "4855",
        "dispute_type": "service_not_provided",
        "issuing_bank": "Wells Fargo",
        "chargeback_amount": 399.99,
        "analyst_id": "analyst_013",
        "status": "won",
        "opened_at": random_date(40, 38),
        "closed_at": random_date(25, 23),
        "outcome": "won",
        "notes": "Customer claimed not received. Merchant provided delivery confirmation, signature, GPS tracking. Chargeback reversed.",
        "fraud_type": "not_guilty"
    })

    # ========== ADDITIONAL TRUE FRAUD CASES (3 more cases) ==========

    # Case 14: Card Skimming - True Fraud (cust_003 - has history)
    cb14_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb14_tx_id, "cust_003", "merch_002", 675.50, "USD", "visa", "1234",
         random_date(42, 38), "disputed", "N", "N", 0, "AUTH45678",
         "198.51.100.10", "DEV999003", 92.3, "high", 1,
         json.dumps({"cards_last_24h": 6, "same_ip_count": 0, "transactions_last_week": 9}),
         random_date(42, 38))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_014",
        "transaction_id": cb14_tx_id,
        "dispute_date": random_date(38, 33),
        "reason_code": "4855",
        "dispute_type": "fraud",
        "issuing_bank": "Wells Fargo",
        "chargeback_amount": 675.50,
        "analyst_id": "analyst_014",
        "status": "open",
        "opened_at": random_date(33, 31),
        "closed_at": None,
        "outcome": None,
        "notes": "Card skimming detected. Transaction from compromised terminal. Multiple unauthorized transactions from same card.",
        "fraud_type": "true_fraud"
    })

    # Case 15: CNP Fraud - True Fraud (cust_001 - has history with cb_001)
    cb15_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb15_tx_id, "cust_001", "merch_004", 1125.00, "USD", "visa", "4521",
         random_date(50, 45), "disputed", "N", "N", 0, "AUTH56789",
         "172.217.12.46", "DEV999004", 89.7, "high", 1,
         json.dumps({"cards_last_24h": 4, "same_ip_count": 0, "transactions_last_week": 6}),
         random_date(50, 45))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_015",
        "transaction_id": cb15_tx_id,
        "dispute_date": random_date(45, 40),
        "reason_code": "4855",
        "dispute_type": "fraud",
        "issuing_bank": "Chase Bank",
        "chargeback_amount": 1125.00,
        "analyst_id": "analyst_015",
        "status": "open",
        "opened_at": random_date(40, 38),
        "closed_at": None,
        "outcome": None,
        "notes": "Card Not Present (CNP) fraud. Card details stolen. Transaction from unusual location. Customer reported card lost.",
        "fraud_type": "true_fraud"
    })

    # Case 16: Synthetic Identity Fraud - True Fraud (new customer or cust_007)
    cb16_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb16_tx_id, "cust_007", "merch_001", 825.75, "USD", "mastercard", "7890",
         random_date(55, 50), "disputed", "Z", "N", 0, "AUTH67891",
         "104.248.90.2", "DEV999005", 91.2, "high", 1,
         json.dumps({"cards_last_24h": 7, "same_ip_count": 0, "transactions_last_week": 11}),
         random_date(55, 50))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_016",
        "transaction_id": cb16_tx_id,
        "dispute_date": random_date(50, 45),
        "reason_code": "4853",
        "dispute_type": "fraud",
        "issuing_bank": "Wells Fargo",
        "chargeback_amount": 825.75,
        "analyst_id": "analyst_016",
        "status": "open",
        "opened_at": random_date(45, 43),
        "closed_at": None,
        "outcome": None,
        "notes": "Synthetic identity fraud suspected. Account opened recently with minimal history. High-value transaction from new device.",
        "fraud_type": "true_fraud"
    })

    # ========== ADDITIONAL FRIENDLY FRAUD CASES (4 more cases) ==========

    # Case 17: Item Not Received - Repeat Offender (cust_003 - has history)
    cb17_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb17_tx_id, "cust_003", "merch_003", 425.99, "USD", "visa", "1234",
         random_date(120, 115), "disputed", "Y", "Y", 1, "AUTH78901",
         "192.168.1.100", "DEV123456", 14.5, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 5, "transactions_last_week": 2}),
         random_date(120, 115))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_017",
        "transaction_id": cb17_tx_id,
        "dispute_date": random_date(110, 105),
        "reason_code": "4855",
        "dispute_type": "service_not_provided",
        "issuing_bank": "Wells Fargo",
        "chargeback_amount": 425.99,
        "analyst_id": "analyst_017",
        "status": "won",
        "opened_at": random_date(105, 103),
        "closed_at": random_date(90, 88),
        "outcome": "won",
        "notes": "Customer claims item never received. Tracking shows delivered. Customer has 3 previous 'item not received' claims. Chargeback reversed in favor of merchant.",
        "fraud_type": "friendly_fraud"
    })

    # Case 18: Subscription Renewal Dispute (cust_005 - has history)
    cb18_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb18_tx_id, "cust_005", "merch_001", 99.99, "USD", "visa", "9012",
         random_date(180, 175), "disputed", "Y", "Y", 1, "AUTH89012",
         "192.168.1.102", "DEV123458", 11.0, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 12, "transactions_last_week": 1}),
         random_date(180, 175))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_018",
        "transaction_id": cb18_tx_id,
        "dispute_date": random_date(170, 165),
        "reason_code": "4855",
        "dispute_type": "service_not_provided",
        "issuing_bank": "Chase Bank",
        "chargeback_amount": 99.99,
        "analyst_id": "analyst_018",
        "status": "won",
        "opened_at": random_date(165, 163),
        "closed_at": random_date(150, 148),
        "outcome": "won",
        "notes": "Customer claims subscription cancelled but was charged. Previous subscription dispute history. Merchant provided evidence, chargeback reversed.",
        "fraud_type": "friendly_fraud"
    })

    # Case 19: Quality Issue - Repeat Pattern (cust_004 - has history)
    cb19_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb19_tx_id, "cust_004", "merch_004", 375.50, "USD", "amex", "5678",
         random_date(200, 195), "disputed", "Y", "Y", 1, "AUTH90123",
         "192.168.1.101", "DEV123457", 13.0, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 8, "transactions_last_week": 3}),
         random_date(200, 195))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_019",
        "transaction_id": cb19_tx_id,
        "dispute_date": random_date(190, 185),
        "reason_code": "4855",
        "dispute_type": "service_not_provided",
        "issuing_bank": "Citi Bank",
        "chargeback_amount": 375.50,
        "analyst_id": "analyst_019",
        "status": "won",
        "opened_at": random_date(185, 183),
        "closed_at": random_date(170, 168),
        "outcome": "won",
        "notes": "Customer claims product defective. Merchant provided refund but customer filed chargeback. Pattern of quality disputes. Chargeback reversed.",
        "fraud_type": "friendly_fraud"
    })

    # Case 20: Family Member Purchase (cust_006 - has history)
    cb20_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb20_tx_id, "cust_006", "merch_002", 275.25, "USD", "mastercard", "3456",
         random_date(150, 145), "disputed", "Y", "Y", 1, "AUTH01234",
         "192.168.1.103", "DEV123459", 16.5, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 6, "transactions_last_week": 4}),
         random_date(150, 145))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_020",
        "transaction_id": cb20_tx_id,
        "dispute_date": random_date(140, 135),
        "reason_code": "4855",
        "dispute_type": "fraud",
        "issuing_bank": "Bank of America",
        "chargeback_amount": 275.25,
        "analyst_id": "analyst_020",
        "status": "won",
        "opened_at": random_date(135, 133),
        "closed_at": random_date(120, 118),
        "outcome": "won",
        "notes": "Customer claims unauthorized. Same IP, device, and shipping address as previous orders. Likely family member. Previous similar claim. Chargeback reversed.",
        "fraud_type": "friendly_fraud"
    })

    # ========== ADDITIONAL MERCHANT ERROR CASES (3 more cases) ==========

    # Case 21: Processing Error (cust_001 - has history)
    cb21_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb21_tx_id, "cust_001", "merch_002", 189.99, "USD", "visa", "4521",
         random_date(100, 95), "disputed", "Y", "Y", 1, "AUTH12346",
         "192.168.1.100", "DEV123456", 6.0, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 5, "transactions_last_week": 2}),
         random_date(100, 95))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_021",
        "transaction_id": cb21_tx_id,
        "dispute_date": random_date(90, 85),
        "reason_code": "4837",
        "dispute_type": "duplicate",
        "issuing_bank": "Chase Bank",
        "chargeback_amount": 189.99,
        "analyst_id": "analyst_021",
        "status": "lost",
        "opened_at": random_date(85, 83),
        "closed_at": random_date(75, 73),
        "outcome": "lost",
        "notes": "Payment processing error caused duplicate authorization. Merchant confirmed error. Refund processed. Chargeback upheld in favor of customer.",
        "fraud_type": "merchant_error"
    })

    # Case 22: Refund Not Processed (cust_002 - has history)
    cb22_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb22_tx_id, "cust_002", "merch_003", 319.99, "USD", "mastercard", "5432",
         random_date(130, 125), "disputed", "Y", "Y", 1, "AUTH23457",
         "192.168.1.101", "DEV123457", 7.5, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 8, "transactions_last_week": 3}),
         random_date(130, 125))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_022",
        "transaction_id": cb22_tx_id,
        "dispute_date": random_date(120, 115),
        "reason_code": "4837",
        "dispute_type": "duplicate",
        "issuing_bank": "Bank of America",
        "chargeback_amount": 319.99,
        "analyst_id": "analyst_022",
        "status": "lost",
        "opened_at": random_date(115, 113),
        "closed_at": random_date(105, 103),
        "outcome": "lost",
        "notes": "Customer returned item and refund was authorized but not processed due to system error. Merchant acknowledged and processed refund. Chargeback upheld in favor of customer.",
        "fraud_type": "merchant_error"
    })

    # Case 23: Authorization Hold Not Released (cust_007 - has history)
    cb23_tx_id = generate_id("txn", transaction_counter)
    transaction_counter += 1

    cursor.execute(
        """INSERT INTO transactions
           (transaction_id, customer_id, merchant_id, amount, currency, payment_method,
            card_last_4, transaction_date, status, avs_check, cvv_check, three_ds_used,
            auth_code, ip_address, device_fingerprint, fraud_score, risk_level,
            velocity_flag, velocity_data, risk_assessed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cb23_tx_id, "cust_007", "merch_004", 225.00, "USD", "visa", "7890",
         random_date(75, 70), "disputed", "Y", "Y", 1, "AUTH34568",
         "192.168.1.104", "DEV123460", 9.0, "low", 0,
         json.dumps({"cards_last_24h": 1, "same_ip_count": 10, "transactions_last_week": 2}),
         random_date(75, 70))
    )

    chargeback_cases.append({
        "chargeback_id": "cb_023",
        "transaction_id": cb23_tx_id,
        "dispute_date": random_date(65, 60),
        "reason_code": "4837",
        "dispute_type": "duplicate",
        "issuing_bank": "Wells Fargo",
        "chargeback_amount": 225.00,
        "analyst_id": "analyst_023",
        "status": "lost",
        "opened_at": random_date(60, 58),
        "closed_at": random_date(50, 48),
        "outcome": "lost",
        "notes": "Authorization hold from cancelled order not released. Merchant confirmed error and released hold. Customer charged twice. Chargeback upheld in favor of customer.",
        "fraud_type": "merchant_error"
    })

    # Insert all chargebacks
    for cb in chargeback_cases:
        cursor.execute(
            """INSERT INTO chargebacks
               (chargeback_id, transaction_id, dispute_date, reason_code, dispute_type,
                issuing_bank, chargeback_amount, analyst_id, status, opened_at, closed_at,
                outcome, retrieval_request_date, response_deadline, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (cb["chargeback_id"], cb["transaction_id"], cb["dispute_date"], cb["reason_code"],
             cb["dispute_type"], cb["issuing_bank"], cb["chargeback_amount"], cb["analyst_id"],
             cb["status"], cb["opened_at"], cb["closed_at"], cb["outcome"],
             None, random_date(30, 10), cb["notes"])
        )

    # 5. Create Case Events with Detailed Evidence
    print("📝 Creating case events with detailed evidence...")

    # Case-specific evidence templates with rich data
    case_evidence = {
        "cb_001": [  # Stolen Card - True Fraud
            ("support_ticket", {
                "ticket_id": "TKT12345",
                "customer_contact_date": random_date(25, 20),
                "contact_method": "phone",
                "customer_statement": "Card stolen on date X, reported immediately to bank",
                "card_cancelled": True,
                "police_report": "POL-RPT-2024-001",
                "card_issuer_notified": True
            }, "Customer reported card stolen. Immediate card cancellation requested. Police report filed."),
            ("transaction_analysis", {
                "unusual_location": True,
                "location_country": "Russia",
                "location_city": "Moscow",
                "customer_location": "San Francisco, CA",
                "distance_miles": 5900,
                "time_of_transaction": "03:45 AM local time",
                "multiple_cards_24h": 8,
                "velocity_score": 95.5
            }, "Transaction originated from Russia (IP: 185.220.101.45), 5900 miles from customer's location. Multiple cards used in 24h."),
            ("fraud_indicators", {
                "avs_match": "N",
                "cvv_match": "N",
                "3ds_used": False,
                "device_fingerprint": "DEV999001",
                "device_known": False,
                "browser_fingerprint": "Mozilla/5.0 (unknown) - first seen",
                "ip_reputation": "high_risk",
                "transaction_pattern": "unusual_behavior"
            }, "Strong fraud indicators: AVS/CVV failed, no 3DS, new device, high-risk IP address."),
            ("velocity_check", {
                "cards_last_24h": 8,
                "transactions_last_week": 12,
                "amount_last_24h": 8750.50,
                "velocity_flag": True,
                "same_ip_count": 0,
                "risk_level": "critical"
            }, "High velocity detected: 8 different cards used in 24h, $8,750.50 in transactions, 12 transactions in 7 days."),
            ("previous_dispute", {
                "total_disputes": 0,
                "fraud_disputes": 0,
                "customer_standing": "good",
                "account_age_days": 1245,
                "first_dispute": True
            }, "Customer has 0 previous disputes. First-time fraud claim. Account in good standing for 3.4 years."),
        ],
        "cb_002": [  # Account Takeover - True Fraud
            ("support_ticket", {
                "ticket_id": "TKT12346",
                "customer_contact_date": random_date(23, 18),
                "contact_method": "email",
                "customer_statement": "Received email about password change. Did not authorize. Account locked.",
                "account_locked": True,
                "password_reset_attempts": 5,
                "suspicious_activity_alert": True
            }, "Customer reported unauthorized account access. Account locked after suspicious login attempts."),
            ("login_analysis", {
                "login_location": "Ukraine",
                "login_ip": "203.0.113.22",
                "login_device": "Windows 10 - new device",
                "customer_location": "New York, NY",
                "login_time": "02:15 AM EST",
                "device_known": False,
                "browser_fingerprint": "Chrome/120.0 - first seen",
                "session_duration": "45 minutes",
                "actions_taken": ["password_change", "email_change", "purchase"]
            }, "Account login from Ukraine (IP: 203.0.113.22) at 2:15 AM. New device, password and email changed, then purchase made."),
            ("fraud_indicators", {
                "avs_match": "Z",
                "cvv_match": "N",
                "3ds_used": False,
                "device_fingerprint": "DEV999002",
                "ip_reputation": "medium_risk",
                "account_takeover_score": 88.2,
                "session_anomaly": True
            }, "Account takeover indicators: Partial AVS match, CVV failed, no 3DS, new device, suspicious session activity."),
            ("velocity_check", {
                "cards_last_24h": 5,
                "transactions_last_week": 7,
                "amount_last_24h": 3200.00,
                "same_ip_count": 0,
                "account_access_pattern": "unusual"
            }, "Multiple unauthorized transactions: 5 cards in 24h, $3,200 total, all from different IP addresses."),
            ("previous_dispute", {
                "total_disputes": 0,
                "account_security": "good",
                "first_security_incident": True
            }, "No previous disputes. First security incident. Customer maintains account security practices."),
        ],
        "cb_003": [  # Item Not Received - Friendly Fraud
            ("support_ticket", {
                "ticket_id": "TKT12347",
                "customer_contact_date": random_date(35, 30),
                "contact_method": "chat",
                "customer_statement": "Ordered item on date X, never received. Tracking shows delivered but not at my address.",
                "tracking_number": "1Z999AA10123456784",
                "delivery_date": random_date(40, 35),
                "delivery_status": "delivered"
            }, "Customer contacted support claiming item never received. Tracking shows delivered."),
            ("shipping_evidence", {
                "tracking_number": "1Z999AA10123456784",
                "carrier": "UPS",
                "delivered_date": random_date(40, 35),
                "delivery_address": "123 Main St, San Francisco, CA 94102",
                "signature_required": True,
                "signature_name": "E. Williams",
                "delivery_photo": "PHOTO-DEL-2024-001",
                "gps_coordinates": "37.7749,-122.4194",
                "delivery_time": "2:30 PM"
            }, "Delivery confirmed: Tracking shows delivered to customer address on date. Signature captured: 'E. Williams'. GPS coordinates match."),
            ("login", {
                "login_location": "San Francisco, CA",
                "login_ip": "192.168.1.100",
                "login_device": "iPhone 14 Pro - known device",
                "device_fingerprint": "DEV123456",
                "login_time": random_date(45, 42),
                "device_known": True,
                "same_ip_as_transaction": True
            }, "Customer logged in from usual location (San Francisco). Same device and IP as transaction. Device fingerprint matches historical data."),
            ("refund", {
                "refund_offered": True,
                "refund_date": random_date(32, 30),
                "refund_amount": 299.99,
                "refund_status": "declined",
                "customer_response": "Customer declined refund, filed chargeback instead",
                "refund_method": "original_payment"
            }, "Merchant offered full refund ($299.99) but customer declined. Customer filed chargeback instead of accepting refund."),
            ("previous_dispute", {
                "total_disputes": 3,
                "similar_disputes": 2,
                "dispute_pattern": "item_not_received",
                "win_rate": 0.0,
                "customer_behavior": "repeat_offender"
            }, "Customer has 3 previous disputes, 2 for 'item not received'. Pattern of similar claims. All previous cases lost by customer."),
        ],
        "cb_004": [  # Product Quality Issue - Friendly Fraud
            ("support_ticket", {
                "ticket_id": "TKT12348",
                "customer_contact_date": random_date(50, 45),
                "contact_method": "email",
                "customer_statement": "Product received but defective. Doesn't work as described.",
                "product_sku": "ELEC-12345",
                "order_date": random_date(60, 55),
                "return_requested": True
            }, "Customer contacted support claiming product defective. Return requested."),
            ("refund", {
                "refund_offered": True,
                "refund_date": random_date(48, 45),
                "refund_amount": 549.99,
                "refund_status": "processed",
                "refund_method": "credit_card",
                "refund_confirmation": "REF-2024-001",
                "customer_acknowledgment": False
            }, "Merchant processed full refund ($549.99) on date. Customer received refund confirmation but filed chargeback anyway."),
            ("product_evidence", {
                "product_sku": "ELEC-12345",
                "warranty_status": "active",
                "return_window": "30 days",
                "return_request_date": random_date(50, 45),
                "days_since_purchase": 12,
                "return_policy_compliance": True,
                "product_condition": "unopened",
                "return_shipping_label": "LABEL-2024-001"
            }, "Product return processed within 30-day window. Return shipping label provided. Customer received refund but still filed chargeback."),
            ("login", {
                "login_location": "Los Angeles, CA",
                "login_ip": "192.168.1.101",
                "device_fingerprint": "DEV123457",
                "device_known": True,
                "same_ip_as_transaction": True,
                "login_frequency": "daily"
            }, "Customer logged in from usual location. Same device and IP as transaction. Regular account activity."),
            ("previous_dispute", {
                "total_disputes": 1,
                "similar_disputes": 1,
                "dispute_pattern": "quality_issue",
                "refund_after_chargeback": True
            }, "Customer has 1 previous dispute for quality issue. Previously received refund after chargeback."),
        ],
        "cb_005": [  # Subscription Cancellation - Friendly Fraud
            ("support_ticket", {
                "ticket_id": "TKT12349",
                "customer_contact_date": random_date(80, 75),
                "contact_method": "email",
                "customer_statement": "Cancelled subscription on date X but was charged anyway. Should not have been billed.",
                "subscription_id": "SUB-78901",
                "cancellation_date_claimed": random_date(92, 88),
                "billing_date": random_date(90, 85)
            }, "Customer claims subscription cancelled before billing cycle but was charged anyway."),
            ("subscription_evidence", {
                "subscription_id": "SUB-78901",
                "subscription_start": random_date(180, 175),
                "billing_cycle": "monthly",
                "cancellation_date_actual": random_date(88, 85),
                "cancellation_date_claimed": random_date(92, 88),
                "last_billing_date": random_date(90, 85),
                "tos_agreement": "TOS-2024-001",
                "cancellation_policy": "7-day notice required",
                "cancellation_method": "email",
                "cancellation_confirmation": "CANCEL-2024-001"
            }, "Subscription records show cancellation on date (3 days after billing). Customer claims cancellation before billing. 7-day notice policy applies."),
            ("login", {
                "login_location": "Chicago, IL",
                "login_ip": "192.168.1.102",
                "device_fingerprint": "DEV123458",
                "device_known": True,
                "account_activity": "active",
                "service_usage": "last_30_days"
            }, "Customer logged in from usual location. Account shows active service usage in last 30 days after claimed cancellation."),
            ("refund", {
                "refund_offered": True,
                "refund_date": random_date(78, 75),
                "refund_amount": 79.99,
                "refund_status": "pending",
                "customer_response": "pending"
            }, "Merchant offered prorated refund. Waiting for customer response."),
            ("previous_dispute", {
                "total_disputes": 0,
                "subscription_history": "new_customer",
                "first_billing_cycle": True
            }, "No previous disputes. Customer is new subscriber. This is first billing cycle dispute."),
        ],
        "cb_006": [  # Unauthorized Family Member - Friendly Fraud
            ("support_ticket", {
                "ticket_id": "TKT12350",
                "customer_contact_date": random_date(30, 25),
                "contact_method": "phone",
                "customer_statement": "Did not authorize this transaction. Don't recognize this purchase.",
                "transaction_amount": 199.99,
                "merchant_name": "Home Essentials"
            }, "Customer claims unauthorized transaction. Does not recognize purchase."),
            ("transaction_analysis", {
                "ip_address": "192.168.1.103",
                "device_fingerprint": "DEV123459",
                "shipping_address": "123 Oak St, Boston, MA 02101",
                "billing_address": "123 Oak St, Boston, MA 02101",
                "email_used": "j.taylor@email.com",
                "address_match": True,
                "device_match": True,
                "ip_match": True,
                "historical_orders": 4
            }, "Transaction analysis: Same IP (192.168.1.103), device (DEV123459), shipping address, and email as 4 previous orders."),
            ("login", {
                "login_location": "Boston, MA",
                "login_ip": "192.168.1.103",
                "device_fingerprint": "DEV123459",
                "device_known": True,
                "same_ip_as_transaction": True,
                "login_frequency": "weekly"
            }, "Customer logged in from same location (Boston). Same device and IP as transaction. Regular account activity."),
            ("fraud_indicators", {
                "avs_match": "Y",
                "cvv_match": "Y",
                "3ds_used": True,
                "device_known": True,
                "ip_reputation": "low_risk",
                "fraud_score": 18.0,
                "risk_level": "low"
            }, "All fraud checks passed: AVS match, CVV match, 3DS used, known device, low risk IP. Fraud score: 18.0."),
            ("previous_dispute", {
                "total_disputes": 2,
                "similar_disputes": 1,
                "dispute_pattern": "unauthorized_family",
                "family_member_pattern": True
            }, "Customer has 2 previous disputes. Pattern suggests family member usage. Previous 'unauthorized' claim resolved in favor of merchant."),
        ],
        "cb_007": [  # Duplicate Charge - Merchant Error
            ("support_ticket", {
                "ticket_id": "TKT12351",
                "customer_contact_date": random_date(15, 12),
                "contact_method": "chat",
                "customer_statement": "Charged twice for same order. Order #ORD-12345 charged on date X and date Y.",
                "order_number": "ORD-12345",
                "transaction_ids": [cb7_tx_id, f"{cb7_tx_id}_DUPLICATE"],
                "amount": 149.99
            }, "Customer reported duplicate charge for same order. Two identical transactions detected."),
            ("merchant_investigation", {
                "order_number": "ORD-12345",
                "transaction_1": cb7_tx_id,
                "transaction_2": f"{cb7_tx_id}_DUPLICATE",
                "amount_1": 149.99,
                "amount_2": 149.99,
                "transaction_1_date": random_date(20, 18),
                "transaction_2_date": random_date(20, 18),
                "time_difference_seconds": 45,
                "merchant_confirmed": True,
                "error_type": "system_duplicate",
                "root_cause": "payment_gateway_timeout_retry"
            }, "Merchant investigation: Confirmed duplicate charge. Same order #ORD-12345 charged twice within 45 seconds. System error due to payment gateway timeout retry."),
            ("refund", {
                "refund_processed": True,
                "refund_date": random_date(12, 10),
                "refund_amount": 149.99,
                "refund_method": "credit_card",
                "refund_confirmation": "REF-2024-002",
                "refund_status": "completed",
                "customer_notified": True
            }, "Merchant confirmed error and processed immediate refund ($149.99). Refund confirmation sent to customer."),
            ("login", {
                "login_location": "San Francisco, CA",
                "login_ip": "192.168.1.100",
                "device_known": True,
                "same_ip_as_transaction": True
            }, "Customer logged in from usual location. Same IP as transaction."),
            ("system_fix", {
                "issue_resolved": True,
                "fix_date": random_date(10, 8),
                "fix_description": "Payment gateway retry logic updated to prevent duplicate charges",
                "prevention_measures": "Added duplicate transaction detection"
            }, "System fix implemented: Payment gateway retry logic updated. Duplicate transaction detection added."),
        ],
        "cb_008": [  # Wrong Amount - Merchant Error
            ("support_ticket", {
                "ticket_id": "TKT12352",
                "customer_contact_date": random_date(18, 15),
                "contact_method": "email",
                "customer_statement": "Ordered item for $99.99 but charged $249.99. Price on website was $99.99.",
                "order_number": "ORD-12346",
                "expected_amount": 99.99,
                "charged_amount": 249.99,
                "difference": 150.00
            }, "Customer reported wrong amount charged. Expected $99.99, charged $249.99."),
            ("merchant_investigation", {
                "order_number": "ORD-12346",
                "product_sku": "PROD-56789",
                "website_price": 99.99,
                "charged_amount": 249.99,
                "pricing_error": True,
                "error_type": "database_price_mismatch",
                "correct_price": 99.99,
                "error_source": "price_sync_issue",
                "merchant_confirmed": True
            }, "Merchant investigation: Confirmed pricing error. Product SKU PROD-56789 shows $99.99 on website but database had old price $249.99. Price sync issue."),
            ("refund", {
                "refund_processed": True,
                "refund_date": random_date(15, 13),
                "refund_amount": 150.00,
                "refund_method": "credit_card",
                "refund_confirmation": "REF-2024-003",
                "partial_refund": True,
                "customer_notified": True
            }, "Merchant processed partial refund ($150.00 difference). Customer charged correct amount of $99.99."),
            ("login", {
                "login_location": "New York, NY",
                "login_ip": "192.168.1.101",
                "device_known": True
            }, "Customer logged in from usual location."),
            ("system_fix", {
                "issue_resolved": True,
                "fix_date": random_date(13, 11),
                "fix_description": "Price database sync fixed. Added validation to prevent price mismatches",
                "prevention_measures": "Automated price validation before checkout"
            }, "System fix: Price database sync corrected. Added automated price validation to prevent future mismatches."),
        ],
        "cb_009": [  # Legitimate Purchase - Not Guilty
            ("support_ticket", {
                "ticket_id": "TKT12353",
                "customer_contact_date": random_date(60, 55),
                "contact_method": "chargeback_notification",
                "customer_statement": "Customer filed chargeback claiming unauthorized transaction.",
                "chargeback_reason": "fraud",
                "amount": 179.99
            }, "Customer filed chargeback claiming unauthorized transaction. Chargeback received for investigation."),
            ("transaction_evidence", {
                "ip_address": "192.168.1.100",
                "device_fingerprint": "DEV123456",
                "shipping_address": "123 Main St, San Francisco, CA 94102",
                "billing_address": "123 Main St, San Francisco, CA 94102",
                "email_used": "emma.w@email.com",
                "email_confirmation": "EMAIL-CONF-2024-001",
                "order_confirmation_sent": True,
                "order_confirmation_opened": True,
                "order_confirmation_date": random_date(70, 65)
            }, "Transaction evidence: Same IP, device, shipping address, and email as customer. Order confirmation email sent and opened by customer."),
            ("login", {
                "login_location": "San Francisco, CA",
                "login_ip": "192.168.1.100",
                "device_fingerprint": "DEV123456",
                "device_known": True,
                "login_before_transaction": True,
                "login_time": random_date(70, 69),
                "transaction_time": random_date(70, 65)
            }, "Customer logged in from usual location 1 hour before transaction. Same device and IP. Device fingerprint matches account history."),
            ("delivery_evidence", {
                "tracking_number": "1Z999AA10123456785",
                "carrier": "FedEx",
                "delivered_date": random_date(68, 65),
                "delivery_address": "123 Main St, San Francisco, CA 94102",
                "signature_required": True,
                "signature_name": "E. Williams",
                "delivery_photo": "PHOTO-DEL-2024-002",
                "gps_coordinates": "37.7749,-122.4194"
            }, "Delivery confirmed: Item delivered to customer address. Signature captured: 'E. Williams'. GPS coordinates match shipping address."),
            ("previous_dispute", {
                "total_disputes": 1,
                "similar_disputes": 1,
                "dispute_pattern": "unauthorized_claim",
                "win_rate": 0.0
            }, "Customer has 1 previous dispute for 'unauthorized' transaction. Previous case lost by customer. Pattern of chargeback abuse."),
        ],
        "cb_010": [  # Subscription Renewal - Not Guilty
            ("support_ticket", {
                "ticket_id": "TKT12354",
                "customer_contact_date": random_date(75, 70),
                "contact_method": "chargeback_notification",
                "customer_statement": "Customer filed chargeback claiming unauthorized subscription charge.",
                "subscription_id": "SUB-78902",
                "amount": 49.99
            }, "Customer filed chargeback claiming unauthorized subscription. Chargeback received for investigation."),
            ("subscription_evidence", {
                "subscription_id": "SUB-78902",
                "subscription_start": random_date(240, 235),
                "billing_cycle": "monthly",
                "tos_agreement_date": random_date(240, 235),
                "tos_agreement_signed": True,
                "tos_version": "v2.1",
                "agreement_acceptance_ip": "192.168.1.101",
                "usage_logs": {
                    "last_30_days": 180,
                    "last_7_days": 45,
                    "last_login": random_date(85, 83)
                }
            }, "Subscription evidence: Active subscription for 8 months. TOS signed and accepted. Customer logged in 2 days before billing. 180 usage sessions in last 30 days."),
            ("login", {
                "login_location": "Los Angeles, CA",
                "login_ip": "192.168.1.101",
                "device_fingerprint": "DEV123457",
                "device_known": True,
                "login_frequency": "daily",
                "last_login_before_billing": random_date(85, 83)
            }, "Customer logged in from usual location. Same device and IP as subscription signup. Active daily usage. Last login 2 days before billing."),
            ("refund", {
                "refund_offered": False,
                "chargeback_response": "evidence_package_submitted",
                "evidence_submitted_date": random_date(70, 68),
                "evidence_package": {
                    "tos_agreement": "TOS-2024-002",
                    "usage_logs": "LOGS-2024-001",
                    "ip_match_evidence": "IP-EVIDENCE-001",
                    "device_match_evidence": "DEVICE-EVIDENCE-001"
                }
            }, "Merchant provided comprehensive evidence package: Signed TOS, 6 months usage logs, IP match, device match. Chargeback response submitted."),
            ("previous_dispute", {
                "total_disputes": 0,
                "subscription_history": "long_term",
                "billing_history": "consistent"
            }, "No previous disputes. Long-term subscriber with consistent billing history. 8 months of successful payments."),
        ],
        "cb_011": [  # Digital Goods Delivered - Not Guilty
            ("support_ticket", {
                "ticket_id": "TKT12355",
                "customer_contact_date": random_date(40, 35),
                "contact_method": "chargeback_notification",
                "customer_statement": "Customer filed chargeback claiming digital product not received.",
                "product_type": "digital_license",
                "amount": 89.99
            }, "Customer filed chargeback claiming digital product not received. Chargeback received for investigation."),
            ("delivery_evidence", {
                "product_type": "digital_license",
                "delivery_method": "email",
                "delivery_email": "lisa.a@email.com",
                "delivery_date": random_date(50, 45),
                "email_opened": True,
                "email_opened_date": random_date(50, 49),
                "license_key_sent": "LICENSE-2024-001",
                "download_link_sent": True,
                "download_link_accessed": True,
                "download_ip": "192.168.1.102",
                "download_date": random_date(50, 48),
                "download_count": 3
            }, "Digital delivery confirmed: License key sent via email. Email opened by customer. Download link accessed 3 times from customer IP (192.168.1.102)."),
            ("usage_analytics", {
                "product_activated": True,
                "activation_date": random_date(50, 48),
                "activation_ip": "192.168.1.102",
                "usage_sessions": 12,
                "last_usage_date": random_date(45, 40),
                "usage_duration_hours": 45,
                "feature_usage": ["feature_a", "feature_b", "feature_c"]
            }, "Product usage analytics: License activated and used 12 times. 45 hours of usage. Last usage 5 days before chargeback. Multiple features accessed."),
            ("login", {
                "login_location": "Chicago, IL",
                "login_ip": "192.168.1.102",
                "device_fingerprint": "DEV123458",
                "device_known": True,
                "same_ip_as_download": True,
                "same_ip_as_activation": True
            }, "Customer logged in from usual location. Same IP used for download, activation, and usage. Device fingerprint matches."),
            ("previous_dispute", {
                "total_disputes": 0,
                "digital_purchases": 5,
                "all_delivered": True
            }, "No previous disputes. Customer has 5 previous digital purchases, all successfully delivered and activated."),
        ],
        "cb_012": [  # Return Policy Violation - Not Guilty
            ("support_ticket", {
                "ticket_id": "TKT12356",
                "customer_contact_date": random_date(55, 50),
                "contact_method": "chargeback_notification",
                "customer_statement": "Customer filed chargeback claiming defective product.",
                "product_sku": "PROD-12346",
                "amount": 299.99
            }, "Customer filed chargeback claiming defective product. Chargeback received for investigation."),
            ("return_policy_evidence", {
                "return_window_days": 30,
                "purchase_date": random_date(65, 60),
                "return_request_date": random_date(55, 50),
                "days_since_purchase": 45,
                "return_window_expired": True,
                "return_policy_url": "https://merchant.com/returns",
                "policy_acknowledged": True,
                "policy_acknowledgment_date": random_date(65, 60)
            }, "Return policy: 30-day return window. Purchase made 45 days ago. Return window expired 15 days before chargeback. Customer acknowledged policy at purchase."),
            ("product_evidence", {
                "product_sku": "PROD-12346",
                "product_condition_received": "new",
                "product_condition_returned": "used",
                "return_photos": ["PHOTO-RET-001", "PHOTO-RET-002"],
                "product_usage_evidence": True,
                "warranty_claim": False,
                "defect_photos_provided": False
            }, "Product evidence: Item received new, returned used. Photos show significant wear. No defect photos provided. Warranty claim not filed."),
            ("refund", {
                "refund_offered": False,
                "chargeback_response": "evidence_package_submitted",
                "evidence_submitted_date": random_date(50, 48),
                "evidence_package": {
                    "return_policy": "POLICY-2024-001",
                    "product_photos": "PHOTOS-2024-001",
                    "policy_acknowledgment": "ACK-2024-001"
                }
            }, "Merchant provided evidence package: Return policy, photos of used item, policy acknowledgment. Chargeback response submitted."),
            ("previous_dispute", {
                "total_disputes": 2,
                "similar_disputes": 1,
                "dispute_pattern": "return_policy_violation",
                "win_rate": 0.0
            }, "Customer has 2 previous disputes. Pattern of return policy violations. All previous cases lost by customer."),
        ],
        "cb_013": [  # Item Delivered - Not Guilty
            ("support_ticket", {
                "ticket_id": "TKT12357",
                "customer_contact_date": random_date(45, 40),
                "contact_method": "chargeback_notification",
                "customer_statement": "Customer filed chargeback claiming item never received.",
                "order_number": "ORD-12347",
                "amount": 399.99
            }, "Customer filed chargeback claiming item never received. Chargeback received for investigation."),
            ("delivery_evidence", {
                "tracking_number": "1Z999AA10123456786",
                "carrier": "UPS",
                "delivered_date": random_date(52, 50),
                "delivery_address": "456 Pine St, Seattle, WA 98101",
                "signature_required": True,
                "signature_name": "M. Garcia",
                "signature_match": True,
                "delivery_photo": "PHOTO-DEL-2024-003",
                "gps_coordinates": "47.6062,-122.3321",
                "gps_match": True,
                "delivery_time": "3:45 PM",
                "delivery_proof": "COMPLETE"
            }, "Delivery confirmed: Item delivered to customer address. Signature captured: 'M. Garcia'. GPS coordinates match shipping address. Photo evidence available."),
            ("login", {
                "login_location": "Seattle, WA",
                "login_ip": "192.168.1.104",
                "device_fingerprint": "DEV123460",
                "device_known": True,
                "same_ip_as_transaction": True,
                "login_after_delivery": True,
                "login_date": random_date(51, 50)
            }, "Customer logged in from usual location (Seattle) 1 day after delivery. Same device and IP as transaction."),
            ("refund", {
                "refund_offered": False,
                "chargeback_response": "evidence_package_submitted",
                "evidence_submitted_date": random_date(40, 38),
                "evidence_package": {
                    "delivery_confirmation": "DEL-2024-001",
                    "signature_proof": "SIG-2024-001",
                    "gps_tracking": "GPS-2024-001",
                    "delivery_photo": "PHOTO-2024-001"
                }
            }, "Merchant provided comprehensive evidence: Delivery confirmation, signature proof, GPS tracking, delivery photo. Chargeback response submitted."),
            ("previous_dispute", {
                "total_disputes": 1,
                "similar_disputes": 1,
                "dispute_pattern": "item_not_received",
                "win_rate": 0.0
            }, "Customer has 1 previous dispute for 'item not received'. Previous case lost by customer. Delivery was confirmed in previous case."),
        ],
        "cb_014": [  # Card Skimming - True Fraud
            ("support_ticket", {
                "ticket_id": "TKT12358",
                "customer_contact_date": random_date(38, 33),
                "contact_method": "phone",
                "customer_statement": "Noticed unauthorized transactions. Card used at gas station recently.",
                "card_cancelled": True,
                "terminal_compromised": True,
                "merchant_notified": True
            }, "Customer reported card skimming. Card cancelled. Compromised terminal identified."),
            ("transaction_analysis", {
                "unusual_location": True,
                "location_country": "USA",
                "location_city": "Los Angeles, CA",
                "customer_location": "San Francisco, CA",
                "distance_miles": 380,
                "terminal_id": "TERM-COMP-2024-001",
                "terminal_risk": "high",
                "multiple_cards_24h": 6,
                "velocity_score": 92.3
            }, "Transaction from compromised terminal in Los Angeles. Terminal flagged for skimming. 6 cards used in 24h from same terminal."),
            ("fraud_indicators", {
                "avs_match": "N",
                "cvv_match": "N",
                "3ds_used": False,
                "device_fingerprint": "DEV999003",
                "device_known": False,
                "terminal_compromised": True,
                "ip_reputation": "medium_risk",
                "transaction_pattern": "skimming_pattern"
            }, "Strong fraud indicators: AVS/CVV failed, no 3DS, new device, compromised terminal. Skimming pattern detected."),
            ("velocity_check", {
                "cards_last_24h": 6,
                "transactions_last_week": 9,
                "amount_last_24h": 4850.75,
                "velocity_flag": True,
                "same_terminal_count": 6,
                "risk_level": "critical"
            }, "High velocity detected: 6 different cards from same terminal in 24h, $4,850.75 in transactions, 9 transactions in 7 days."),
            ("previous_dispute", {
                "total_disputes": 2,
                "fraud_disputes": 1,
                "customer_standing": "good",
                "first_skimming_incident": True
            }, "Customer has 2 previous disputes (1 fraud). First skimming incident. Account in good standing."),
        ],
        "cb_015": [  # CNP Fraud - True Fraud
            ("support_ticket", {
                "ticket_id": "TKT12359",
                "customer_contact_date": random_date(45, 40),
                "contact_method": "email",
                "customer_statement": "Card lost on date X. Reported to bank immediately. These transactions are not mine.",
                "card_lost": True,
                "card_cancelled": True,
                "card_issuer_notified": True
            }, "Customer reported card lost. Card cancelled. Card issuer notified immediately."),
            ("transaction_analysis", {
                "unusual_location": True,
                "location_country": "Brazil",
                "location_city": "São Paulo",
                "customer_location": "San Francisco, CA",
                "distance_miles": 6500,
                "time_of_transaction": "04:20 AM local time",
                "cnp_transaction": True,
                "card_details_stolen": True
            }, "Card Not Present (CNP) transaction from Brazil (IP: 172.217.12.46), 6500 miles from customer location. Card details stolen."),
            ("fraud_indicators", {
                "avs_match": "N",
                "cvv_match": "N",
                "3ds_used": False,
                "device_fingerprint": "DEV999004",
                "device_known": False,
                "ip_reputation": "high_risk",
                "cnp_fraud_score": 89.7,
                "transaction_pattern": "stolen_card_details"
            }, "Strong CNP fraud indicators: AVS/CVV failed, no 3DS, new device, high-risk IP. Stolen card details pattern."),
            ("velocity_check", {
                "cards_last_24h": 4,
                "transactions_last_week": 6,
                "amount_last_24h": 4250.00,
                "velocity_flag": True,
                "same_ip_count": 0,
                "risk_level": "critical"
            }, "High velocity detected: 4 cards in 24h, $4,250.00 in transactions, 6 transactions in 7 days from different IPs."),
            ("previous_dispute", {
                "total_disputes": 1,
                "fraud_disputes": 1,
                "customer_standing": "good",
                "account_age_days": 1245,
                "first_card_loss": True
            }, "Customer has 1 previous fraud dispute (cb_001). First card loss incident. Account in good standing for 3.4 years."),
        ],
        "cb_016": [  # Synthetic Identity Fraud - True Fraud
            ("support_ticket", {
                "ticket_id": "TKT12360",
                "customer_contact_date": random_date(50, 45),
                "contact_method": "phone",
                "customer_statement": "Account opened fraudulently. Identity stolen. Never created this account.",
                "account_closure_requested": True,
                "identity_theft_report": "IDT-RPT-2024-001",
                "fraud_department_notified": True
            }, "Customer reported synthetic identity fraud. Account opened fraudulently. Identity theft report filed."),
            ("transaction_analysis", {
                "unusual_location": True,
                "location_country": "Nigeria",
                "location_city": "Lagos",
                "account_creation_date": random_date(60, 55),
                "account_age_days": 5,
                "minimal_history": True,
                "synthetic_pattern": True,
                "multiple_cards_24h": 7
            }, "Transaction from Nigeria (IP: 104.248.90.2). Account created 5 days ago with minimal history. Synthetic identity pattern."),
            ("fraud_indicators", {
                "avs_match": "Z",
                "cvv_match": "N",
                "3ds_used": False,
                "device_fingerprint": "DEV999005",
                "device_known": False,
                "ip_reputation": "high_risk",
                "synthetic_score": 91.2,
                "account_age_risk": "new_account"
            }, "Synthetic fraud indicators: Partial AVS match, CVV failed, no 3DS, new device, new account, high-risk IP."),
            ("velocity_check", {
                "cards_last_24h": 7,
                "transactions_last_week": 11,
                "amount_last_24h": 6250.25,
                "velocity_flag": True,
                "same_ip_count": 0,
                "risk_level": "critical"
            }, "High velocity detected: 7 cards in 24h, $6,250.25 in transactions, 11 transactions in 7 days from new account."),
            ("previous_dispute", {
                "total_disputes": 1,
                "fraud_disputes": 0,
                "account_type": "synthetic",
                "first_identity_theft": True
            }, "Customer has 1 previous dispute (not_guilty case). Account identified as synthetic identity. First identity theft report."),
        ],
        "cb_017": [  # Item Not Received - Repeat Offender
            ("support_ticket", {
                "ticket_id": "TKT12361",
                "customer_contact_date": random_date(110, 105),
                "contact_method": "chat",
                "customer_statement": "Ordered item on date X, never received. Tracking shows delivered but package stolen.",
                "tracking_number": "1Z999AA10123456787",
                "delivery_date": random_date(115, 110),
                "delivery_status": "delivered",
                "previous_claims": 3
            }, "Customer contacted support claiming item never received. Tracking shows delivered. Customer has 3 previous 'item not received' claims."),
            ("shipping_evidence", {
                "tracking_number": "1Z999AA10123456787",
                "carrier": "FedEx",
                "delivered_date": random_date(115, 110),
                "delivery_address": "123 Main St, San Francisco, CA 94102",
                "signature_required": True,
                "signature_name": "E. Williams",
                "delivery_photo": "PHOTO-DEL-2024-004",
                "gps_coordinates": "37.7749,-122.4194",
                "delivery_time": "11:15 AM"
            }, "Delivery confirmed: Tracking shows delivered to customer address. Signature captured: 'E. Williams'. GPS coordinates match."),
            ("login", {
                "login_location": "San Francisco, CA",
                "login_ip": "192.168.1.100",
                "device_fingerprint": "DEV123456",
                "device_known": True,
                "same_ip_as_transaction": True,
                "login_frequency": "daily"
            }, "Customer logged in from usual location (San Francisco). Same device and IP as transaction. Regular account activity."),
            ("previous_dispute", {
                "total_disputes": 4,
                "similar_disputes": 3,
                "dispute_pattern": "item_not_received",
                "win_rate": 0.0,
                "customer_behavior": "repeat_offender",
                "risk_flag": "high_risk_customer"
            }, "Customer has 4 previous disputes, 3 for 'item not received'. All previous cases lost by customer. High-risk repeat offender pattern."),
        ],
        "cb_018": [  # Subscription Renewal Dispute
            ("support_ticket", {
                "ticket_id": "TKT12362",
                "customer_contact_date": random_date(170, 165),
                "contact_method": "email",
                "customer_statement": "Cancelled subscription months ago but was charged again. Should not have been billed.",
                "subscription_id": "SUB-78903",
                "cancellation_date_claimed": random_date(185, 180),
                "billing_date": random_date(180, 175)
            }, "Customer claims subscription cancelled before billing cycle but was charged anyway. Previous subscription dispute history."),
            ("subscription_evidence", {
                "subscription_id": "SUB-78903",
                "subscription_start": random_date(240, 235),
                "billing_cycle": "monthly",
                "cancellation_date_actual": random_date(178, 175),
                "cancellation_date_claimed": random_date(185, 180),
                "last_billing_date": random_date(180, 175),
                "tos_agreement": "TOS-2024-003",
                "cancellation_policy": "7-day notice required",
                "previous_dispute": "cb_005"
            }, "Subscription records show cancellation 3 days after billing. Customer claims cancellation before billing. Previous subscription dispute (cb_005)."),
            ("login", {
                "login_location": "Chicago, IL",
                "login_ip": "192.168.1.102",
                "device_fingerprint": "DEV123458",
                "device_known": True,
                "account_activity": "active",
                "service_usage": "last_30_days"
            }, "Customer logged in from usual location. Account shows active service usage in last 30 days after claimed cancellation."),
            ("previous_dispute", {
                "total_disputes": 2,
                "similar_disputes": 2,
                "dispute_pattern": "subscription_renewal",
                "subscription_history": "repeat_offender"
            }, "Customer has 2 previous disputes, both for subscription renewal. Pattern of subscription chargeback abuse."),
        ],
        "cb_019": [  # Quality Issue - Repeat Pattern
            ("support_ticket", {
                "ticket_id": "TKT12363",
                "customer_contact_date": random_date(190, 185),
                "contact_method": "email",
                "customer_statement": "Product received but defective. Doesn't work as described. Same issue as before.",
                "product_sku": "PROD-12347",
                "order_date": random_date(200, 195),
                "return_requested": True,
                "previous_quality_claims": 1
            }, "Customer contacted support claiming product defective. Return requested. Previous quality dispute (cb_004)."),
            ("refund", {
                "refund_offered": True,
                "refund_date": random_date(188, 185),
                "refund_amount": 375.50,
                "refund_status": "processed",
                "refund_method": "credit_card",
                "refund_confirmation": "REF-2024-004",
                "customer_acknowledgment": False
            }, "Merchant processed full refund ($375.50). Customer received refund confirmation but filed chargeback anyway."),
            ("product_evidence", {
                "product_sku": "PROD-12347",
                "warranty_status": "active",
                "return_window": "30 days",
                "return_request_date": random_date(190, 185),
                "days_since_purchase": 15,
                "return_policy_compliance": True,
                "product_condition": "unopened",
                "pattern_match": "cb_004"
            }, "Product return processed within 30-day window. Customer received refund but still filed chargeback. Matches pattern from cb_004."),
            ("previous_dispute", {
                "total_disputes": 2,
                "similar_disputes": 2,
                "dispute_pattern": "quality_issue",
                "refund_after_chargeback": True,
                "repeat_pattern": True
            }, "Customer has 2 previous disputes, both for quality issues. Previously received refund after chargeback. Repeat pattern detected."),
        ],
        "cb_020": [  # Family Member Purchase
            ("support_ticket", {
                "ticket_id": "TKT12364",
                "customer_contact_date": random_date(140, 135),
                "contact_method": "phone",
                "customer_statement": "Did not authorize this transaction. Don't recognize this purchase.",
                "transaction_amount": 275.25,
                "merchant_name": "FashionHub",
                "previous_similar_claim": "cb_006"
            }, "Customer claims unauthorized transaction. Does not recognize purchase. Previous similar claim (cb_006)."),
            ("transaction_analysis", {
                "ip_address": "192.168.1.103",
                "device_fingerprint": "DEV123459",
                "shipping_address": "123 Oak St, Boston, MA 02101",
                "billing_address": "123 Oak St, Boston, MA 02101",
                "email_used": "j.taylor@email.com",
                "address_match": True,
                "device_match": True,
                "ip_match": True,
                "historical_orders": 6
            }, "Transaction analysis: Same IP (192.168.1.103), device (DEV123459), shipping address, and email as 6 previous orders."),
            ("login", {
                "login_location": "Boston, MA",
                "login_ip": "192.168.1.103",
                "device_fingerprint": "DEV123459",
                "device_known": True,
                "same_ip_as_transaction": True,
                "login_frequency": "weekly"
            }, "Customer logged in from same location (Boston). Same device and IP as transaction. Regular account activity."),
            ("previous_dispute", {
                "total_disputes": 3,
                "similar_disputes": 2,
                "dispute_pattern": "unauthorized_family",
                "family_member_pattern": True,
                "previous_case": "cb_006"
            }, "Customer has 3 previous disputes, 2 for 'unauthorized' (including cb_006). Strong pattern suggests family member usage."),
        ],
        "cb_021": [  # Processing Error - Merchant Error
            ("support_ticket", {
                "ticket_id": "TKT12365",
                "customer_contact_date": random_date(90, 85),
                "contact_method": "chat",
                "customer_statement": "Charged twice for same order. Payment gateway error caused duplicate charge.",
                "order_number": "ORD-12348",
                "transaction_ids": [cb21_tx_id, f"{cb21_tx_id}_DUPLICATE"],
                "amount": 189.99,
                "payment_gateway_error": True
            }, "Customer reported duplicate charge due to payment processing error. Two identical transactions detected."),
            ("merchant_investigation", {
                "order_number": "ORD-12348",
                "transaction_1": cb21_tx_id,
                "transaction_2": f"{cb21_tx_id}_DUPLICATE",
                "amount_1": 189.99,
                "amount_2": 189.99,
                "transaction_1_date": random_date(100, 95),
                "transaction_2_date": random_date(100, 95),
                "time_difference_seconds": 30,
                "merchant_confirmed": True,
                "error_type": "gateway_timeout",
                "root_cause": "payment_gateway_retry"
            }, "Merchant investigation: Confirmed duplicate charge. Same order charged twice within 30 seconds. Payment gateway timeout retry error."),
            ("refund", {
                "refund_processed": True,
                "refund_date": random_date(85, 83),
                "refund_amount": 189.99,
                "refund_method": "credit_card",
                "refund_confirmation": "REF-2024-005",
                "refund_status": "completed",
                "customer_notified": True
            }, "Merchant confirmed error and processed immediate refund ($189.99). Refund confirmation sent to customer."),
            ("previous_dispute", {
                "total_disputes": 2,
                "merchant_error_disputes": 1,
                "previous_case": "cb_007",
                "customer_relationship": "good"
            }, "Customer has 2 previous disputes (1 merchant error - cb_007). Good customer relationship. Merchant errors acknowledged and resolved."),
        ],
        "cb_022": [  # Refund Not Processed - Merchant Error
            ("support_ticket", {
                "ticket_id": "TKT12366",
                "customer_contact_date": random_date(120, 115),
                "contact_method": "email",
                "customer_statement": "Returned item and refund was authorized but never received. Waiting 2 weeks for refund.",
                "order_number": "ORD-12349",
                "return_date": random_date(125, 120),
                "refund_authorized": True,
                "refund_status": "pending"
            }, "Customer reported refund authorized but not processed. Return completed 2 weeks ago. Refund still pending."),
            ("merchant_investigation", {
                "order_number": "ORD-12349",
                "return_date": random_date(125, 120),
                "refund_authorized_date": random_date(125, 120),
                "refund_processed_date": None,
                "system_error": True,
                "error_type": "refund_processing_failure",
                "error_source": "refund_system_bug",
                "merchant_confirmed": True,
                "refund_amount": 319.99
            }, "Merchant investigation: Confirmed refund authorization but processing failed due to system bug. Refund system error identified."),
            ("refund", {
                "refund_processed": True,
                "refund_date": random_date(115, 113),
                "refund_amount": 319.99,
                "refund_method": "credit_card",
                "refund_confirmation": "REF-2024-006",
                "refund_status": "completed",
                "refund_delay_days": 14,
                "customer_notified": True,
                "apology_sent": True
            }, "Merchant acknowledged error and processed refund ($319.99) with 14-day delay. Apology sent to customer."),
            ("previous_dispute", {
                "total_disputes": 2,
                "merchant_error_disputes": 1,
                "previous_case": "cb_008",
                "customer_relationship": "good"
            }, "Customer has 2 previous disputes (1 merchant error - cb_008). Good customer relationship. Merchant errors acknowledged."),
        ],
        "cb_023": [  # Authorization Hold Not Released - Merchant Error
            ("support_ticket", {
                "ticket_id": "TKT12367",
                "customer_contact_date": random_date(65, 60),
                "contact_method": "chat",
                "customer_statement": "Cancelled order but authorization hold not released. Charged twice for cancelled order.",
                "order_number": "ORD-12350",
                "order_cancelled_date": random_date(75, 70),
                "authorization_hold": True,
                "hold_released": False
            }, "Customer reported authorization hold not released after order cancellation. Charged for cancelled order."),
            ("merchant_investigation", {
                "order_number": "ORD-12350",
                "order_cancelled_date": random_date(75, 70),
                "authorization_hold_date": random_date(75, 70),
                "hold_release_date": None,
                "system_error": True,
                "error_type": "authorization_hold_failure",
                "error_source": "payment_processor_bug",
                "merchant_confirmed": True,
                "hold_amount": 225.00
            }, "Merchant investigation: Confirmed authorization hold not released due to payment processor bug. System error identified."),
            ("refund", {
                "refund_processed": True,
                "refund_date": random_date(60, 58),
                "refund_amount": 225.00,
                "refund_method": "credit_card",
                "refund_confirmation": "REF-2024-007",
                "refund_status": "completed",
                "hold_released": True,
                "customer_notified": True
            }, "Merchant confirmed error, released authorization hold, and processed refund ($225.00). Refund confirmation sent to customer."),
            ("system_fix", {
                "issue_resolved": True,
                "fix_date": random_date(58, 56),
                "fix_description": "Payment processor authorization hold release logic fixed",
                "prevention_measures": "Added automated hold release for cancelled orders"
            }, "System fix implemented: Payment processor authorization hold release logic corrected. Automated hold release added for cancelled orders."),
            ("previous_dispute", {
                "total_disputes": 2,
                "merchant_error_disputes": 0,
                "previous_case": "cb_013",
                "customer_relationship": "good"
            }, "Customer has 2 previous disputes (1 not_guilty - cb_013). Good customer relationship. First merchant error case."),
        ]
    }

    for cb in chargeback_cases:
        cb_id = cb["chargeback_id"]
        events = case_evidence.get(cb_id, [])
        
        if not events:
            # Fallback to generic events if case not found
            fraud_type = cb["fraud_type"]
            generic_events = {
                "true_fraud": [
                    ("support_ticket", {"ticket_id": f"TKT{random.randint(10000, 99999)}"}, "Customer reported fraud."),
                    ("login", {"ip_address": "192.168.1.100"}, "Customer logged in from unusual location."),
                ],
                "friendly_fraud": [
                    ("support_ticket", {"ticket_id": f"TKT{random.randint(10000, 99999)}"}, "Customer contacted support."),
                    ("refund", {"refund_amount": cb["chargeback_amount"]}, "Merchant offered refund."),
                ],
                "merchant_error": [
                    ("support_ticket", {"ticket_id": f"TKT{random.randint(10000, 99999)}"}, "Customer reported error."),
                    ("refund", {"refund_amount": cb["chargeback_amount"]}, "Merchant processed refund."),
                ],
                "not_guilty": [
                    ("support_ticket", {"ticket_id": f"TKT{random.randint(10000, 99999)}"}, "Chargeback received."),
                    ("refund", {"evidence_submitted": True}, "Evidence package submitted."),
                ]
            }
            events = generic_events.get(fraud_type, [])
            for event_type, event_data, description in events:
                event_date = random_date(10, 1)
                cursor.execute(
                    """INSERT INTO case_events
                       (chargeback_id, event_type, event_date, event_data, description)
                       VALUES (?, ?, ?, ?, ?)""",
                    (cb_id, event_type, event_date, json.dumps(event_data), description)
                )
        else:
            for event_type, event_data, description in events:
                event_date = random_date(10, 1)
                cursor.execute(
                    """INSERT INTO case_events
                       (chargeback_id, event_type, event_date, event_data, description)
                       VALUES (?, ?, ?, ?, ?)""",
                    (cb_id, event_type, event_date, json.dumps(event_data), description)
                )

    # 6. Update customer statistics
    print("📊 Updating customer statistics...")
    for customer_id, _, _, _ in customers_data:
        cursor.execute(
            """SELECT COUNT(*) as cnt FROM chargebacks c
               JOIN transactions t ON c.transaction_id = t.transaction_id
               WHERE t.customer_id = ?""",
            (customer_id,)
        )
        count = cursor.fetchone()[0]
        cursor.execute(
            "UPDATE customers SET total_chargebacks = ? WHERE customer_id = ?",
            (count, customer_id)
        )

    conn.commit()

    # Summary
    true_fraud_count = sum(1 for cb in chargeback_cases if cb["fraud_type"] == "true_fraud")
    friendly_fraud_count = sum(1 for cb in chargeback_cases if cb["fraud_type"] == "friendly_fraud")
    merchant_error_count = sum(1 for cb in chargeback_cases if cb["fraud_type"] == "merchant_error")
    not_guilty_count = sum(1 for cb in chargeback_cases if cb["fraud_type"] == "not_guilty")

    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM case_events")
    total_events = cursor.fetchone()[0]

    print("\n✅ Database seeded successfully!")
    print(f"\n📋 Summary:")
    print(f"   - {len(merchants)} merchants")
    print(f"   - {len(customers_data)} customers")
    print(f"   - {total_transactions} transactions")
    print(f"   - {len(chargeback_cases)} chargebacks")
    print(f"      • {true_fraud_count} True Fraud cases")
    print(f"      • {friendly_fraud_count} Friendly Fraud cases")
    print(f"      • {merchant_error_count} Merchant Error cases")
    print(f"      • {not_guilty_count} Not Guilty (Merchant Won) cases")
    print(f"   - {total_events} case events")
    print("\n🚀 Ready for analysis!")

    conn.close()


if __name__ == "__main__":
    seed_database()
