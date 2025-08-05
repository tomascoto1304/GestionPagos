# backend/app.py
import sqlite3
import bcrypt
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# --- CONFIGURACIÓN DE LA BASE DE DATOS PARA RENDER ---
DATABASE_PATH = os.path.join(os.environ.get('RENDER_DISK_PATH', '..'), 'database', 'pagos.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')

def init_db():
    """Inicializa la base de datos si no existe."""
    db_dir = os.path.dirname(DATABASE_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    if not os.path.exists(DATABASE_PATH):
        print("Creando la base de datos...")
        conn = sqlite3.connect(DATABASE_PATH)
        with open(SCHEMA_PATH, 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        print("Base de datos creada exitosamente.")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- RUTAS DE AUTENTICACIÓN (SIMPLIFICADAS) ---
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    nombre, apellido, email, password, id_rol = data.get('nombre'), data.get('apellido'), data.get('email'), data.get('password'), data.get('id_rol')
    if not all([nombre, apellido, email, password, id_rol]):
        return jsonify({"error": "Faltan datos"}), 400
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO usuarios (nombre, apellido, email, password_hash, id_rol) VALUES (?, ?, ?, ?, ?)", (nombre, apellido, email, hashed_password, id_rol))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "El correo electrónico ya está registrado"}), 409
    finally:
        conn.close()
    return jsonify({"message": "Usuario registrado exitosamente"}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email, password = data.get('email'), data.get('password')
    if not email or not password:
        return jsonify({"error": "Faltan correo o contraseña"}), 400
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "Credenciales inválidas"}), 401
    if bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
        user_data = {"id_usuario": user['id_usuario'], "nombre": user['nombre'], "apellido": user['apellido'], "email": user['email'], "id_rol": user['id_rol']}
        return jsonify({"message": "Inicio de sesión exitoso", "user": user_data}), 200
    else:
        return jsonify({"error": "Credenciales inválidas"}), 401

# --- RUTAS CRUD PARA CATÁLOGO DE MONEDAS ---
@app.route('/api/catalogos/monedas', methods=['GET'])
def get_monedas():
    conn = get_db_connection()
    monedas_cursor = conn.execute("SELECT id_moneda, codigo_moneda, nombre_moneda, tipo_cambio, ultima_actualizacion FROM monedas ORDER BY nombre_moneda").fetchall()
    conn.close()
    monedas = [dict(row) for row in monedas_cursor]
    return jsonify(monedas), 200

@app.route('/api/catalogos/monedas', methods=['POST'])
def add_moneda():
    data = request.get_json()
    nombre_moneda, codigo_moneda, tipo_cambio = data.get('nombre_moneda'), data.get('codigo_moneda'), data.get('tipo_cambio')
    if not all([nombre_moneda, codigo_moneda, tipo_cambio]):
        return jsonify({"error": "Faltan datos"}), 400
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO monedas (nombre_moneda, codigo_moneda, tipo_cambio) VALUES (?, ?, ?)", (nombre_moneda, codigo_moneda, tipo_cambio))
        conn.commit()
        new_moneda_id = cursor.lastrowid
        new_moneda = conn.execute("SELECT * FROM monedas WHERE id_moneda = ?", (new_moneda_id,)).fetchone()
        return jsonify(dict(new_moneda)), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "El código o nombre de la moneda ya existe"}), 409
    finally:
        conn.close()

@app.route('/api/catalogos/monedas/<int:id_moneda>', methods=['PUT'])
def update_moneda(id_moneda):
    data = request.get_json()
    nombre_moneda, codigo_moneda, tipo_cambio = data.get('nombre_moneda'), data.get('codigo_moneda'), data.get('tipo_cambio')
    if not all([nombre_moneda, codigo_moneda, tipo_cambio]):
        return jsonify({"error": "Faltan datos"}), 400
    conn = get_db_connection()
    try:
        conn.execute("UPDATE monedas SET nombre_moneda = ?, codigo_moneda = ?, tipo_cambio = ?, ultima_actualizacion = CURRENT_TIMESTAMP WHERE id_moneda = ?", (nombre_moneda, codigo_moneda, tipo_cambio, id_moneda))
        conn.commit()
        updated_moneda = conn.execute("SELECT * FROM monedas WHERE id_moneda = ?", (id_moneda,)).fetchone()
        return jsonify(dict(updated_moneda)), 200
    except sqlite3.IntegrityError:
        return jsonify({"error": "El código o nombre de la moneda ya existe"}), 409
    finally:
        conn.close()

