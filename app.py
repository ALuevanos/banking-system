from flask import Flask, render_template, request, redirect, session, url_for, flash
from db_config import get_connection

app = Flask(__name__)
app.secret_key = '12345'  # Needed to use sessions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/customers')
def customers():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Customer")
    customers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('customers.html', customers=customers)

@app.route('/login', methods=['GET', 'POST'])
def login():
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

@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/login')
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/login')

@app.route('/er-diagram')
def er_diagram():
    if 'admin' not in session:
        return redirect('/login')
    return render_template('er.html')

# ⬇️ This should always go last!
if __name__ == '__main__':
    app.run(debug=True)
