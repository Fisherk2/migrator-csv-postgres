-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙
-- DANGEROUS SCRIPT - DROP DATABASE
-- Purpose: Borra la base de datos del proyecto con múltiples salvaguardas
-- Author: fisherk2
-- Version: 1.0
-- Date: 2026-03-13
-- DANGER LEVEL: CRITICAL - OPERACIÓN DESTRUCTIVA
-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙

-- ⚠️⚠️⚠️ ADVERTENCIA: ESTE SCRIPT ELIMINARÁ TODOS LOS DATOS ⚠️⚠️⚠️
-- ⚠️⚠️⚠️ ADVERTENCIA: ESTA OPERACIÓN ES IRREVERSIBLE ⚠️⚠️⚠️
-- ⚠️⚠️⚠️ ADVERTENCIA: NUNCA EJECUTAR EN PRODUCCIÓN SIN APROBACIÓN ⚠️⚠️⚠️

--◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤
-- VERIFICACIÓN DE SEGURIDAD - NO CONTINUAR SI NO ESTÁ SEGURO
--◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤

-- ■■■■■■■■■■■■■ Editar el nombre de la base de datos antes de ejecutar ■■■■■■■■■■■■■
-- Cambiar 'your_database_name' por el nombre real de la base de datos
DO $$
BEGIN
    RAISE NOTICE 'Verificación de seguridad: Editar el nombre de la base de datos antes de continuar';
    RAISE NOTICE 'Nombre actual: your_database_name - DEBE SER CAMBIADO';
END $$;

--◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤
-- ELIMINACIÓN CONDICIONAL Y SEGURA
--◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤

-- ■■■■■■■■■■■■■ Verificar si la base de datos existe antes de intentar eliminarla ■■■■■■■■■■■■■
-- Esto previene errores si la base de datos ya fue eliminada
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_database WHERE datname = 'your_database_name') THEN
        RAISE NOTICE 'Base de datos encontrada: %', 'your_database_name';
        -- Terminar todas las conexiones activas a la base de datos
        -- Esto previene el error "database is being accessed by other users"
        RAISE NOTICE 'Terminando conexiones activas...';
        PERFORM pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname = 'your_database_name' 
        AND pid <> pg_backend_pid();
        -- Esperar un momento para que las conexiones se terminen completamente
        PERFORM pg_sleep(1);
        RAISE NOTICE 'Eliminando base de datos: %', 'your_database_name';
        -- Salir del bloque DO para ejecutar DROP DATABASE fuera de transacción
        RAISE NOTICE 'Saliendo del bloque de transacción para eliminar base de datos...';
    ELSE
        RAISE NOTICE 'La base de datos % no existe, no se requiere eliminación', 'your_database_name';
    END IF;
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error al verificar base de datos: %', SQLERRM;
END $$;

-- ◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤ ⎡ Ejecutar DROP DATABASE fuera de transacción ⎦ ◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤
DROP DATABASE IF EXISTS your_database_name;

--◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤
-- VERIFICACIÓN FINAL
--◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤

-- ■■■■■■■■■■■■■ Confirmar que la base de datos fue eliminada ■■■■■■■■■■■■■
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'your_database_name') THEN
        RAISE NOTICE '✅ Verificación exitosa: La base de datos ya no existe';
    ELSE
        RAISE EXCEPTION '❌ Error: La base de datos todavía existe';
    END IF;
END $$;

--◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤
-- INSTRUCCIONES DE USO SEGURO
--◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤

--▁▂▃▄▅▆▇███████ CÓMO EJECUTAR ESTE SCRIPT DE FORMA SEGURA ███████▇▆▅▄▃▂▁

-- 1. Backup completo de la base de datos: pg_dump your_database_name > backup.sql
-- 2. Verificar que estás en el entorno correcto (development/testing)
-- 3. Editar 'your_database_name' con el nombre real de la BD
-- 4. Ejecutar: psql -U postgres -d postgres -f drop_database.sql
-- 5. Verificar que la base de datos fue eliminada: \l

-- ⚠️⚠️⚠️ RECORDATORIO FINAL: ESTE SCRIPT ES DESTRUCTIVO ⚠️⚠️⚠️
-- ⚠️⚠️⚠️ NO EJECUTAR EN PRODUCCIÓN SIN SUPERVISIÓN ⚠️⚠️⚠️