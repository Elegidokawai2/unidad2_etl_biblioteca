import pandas as pd
import mysql.connector
from datetime import datetime
from pathlib import Path

print("Leyendo archivo CSV...")

BASE_DIR = Path(__file__).resolve().parent.parent
ARCHIVO = BASE_DIR / "data" / "prestamos_biblioteca_100.csv"

if not ARCHIVO.exists():
    raise FileNotFoundError(f"No se encontró el archivo: {ARCHIVO}")

df = pd.read_csv(ARCHIVO)

print("Realizando limpieza básica...")

# Estandarizar nombres de columnas
df.columns = (
    df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
)

# Limpiar columnas de texto
columnas_texto = [
    "alumno",
    "carrera",
    "libro",
    "categoria",
    "sede"
]

for columna in columnas_texto:
    df[columna] = df[columna].astype(str).str.strip()

# Conversión de tipos
df["fecha_prestamo"] = pd.to_datetime(
    df["fecha_prestamo"],
    errors="coerce"
)

df["dias_prestamo"] = pd.to_numeric(
    df["dias_prestamo"],
    errors="coerce"
)

df["multa_diaria"] = pd.to_numeric(
    df["multa_diaria"],
    errors="coerce"
)

df["total_multa"] = pd.to_numeric(
    df["total_multa"],
    errors="coerce"
)

print("Validando registros...")

filas_leidas = len(df)
filas_validas = 0
filas_rechazadas = 0

registros_validos = []
registros_erroneos = []

seen_ids = set()

columnas_obligatorias = [
    "id_prestamo",
    "fecha_prestamo",
    "alumno",
    "carrera",
    "libro",
    "categoria",
    "dias_prestamo",
    "multa_diaria",
    "sede",
    "total_multa"
]

# Validación registro por registro
for fila_idx, row in df.iterrows():

    descripcion_error = None

    # Valores nulos
    if row[columnas_obligatorias].isnull().any():
        descripcion_error = "Valores nulos en columnas obligatorias"

    else:

        id_prestamo = int(row["id_prestamo"])

        # Duplicado
        if id_prestamo in seen_ids:

            descripcion_error = "id_prestamo duplicado"

        else:

            total_calculado = (
                row["dias_prestamo"] *
                row["multa_diaria"]
            )

            # Total incorrecto
            if abs(total_calculado - row["total_multa"]) > 0.0001:

                descripcion_error = (
                    "total_multa incorrecto"
                )

    if descripcion_error:

        filas_rechazadas += 1

        registros_erroneos.append({

            "fila_csv": fila_idx + 2,

            "id_registro": int(row["id_prestamo"]),

            "descripcion_error": descripcion_error,

            "datos_originales": row.to_json(
                date_format="iso",
                force_ascii=False
            )

        })

    else:

        filas_validas += 1

        seen_ids.add(int(row["id_prestamo"]))

        registros_validos.append(row)

print("-----------------------------------")
print("Filas leídas:", filas_leidas)
print("Filas válidas:", filas_validas)
print("Filas rechazadas:", filas_rechazadas)
print("-----------------------------------")

print("Conectando a MySQL...")

conexion = mysql.connector.connect(
    host="localhost",
    port=3307,
    user="root",
    password="root123"
)

cursor = conexion.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS biblioteca_dw")
conexion.commit()
cursor.close()
conexion.close()

conexion = mysql.connector.connect(
    host="localhost",
    port=3307,
    user="root",
    password="root123",
    database="biblioteca_dw"
)

cursor = conexion.cursor()

print("Creando tablas...")

# TABLAS DE DIMENSIONES
cursor.execute("""
CREATE TABLE IF NOT EXISTS dim_alumno
(
    id_alumno INT AUTO_INCREMENT PRIMARY KEY,
    alumno VARCHAR(100) UNIQUE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dim_carrera
(
    id_carrera INT AUTO_INCREMENT PRIMARY KEY,
    carrera VARCHAR(100) UNIQUE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dim_libro
(
    id_libro INT AUTO_INCREMENT PRIMARY KEY,
    libro VARCHAR(150),
    categoria VARCHAR(100),
    UNIQUE(libro, categoria)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dim_sede
(
    id_sede INT AUTO_INCREMENT PRIMARY KEY,
    sede VARCHAR(100) UNIQUE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dim_fecha
(
    id_fecha INT PRIMARY KEY,
    fecha DATE UNIQUE,
    anio INT,
    mes INT,
    dia INT
);
""")

