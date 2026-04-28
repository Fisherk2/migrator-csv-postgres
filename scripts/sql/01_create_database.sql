-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙
-- Database Script de creación de base de datos
-- Purpose: Crear una base de datos PostgreSQL con locale y encoding UTF-8
-- Author: fisherk2
-- Version: 1.0
-- Date: 2026-04-16
-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙

-- ■■■■■■■■■■■■■ Establecer variables de sesión para creación consistente de base de datos ■■■■■■■■■■■■■
-- SET client_encoding = 'UTF8';
-- SET client_min_messages = warning;

-- ■■■■■■■■■■■■ Crear base de datos con encoding UTF8 y locale apropiado ■■■■■■■■■■■■
-- Usando template0 para evitar copiar configuraciones de base de datos existentes
-- LC_COLLATE y LC_CTYPE configurados a 'en_US.UTF-8' para operaciones consistentes de strings
-- Nota: PostgreSQL no soporta "IF NOT EXISTS" en CREATE DATABASE, usamos enfoque con shell
-- Primero verificamos si existe, luego creamos si es necesario

-- ■■■■■■■■■■■ Verificar si la base de datos ya existe (La verificación se maneja en Python) ■■■■■■■■■■■■■
-- Nota: Usamos variables de entorno para hacerlo dinámico y seguro
-- Solo descomentar si se ejecuta directamente
--DO $$
--BEGIN
--    IF EXISTS (SELECT 1 FROM pg_database WHERE datname = 'migrator_ecommerce') THEN
--        RAISE NOTICE 'Base de datos % ya existe. Omitiendo creación.', 'migrator_ecommerce';
--    ELSE
--        RAISE NOTICE 'Creando base de datos %...', 'migrator_ecommerce';
--    END IF;
--END $$;

-- ■■■■■■■■■■■ Crear base de datos (solo si no existe) ■■■■■■■■■■■■■■■■
-- DECISIÓN: Comandos separados por punto y coma para ejecución individual en Python
-- Python reemplaza estos placeholders con valores de variables de entorno
CREATE DATABASE {{DB_NAME}}
    WITH
    OWNER = {{DB_USER}}
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    TEMPLATE = template0;

GRANT ALL PRIVILEGES ON DATABASE {{DB_NAME}} TO {{DB_USER}};

COMMENT ON DATABASE {{DB_NAME}} IS 'Base de datos principal de la aplicación - creada con create_database.sql';

-- ■■■■■■■■■■■■■ Desconectarse de la nueva base de datos para retornar al estado de conexión original ■■■■■■■■■■■■■
-- Esto previene que scripts subsecuentes se ejecuten accidentalmente contra la base de datos incorrecta
-- psycopg2 utiliza dual-connection pattern: primero conecta a postgres, luego a la nueva BD
-- Solo descomentar si se ejecuta directamente
-- \c postgres

-- ■■■■■■■■■■■■ Mensaje de finalización del script de creación de base de datos (La verificación se maneja en Python) ■■■■■■■■■■■■
-- Esto proporciona retroalimentación clara de que la base de datos está lista para migraciones
-- Solo descomentar si se ejecuta directamente
--DO $$
--BEGIN
--    IF EXISTS (SELECT 1 FROM pg_database WHERE datname = 'migrator_ecommerce') THEN
--        RAISE NOTICE 'Script de creación de base de datos completado. Base de datos "migrator_ecommerce" está lista para migraciones.';
--    END IF;
--END $$;