@app.route('/api/catalogos/monedas/<int:id_moneda>', methods=['DELETE'])
def delete_moneda(id_moneda):
    conn = get_db_connection()
    conn.execute("DELETE FROM monedas WHERE id_moneda = ?", (id_moneda,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Moneda eliminada exitosamente"}), 200

@app.route('/api/catalogos/tipos_pago', methods=['GET'])
def get_tipos_pago():
    conn = get_db_connection()
    tipos_pago_cursor = conn.execute("SELECT id_tipo_pago, nombre_tipo, siglas FROM tipos_pago ORDER BY nombre_tipo").fetchall()
    conn.close()
    tipos_pago = [dict(row) for row in tipos_pago_cursor]
    return jsonify(tipos_pago), 200

@app.route('/api/catalogos/tipos_pago', methods=['POST'])
def add_tipo_pago():
    data = request.get_json()
    nombre_tipo, siglas = data.get('nombre_tipo'), data.get('siglas')
    if not nombre_tipo or not siglas:
        return jsonify({"error": "Faltan datos"}), 400
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tipos_pago (nombre_tipo, siglas) VALUES (?, ?)", (nombre_tipo, siglas))
        conn.commit()
        new_id = cursor.lastrowid
        new_tipo_pago = conn.execute("SELECT * FROM tipos_pago WHERE id_tipo_pago = ?", (new_id,)).fetchone()
        return jsonify(dict(new_tipo_pago)), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "El nombre o las siglas del tipo de pago ya existen"}), 409
    finally:
        conn.close()

@app.route('/api/catalogos/tipos_pago/<int:id_tipo_pago>', methods=['PUT'])
def update_tipo_pago(id_tipo_pago):
    data = request.get_json()
    nombre_tipo, siglas = data.get('nombre_tipo'), data.get('siglas')
    if not nombre_tipo or not siglas:
        return jsonify({"error": "Faltan datos"}), 400
    conn = get_db_connection()
    try:
        conn.execute("UPDATE tipos_pago SET nombre_tipo = ?, siglas = ? WHERE id_tipo_pago = ?", (nombre_tipo, siglas, id_tipo_pago))
        conn.commit()
        updated_tipo_pago = conn.execute("SELECT * FROM tipos_pago WHERE id_tipo_pago = ?", (id_tipo_pago,)).fetchone()
        return jsonify(dict(updated_tipo_pago)), 200
    except sqlite3.IntegrityError:
        return jsonify({"error": "El nombre o las siglas del tipo de pago ya existen"}), 409
    finally:
        conn.close()

@app.route('/api/catalogos/tipos_pago/<int:id_tipo_pago>', methods=['DELETE'])
def delete_tipo_pago(id_tipo_pago):
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM tipos_pago WHERE id_tipo_pago = ?", (id_tipo_pago,))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "No se puede eliminar el tipo de pago porque está en uso"}), 409
    finally:
        conn.close()
    return jsonify({"message": "Tipo de pago eliminado exitosamente"}), 200

@app.route('/api/catalogos/tipos_devolucion', methods=['GET'])
def get_tipos_devolucion():
    conn = get_db_connection()
    tipos_dev_cursor = conn.execute("SELECT * FROM tipos_devolucion ORDER BY nombre_devolucion").fetchall()
    conn.close()
    tipos_devolucion = [dict(row) for row in tipos_dev_cursor]
    return jsonify(tipos_devolucion), 200

