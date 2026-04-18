-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- Índices Estratégicos: Migrador CSV - PostgreSQL
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- Optimización para queries frecuentes del MVP
-- Ejecutar después de 02_create_schema.sql
-- Compatible con PostgreSQL 12+

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- ÍNDICES PARA FOREIGN KEYS
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

-- Índice para FK orders.customer_id (joins y validaciones)
CREATE INDEX IF NOT EXISTS idx_orders_customer_id_fk 
ON public.orders(customer_id);

-- PROPÓSITO: Acelerar joins orders-customers y validaciones de FK
-- QUERY ESPERADA: SELECT o.*, c.name FROM orders o JOIN customers c ON o.customer_id = c.id
-- COSTO DE ESCRITURA: Bajo (solo afecta inserts/updates en orders)

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- ÍNDICES PARA BÚSQUEDAS ÚNICAS
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

-- NOTA: customers.email ya tiene índice UNIQUE implícito por constraint
-- No se crea índice adicional para evitar duplicidad

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- ÍNDICES PARCIALES (FILTROS FRECUENTES)
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

-- Índice parcial para productos activos (catálogo)
CREATE INDEX IF NOT EXISTS idx_products_active_partial 
ON public.products(id) 
WHERE is_active = true;

-- PROPÓSITO: Optimizar catálogo de productos disponibles
-- QUERY ESPERADA: SELECT * FROM products WHERE is_active = true
-- COSTO DE ESCRITURA: Bajo (solo productos activos)

-- Índice parcial para órdenes pendientes (procesamiento)
CREATE INDEX IF NOT EXISTS idx_orders_pending_partial 
ON public.orders(id, customer_id, total_amount) 
WHERE status = 'pending';

-- PROPÓSITO: Optimizar procesamiento de órdenes pendientes
-- QUERY ESPERADA: SELECT * FROM orders WHERE status = 'pending' ORDER BY id
-- COSTO DE ESCRITURA: Medio (afecta cambios de status)

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- ÍNDICES COMPUESTOS (REPORTING)
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

-- Índice compuesto para reporting de órdenes por fecha y estado
CREATE INDEX IF NOT EXISTS idx_orders_date_status_compound 
ON public.orders(order_date, status, total_amount);

-- PROPÓSITO: Optimizar reportes diarios y filtrado por estado
-- QUERY ESPERADA: SELECT status, COUNT(*), SUM(total_amount) FROM orders WHERE order_date >= '2024-01-01' GROUP BY status
-- COSTO DE ESCRITURA: Medio (afecta todas las órdenes nuevas)

-- Índice compuesto para búsquedas de productos por precio y stock
CREATE INDEX IF NOT EXISTS idx_products_price_stock_compound 
ON public.products(price, stock_quantity) 
WHERE is_active = true;

-- PROPÓSITO: Optimizar filtros de rango de precio y disponibilidad
-- QUERY ESPERADA: SELECT * FROM products WHERE price BETWEEN 10 AND 100 AND stock_quantity > 0
-- COSTO DE ESCRITURA: Medio (solo productos activos)

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- ÍNDICES PARA VALIDACIÓN DE DOMINIO
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

-- Índice para detección de duplicados en migración (email)
-- NOTA: Ya existe como UNIQUE constraint, no se duplica

-- Índice para validación de rangos (price >= 0)
-- NOTA: CHECK constraints no necesitan índices adicionales

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- ESTADÍSTICAS Y MONITOREO
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

-- Actualizar estadísticas para optimizador de queries
ANALYZE public.customers;
ANALYZE public.products;
ANALYZE public.orders;

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- NOTAS DE PERFORMANCE
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- 1. Los índices parciales reducen espacio y mejoran scans para filtros comunes
-- 2. Índices compuestos optimizan queries ORDER BY sin sorting extra
-- 3. Se evita duplicar índices UNIQUE existentes
-- 4. ANALYZE asegura que el optimizador tenga estadísticas actualizadas