from flask import Blueprint, render_template, request, redirect, url_for, flash
from db_config import get_connection

account_bp = Blueprint('account', __name__)

# View all accounts
@account_bp.route('/accounts')
def view_accounts():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.account_id, a.balance, a.customer_id, c.name AS customer_name
        FROM account a
        JOIN customer c ON a.customer_id = c.customer_id
    """)
    accounts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('accounts.html', accounts=accounts)

# Create new account
@account_bp.route('/accounts/create', methods=['GET', 'POST'])
def create_account():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT customer_id, name FROM customer")
    customers = cursor.fetchall()

    if request.method == 'POST':
        account_id = request.form['account_id']
        balance = request.form['balance']
        customer_id = request.form['customer_id']

        try:
            cursor.execute("""
                INSERT INTO account (account_id, balance, customer_id)
                VALUES (%s, %s, %s)
            """, (account_id, balance, customer_id))
            conn.commit()
            flash('Account created successfully.', 'success')
            return redirect(url_for('account.view_accounts'))
        except Exception as e:
            conn.rollback()
            flash(f'Error creating account: {str(e)}', 'danger')

    cursor.close()
    conn.close()
    return render_template('accounts_create.html', customers=customers)

# Edit account
@account_bp.route('/accounts/edit/<account_id>', methods=['GET', 'POST'])
def edit_account(account_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM account WHERE account_id = %s", (account_id,))
    account = cursor.fetchone()

    if request.method == 'POST':
        balance = request.form['balance']
        try:
            cursor.execute("UPDATE account SET balance = %s WHERE account_id = %s", (balance, account_id))
            conn.commit()
            flash('Account updated successfully.', 'success')
            return redirect(url_for('account.view_accounts'))
        except Exception as e:
            conn.rollback()
            flash(f'Error updating account: {str(e)}', 'danger')

    cursor.close()
    conn.close()
    return render_template('accounts_edit.html', account=account)

@account_bp.route('/accounts/delete/<account_id>')
def delete_account(account_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Delete from dependent tables first
        cursor.execute("DELETE FROM transaction WHERE account_no = %s", (account_id,))
        cursor.execute("DELETE FROM checking_account WHERE account_id = %s", (account_id,))
        cursor.execute("DELETE FROM saving_account WHERE account_id = %s", (account_id,))
        
        # Then delete from account table
        cursor.execute("DELETE FROM account WHERE account_id = %s", (account_id,))
        conn.commit()
        flash('Account deleted successfully.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting account: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('account.view_accounts'))