@app.route('/api/catalogos/tipos_devolucion', methods=['POST'])
def add_tipo_devolucion():
    data = request.get_json()
    nombre_devolucion, descripcion = data.get('nombre_devolucion'), data.get('descripcion')
    if not nombre_devolucion:
        return jsonify({"error": "El nombre es requerido"}), 400
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tipos_devolucion (nombre_devolucion, descripcion) VALUES (?, ?)", (nombre_devolucion, descripcion))
        conn.commit()
        new_id = cursor.lastrowid
        new_tipo_dev = conn.execute("SELECT * FROM tipos_devolucion WHERE id_tipo_devolucion = ?", (new_id,)).fetchone()
        return jsonify(dict(new_tipo_dev)), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "El nombre del tipo de devolución ya existe"}), 409
    finally:
        conn.close()

@app.route('/api/catalogos/tipos_devolucion/<int:id_tipo_devolucion>', methods=['PUT'])
def update_tipo_devolucion(id_tipo_devolucion):
    data = request.get_json()
    nombre_devolucion, descripcion = data.get('nombre_devolucion'), data.get('descripcion')
    if not nombre_devolucion:
        return jsonify({"error": "El nombre es requerido"}), 400
    conn = get_db_connection()
    conn.execute("UPDATE tipos_devolucion SET nombre_devolucion = ?, descripcion = ? WHERE id_tipo_devolucion = ?", (nombre_devolucion, descripcion, id_tipo_devolucion))
    conn.commit()
    updated_tipo_dev = conn.execute("SELECT * FROM tipos_devolucion WHERE id_tipo_devolucion = ?", (id_tipo_devolucion,)).fetchone()
    conn.close()
    return jsonify(dict(updated_tipo_dev)), 200

