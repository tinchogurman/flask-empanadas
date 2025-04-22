from flask import Flask, render_template, request, send_file, Response
import sqlite3
import os
from datetime import datetime
import csv

app = Flask(__name__)

# Ruta a la base de datos principal
DB_PATH = os.path.join(os.path.dirname(__file__), 'empanadas.db')

# Crear tablas si no existen
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabla principal de sabores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS EmpanadaFlavors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flavor TEXT UNIQUE,
            count INTEGER
        )
    ''')

    # Tabla histórica
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS EmpanadaFlavors_History (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flavor TEXT,
            count INTEGER,
            snapshot_date TEXT,
            UNIQUE(flavor, snapshot_date)
        )
    ''')

    # Tabla de proveedores y gastos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SuppliersAndExpenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name TEXT NOT NULL,
            description TEXT,
            amount REAL,
            expense_date TEXT DEFAULT (datetime('now'))
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# HOME
@app.route('/')
def home():
    return render_template('home.html')

# PÁGINA DE VOTACIÓN
@app.route('/votar')
def votar():
    image_folder = os.path.join(app.static_folder, 'images', 'empanadas')
    images = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return render_template('index.html', images=images)

# PROCESAR VOTO
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

# VER SABORES
@app.route('/flavors')
def flavors():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT flavor, count FROM EmpanadaFlavors ORDER BY count DESC")
    data = cursor.fetchall()
    conn.close()
    return render_template('flavors.html', flavors=data)

# DESCARGAR BASE DE DATOS
@app.route('/download-db')
def download_db():
    filename = f"empanadas-{datetime.now().strftime('%Y-%m-%d_%H-%M')}.db"
    return send_file(DB_PATH, as_attachment=True, download_name=filename)

# RESET MANUAL
@app.route('/reset-db')
def reset_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM EmpanadaFlavors")
    conn.commit()
    conn.close()
    return "🥟 La base de datos ha sido reiniciada exitosamente."

# NUEVA SECCIÓN: GASTOS Y PROVEEDORES
@app.route('/gastos', methods=['GET', 'POST'])
def gastos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == 'POST':
        supplier = request.form['supplier']
        description = request.form['description']
        amount = float(request.form['amount'])
        date = request.form.get('date') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            INSERT INTO SuppliersAndExpenses (supplier_name, description, amount, expense_date)
            VALUES (?, ?, ?, ?)
        ''', (supplier, description, amount, date))
        conn.commit()

    cursor.execute("SELECT * FROM SuppliersAndExpenses ORDER BY expense_date DESC")
    gastos = cursor.fetchall()
    conn.close()
    return render_template('gastos.html', gastos=gastos)

# INICIAR FLASK LOCAL
if __name__ == '__main__':
    app.run(debug=True)

@app.route('/gastos-csv')
def download_gastos_csv():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT supplier_name, description, amount, expense_date FROM SuppliersAndExpenses")
    rows = cursor.fetchall()
    conn.close()

    def generate():
        data = csv.writer([])
        yield "Proveedor,Descripción,Monto,Fecha\n"
        for row in rows:
            yield f"{row[0]},{row[1]},{row[2]},{row[3]}\n"

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=gastos.csv"})
                    
                    
@app.route('/gastos-proveedores')
def resumen_proveedores():
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