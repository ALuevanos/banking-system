import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345",  
        database="banking_system"        
    )

# Connect and fetch customers
conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT * FROM customer;")
rows = cursor.fetchall()

for row in rows:
    print(f"Customer ID: {row[0]}, Name: {row[1]}, Address: {row[2]}, Phone: {row[3]}, Banker ID: {row[4]}")

cursor.close()
conn.close()
