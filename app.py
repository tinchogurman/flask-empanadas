from flask import Flask, render_template, request, send_file
import sqlite3
import os

app = Flask(__name__)

# Ruta al archivo .db
DB_PATH = os.path.join(os.path.dirname(__file__), 'empanadas.db')
print("📍 Ruta real del archivo SQLite:", DB_PATH)

# Crear tabla si no existe
def init_db():
    if not os.path.exists(DB_PATH):  # Solo crea si no existe
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

# Página principal con formulario y galería
@app.route('/')
def index():
    image_folder = os.path.join(app.static_folder, 'images')
    images = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return render_template('index.html', images=images)

# Proceso del formulario
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
    
    conn.commit()  # 🔥 Acá estaba el problema
    conn.close()

    return render_template('result.html', flavor=flavor)

# Ver todos los sabores registrados
@app.route('/flavors')
def flavors():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT flavor, count FROM EmpanadaFlavors ORDER BY count DESC")
    data = cursor.fetchall()
    conn.close()
    return render_template('flavors.html', flavors=data)

if __name__ == '__main__':
    app.run(debug=True)

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
    return "🧹 All data deleted. Ready for fresh voting!"
