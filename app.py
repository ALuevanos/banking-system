
from flask import Flask, render_template, request, redirect, session, flash, url_for
from db_config import get_connection

app = Flask(__name__)
app.secret_key = '12345'

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Admin Login
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

# Admin Logout
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

# Admin Dashboard
@app.route('/dashboard')
def dashboard():
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
        LIMIT 5
    """)
    recent_transactions = cursor.fetchall()

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

    cursor.execute("SELECT SUM(amount) AS total_income FROM transaction WHERE transaction_type = 'deposit'")
    total_income = cursor.fetchone()['total_income'] or 0

    cursor.execute("SELECT SUM(amount) AS total_outcome FROM transaction WHERE transaction_type = 'withdrawal'")
    total_outcome = cursor.fetchone()['total_outcome'] or 0

    cursor.execute("SELECT SUM(balance) AS current_balance FROM account")
    current_balance = cursor.fetchone()['current_balance'] or 0

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

# ----------------- CUSTOMER LOGIN SYSTEM -----------------
@app.route('/customer_login', methods=['GET', 'POST'])
def customer_login():
    if 'customer_id' in session:
        return redirect('/customer_dashboard')

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Customer WHERE customer_id = %s AND password = %s", (customer_id, password))
        customer = cursor.fetchone()
        cursor.close()
        conn.close()

        if customer:
            session['customer_id'] = customer['customer_id']
            return redirect('/customer_dashboard')
        else:
            flash("Invalid Customer ID or Password")
            return redirect('/customer_login')

    return render_template('customer_login.html')

@app.route('/customer_dashboard')
def customer_dashboard():
    if 'customer_id' not in session:
        return redirect('/customer_login')

    customer_id = session['customer_id']
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Customer WHERE customer_id = %s", (customer_id,))
    customer = cursor.fetchone()

    cursor.execute("SELECT * FROM Account WHERE customer_id = %s", (customer_id,))
    accounts = cursor.fetchall()

    cursor.execute("""
        SELECT l.* FROM Loan l
        JOIN borrow b ON l.loan_id = b.loan_id
        WHERE b.customer_id = %s
    """, (customer_id,))
    loans = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'customer_dashboard.html',
        customer=customer,
        customer_accounts=accounts,
        customer_loans=loans
    )

@app.route('/customer_logout')
def customer_logout():
    session.pop('customer_id', None)
    return redirect('/customer_login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        name = request.form['name']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("INSERT INTO customer (customer_id, name, password) VALUES (%s, %s, %s)",
                           (customer_id, name, password))

            cursor.execute("INSERT INTO account (account_id, balance, customer_id) VALUES (%s, %s, %s)",
                           (str(int(customer_id) + 1000), 0.00, customer_id))

            conn.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('customer_login'))

        except Exception as e:
            conn.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')

        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

# Run App
if __name__ == '__main__':
    app.run(debug=True)
