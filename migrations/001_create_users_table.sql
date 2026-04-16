-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙
-- Migration: 001_create_users_table.sql
-- Purpose: Crear tablas de usuarios con sus index, triggers y constraints
-- Author: fisherk2
-- Version: 1.0
-- Date: 2026-03-13
-- Dependencies: create_database.sql debe ser ejecutado primero
-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙

-- ■■■■■■■■■■■■■ Conectar a la base de datos ■■■■■■■■■■■■■
\c your_database_name

-- ■■■■■■■■■■■■■ Crear tabla de usuarios ■■■■■■■■■■■■■
-- Usar SERIAL para autoincrementar la llave primaria
CREATE TABLE IF NOT EXISTS users (
    -- Identificador de la llave primaria
    id SERIAL PRIMARY KEY,
    
    -- Campos de autenticación del usuario
    username VARCHAR(50) NOT NULL UNIQUE,  -- Nombre de usuario único para login
    email VARCHAR(255) NOT NULL UNIQUE,     -- Email para autenticación y notificaciones
    password_hash VARCHAR(255) NOT NULL,     -- Contraseña hasheada (255 caracteres para bcrypt/argon2)
    
    -- Información del perfil del usuario
    first_name VARCHAR(100),                -- Nombre del usuario
    last_name VARCHAR(100),                 -- Apellido del usuario
    phone VARCHAR(20),                      -- Teléfono de contacto opcional
    
    -- Gestión de estado y rol del usuario
    is_active BOOLEAN DEFAULT true,         -- Estado de cuenta para soft delete/suspensión
    is_verified BOOLEAN DEFAULT false,      -- Estado de verificación de email
    role_id INTEGER,                        -- Clave foránea a tabla roles (futura migración)
    
    -- Timestamps para auditoría
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- Timestamp de creación del registro
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- Timestamp de última modificación
    last_login_at TIMESTAMP WITH TIME ZONE,            -- Timestamp del último login exitoso
    
    -- Restricciones para integridad de datos
    CONSTRAINT users_username_length CHECK (LENGTH(username) >= 3),
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT users_password_hash_length CHECK (LENGTH(password_hash) >= 60)  -- Mínimo para bcrypt
);

-- ■■■■■■■■■■■■■ Agregar comentarios para documentación en catálogo de PostgreSQL ■■■■■■■■■■■■■
COMMENT ON TABLE users IS 'Tabla principal de gestión de usuarios almacenando información de autenticación y perfil';
COMMENT ON COLUMN users.id IS 'Identificador primario de registros de usuario';
COMMENT ON COLUMN users.username IS 'Nombre de usuario único para login del sistema (3-50 caracteres)';
COMMENT ON COLUMN users.email IS 'Dirección email única para autenticación y notificaciones';
COMMENT ON COLUMN users.password_hash IS 'Contraseña hasheada usando bcrypt/argon2 (mínimo 60 caracteres)';
COMMENT ON COLUMN users.first_name IS 'Nombre del usuario (opcional para completar perfil)';
COMMENT ON COLUMN users.last_name IS 'Apellido del usuario (opcional para completar perfil)';
COMMENT ON COLUMN users.phone IS 'Número de teléfono de contacto opcional para verificación';
COMMENT ON COLUMN users.is_active IS 'Flag de estado de cuenta para soft delete y suspensión';
COMMENT ON COLUMN users.is_verified IS 'Estado de verificación de email para cumplimiento de seguridad';
COMMENT ON COLUMN users.role_id IS 'Referencia de clave foránea a tabla roles (para agregar en futura migración)';
COMMENT ON COLUMN users.created_at IS 'Timestamp cuando se creó el registro de usuario (UTC)';
COMMENT ON COLUMN users.updated_at IS 'Timestamp cuando se modificó por última vez el registro de usuario (UTC)';
COMMENT ON COLUMN users.last_login_at IS 'Timestamp del último login exitoso para auditoría';

-- ■■■■■■■■■■■■■ Crear índices para optimización de rendimiento ■■■■■■■■■■■■■
-- Índice único en email para búsquedas rápidas de autenticación
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Índice en username para rendimiento adicional de autenticación
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Índice en is_active para filtrar usuarios activos en consultas
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Índice en created_at para ordenamiento y reportes
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- ■■■■■■■■■■■■■ Crear trigger para timestamp automático de updated_at ■■■■■■■■■■■■■
-- Esto asegura que updated_at siempre esté actualizado cuando se modifican registros
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 
-- ■■■■■■■■■■■■■ Crear trigger para actualizar timestamp (manejando existencia) ■■■■■■■■■■■■■
DROP TRIGGER IF EXISTS trigger_users_updated_at ON users;
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ■■■■■■■■■■■■■ Proporcionar retroalimentación para migración exitosa ■■■■■■■■■■■■■
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        RAISE NOTICE 'Tabla users creada exitosamente con índices y triggers';
    ELSE
        RAISE EXCEPTION 'Falló la creación de la tabla users';
    END IF;
END $$;