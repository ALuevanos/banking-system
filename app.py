from flask import Flask, render_template, request, redirect, session, flash, url_for
from db_config import get_connection

app = Flask(__name__)
app.secret_key = '12345'

# --------------------------- HOME ---------------------------
@app.route('/')
def index():
    return render_template('index.html')

# --------------------------- ADMIN LOGIN ---------------------------
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

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

# --------------------------- CUSTOMER LOGIN ---------------------------
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

@app.route('/customer_logout')
def customer_logout():
    session.pop('customer_id', None)
    return redirect('/customer_login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register'))

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT MAX(customer_id) AS max_id FROM customer")
        max_id = cursor.fetchone()['max_id']
        new_customer_id = str(int(max_id) + 1) if max_id else "1000"

        try:
            cursor.execute("INSERT INTO customer (customer_id, name, password) VALUES (%s, %s, %s)",
                           (new_customer_id, name, password))
            cursor.execute("INSERT INTO account (account_id, balance, customer_id) VALUES (%s, %s, %s)",
                           (str(int(new_customer_id) + 1000), 0.00, new_customer_id))
            conn.commit()
            flash(f'Registration successful! Your Customer ID is {new_customer_id}. Please login.', 'success')
            return redirect(url_for('customer_login'))
        except Exception as e:
            conn.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

# --------------------------- ADMIN DASHBOARD ---------------------------
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

# --------------------------- CUSTOMER ACTIONS ---------------------------
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))

    if request.method == 'POST':
        amount = float(request.form['amount'])
        customer_id = session['customer_id']

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE account SET balance = balance + %s WHERE customer_id = %s", (amount, customer_id))
        cursor.execute("""
            INSERT INTO transaction (account_no, amount, transaction_type, transaction_date)
            VALUES (
                (SELECT account_id FROM account WHERE customer_id = %s),
                %s,
                'deposit',
                NOW()
            )
        """, (customer_id, amount))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Deposit successful!", "success")
        return redirect('/customer_dashboard')

    return render_template('deposit.html')

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))

    if request.method == 'POST':
        amount = float(request.form['amount'])
        customer_id = session['customer_id']

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT balance FROM account WHERE customer_id = %s", (customer_id,))
        balance = cursor.fetchone()['balance']

        if amount > balance:
            flash("Insufficient funds!", "danger")
        else:
            cursor.execute("UPDATE account SET balance = balance - %s WHERE customer_id = %s", (amount, customer_id))
            cursor.execute("""
                INSERT INTO transaction (account_no, amount, transaction_type, transaction_date)
                VALUES (
                    (SELECT account_id FROM account WHERE customer_id = %s),
                    %s,
                    'withdrawal',
                    NOW()
                )
            """, (customer_id, amount))
            conn.commit()
            flash("Withdrawal successful!", "success")

        cursor.close()
        conn.close()
        return redirect('/customer_dashboard')

    return render_template('withdraw.html')

@app.route('/pay_loan', methods=['GET', 'POST'])
def pay_loan():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))

    customer_id = session['customer_id']
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT l.loan_id, l.amount
        FROM loan l
        JOIN borrow b ON l.loan_id = b.loan_id
        WHERE b.customer_id = %s
    """, (customer_id,))
    loan = cursor.fetchone()

    if request.method == 'POST':
        pay_amount = float(request.form['pay_amount'])

        cursor.execute("""
            INSERT INTO payment (loan_id, pay_amount, payment_day)
            VALUES (%s, %s, NOW())
        """, (loan['loan_id'], pay_amount))

        conn.commit()
        flash("Loan payment successful!", "success")
        return redirect('/customer_dashboard')

    cursor.close()
    conn.close()
    return render_template('pay_loan.html', loan=loan)

# --------------------------- CRUD BLUEPRINT ROUTES ---------------------------
from routes.customer_crud import customer_bp
from routes.account_crud import account_bp
from routes.loan_crud import loan_bp
from routes.payment_crud import payment_bp
from routes.employee_crud import employee_bp
from routes.branch_crud import branch_bp
from routes.transaction_crud import transaction_bp

app.register_blueprint(customer_bp)
app.register_blueprint(account_bp)
app.register_blueprint(loan_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(branch_bp)
app.register_blueprint(transaction_bp)

# --------------------------- RUN SERVER ---------------------------
if __name__ == '__main__':
    app.run(debug=True)
