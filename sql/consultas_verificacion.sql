-- 1. ¿Cuántos registros hay en fact_prestamos?
SELECT COUNT(*) AS total_prestamos
FROM fact_prestamos;


-- 2. ¿Cuántos registros hay en etl_errores?
SELECT COUNT(*) AS total_errores
FROM etl_errores;


-- 3. ¿Qué errores fueron registrados?
SELECT
    id_registro,
    descripcion_error,
    fecha_error
FROM etl_errores;


-- 4. ¿Cuál fue el último estado registrado en etl_log?
SELECT
    fecha_ejecucion,
    estado,
    filas_leidas,
    filas_cargadas,
    filas_rechazadas
FROM etl_log
ORDER BY id_log DESC
LIMIT 1;


-- 5. Total de multas por carrera
SELECT
    dc.carrera,
    SUM(fp.total_multa) AS total_multas
FROM fact_prestamos fp
JOIN dim_carrera dc
ON fp.id_carrera = dc.id_carrera
GROUP BY dc.carrera
ORDER BY total_multas DESC;


-- 6. Total de multas por categoría de libro
SELECT
    dl.categoria,
    SUM(fp.total_multa) AS total_multas
FROM fact_prestamos fp
JOIN dim_libro dl
ON fp.id_libro = dl.id_libro
GROUP BY dl.categoria
ORDER BY total_multas DESC;


-- 7. Promedio de días de préstamo por sede
SELECT
    ds.sede,
    AVG(fp.dias_prestamo) AS promedio_dias
FROM fact_prestamos fp
JOIN dim_sede ds
ON fp.id_sede = ds.id_sede
GROUP BY ds.sede;


-- 8. Los 5 libros con mayor total de multa
SELECT
    dl.libro,
    SUM(fp.total_multa) AS total_multa
FROM fact_prestamos fp
JOIN dim_libro dl
ON fp.id_libro = dl.id_libro
GROUP BY dl.libro
ORDER BY total_multa DESC
LIMIT 5;


-- 9. Préstamos detallados
SELECT
    df.fecha,
    da.alumno,
    dc.carrera,
    dl.libro,
    dl.categoria,
    ds.sede,
    fp.total_multa
FROM fact_prestamos fp
JOIN dim_fecha df
ON fp.id_fecha = df.id_fecha
JOIN dim_alumno da
ON fp.id_alumno = da.id_alumno
JOIN dim_carrera dc
ON fp.id_carrera = dc.id_carrera
JOIN dim_libro dl
ON fp.id_libro = dl.id_libro
JOIN dim_sede ds
ON fp.id_sede = ds.id_sede
ORDER BY fp.id_prestamo;


-- 10. Conteo de préstamos por sede
SELECT
    ds.sede,
    COUNT(*) AS total_prestamos
FROM fact_prestamos fp
JOIN dim_sede ds
ON fp.id_sede = ds.id_sede
GROUP BY ds.sede
ORDER BY total_prestamos DESC;