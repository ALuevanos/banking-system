from flask import Blueprint, render_template, request, redirect, url_for, flash
from db_config import get_connection

loan_bp = Blueprint('loan_bp', __name__)

@loan_bp.route('/loans')
def list_loans():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT l.loan_id, l.amount, c.name AS customer_name
        FROM loan l
        JOIN borrow b ON l.loan_id = b.loan_id
        JOIN customer c ON b.customer_id = c.customer_id
    """)
    loans = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('loans.html', loans=loans)

@loan_bp.route('/loans/add', methods=['GET', 'POST'])
def add_loan():
    if request.method == 'POST':
        loan_id = request.form['loan_id']
        amount = request.form['amount']
        customer_id = request.form['customer_id']

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO loan (loan_id, amount) VALUES (%s, %s)", (loan_id, amount))
            cursor.execute("INSERT INTO borrow (customer_id, loan_id) VALUES (%s, %s)", (customer_id, loan_id))
            conn.commit()
            flash('Loan added successfully.')
        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}')
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('loan_bp.list_loans'))

    return render_template('add_loan.html')

@loan_bp.route('/loans/edit/<loan_id>', methods=['GET', 'POST'])
def edit_loan(loan_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        amount = request.form['amount']
        cursor.execute("UPDATE loan SET amount = %s WHERE loan_id = %s", (amount, loan_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Loan updated successfully.')
        return redirect(url_for('loan_bp.list_loans'))

    cursor.execute("SELECT * FROM loan WHERE loan_id = %s", (loan_id,))
    loan = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_loan.html', loan=loan)

@loan_bp.route('/loans/delete/<loan_id>')
def delete_loan(loan_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM borrow WHERE loan_id = %s", (loan_id,))
        cursor.execute("DELETE FROM loan WHERE loan_id = %s", (loan_id,))
        conn.commit()
        flash('Loan deleted successfully.')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('loan_bp.list_loans'))
