from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db_config import get_connection

payment_bp = Blueprint('payment_bp', __name__)

@payment_bp.route('/payments')
def view_payments():
    if 'admin' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.payment_no, p.pay_amount, p.payment_day, p.loan_id, c.name AS customer_name
        FROM payment p
        JOIN loan l ON p.loan_id = l.loan_id
        JOIN borrow b ON l.loan_id = b.loan_id
        JOIN customer c ON b.customer_id = c.customer_id
    """)
    payments = cursor.fetchall()

    cursor.execute("SELECT SUM(pay_amount) AS total_collected FROM payment")
    total_result = cursor.fetchone()
    total_collected = total_result['total_collected'] or 0

    cursor.close()
    conn.close()
    return render_template('payments.html', payments=payments, total_collected=total_collected)

@payment_bp.route('/payments/add', methods=['GET', 'POST'])
def add_payment():
    if 'admin' not in session:
        return redirect('/login')

    if request.method == 'POST':
        loan_id = request.form['loan_id']
        pay_amount = request.form['pay_amount']
        payment_day = request.form['payment_day']

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO payment (loan_id, pay_amount, payment_day)
                VALUES (%s, %s, %s)
            """, (loan_id, pay_amount, payment_day))
            conn.commit()
            flash('Payment added successfully', 'success')
            return redirect(url_for('payment_bp.view_payments'))
        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('payments_add.html')

@payment_bp.route('/payments/edit/<int:payment_no>', methods=['GET', 'POST'])
def edit_payment(payment_no):
    if 'admin' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        loan_id = request.form['loan_id']
        pay_amount = request.form['pay_amount']
        payment_day = request.form['payment_day']

        try:
            cursor.execute("""
                UPDATE payment
                SET loan_id = %s, pay_amount = %s, payment_day = %s
                WHERE payment_no = %s
            """, (loan_id, pay_amount, payment_day, payment_no))
            conn.commit()
            flash('Payment updated successfully', 'success')
            return redirect(url_for('payment_bp.view_payments'))
        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'danger')

    cursor.execute("SELECT * FROM payment WHERE payment_no = %s", (payment_no,))
    payment = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('payments_edit.html', payment=payment)

@payment_bp.route('/payments/delete/<int:payment_no>', methods=['POST'])
def delete_payment(payment_no):
    if 'admin' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM payment WHERE payment_no = %s", (payment_no,))
        conn.commit()
        flash('Payment deleted successfully', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('payment_bp.view_payments'))
