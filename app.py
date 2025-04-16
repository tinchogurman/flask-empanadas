from flask import Flask, render_template, request, send_file
import sqlite3
import os

app = Flask(__name__)

# Ruta a la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), 'empanadas.db')
print("📍 Ruta real del archivo SQLite:", DB_PATH)

# Crear base si no existe
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

# 🏠 Nueva página principal
@app.route('/home')
def home():
    return render_template('home.html')

# Página de votación
@app.route('/')
def index():
    image_folder = os.path.join(app.static_folder, 'images')
    images = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return render_template('index.html', images=images)

# Envío del voto
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
        print(f"🟦 Actualizado {flavor}")
    else:
        cursor.execute("INSERT INTO EmpanadaFlavors (flavor, count) VALUES (?, ?)", (flavor, 1))
        print(f"🟩 Insertado nuevo sabor: {flavor}")
    
    conn.commit()
    conn.close()

    return render_template('result.html', flavor=flavor)

# Ver los sabores registrados
@app.route('/flavors')
def flavors():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT flavor, count FROM EmpanadaFlavors ORDER BY count DESC")
    data = cursor.fetchall()
    conn.close()
    return render_template('flavors.html', flavors=data)

# Descargar la base de datos
@app.route('/download-db')
def download_db():
    return send_file(DB_PATH, as_attachment=True)

# Reiniciar la base de datos manualmente
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
