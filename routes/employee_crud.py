from flask import Blueprint, render_template, request, redirect, flash, url_for
from db_config import get_connection

employee_bp = Blueprint('employee_bp', __name__)

@employee_bp.route('/employees')
def view_employees():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employee")
    employees = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('employee.html', employees=employees)  # Updated here

@employee_bp.route('/employees/add', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        name = request.form['name']
        start_date = request.form['start_date']
        phone_no = request.form['phone_no']

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO employee (name, start_date, phone_no) VALUES (%s, %s, %s)",
                       (name, start_date, phone_no))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Employee added successfully!', 'success')
        return redirect(url_for('employee_bp.view_employees'))

    return render_template('add_employee.html')

@employee_bp.route('/employees/edit/<int:emp_id>', methods=['GET', 'POST'])
def edit_employee(emp_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        start_date = request.form['start_date']
        phone_no = request.form['phone_no']

        cursor.execute("UPDATE employee SET name=%s, start_date=%s, phone_no=%s WHERE emp_id=%s",
                       (name, start_date, phone_no, emp_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Employee updated successfully!', 'success')
        return redirect(url_for('employee_bp.view_employees'))

    cursor.execute("SELECT * FROM employee WHERE emp_id = %s", (emp_id,))
    employee = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_employee.html', employee=employee)

@employee_bp.route('/employees/delete/<int:emp_id>')
def delete_employee(emp_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employee WHERE emp_id = %s", (emp_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Employee deleted successfully!', 'success')
    return redirect(url_for('employee_bp.view_employees'))
