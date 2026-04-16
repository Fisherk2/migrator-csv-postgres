-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙
-- Migration: 002_create_projects_table.sql
-- Purpose: Crear tabla de proyectos referenciando a la tabla de usuarios
-- Author: fisherk2
-- Version: 1.0
-- Date: 2026-03-13
-- Dependencies: 001_create_users_table.sql debe ser ejecutado primero
-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙

-- ■■■■■■■■■■■■■ Crear tabla de proyectos ■■■■■■■■■■■■■
-- Usando SERIAL para auto-incrementar la llave primaria siguiendo las convenciones del equipo

CREATE TABLE IF NOT EXISTS projects (
    -- Identificador de llave primaria
    id SERIAL PRIMARY KEY,
    
    -- Campos de identificación del proyecto
    name VARCHAR(100) NOT NULL,             -- Nombre del proyecto para identificación
    description TEXT,                       -- Descripción detallada del proyecto
    code VARCHAR(20) UNIQUE,                -- Código único del proyecto para referencia
    
    -- Relación con tabla users (propietario)
    user_id INTEGER NOT NULL,               -- Clave foránea a users.id (propietario del proyecto)
    
    -- Estado y metadatos del proyecto
    status VARCHAR(20) DEFAULT 'active',    -- Estado del proyecto (active, completed, cancelled)
    priority VARCHAR(10) DEFAULT 'medium',  -- Prioridad del proyecto (low, medium, high)
    start_date DATE,                        -- Fecha de inicio del proyecto
    end_date DATE,                          -- Fecha de finalización del proyecto
    budget DECIMAL(12, 2),                  -- Presupuesto del proyecto (decimal para precisión)
    
    -- Timestamps para auditoría
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- Timestamp de creación del registro
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- Timestamp de última modificación
    
    -- Restricciones para integridad de datos
    CONSTRAINT projects_name_length CHECK (LENGTH(name) >= 3),
    CONSTRAINT projects_status_valid CHECK (status IN ('active', 'completed', 'cancelled', 'on_hold')),
    CONSTRAINT projects_priority_valid CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT projects_date_order CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date),
    CONSTRAINT projects_budget_positive CHECK (budget IS NULL OR budget >= 0),
    
    -- Restricción de clave foránea con acciones en cascada
    CONSTRAINT fk_projects_users 
        FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);

-- ■■■■■■■■■■■■■ Agregar comentarios para documentación en catálogo de PostgreSQL ■■■■■■■■■■■■■
COMMENT ON TABLE projects IS 'Tabla de gestión de proyectos con relación de propietario a usuarios';
COMMENT ON COLUMN projects.id IS 'Identificador primario de registros de proyecto';
COMMENT ON COLUMN projects.name IS 'Nombre del proyecto para identificación (mínimo 3 caracteres)';
COMMENT ON COLUMN projects.description IS 'Descripción detallada del proyecto y sus objetivos';
COMMENT ON COLUMN projects.code IS 'Código único del proyecto para referencia interna';
COMMENT ON COLUMN projects.user_id IS 'ID del usuario propietario del proyecto (relación con users.id)';
COMMENT ON COLUMN projects.status IS 'Estado del proyecto (active, completed, cancelled, on_hold)';
COMMENT ON COLUMN projects.priority IS 'Prioridad del proyecto (low, medium, high, critical)';
COMMENT ON COLUMN projects.start_date IS 'Fecha de inicio planificada del proyecto';
COMMENT ON COLUMN projects.end_date IS 'Fecha de finalización planificada del proyecto';
COMMENT ON COLUMN projects.budget IS 'Presupuesto del proyecto con precisión decimal';
COMMENT ON COLUMN projects.created_at IS 'Timestamp cuando se creó el registro de proyecto (UTC)';
COMMENT ON COLUMN projects.updated_at IS 'Timestamp cuando se modificó por última vez el registro de proyecto (UTC)';

-- ■■■■■■■■■■■■■ Crear índices para optimización de rendimiento ■■■■■■■■■■■■■
-- Índice en user_id para consultas rápidas por propietario del proyecto
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);

-- Índice en status para filtrar proyectos por estado
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- Índice en priority para filtrar por importancia
CREATE INDEX IF NOT EXISTS idx_projects_priority ON projects(priority);

-- Índice en created_at para ordenamiento y reportes
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);

-- Índice en name para funcionalidad de búsqueda
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);

-- ■■■■■■■■■■■■■ Reutilizar la función trigger existente para timestamp updated_at ■■■■■■■■■■■■■
-- Esto asegura que updated_at siempre esté actualizado cuando se modifican registros
-- Crear trigger para actualizar timestamp (manejando existencia)
DROP TRIGGER IF EXISTS trigger_projects_updated_at ON projects;
CREATE TRIGGER trigger_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ■■■■■■■■■■■■■ Proporcionar retroalimentación para migración exitosa ■■■■■■■■■■■■■
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'projects') THEN
        RAISE NOTICE 'Tabla projects creada exitosamente con índices, triggers y foreign key a users';
    ELSE
        RAISE EXCEPTION 'Falló la creación de la tabla projects';
    END IF;
END $$;