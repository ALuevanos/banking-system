from flask import Flask, render_template
from db_config import get_connection  # this will be used in later steps

app = Flask(__name__)

# Home page route
@app.route('/')
def index():
    return render_template('index.html')  # will show our homepage

if __name__ == '__main__':
    app.run(debug=True)


@app.route('/customers')
def customers():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Customer")
    customers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('customers.html', customers=customers)
