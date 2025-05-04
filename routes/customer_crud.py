from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db_config import get_connection

customer_bp = Blueprint('customer', __name__)

# Existing customer list route (keep this if you already had it)
@customer_bp.route('/customers')
def customers():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customer")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('customers.html', customers=data)

# ✅ NEW: Customer Dashboard Route
@customer_bp.route('/customer_dashboard')
def customer_dashboard():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))

    customer_id = session['customer_id']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get customer info
    cursor.execute("SELECT * FROM customer WHERE customer_id = %s", (customer_id,))
    customer = cursor.fetchone()

    # Get customer accounts
    cursor.execute("SELECT * FROM account WHERE customer_id = %s", (customer_id,))
    customer_accounts = cursor.fetchall()

    # Get customer loans (FIXED using JOIN with borrow table)
    cursor.execute("""
        SELECT l.*
        FROM loan l
        JOIN borrow b ON l.loan_id = b.loan_id
        WHERE b.customer_id = %s
    """, (customer_id,))
    customer_loans = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('customer_dashboard.html',
                           customer=customer,
                           customer_accounts=customer_accounts,
                           customer_loans=customer_loans)