# TABLA DE HECHOS
cursor.execute("""
CREATE TABLE IF NOT EXISTS fact_prestamos
(
    id_prestamo INT PRIMARY KEY,

    id_fecha INT,
    id_alumno INT,
    id_carrera INT,
    id_libro INT,
    id_sede INT,

    dias_prestamo DECIMAL(10,2),
    multa_diaria DECIMAL(10,2),
    total_multa DECIMAL(10,2),

    FOREIGN KEY(id_fecha)
        REFERENCES dim_fecha(id_fecha),

    FOREIGN KEY(id_alumno)
        REFERENCES dim_alumno(id_alumno),

    FOREIGN KEY(id_carrera)
        REFERENCES dim_carrera(id_carrera),

    FOREIGN KEY(id_libro)
        REFERENCES dim_libro(id_libro),

    FOREIGN KEY(id_sede)
        REFERENCES dim_sede(id_sede)
);
""")

# TABLA DE ERRORES
cursor.execute("""
CREATE TABLE IF NOT EXISTS etl_errores
(
    id_error INT AUTO_INCREMENT PRIMARY KEY,

    fecha_error DATETIME,

    archivo_origen VARCHAR(255),

    fila_csv INT,

    id_registro INT,

    descripcion_error VARCHAR(255),

    datos_originales TEXT
);
""")

# BITÁCORA ETL
cursor.execute("""
CREATE TABLE IF NOT EXISTS etl_log
(
    id_log INT AUTO_INCREMENT PRIMARY KEY,

    fecha_ejecucion DATETIME,

    archivo_origen VARCHAR(255),

    filas_leidas INT,

    filas_cargadas INT,

    filas_rechazadas INT,

    estado VARCHAR(50)
);
""")

print("Limpiando tablas...")

cursor.execute("DELETE FROM fact_prestamos")
cursor.execute("DELETE FROM dim_alumno")
cursor.execute("DELETE FROM dim_carrera")
cursor.execute("DELETE FROM dim_libro")
cursor.execute("DELETE FROM dim_sede")
cursor.execute("DELETE FROM dim_fecha")
cursor.execute("DELETE FROM etl_errores")

conexion.commit()

print("Reiniciando AUTO_INCREMENT...")

cursor.execute("ALTER TABLE dim_alumno AUTO_INCREMENT = 1")
cursor.execute("ALTER TABLE dim_carrera AUTO_INCREMENT = 1")
cursor.execute("ALTER TABLE dim_libro AUTO_INCREMENT = 1")
cursor.execute("ALTER TABLE dim_sede AUTO_INCREMENT = 1")

conexion.commit()

print("Cargando dimensiones...")

# CARGAR DIMENSIONES
for row in registros_validos:

    cursor.execute(
        """
        INSERT INTO dim_alumno(alumno)
        VALUES(%s)
        ON DUPLICATE KEY UPDATE id_alumno=id_alumno
        """,
        (row["alumno"],)
    )

    cursor.execute(
        """
        INSERT INTO dim_carrera(carrera)
        VALUES(%s)
        ON DUPLICATE KEY UPDATE id_carrera=id_carrera
        """,
        (row["carrera"],)
    )

    cursor.execute(
        """
        INSERT INTO dim_libro(libro, categoria)
        VALUES(%s,%s)
        ON DUPLICATE KEY UPDATE id_libro=id_libro
        """,
        (
            row["libro"],
            row["categoria"]
        )
    )

    cursor.execute(
        """
        INSERT INTO dim_sede(sede)
        VALUES(%s)
        ON DUPLICATE KEY UPDATE id_sede=id_sede
        """,
        (row["sede"],)
    )

for row in registros_validos:

    id_fecha = int(
        row["fecha_prestamo"].strftime("%Y%m%d")
    )

    cursor.execute(
        """
        INSERT INTO dim_fecha(
            id_fecha,
            fecha,
            anio,
            mes,
            dia
        )
        VALUES(%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE id_fecha=id_fecha
        """,
        (
            id_fecha,
            row["fecha_prestamo"].date(),
            row["fecha_prestamo"].year,
            row["fecha_prestamo"].month,
            row["fecha_prestamo"].day
        )
    )

conexion.commit()

print("Consultando dimensiones...")

