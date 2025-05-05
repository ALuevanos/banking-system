from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db_config import get_connection

customer_bp = Blueprint('customer', __name__)

# View all customers (admin)
@customer_bp.route('/customers')
def customers():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT customer_id, name, address, phone FROM customer")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('customers.html', customers=data)

# Edit a customer
@customer_bp.route('/customers/edit/<int:customer_id>', methods=['GET', 'POST'])
def edit_customer(customer_id):
    if 'admin' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']

        try:
            cursor.execute("""
                UPDATE customer
                SET name = %s, address = %s, phone = %s
                WHERE customer_id = %s
            """, (name, address, phone, customer_id))
            conn.commit()
            flash("Customer updated successfully", "success")
            return redirect(url_for('customer.customers'))
        except Exception as e:
            conn.rollback()
            flash(f"Error updating customer: {e}", "danger")

    cursor.execute("SELECT * FROM customer WHERE customer_id = %s", (customer_id,))
    customer = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('edit_customer.html', customer=customer)

# Delete a customer
@customer_bp.route('/customers/delete/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    if 'admin' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM customer WHERE customer_id = %s", (customer_id,))
        conn.commit()
        flash("Customer deleted successfully", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting customer: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('customer.customers'))