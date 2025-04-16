from flask import Flask, render_template, request
import pyodbc, os

app = Flask(__name__)

server = r'CPC-marti-YGW4P\SQLEXPRESS'
database = 'Prueba'

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    f'SERVER={server};'
    f'DATABASE={database};'
    'Trusted_Connection=yes;'
)

# Crear tabla si no existe
cursor = conn.cursor()
cursor.execute("""
IF NOT EXISTS (
    SELECT * FROM sysobjects WHERE name='EmpanadaFlavors' AND xtype='U'
)
BEGIN
    CREATE TABLE EmpanadaFlavors (
        Id INT IDENTITY(1,1) PRIMARY KEY,
        Flavor VARCHAR(100) UNIQUE,
        Count INT
    )
END
""")
conn.commit()

@app.route('/')
def index():
    image_folder = os.path.join(app.static_folder, 'images')
    images = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return render_template('index.html', images=images)

@app.route('/submit', methods=['POST'])
def submit():
    flavor = request.form['flavor'].strip().title()

    cursor = conn.cursor()
    # Verificar si ya existe
    cursor.execute("SELECT Count FROM EmpanadaFlavors WHERE Flavor = ?", (flavor,))
    row = cursor.fetchone()

    if row:
        # Ya existe → actualizar cantidad
        nueva_cantidad = row[0] + 1
        cursor.execute("UPDATE EmpanadaFlavors SET Count = ? WHERE Flavor = ?", (nueva_cantidad, flavor))
    else:
        # Nuevo sabor → insertar
        cursor.execute("INSERT INTO EmpanadaFlavors (Flavor, Count) VALUES (?, ?)", (flavor, 1))
    
    conn.commit()

    return render_template('result.html', flavor=flavor)

@app.route('/flavors')
def flavors():
    cursor = conn.cursor()
    cursor.execute("SELECT Flavor, Count FROM EmpanadaFlavors ORDER BY Count DESC")
    flavors_list = cursor.fetchall()
    return render_template('flavors.html', flavors=flavors_list)

if __name__ == '__main__':
    app.run(debug=True)
