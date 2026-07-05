# Unidad 2 - ETL Biblioteca

## Objetivo

Desarrollar un proceso ETL que permita leer un archivo CSV de préstamos de biblioteca, realizar una limpieza básica, validar la información, cargar los registros válidos en un mini Data Warehouse en MySQL y registrar los errores detectados durante la ejecución.

---

## Requisitos

- Python 3
- MySQL
- Base de datos `biblioteca_dw`
- Librerías:
  - pandas
  - mysql-connector-python

---

## Crear la base de datos

Antes de ejecutar el proyecto, crear la base de datos en MySQL:

```sql
CREATE DATABASE biblioteca_dw;
```

Las tablas serán creadas automáticamente por el script.

---

## Instalar las librerías

```bash
pip install pandas mysql-connector-python
```

---

## Estructura del proyecto

```
unidad2_etl_biblioteca/
│
├── data/
│   └── prestamos_biblioteca_100.csv
│
├── scripts/
│   └── etl_biblioteca.py
│
├── sql/
│   └── consultas_verificacion.sql
│
├── evidencias/
│   ├── evidencias_unidad2.pdf
│   └── reporte_ejecucion.txt
│
└── README.md
```

---

## Ejecución

Desde la carpeta principal del proyecto ejecutar:

```bash
python scripts/etl_biblioteca.py
```

---

## Resultado esperado

Al finalizar la ejecución se obtiene:

- Filas leídas: **100**
- Filas cargadas: **98**
- Filas rechazadas: **2**
- Estado: **FINALIZADO_CON_ERRORES**

Los errores esperados son:

- id_prestamo **5099** → total_multa incorrecto.
- id_prestamo **5002** → id_prestamo duplicado.

Además, el proceso:

- Crea las tablas del Data Warehouse.
- Carga los registros válidos en `fact_prestamos`.
- Registra los errores en `etl_errores`.
- Guarda la ejecución en `etl_log`.
- Genera el archivo `evidencias/reporte_ejecucion.txt`.