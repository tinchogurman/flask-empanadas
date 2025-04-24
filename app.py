from flask import Flask, render_template, request, send_file, redirect, url_for, session, flash, Response
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave-supersecreta"  # Clave para sesiones
GASTOS_PASSWORD = "admin123"

DB_PATH = os.path.join(os.path.dirname(__file__), 'empanadas.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS EmpanadaFlavors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flavor TEXT UNIQUE,
            count INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS EmpanadaFlavors_History (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flavor TEXT,
            count INTEGER,
            snapshot_date TEXT,
            UNIQUE(flavor, snapshot_date)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SuppliersAndExpenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT NOT NULL,
            description TEXT,
            amount REAL,
            category TEXT,
            expense_date TEXT DEFAULT (datetime('now'))
        )
    ''')

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/votar')
def votar():
    image_folder = os.path.join(app.static_folder, 'images', 'empanadas')
    images = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return render_template('index.html', images=images)

@app.route('/submit', methods=['POST'])
def submit():
    flavor = request.form['flavor'].strip()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT count FROM EmpanadaFlavors WHERE flavor = ?", (flavor,))
    row = cursor.fetchone()

    if row:
        cursor.execute("UPDATE EmpanadaFlavors SET count = count + 1 WHERE flavor = ?", (flavor,))
    else:
        cursor.execute("INSERT INTO EmpanadaFlavors (flavor, count) VALUES (?, ?)", (flavor, 1))
    
    conn.commit()
    conn.close()
    return render_template('result.html', flavor=flavor)

@app.route('/flavors')
def flavors():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT flavor, count FROM EmpanadaFlavors ORDER BY count DESC")
    data = cursor.fetchall()
    conn.close()
    return render_template('flavors.html', flavors=data)

@app.route('/download-db')
def download_db():
    filename = f"empanadas-{datetime.now().strftime('%Y-%m-%d_%H-%M')}.db"
    return send_file(DB_PATH, as_attachment=True, download_name=filename)

@app.route('/reset-db')
def reset_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM EmpanadaFlavors")
    conn.commit()
    conn.close()
    return "🥟 La base de datos ha sido reiniciada exitosamente."

@app.route('/login-gastos', methods=['GET', 'POST'])
def login_gastos():
    if request.method == 'POST':
        password = request.form['password']
        if password == GASTOS_PASSWORD:
            session['autorizado_gastos'] = True
            return redirect(url_for('gastos'))
        else:
            flash("Contraseña incorrecta")
    return render_template('login_gastos.html')

@app.route('/gastos', methods=['GET', 'POST'])
def gastos():
    if not session.get('autorizado_gastos'):
        return redirect(url_for('login_gastos'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == 'POST':
        supplier = request.form['supplier']
        description = request.form['description']
        amount = float(request.form['amount'])
        category = request.form['category']
        if request.form.get('date'):
            raw_date = request.form['date']
            date = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M').strftime('%d-%m-%Y %H:%M:%S')
        else:
            date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

        cursor.execute('''
            INSERT INTO SuppliersAndExpenses (supplier_name, description, amount, category, expense_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (supplier, description, amount, category, date))
        conn.commit()

    # Total general
    cursor.execute("SELECT SUM(amount) FROM SuppliersAndExpenses")
    total_gastos = cursor.fetchone()[0] or 0

    # Por categoría
    cursor.execute("SELECT category, SUM(amount) FROM SuppliersAndExpenses GROUP BY category")
    categorias = cursor.fetchall()

    # Lista completa
    cursor.execute("SELECT * FROM SuppliersAndExpenses ORDER BY expense_date DESC")
    gastos = cursor.fetchall()
    conn.close()

    return render_template('gastos.html', gastos=gastos, total_gastos=total_gastos, categorias=categorias)

@app.route('/gastos-csv')
def download_gastos_csv():
    if not session.get('autorizado_gastos'):
        return redirect(url_for('login_gastos'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT supplier_name, description, amount, expense_date FROM SuppliersAndExpenses")
    rows = cursor.fetchall()
    conn.close()

    csv_data = "Proveedor,Descripción,Monto,Fecha\n"
    for row in rows:
        csv_data += f"{row[0]},{row[1]},{row[2]},{row[3]}\n"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=gastos.csv"}
    )

@app.route('/gastos-proveedores')
def resumen_proveedores():
    if not session.get('autorizado_gastos'):
        return redirect(url_for('login_gastos'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT supplier_name, SUM(amount) as total
        FROM SuppliersAndExpenses
        GROUP BY supplier_name
        ORDER BY total DESC
    ''')
    resumen = cursor.fetchall()
    conn.close()
    return render_template('resumen_proveedores.html', resumen=resumen)

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/delete-expense', methods=['POST'])
def delete_expense():
    if not session.get('autorizado_gastos'):
        return redirect(url_for('login_gastos'))

    expense_id = request.form.get('expense_id')
    if expense_id:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM SuppliersAndExpenses WHERE id = ?", (expense_id,))
        conn.commit()
        conn.close()
    return redirect(url_for('gastos'))
