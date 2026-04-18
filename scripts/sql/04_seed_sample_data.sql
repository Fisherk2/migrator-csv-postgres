-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- Datos de Prueba: Migrador CSV - PostgreSQL
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- Dataset realista para smoke tests y validación
-- Ejecutar después de 03_create_indexes.sql
-- Compatible con PostgreSQL 12+

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- TRANSACCIÓN PRINCIPAL (ATÓMICA)
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
BEGIN;

-- Limpieza segura previa (respeta constraints FK)
TRUNCATE TABLE orders, products, customers RESTART IDENTITY CASCADE;

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- CLIENTES (5 registros)
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

-- PROPÓSITO DE PRUEBA: Emails válidos y únicos para validación de formato RFC 5322
INSERT INTO public.customers (name, email, phone) VALUES
('Ana María García', 'ana.garcia@example.com', '+52-55-1234-5678'),
('Carlos Rodríguez López', 'carlos.rod@example.com', '+1-212-555-0123'),
('María Fernanda Silva', 'maria.silva@example.com', '+34-91-876-5432'),
('José Antonio Martínez', 'jose.martinez@example.com', '+52-33-9876-5432'),
('Laura Patricia Hernández', 'laura.hernandez@example.com', '+1-305-456-7890');

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- PRODUCTOS (5 registros)
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

-- PROPÓSITO DE PRUEBA: Precios positivos y stock >= 0 para validación de CHECK constraints
INSERT INTO public.products (name, description, price, stock_quantity, is_active) VALUES
('Laptop Pro 15"', 'Laptop de alto rendimiento para desarrollo', 1599.99, 25, true),
('Mouse Inalámbrico', 'Mouse ergonómico recargable USB-C', 29.99, 150, true),
('Monitor 4K 27"', 'Monitor IPS con HDR y USB-C', 499.99, 12, true),
('Teclado Mecánico', 'Teclado RGB switch blue, español', 89.99, 45, true),
('Webcam HD 1080p', 'Webcam con micrófono integrado', 49.99, 0, false);

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- ÓRDENES (5 registros)
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

-- PROPÓSITO DE PRUEBA: Integridad referencial y estados válidos del ciclo de vida
INSERT INTO public.orders (customer_id, order_date, total_amount, status) VALUES
-- Órden 1: Cliente 1, productos múltiples, completada
(1, '2024-01-15', 1729.98, 'completed'),

-- Órden 2: Cliente 2, producto simple, pendiente
(2, '2024-01-20', 499.99, 'pending'),

-- Órden 3: Cliente 3, combo productos, en procesamiento
(3, '2024-01-22', 639.97, 'processing'),

-- Órden 4: Cliente 4, producto agotado, cancelada
(4, '2024-01-25', 49.99, 'cancelled'),

-- Órden 5: Cliente 5, compra reciente, shipped
(5, '2024-01-28', 1689.98, 'shipped');

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- ESTADÍSTICAS DE DATOS TEMPORALES (antes de limpieza)
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
SELECT 'customers' as table_name, COUNT(*) as record_count FROM public.customers
UNION ALL
SELECT 'products', COUNT(*) FROM public.products
UNION ALL
SELECT 'orders', COUNT(*) FROM public.orders;

COMMIT;

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- VERIFICACIÓN FINAL Y LIMPIEZA AUTOMÁTICA
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

-- Mostrar resultados de integridad y estadísticas antes de limpiar
\echo '=== VERIFICACIÓN DE INTEGRIDAD REFERENCIAL ==='
SELECT 
    o.id as order_id,
    o.customer_id,
    c.name as customer_name,
    o.status,
    o.total_amount
FROM public.orders o
JOIN public.customers c ON o.customer_id = c.id
ORDER BY o.id;

\echo '=== VALIDACIÓN DE REGLAS DE NEGOCIO ==='
SELECT 
    p.id,
    p.name,
    p.price,
    p.stock_quantity,
    p.is_active,
    CASE 
        WHEN p.price < 0 THEN 'ERROR: Precio negativo'
        WHEN p.stock_quantity < 0 THEN 'ERROR: Stock negativo'
        ELSE 'OK'
    END as validation
FROM public.products p
ORDER BY p.id;

\echo '=== ESTADÍSTICAS DE DATOS TEMPORALES ==='
SELECT 'customers' as table_name, COUNT(*) as record_count FROM public.customers
UNION ALL
SELECT 'products', COUNT(*) FROM public.products
UNION ALL
SELECT 'orders', COUNT(*) FROM public.orders;

\echo '=== LIMPIEZA AUTOMÁTICA: VOLVIENDO A ESTADO VACÍO ==='
TRUNCATE TABLE orders, products, customers RESTART IDENTITY CASCADE;

\echo '=== VERIFICACIÓN DE LIMPIEZA ==='
SELECT 'customers' as table_name, COUNT(*) as record_count FROM public.customers
UNION ALL
SELECT 'products', COUNT(*) FROM public.products
UNION ALL
SELECT 'orders', COUNT(*) FROM public.orders;

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- NOTAS DE TESTING
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- 1. Los emails son únicos y válidos para probar constraint UNIQUE
-- 2. Los teléfonos usan formatos internacionales (+código-área-número)
-- 3. Los precios usan 2 decimales y respetan CHECK (price >= 0)
-- 4. El stock incluye un producto agotado (id=5, stock=0) para testing de is_active=false
-- 5. Los estados de órden cubren el ciclo completo del e-commerce
-- 6. La transacción garantiza atomicidad: todo o nada se inserta