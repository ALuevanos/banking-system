from flask import Flask, render_template, request, redirect, session, flash
from db_config import get_connection

app = Flask(__name__)
app.secret_key = '12345'

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'admin' in session:
        return redirect('/dashboard')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Admin WHERE username = %s AND password = %s", (username, password))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin:
            session['admin'] = admin['username']
            return redirect('/dashboard')
        else:
            flash("Invalid username or password")
            return redirect('/login')

    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Recent Transactions
    cursor.execute("""
        SELECT t.transaction_id, t.amount, t.transaction_type, t.transaction_date, c.name AS customer_name
        FROM transaction t
        JOIN account a ON t.account_no = a.account_id
        JOIN customer c ON a.customer_id = c.customer_id
        ORDER BY t.transaction_date DESC
        LIMIT 5
    """)
    recent_transactions = cursor.fetchall()

    # Recent Payments
    cursor.execute("""
        SELECT p.payment_no, p.pay_amount, p.payment_day, c.name AS customer_name
        FROM payment p
        JOIN loan l ON p.loan_id = l.loan_id
        JOIN borrow b ON l.loan_id = b.loan_id
        JOIN customer c ON b.customer_id = c.customer_id
        ORDER BY p.payment_day DESC
        LIMIT 5
    """)
    recent_payments = cursor.fetchall()

    # Total Income
    cursor.execute("SELECT SUM(amount) AS total_income FROM transaction WHERE transaction_type = 'deposit'")
    total_income = cursor.fetchone()['total_income'] or 0

    # Total Outcome
    cursor.execute("SELECT SUM(amount) AS total_outcome FROM transaction WHERE transaction_type = 'withdrawal'")
    total_outcome = cursor.fetchone()['total_outcome'] or 0

    # Current Balance
    cursor.execute("SELECT SUM(balance) AS current_balance FROM account")
    current_balance = cursor.fetchone()['current_balance'] or 0

    # Active Customers
    cursor.execute("SELECT COUNT(*) AS count FROM customer")
    customer_count = cursor.fetchone()['count']

    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        total_income=total_income,
        total_outcome=total_outcome,
        current_balance=current_balance,
        customer_count=customer_count,
        recent_transactions=recent_transactions,
        recent_payments=recent_payments
    )

# Customers
@app.route('/customers')
def customers():
    if 'admin' not in session:
        return redirect('/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customer")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('customers.html', customers=data)

# Accounts
@app.route('/accounts')
def accounts():
    if 'admin' not in session:
        return redirect('/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.account_id, a.balance, c.name AS customer_name,
               ca.overdraft_amount, sa.interest_rate
        FROM account a
        LEFT JOIN customer c ON c.customer_id = a.customer_id
        LEFT JOIN checking_account ca ON ca.account_id = a.account_id
        LEFT JOIN saving_account sa ON sa.account_id = a.account_id
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('accounts.html', accounts=data)

# Loans
@app.route('/loans')
def loans():
    if 'admin' not in session:
        return redirect('/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT l.loan_id, l.amount, c.name AS customer_name
        FROM loan l
        JOIN borrow b ON l.loan_id = b.loan_id
        JOIN customer c ON b.customer_id = c.customer_id
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('loans.html', loans=data)

# Payments
@app.route('/payments')
def payments():
    if 'admin' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.payment_no, p.pay_amount, p.payment_day, l.loan_id, c.name AS customer_name
        FROM payment p
        JOIN loan l ON p.loan_id = l.loan_id
        JOIN borrow b ON l.loan_id = b.loan_id
        JOIN customer c ON b.customer_id = c.customer_id
        ORDER BY p.payment_day DESC
    """)
    data = cursor.fetchall()
    total_payments = sum(p['pay_amount'] for p in data)

    cursor.close()
    conn.close()

    return render_template('payments.html', payments=data, total_payments=total_payments)


# Employees
@app.route('/employees')
def employees():
    if 'admin' not in session:
        return redirect('/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.emp_id, e.name, e.start_date, e.phone_no, c.name AS customer_name
        FROM employee e
        LEFT JOIN banker b ON e.emp_id = b.emp_id
        LEFT JOIN customer c ON b.customer_id = c.customer_id
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('employees.html', employees=data)

# Branches
@app.route('/branches')
def branches():
    if 'admin' not in session:
        return redirect('/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM branch")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('branches.html', branches=data)

# Transactions
@app.route('/transactions')
def transactions():
    if 'admin' not in session:
        return redirect('/login')
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.transaction_id, t.amount, t.transaction_type, t.transaction_date, c.name AS customer_name
        FROM transaction t
        JOIN account a ON t.account_no = a.account_id
        JOIN customer c ON a.customer_id = c.customer_id
        ORDER BY t.transaction_date DESC
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('transactions.html', transactions=data)

# Run App
if __name__ == '__main__':
    app.run(debug=True)
