-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙
-- Seed: 001_seed_users.sql
-- Purpose: Poblar tabla de usuarios con datos de prueba
-- Author: fisherk2
-- Version: 1.0
-- Date: 2026-03-13
-- Dependencies: 001_create_users_table.sql debe ser ejecutado primero
-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙

-- ■■■■■■■■■■■■■ Limpiar datos existentes de forma segura ■■■■■■■■■■■■■
-- TRUNCATE reinicia secuencias y es más eficiente que DELETE para tablas completas
TRUNCATE TABLE users RESTART IDENTITY CASCADE;

-- ■■■■■■■■■■■■■ Insertar usuarios de ejemplo con hashes de contraseña seguros ■■■■■■■■■■■■■
-- Usando ON CONFLICT DO NOTHING para idempotencia y evitar duplicados
INSERT INTO users (username, email, password_hash, first_name, last_name, phone, is_active, is_verified, created_at, updated_at) VALUES
-- Usuario administrador principal para testing de roles
('admin_user', 'admin.test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LrUpmX', 'Admin', 'Test', '+1234567890', true, true, NOW(), NOW()),

-- Usuario estándar para testing funcional básico
('john_doe', 'john.doe@example.com', '$2b$12$9XqYcWZqKdA8xKjNqQZ9eG5rT7zLmN8pQrS6tUvW3xYcZfRjHhKqX', 'John', 'Doe', '+1987654321', true, true, NOW(), NOW()),

-- Usuario inactivo para testing de soft delete
('jane_smith', 'jane.smith@example.com', '$2b$12$YzA1b2N3c4R5e6f7g8h9iJ0kL1mN2oP3qR4sT5uV6wX7yZ8a9b0cX', 'Jane', 'Smith', '+1122334455', false, false, NOW(), NOW()),

-- Usuario no verificado para testing de flujo de verificación
('mike_wilson', 'mike.wilson@example.com', '$2b$12$dE4f5g6h7iJ8kL9mN0oP1qR2sT3uV4wX5yZ6a7b8c9d0eF1g2h3i4j5', 'Mike', 'Wilson', '+1555666777', true, false, NOW(), NOW()),

-- Usuario premium para testing de features especiales
('sarah_jones', 'sarah.jones@example.com', '$2b$12$fG6h7iJ8kL9mN0oP1qR2sT3uV4wX5yZ6a7b8c9d0eF1g2h3i4j5k6l7', 'Sarah', 'Jones', '+1888999000', true, true, NOW(), NOW())
ON CONFLICT (username) DO NOTHING;

-- ■■■■■■■■■■■■■ Insertar usuarios adicionales para testing de carga y paginación ■■■■■■■■■■■■■
-- Usuarios con nombres genéricos para testing de búsqueda y ordenamiento
INSERT INTO users (username, email, password_hash, first_name, last_name, is_active, is_verified, created_at, updated_at) VALUES
('test_user_1', 'test.user1@example.com', '$2b$12$hI8j9kL0mN1oP2qR3sT4uV5wX6yZ7a8b9c0dE1f2g3h4i5j6k7l8m9', 'Test', 'User One', true, true, NOW(), NOW()),
('test_user_2', 'test.user2@example.com', '$2b$12$jK9l0mN1oP2qR3sT4uV5wX6yZ7a8b9c0dE1f2g3h4i5j6k7l8m9n0', 'Test', 'User Two', true, true, NOW(), NOW()),
('test_user_3', 'test.user3@example.com', '$2b$12$kL0mN1oP2qR3sT4uV5wX6yZ7a8b9c0dE1f2g3h4i5j6k7l8m9n0o1', 'Test', 'User Three', true, true, NOW(), NOW())
ON CONFLICT (username) DO NOTHING;

-- ■■■■■■■■■■■■■ Verificar inserción exitosa y proporcionar retroalimentación ■■■■■■■■■■■■■
DO $$
DECLARE
    user_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count FROM users;
    
    IF user_count > 0 THEN
        RAISE NOTICE 'Seed data inserted successfully. Total users: %', user_count;
    ELSE
        RAISE EXCEPTION 'Failed to insert seed data';
    END IF;
END $$;

--▁▂▃▄▅▆▇███████ Nota sobre passwords de ejemplo ███████▇▆▅▄▃▂▁ 

-- Los hashes son placeholder de bcrypt (60 caracteres mínimos)
-- En producción, generar hashes reales con: bcrypt.hashSync('password', 12)
-- Para testing, pueden usar passwords simples como: 'password123', 'admin123', etc.