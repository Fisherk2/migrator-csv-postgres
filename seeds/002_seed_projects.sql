-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙
-- Seed: 002_seed_projects.sql
-- Purpose: Poblar tabla de proyectos con datos de prueba
-- Author: fisherk2
-- Version: 1.0
-- Date: 2026-03-13
-- Dependencies: 001_create_projects_table.sql y 001_seed_users.sql deben ser ejecutados primero
-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙

-- ■■■■■■■■■■■■■ Limpiar datos existentes de forma segura ■■■■■■■■■■■■■
-- TRUNCATE reinicia secuencias y respeta integridad referencial con CASCADE
TRUNCATE TABLE projects RESTART IDENTITY CASCADE;

-- ■■■■■■■■■■■■■ Insertar proyectos de ejemplo para usuarios existentes ■■■■■■■■■■■■■
-- Usando subqueries para obtener user_id válidos de la tabla users
-- Usando ON CONFLICT DO NOTHING para idempotencia y evitar duplicados
INSERT INTO projects (name, description, code, user_id, status, priority, start_date, end_date, budget, created_at, updated_at) VALUES
-- Proyectos para admin_user (ID: 1) - Usuario administrador
('Website Redesign', 'Complete redesign of company website with modern UI/UX', 'WEB001', 
 (SELECT id FROM users WHERE username = 'admin_user' LIMIT 1), 'active', 'high', 
 '2024-01-15', '2024-03-30', 25000.00, NOW(), NOW()),
('Database Migration', 'Migrate legacy database to PostgreSQL with zero downtime', 'DB001', 
 (SELECT id FROM users WHERE username = 'admin_user' LIMIT 1), 'completed', 'critical', 
 '2024-02-01', '2024-02-28', 15000.00, NOW(), NOW()),
-- Proyectos para john_doe (ID: 2) - Usuario estándar
('Mobile App Development', 'Develop cross-platform mobile application', 'MOB001', 
 (SELECT id FROM users WHERE username = 'john_doe' LIMIT 1), 'active', 'medium', 
 '2024-03-01', '2024-06-30', 45000.00, NOW(), NOW()),
('API Integration', 'Integrate third-party payment processing APIs', 'API001', 
 (SELECT id FROM users WHERE username = 'john_doe' LIMIT 1), 'active', 'low', 
 '2024-03-15', '2024-04-15', 8000.00, NOW(), NOW()),
-- Proyectos para jane_smith (ID: 3) - Usuario inactivo (proyectos cancelados)
('Social Media Campaign', 'Launch comprehensive social media marketing campaign', 'SOC001', 
 (SELECT id FROM users WHERE username = 'jane_smith' LIMIT 1), 'cancelled', 'medium', 
 '2024-01-10', '2024-03-10', 12000.00, NOW(), NOW()),
-- Proyectos para mike_wilson (ID: 4) - Usuario no verificado
('Security Audit', 'Comprehensive security audit and vulnerability assessment', 'SEC001', 
 (SELECT id FROM users WHERE username = 'mike_wilson' LIMIT 1), 'active', 'high', 
 '2024-02-15', '2024-03-15', 18000.00, NOW(), NOW()),
-- Proyectos para sarah_jones (ID: 5) - Usuario premium
('E-commerce Platform', 'Build full-featured e-commerce platform', 'ECOM001', 
 (SELECT id FROM users WHERE username = 'sarah_jones' LIMIT 1), 'active', 'critical', 
 '2024-01-20', '2024-05-30', 75000.00, NOW(), NOW()),
('Cloud Infrastructure', 'Migrate infrastructure to cloud services', 'CLOUD001', 
 (SELECT id FROM users WHERE username = 'sarah_jones' LIMIT 1), 'on_hold', 'high', 
 '2024-04-01', '2024-06-30', 35000.00, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ■■■■■■■■■■■■■ Insertar proyectos adicionales para testing de carga y paginación ■■■■■■■■■■■■■
-- Proyectos para usuarios genéricos de testing
INSERT INTO projects (name, description, user_id, status, priority, budget, created_at, updated_at) VALUES
('Test Project Alpha', 'Testing project for load testing', 
 (SELECT id FROM users WHERE username = 'test_user_1' LIMIT 1), 'active', 'low', 5000.00, NOW(), NOW()),
('Test Project Beta', 'Testing project for pagination testing', 
 (SELECT id FROM users WHERE username = 'test_user_2' LIMIT 1), 'completed', 'medium', 7500.00, NOW(), NOW()),
('Test Project Gamma', 'Testing project for search functionality', 
 (SELECT id FROM users WHERE username = 'test_user_3' LIMIT 1), 'active', 'high', 10000.00, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ■■■■■■■■■■■■■ Verificar inserción exitosa y validar integridad referencial ■■■■■■■■■■■■■
DO $$
DECLARE
    project_count INTEGER;
    orphaned_projects INTEGER;
BEGIN
    -- Contar proyectos insertados
    SELECT COUNT(*) INTO project_count FROM projects;
    
    -- Verificar que no haya proyectos huérfanos (sin user_id válido)
    SELECT COUNT(*) INTO orphaned_projects 
    FROM projects p 
    LEFT JOIN users u ON p.user_id = u.id 
    WHERE u.id IS NULL;
    IF project_count > 0 AND orphaned_projects = 0 THEN
        RAISE NOTICE 'Seed data inserted successfully. Total projects: % (no orphaned records)', project_count;
    ELSIF orphaned_projects > 0 THEN
        RAISE EXCEPTION 'Found % orphaned projects (invalid user_id)', orphaned_projects;
    ELSE
        RAISE EXCEPTION 'Failed to insert seed data';
    END IF;
END $$;

--▁▂▃▄▅▆▇███████ Nota sobre integridad referencial ███████▇▆▅▄▃▂▁
-- Los user_id se obtienen dinámicamente de la tabla users para garantizar FK válidas
-- Si el seed de users no se ejecuta primero, este script fallará (comportamiento esperado)
-- Los códigos de proyecto son únicos para testing de conflictos ON CONFLICT