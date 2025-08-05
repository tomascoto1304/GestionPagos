-- Eliminar tablas si ya existen para empezar de cero
DROP TABLE IF EXISTS bitacora;
DROP TABLE IF EXISTS devoluciones;
DROP TABLE IF EXISTS ordenes_pago;
DROP TABLE IF EXISTS monedas;
DROP TABLE IF EXISTS tipos_pago;
DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS roles;

-- Tabla para los roles de usuario
CREATE TABLE roles (
    id_rol INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_rol TEXT NOT NULL UNIQUE CHECK(nombre_rol IN ('Analista', 'Coordinador', 'Administrador'))
);

-- Tabla para los usuarios del sistema
CREATE TABLE usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    id_rol INTEGER NOT NULL,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (id_rol) REFERENCES roles(id_rol)
);

-- Catálogo de tipos de pago
CREATE TABLE tipos_pago (
    id_tipo_pago INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_tipo TEXT NOT NULL UNIQUE,
    siglas TEXT UNIQUE
);

-- Catálogo de monedas
CREATE TABLE monedas (
    id_moneda INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_moneda TEXT NOT NULL UNIQUE,
    codigo_moneda TEXT NOT NULL UNIQUE, -- ej. USD, EUR, CRC
    tipo_cambio REAL NOT NULL,
    ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla principal de órdenes de pago
CREATE TABLE ordenes_pago (
    id_orden INTEGER PRIMARY KEY AUTOINCREMENT,
    monto REAL NOT NULL,
    id_moneda INTEGER NOT NULL,
    id_tipo_pago INTEGER NOT NULL,
    fecha_factura DATE NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    fecha_pago_real DATE,
    estado TEXT NOT NULL CHECK(estado IN ('Creada', 'Enviada', 'Pagada', 'Devuelta')) DEFAULT 'Creada',
    id_coordinador INTEGER NOT NULL,
    id_analista_asignado INTEGER,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_ultima_modificacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    -- NUEVOS CAMPOS AÑADIDOS --
    urgente INTEGER DEFAULT 0, -- 0 para No, 1 para Sí
    impuesto REAL DEFAULT 0.0,
    descuento REAL DEFAULT 0.0,
    acreedor TEXT,
    documento_compensacion TEXT,
    -- FIN DE NUEVOS CAMPOS --
    FOREIGN KEY (id_moneda) REFERENCES monedas(id_moneda),
    FOREIGN KEY (id_tipo_pago) REFERENCES tipos_pago(id_tipo_pago),
    FOREIGN KEY (id_coordinador) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_analista_asignado) REFERENCES usuarios(id_usuario)
);

-- Tabla para registrar las devoluciones
CREATE TABLE devoluciones (
    id_devolucion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_orden INTEGER NOT NULL,
    motivo TEXT NOT NULL,
    fecha_devolucion DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_analista INTEGER NOT NULL,
    FOREIGN KEY (id_orden) REFERENCES ordenes_pago(id_orden),
    FOREIGN KEY (id_analista) REFERENCES usuarios(id_usuario)
);

-- Bitácora para registrar todas las acciones importantes
CREATE TABLE bitacora (
    id_bitacora INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario_accion INTEGER NOT NULL,
    accion TEXT NOT NULL,
    detalles TEXT,
    id_orden_afectada INTEGER,
    fecha_accion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario_accion) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_orden_afectada) REFERENCES ordenes_pago(id_orden)
);

-- Insertar datos iniciales
INSERT INTO roles (nombre_rol) VALUES ('Analista'), ('Coordinador'), ('Administrador');
INSERT INTO monedas (nombre_moneda, codigo_moneda, tipo_cambio) VALUES
('Dólar estadounidense', 'USD', 1.00), ('Euro', 'EUR', 0.93), ('Real Brasileño', 'BRL', 5.10),
('Colón Costarricense', 'CRC', 560.50), ('Dólar Canadiense', 'CAD', 1.37), ('Franco Suizo', 'CHF', 0.91);
INSERT INTO tipos_pago (nombre_tipo, siglas) VALUES ('Pago a Proveedores', 'PR'), ('Servicios Externos', 'SE'),
('Salarios', 'SA'), ('Impuestos', 'DI');