from flask import Flask, render_template, request, send_file
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'empanadas.db')
print("📍 Ruta real del archivo SQLite:", DB_PATH)

def init_db():
    if not os.path.exists(DB_PATH):
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
        print("📁 Base creada.")
    else:
        print("📁 Base ya existe, no se toca.")

init_db()

# 🏠 Home principal en /
@app.route('/')
def home():
    return render_template('home.html')

# 🗳 Página de votación ahora en /votar
@app.route('/votar')
def votar():
    image_folder = os.path.join(app.static_folder, 'images')
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
    return send_file(DB_PATH, as_attachment=True)

@app.route('/reset-db')
def reset_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM EmpanadaFlavors")
    conn.commit()
    conn.close()
    return "🥟 La base de datos ha sido reiniciada exitosamente."

if __name__ == '__main__':
    app.run(debug=True)
