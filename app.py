from flask import Flask, render_template, request, send_file
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'empanadas.db')
print("📍 Ruta real del archivo SQLite:", DB_PATH)

def init_db():
    if not os.path.isfile(DB_PATH):
        print("📁 No existe empanadas.db → creando base y tabla...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS EmpanadaFlavors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flavor TEXT UNIQUE,
                count INTEGER
            )
        ''')
        conn.commit()
        conn.close()
    else:
        print("✅ Base de datos ya existe → no se modifica.")
        
    CREATE TABLE IF NOT EXISTS SuppliersAndExpenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT NOT NULL,
    description TEXT,
    amount REAL,
    expense_date TEXT DEFAULT (datetime('now'))
)



init_db()

# 🏠 Home principal en /
@app.route('/')
def home():
    return render_template('home.html')

# 🗳 Página de votación ahora en /votar
@app.route('/votar')
def votar():
    image_folder = os.path.join(app.static_folder, 'images', 'empanadas')
    images = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return render_template('index.html', images=images)


@app.route('/submit', methods=['POST'])
def submit():
    flavor = request.form['flavor'].strip()
    print("✨ Recibido flavor:", flavor)

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

## @app.route('/reset-db')
## def reset_db():
##     conn = sqlite3.connect(DB_PATH)
##     cursor = conn.cursor()
##     cursor.execute("DELETE FROM EmpanadaFlavors")
##     conn.commit()
##     conn.close()
##     return "🥟 La base de datos ha sido reiniciada exitosamente."
## 
## if __name__ == '__main__':
##     app.run(debug=True)

# Página para ver y agregar gastos
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
