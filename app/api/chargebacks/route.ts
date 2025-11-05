import { NextResponse } from 'next/server';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';

export async function GET() {
  try {
    // Open database connection
    const db = await open({
      filename: path.join(process.cwd(), 'agents', 'chargeback_system.db'),
      driver: sqlite3.Database
    });

    // Fetch chargeback data with related transaction and customer info
    const chargebacks = await db.all(`
      SELECT
        c.chargeback_id,
        c.dispute_date,
        c.reason_code,
        c.dispute_type,
        c.chargeback_amount,
        c.status,
        c.outcome,
        c.issuing_bank,
        c.analyst_id,
        c.response_deadline,
        t.transaction_id,
        t.amount as transaction_amount,
        t.currency,
        t.payment_method,
        t.transaction_date,
        t.risk_level,
        t.fraud_score,
        cust.customer_id,
        cust.name as customer_name,
        cust.email as customer_email,
        m.merchant_name
      FROM chargebacks c
      JOIN transactions t ON c.transaction_id = t.transaction_id
      JOIN customers cust ON t.customer_id = cust.customer_id
      JOIN merchants m ON t.merchant_id = m.merchant_id
      ORDER BY 
        CASE 
          WHEN c.status IN ('open', 'under_review') THEN 1
          WHEN c.status = 'lost' OR c.outcome = 'lost' THEN 2
          WHEN c.status = 'won' OR c.outcome = 'won' THEN 3
          ELSE 4
        END,
        c.dispute_date DESC
    `);

    await db.close();

    return NextResponse.json({ chargebacks });
  } catch (error) {
    console.error('Error fetching chargebacks:', error);
    return NextResponse.json(
      { error: 'Failed to fetch chargeback data' },
      { status: 500 }
    );
  }
}