# OBTENER IDS
cursor.execute(
    "SELECT id_alumno, alumno FROM dim_alumno"
)

alumnos = {
    nombre: id_alumno
    for id_alumno, nombre in cursor.fetchall()
}

cursor.execute(
    "SELECT id_carrera, carrera FROM dim_carrera"
)

carreras = {
    nombre: id_carrera
    for id_carrera, nombre in cursor.fetchall()
}

cursor.execute(
    "SELECT id_libro, libro, categoria FROM dim_libro"
)

libros = {
    (libro, categoria): id_libro
    for id_libro, libro, categoria in cursor.fetchall()
}

cursor.execute(
    "SELECT id_sede, sede FROM dim_sede"
)

sedes = {
    nombre: id_sede
    for id_sede, nombre in cursor.fetchall()
}

print("Cargando tabla de hechos...")

# CARGAR FACT_PRESTAMOS
for row in registros_validos:

    id_fecha = int(
        row["fecha_prestamo"].strftime("%Y%m%d")
    )

    id_alumno = alumnos[row["alumno"]]
    id_carrera = carreras[row["carrera"]]
    id_libro = libros[
        (
            row["libro"],
            row["categoria"]
        )
    ]
    id_sede = sedes[row["sede"]]

    cursor.execute(
        """
        INSERT INTO fact_prestamos(

            id_prestamo,

            id_fecha,
            id_alumno,
            id_carrera,
            id_libro,
            id_sede,

            dias_prestamo,
            multa_diaria,
            total_multa

        )
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (

            row["id_prestamo"],

            id_fecha,
            id_alumno,
            id_carrera,
            id_libro,
            id_sede,

            row["dias_prestamo"],
            row["multa_diaria"],
            row["total_multa"]

        )
    )

conexion.commit()

print("Guardando errores...")

# ETL_ERRORES
for error in registros_erroneos:

    cursor.execute(
        """
        INSERT INTO etl_errores(

            fecha_error,
            archivo_origen,
            fila_csv,
            id_registro,
            descripcion_error,
            datos_originales

        )
        VALUES(%s,%s,%s,%s,%s,%s)
        """,
        (

            datetime.now(),
            "prestamos_biblioteca_100.csv",

            error["fila_csv"],
            error["id_registro"],
            error["descripcion_error"],
            error["datos_originales"]

        )
    )

estado = "FINALIZADO"

if filas_rechazadas > 0:
    estado = "FINALIZADO_CON_ERRORES"

print("Registrando ejecución...")

cursor.execute(
    """
    INSERT INTO etl_log(

        fecha_ejecucion,
        archivo_origen,
        filas_leidas,
        filas_cargadas,
        filas_rechazadas,
        estado

    )
    VALUES(%s,%s,%s,%s,%s,%s)
    """,
    (

        datetime.now(),
        "prestamos_biblioteca_100.csv",

        filas_leidas,
        filas_validas,
        filas_rechazadas,
        estado

    )
)

conexion.commit()

print("Generando reporte...")

REPORTE_PATH = BASE_DIR / "evidencias" / "reporte_ejecucion.txt"
REPORTE_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(
    REPORTE_PATH,
    "w",
    encoding="utf-8"
) as reporte:

    reporte.write("REPORTE DE EJECUCIÓN ETL\n")
    reporte.write("-----------------------------\n")
    reporte.write("Nombre del alumno: Erick Humberto Teja Carvajal\n")
    reporte.write(f"Fecha: {datetime.now()}\n")
    reporte.write("Archivo: prestamos_biblioteca_100.csv\n")
    reporte.write(f"Filas leídas: {filas_leidas}\n")
    reporte.write(f"Filas cargadas: {filas_validas}\n")
    reporte.write(f"Filas rechazadas: {filas_rechazadas}\n")
    reporte.write(f"Estado: {estado}\n\n")

    reporte.write("Errores detectados:\n")

    for error in registros_erroneos:

        reporte.write(
            f"- ID {error['id_registro']} -> "
            f"{error['descripcion_error']}\n"
        )

conexion.commit()

cursor.close()
conexion.close()

print("-----------------------------------")
print("ETL FINALIZADO")
print("Filas leídas:", filas_leidas)
print("Filas cargadas:", filas_validas)
print("Filas rechazadas:", filas_rechazadas)
print("Estado:", estado)
print("-----------------------------------")