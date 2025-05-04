from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db_config import get_connection

transaction_bp = Blueprint('transaction_bp', __name__)

@transaction_bp.route('/transactions')
def view_transactions():
    if 'admin' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.transaction_id, t.amount, t.transaction_type, t.transaction_date,
               a.account_id, c.name AS customer_name
        FROM transaction t
        JOIN account a ON t.account_no = a.account_id
        JOIN customer c ON a.customer_id = c.customer_id
        ORDER BY t.transaction_date DESC
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('transactions.html', transactions=data)

@transaction_bp.route('/transactions/add', methods=['GET', 'POST'])
def add_transaction():
    if 'admin' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT account_id FROM account")
    accounts = cursor.fetchall()

    if request.method == 'POST':
        account_no = request.form['account_no']
        amount = request.form['amount']
        transaction_type = request.form['transaction_type']

        try:
            cursor.execute("""
                INSERT INTO transaction (account_no, amount, transaction_type, transaction_date)
                VALUES (%s, %s, %s, NOW())
            """, (account_no, amount, transaction_type))

            if transaction_type == 'deposit':
                cursor.execute("UPDATE account SET balance = balance + %s WHERE account_id = %s", (amount, account_no))
            elif transaction_type == 'withdrawal':
                cursor.execute("UPDATE account SET balance = balance - %s WHERE account_id = %s", (amount, account_no))

            conn.commit()
            flash('Transaction added successfully.', 'success')
            return redirect(url_for('transaction_bp.view_transactions'))

        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'danger')

    cursor.close()
    conn.close()
    return render_template('add_transaction.html', accounts=accounts)

@transaction_bp.route('/transactions/delete/<int:transaction_id>')
def delete_transaction(transaction_id):
    if 'admin' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM transaction WHERE transaction_id = %s", (transaction_id,))
        conn.commit()
        flash('Transaction deleted successfully.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('transaction_bp.view_transactions'))
@transaction_bp.route('/transactions/edit/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    if 'admin' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch the existing transaction
    cursor.execute("SELECT * FROM transaction WHERE transaction_id = %s", (transaction_id,))
    transaction = cursor.fetchone()

    if not transaction:
        flash('Transaction not found.', 'danger')
        return redirect(url_for('transaction_bp.view_transactions'))

    if request.method == 'POST':
        amount = request.form['amount']
        transaction_type = request.form['transaction_type']

        try:
            cursor.execute("""
                UPDATE transaction
                SET amount = %s, transaction_type = %s
                WHERE transaction_id = %s
            """, (amount, transaction_type, transaction_id))
            conn.commit()
            flash('Transaction updated successfully.', 'success')
            return redirect(url_for('transaction_bp.view_transactions'))
        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'danger')

    cursor.close()
    conn.close()
    return render_template('transactions_edit.html', transaction=transaction)
