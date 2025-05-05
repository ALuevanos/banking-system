from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db_config import get_connection

branch_bp = Blueprint('branch_bp', __name__)

# View all branches
@branch_bp.route('/branches')
def view_branches():
    if 'admin' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM branch")
    branches = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('branches.html', branches=branches)

# Add a new branch
@branch_bp.route('/branches/add', methods=['GET', 'POST'])
def add_branch():
    if 'admin' not in session:
        return redirect('/login')

    if request.method == 'POST':
        branch_name = request.form['branch_name']
        location = request.form['location']

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO branch (branch_name, location) VALUES (%s, %s)",
                (branch_name, location)
            )
            conn.commit()
            flash('Branch added successfully!', 'success')
            return redirect(url_for('branch_bp.view_branches'))
        except Exception as e:
            conn.rollback()
            flash(f'Error adding branch: {e}', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('add_branch.html')

@branch_bp.route('/branches/edit/<int:branch_id>', methods=['GET', 'POST'])
def edit_branch(branch_id):
    if 'admin' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        city = request.form['city']
        try:
            cursor.execute("UPDATE branch SET name = %s, city = %s WHERE branch_id = %s",
                           (name, city, branch_id))
            conn.commit()
            flash('Branch updated successfully!', 'success')
            return redirect(url_for('branch_bp.view_branches'))
        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'danger')

    cursor.execute("SELECT * FROM branch WHERE branch_id = %s", (branch_id,))
    branch = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_branch.html', branch=branch)

# Delete a branch
@branch_bp.route('/branches/delete/<int:branch_id>', methods=['GET'])
def delete_branch(branch_id):
    if 'admin' not in session:
        return redirect('/login')

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM branch WHERE branch_id = %s", (branch_id,))
        conn.commit()
        flash('Branch deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting branch: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('branch_bp.view_branches'))