@app.route('/api/catalogos/tipos_devolucion/<int:id_tipo_devolucion>', methods=['DELETE'])
def delete_tipo_devolucion(id_tipo_devolucion):
    conn = get_db_connection()
    conn.execute("DELETE FROM tipos_devolucion WHERE id_tipo_devolucion = ?", (id_tipo_devolucion,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Tipo de devolución eliminado exitosamente"}), 200

@app.route('/api/reportes/summary', methods=['GET'])
def get_report_summary():
    conn = get_db_connection()
    pagos_por_coordinador = conn.execute("""
        SELECT u.nombre || ' ' || u.apellido as coordinador, COUNT(o.id_orden) as total_ordenes
        FROM ordenes_pago o JOIN usuarios u ON o.id_coordinador = u.id_usuario GROUP BY o.id_coordinador
    """).fetchall()
    pagos_por_analista = conn.execute("""
        SELECT u.nombre || ' ' || u.apellido as analista, COUNT(b.id_bitacora) as total_acciones
        FROM bitacora b JOIN usuarios u ON b.id_usuario_accion = u.id_usuario WHERE b.accion IN ('PAGAR_ORDEN', 'DEVOLVER_ORDEN') GROUP BY b.id_usuario_accion
    """).fetchall()
    reporte_tipo_pago = conn.execute("""
        SELECT tp.nombre_tipo, COUNT(o.id_orden) as total
        FROM ordenes_pago o JOIN tipos_pago tp ON o.id_tipo_pago = tp.id_tipo_pago GROUP BY tp.nombre_tipo
    """).fetchall()
    total_pagos_realizados = conn.execute("SELECT COUNT(*) as total FROM ordenes_pago WHERE estado = 'Pagada'").fetchone()
    conn.close()
    summary = {
        "pagos_por_coordinador": [dict(row) for row in pagos_por_coordinador],
        "pagos_por_analista": [dict(row) for row in pagos_por_analista],
        "reporte_tipo_pago": [dict(row) for row in reporte_tipo_pago],
        "total_pagos_realizados": dict(total_pagos_realizados)
    }
    return jsonify(summary), 200

@app.route('/api/exchange/update', methods=['POST'])
def update_exchange_rates():
    api_url = "https://open.er-api.com/v6/latest/USD"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        if data.get("result") == "success":
            rates = data.get("rates")
            conn = get_db_connection()
            cursor = conn.cursor()
            for codigo, valor in rates.items():
                cursor.execute("UPDATE monedas SET tipo_cambio = ?, ultima_actualizacion = CURRENT_TIMESTAMP WHERE codigo_moneda = ?", (valor, codigo))
            conn.commit()
            conn.close()
            return jsonify({"message": "Tipos de cambio actualizados exitosamente"}), 200
        else:
            return jsonify({"error": "La respuesta de la API externa no fue exitosa"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Error al conectar con el servicio de tipos de cambio", "details": str(e)}), 503
    except Exception as e:
        return jsonify({"error": "Ocurrió un error inesperado", "details": str(e)}), 500

# --- RUTAS PARA ÓRDENES DE PAGO ---
@app.route('/api/ordenes', methods=['POST'])
def create_orden():
    data = request.get_json()
    id_coordinador, monto, id_moneda, id_tipo_pago, fecha_factura, fecha_vencimiento = data.get('id_coordinador'), data.get('monto'), data.get('id_moneda'), data.get('id_tipo_pago'), data.get('fecha_factura'), data.get('fecha_vencimiento')
    urgente, impuesto, descuento, acreedor, documento_compensacion = data.get('urgente', 0), data.get('impuesto', 0.0), data.get('descuento', 0.0), data.get('acreedor'), data.get('documento_compensacion')
    if not all([id_coordinador, monto, id_moneda, id_tipo_pago, fecha_factura, fecha_vencimiento]):
        return jsonify({"error": "Faltan datos para crear la orden"}), 400
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO ordenes_pago (monto, id_moneda, id_tipo_pago, fecha_factura, fecha_vencimiento, id_coordinador, estado, urgente, impuesto, descuento, acreedor, documento_compensacion) 
               VALUES (?, ?, ?, ?, ?, ?, 'Creada', ?, ?, ?, ?, ?)""",
            (monto, id_moneda, id_tipo_pago, fecha_factura, fecha_vencimiento, id_coordinador, urgente, impuesto, descuento, acreedor, documento_compensacion)
        )
        id_nueva_orden = cursor.lastrowid
        cursor.execute(
            "INSERT INTO bitacora (id_usuario_accion, accion, detalles, id_orden_afectada) VALUES (?, ?, ?, ?)",
            (id_coordinador, 'CREAR_ORDEN', f'Se creó la orden con monto {monto}', id_nueva_orden)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Error en la base de datos", "details": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"message": "Orden de pago creada exitosamente"}), 201

@app.route('/api/ordenes/<int:id_coordinador>', methods=['GET'])
def get_ordenes_by_coordinador(id_coordinador):
    query_params = request.args
    filter_estado, filter_tipo_pago = query_params.get('estado', 'todos'), query_params.get('tipo_pago', 'todos')
    conn = get_db_connection()
    base_query = """
        SELECT o.id_orden, o.monto, o.urgente, o.estado, o.fecha_pago_real, m.codigo_moneda, tp.nombre_tipo as tipo_pago
        FROM ordenes_pago o
        JOIN monedas m ON o.id_moneda = m.id_moneda
        JOIN tipos_pago tp ON o.id_tipo_pago = tp.id_tipo_pago
        WHERE o.id_coordinador = ?
    """
    params = [id_coordinador]
    if filter_estado != 'todos':
        base_query += " AND o.estado = ?"
        params.append(filter_estado)
    if filter_tipo_pago != 'todos':
        base_query += " AND o.id_tipo_pago = ?"
        params.append(filter_tipo_pago)
    base_query += " ORDER BY o.fecha_creacion DESC"
    ordenes_cursor = conn.execute(base_query, tuple(params)).fetchall()
    conn.close()
    ordenes = [dict(row) for row in ordenes_cursor]
    return jsonify(ordenes), 200

@app.route('/api/ordenes/<int:id_orden>/enviar', methods=['PUT'])
def enviar_orden(id_orden):
    data = request.get_json()
    id_usuario = data.get('id_usuario')
    if not id_usuario:
        return jsonify({"error": "No se identificó al usuario"}), 400
    conn = get_db_connection()
    try:
        conn.execute("UPDATE ordenes_pago SET estado = 'Enviada' WHERE id_orden = ?", (id_orden,))
        conn.execute("INSERT INTO bitacora (id_usuario_accion, accion, id_orden_afectada) VALUES (?, ?, ?)", (id_usuario, 'ENVIAR_ORDEN', id_orden))
        conn.commit()
    except Exception as e:
        return jsonify({"error": "Error al actualizar la orden", "details": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"message": "Orden enviada al analista exitosamente"}), 200

@app.route('/api/ordenes/enviadas', methods=['GET'])
def get_ordenes_enviadas():
    query_params = request.args
    search_term, filter_urgente = query_params.get('buscar', ''), query_params.get('urgente', 'todos')
    conn = get_db_connection()
    base_query = """
        SELECT o.*, m.codigo_moneda, u.nombre as coordinador_nombre, u.apellido as coordinador_apellido
        FROM ordenes_pago o
        JOIN monedas m ON o.id_moneda = m.id_moneda
        JOIN usuarios u ON o.id_coordinador = u.id_usuario
        WHERE o.estado = 'Enviada'
    """
    params = []
    if search_term:
        base_query += " AND (o.acreedor LIKE ? OR u.nombre LIKE ? OR u.apellido LIKE ?)"
        like_term = f"%{search_term}%"
        params.extend([like_term, like_term, like_term])
    if filter_urgente == 'si':
        base_query += " AND o.urgente = 1"
    elif filter_urgente == 'no':
        base_query += " AND o.urgente = 0"
    base_query += " ORDER BY o.urgente DESC, o.fecha_vencimiento ASC"
    ordenes_cursor = conn.execute(base_query, params).fetchall()
    conn.close()
    ordenes = [dict(row) for row in ordenes_cursor]
    return jsonify(ordenes), 200

@app.route('/api/ordenes/<int:id_orden>/devolver', methods=['PUT'])
def devolver_orden(id_orden):
    data = request.get_json()
    motivo, id_analista = data.get('motivo', 'Sin motivo especificado'), data.get('id_analista')
    if not id_analista:
        return jsonify({"error": "Se requiere la identificación del analista"}), 400
    conn = get_db_connection()
    try:
        conn.execute("UPDATE ordenes_pago SET estado = 'Devuelta' WHERE id_orden = ?", (id_orden,))
        conn.execute("INSERT INTO devoluciones (id_orden, motivo, id_analista) VALUES (?, ?, ?)", (id_orden, motivo, id_analista))
        conn.execute("INSERT INTO bitacora (id_usuario_accion, accion, detalles, id_orden_afectada) VALUES (?, ?, ?, ?)", (id_analista, 'DEVOLVER_ORDEN', f'Motivo: {motivo}', id_orden))
        conn.commit()
    except Exception as e:
        return jsonify({"error": "Error al devolver la orden", "details": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"message": "Orden devuelta exitosamente"}), 200

@app.route('/api/ordenes/<int:id_orden>/pagar', methods=['PUT'])
def pagar_orden(id_orden):
    data = request.get_json()
    id_analista = data.get('id_analista')
    if not id_analista:
        return jsonify({"error": "No se identificó al analista"}), 400
    conn = get_db_connection()
    try:
        conn.execute("UPDATE ordenes_pago SET estado = 'Pagada', fecha_pago_real = CURRENT_DATE WHERE id_orden = ?", (id_orden,))
        conn.execute("INSERT INTO bitacora (id_usuario_accion, accion, id_orden_afectada) VALUES (?, ?, ?)", (id_analista, 'PAGAR_ORDEN', id_orden))
        conn.commit()
    except Exception as e:
        return jsonify({"error": "Error al pagar la orden", "details": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"message": "Orden marcada como pagada exitosamente"}), 200

@app.route('/api/ordenes/historial', methods=['GET'])
def get_historial_ordenes():
    query_params = request.args
    search_term, filter_estado = query_params.get('buscar', ''), query_params.get('estado', 'todos')
    conn = get_db_connection()
    base_query = """
        SELECT o.*, m.codigo_moneda, u.nombre as coordinador_nombre, u.apellido as coordinador_apellido
        FROM ordenes_pago o
        JOIN monedas m ON o.id_moneda = m.id_moneda
        JOIN usuarios u ON o.id_coordinador = u.id_usuario
    """
    where_clauses, params = [], []
    if search_term:
        where_clauses.append("(o.acreedor LIKE ? OR u.nombre LIKE ? OR u.apellido LIKE ?)")
        like_term = f"%{search_term}%"
        params.extend([like_term, like_term, like_term])
    if filter_estado != 'todos':
        where_clauses.append("o.estado = ?")
        params.append(filter_estado)
    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)
    base_query += " ORDER BY o.id_orden DESC"
    ordenes_cursor = conn.execute(base_query, tuple(params)).fetchall()
    conn.close()
    ordenes = [dict(row) for row in ordenes_cursor]
    return jsonify(ordenes), 200

@app.route('/api/bitacora', methods=['GET'])
def get_bitacora():
    conn = get_db_connection()
    logs_cursor = conn.execute("""
        SELECT b.id_bitacora, u.nombre, u.apellido, b.accion, b.detalles, b.id_orden_afectada, b.fecha_accion
        FROM bitacora b JOIN usuarios u ON b.id_usuario_accion = u.id_usuario ORDER BY b.fecha_accion DESC
    """).fetchall()
    conn.close()
    logs = [dict(row) for row in logs_cursor]
    return jsonify(logs), 200

@app.route('/api/ordenes/detalle/<int:id_orden>', methods=['GET'])
def get_orden_detalle(id_orden):
    conn = get_db_connection()
    orden = conn.execute("SELECT * FROM ordenes_pago WHERE id_orden = ?", (id_orden,)).fetchone()
    conn.close()
    if not orden:
        return jsonify({"error": "Orden no encontrada"}), 404
    return jsonify(dict(orden)), 200

@app.route('/api/ordenes/<int:id_orden>', methods=['PUT'])
def update_orden(id_orden):
    data = request.get_json()
    monto, id_moneda, id_tipo_pago, fecha_factura, fecha_vencimiento = data.get('monto'), data.get('id_moneda'), data.get('id_tipo_pago'), data.get('fecha_factura'), data.get('fecha_vencimiento')
    if not all([monto, id_moneda, id_tipo_pago, fecha_factura, fecha_vencimiento]):
        return jsonify({"error": "Faltan datos para actualizar la orden"}), 400
    conn = get_db_connection()
    try:
        conn.execute(
            """UPDATE ordenes_pago 
               SET monto = ?, id_moneda = ?, id_tipo_pago = ?, fecha_factura = ?, fecha_vencimiento = ?, estado = 'Creada', fecha_ultima_modificacion = CURRENT_TIMESTAMP
               WHERE id_orden = ?""",
            (monto, id_moneda, id_tipo_pago, fecha_factura, fecha_vencimiento, id_orden)
        )
        id_coordinador = data.get('id_coordinador')
        if id_coordinador:
             conn.execute(
                "INSERT INTO bitacora (id_usuario_accion, accion, detalles, id_orden_afectada) VALUES (?, ?, ?, ?)",
                (id_coordinador, 'EDITAR_ORDEN', 'El coordinador modificó la orden', id_orden)
            )
        conn.commit()
    except Exception as e:
        return jsonify({"error": "Error al actualizar la orden", "details": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"message": "Orden actualizada exitosamente"}), 200

@app.route('/')
def index():
    return jsonify({"message": "API del Sistema de Pagos funcionando!"})

if __name__ == '__main__':
    init_db()
    app.run(debug=False, port=5000)
else:
    init_db()