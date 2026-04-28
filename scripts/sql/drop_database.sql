-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙
-- DANGEROUS SCRIPT - DROP DATABASE
-- Purpose: Borra la base de datos del proyecto
-- Author: fisherk2
-- Version: 1.0
-- Date: 2026-04-28
-- DANGER LEVEL: CRITICAL - OPERACIÓN DESTRUCTIVA
-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙

-- ⚠️⚠️⚠️ ADVERTENCIA: ESTE SCRIPT ELIMINARÁ TODOS LOS DATOS ⚠️⚠️⚠️
-- ⚠️⚠️⚠️ ADVERTENCIA: ESTA OPERACIÓN ES IRREVERSIBLE ⚠️⚠️⚠️
-- ⚠️⚠️⚠️ ADVERTENCIA: NUNCA EJECUTAR EN PRODUCCIÓN SIN APROBACIÓN ⚠️⚠️⚠️

--◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤
-- VERIFICACIÓN DE SEGURIDAD - NO CONTINUAR SI NO ESTÁ SEGURO
--◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤

-- ■■■■■■■■■■■■■ DECISIÓN DE DISEÑO: Script simplificado sin bloques DO ■■■■■■■■■■■■■
-- PostgreSQL no permite DROP DATABASE dentro de transacciones.
-- Python maneja la verificación de existencia y terminación de conexiones.
-- Este script solo ejecuta el DROP directo con autocommit=True.

-- ■■■■■■■■■■■■■ Terminar conexiones activas antes de DROP ■■■■■■■■■■■■■
-- Esto previene el error "database is being accessed by other users"
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '{{DB_NAME}}'
AND pid <> pg_backend_pid();

-- ■■■■■■■■■■■■■ DROP DATABASE (requiere autocommit=True) ■■■■■■■■■■■■■
-- DECISIÓN: Usar placeholder {{DB_NAME}} para parametrización
-- Python reemplaza este placeholder con valor de variable de entorno
DROP DATABASE IF EXISTS {{DB_NAME}};

--◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤
-- INSTRUCCIONES DE USO SEGURO
--◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤

--▁▂▃▄▅▆▇███████ CÓMO EJECUTAR ESTE SCRIPT DE FORMA SEGURA ███████▇▆▅▄▃▂▁

-- 1. Backup completo de la base de datos: pg_dump {{DB_NAME}} > backup.sql
-- 2. Verificar que estás en el entorno correcto (development/testing)
-- 3. El placeholder {{DB_NAME}} se reemplaza automáticamente desde Python
-- 4. Ejecutar vía init_db.py o scripts de automatización
-- 5. Verificar que la base de datos fue eliminada: \l

-- ⚠️⚠️⚠️ RECORDATORIO FINAL: ESTE SCRIPT ES DESTRUCTIVO ⚠️⚠️⚠️
-- ⚠️⚠️⚠️ NO EJECUTAR EN PRODUCCIÓN SIN SUPERVISIÓN ⚠️⚠️⚠️