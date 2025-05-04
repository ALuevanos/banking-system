from flask import Blueprint, render_template, request, redirect, url_for, flash
from db_config import get_connection

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/customers')
def customers():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customer")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('customers.html', customers=data)
