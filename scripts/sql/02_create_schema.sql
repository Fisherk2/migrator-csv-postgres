-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙
-- Esquema E-commerce: Migrador CSV - PostgreSQL
-- Purpose: Crear el esquema de tablas para el dominio e-commerce
-- Author: fisherk2
-- Version: 1.0
-- Date: 2026-04-16
-- 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- TABLA: CUSTOMERS
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
CREATE TABLE IF NOT EXISTS public.customers (
    -- Identificador único autoincremental
    id SERIAL PRIMARY KEY,
    
    -- Nombre completo del cliente (obligatorio)
    name VARCHAR(100) NOT NULL,
    
    -- Email único para login y comunicaciones
    email VARCHAR(255) NOT NULL UNIQUE,
    
    -- Teléfono opcional para contacto
    phone VARCHAR(20),
    
    -- Timestamp de creación automático
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Timestamp de última modificación
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comentarios de negocio para customers
COMMENT ON TABLE public.customers IS 'Entidad principal de clientes del e-commerce';
COMMENT ON COLUMN public.customers.id IS 'Identificador único autoincremental';
COMMENT ON COLUMN public.customers.name IS 'Nombre completo requerido para facturación';
COMMENT ON COLUMN public.customers.email IS 'Email único, usado como login principal';
COMMENT ON COLUMN public.customers.phone IS 'Teléfono opcional para contacto y soporte';
COMMENT ON COLUMN public.customers.created_at IS 'Fecha de registro automática';
COMMENT ON COLUMN public.customers.updated_at IS 'Última modificación del registro';

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- TABLA: PRODUCTS
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
CREATE TABLE IF NOT EXISTS public.products (
    -- Identificador único autoincremental
    id SERIAL PRIMARY KEY,
    
    -- Nombre del producto (obligatorio, visible en catálogo)
    name VARCHAR(200) NOT NULL,
    
    -- Descripción detallada para página de producto
    description TEXT,
    
    -- Precio unitario con validación de no negativos
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    
    -- Cantidad disponible en inventario
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    
    -- Estado del producto (activo/inactivo)
    is_active BOOLEAN DEFAULT true
);

-- Comentarios de negocio para products
COMMENT ON TABLE public.products IS 'Catálogo de productos del e-commerce';
COMMENT ON COLUMN public.products.id IS 'Identificador único del producto';
COMMENT ON COLUMN public.products.name IS 'Nombre visible en catálogo y búsquedas';
COMMENT ON COLUMN public.products.description IS 'Detalles para página de producto';
COMMENT ON COLUMN public.products.price IS 'Precio unitario en moneda local';
COMMENT ON COLUMN public.products.stock_quantity IS 'Unidades disponibles para venta';
COMMENT ON COLUMN public.products.is_active IS 'Producto visible/oculto en catálogo';

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- TABLA: ORDERS
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
CREATE TABLE IF NOT EXISTS public.orders (
    -- Identificador único autoincremental
    id SERIAL PRIMARY KEY,
    
    -- Referencia al cliente que realizó la orden
    customer_id INTEGER NOT NULL,
    
    -- Fecha de la orden (default: hoy)
    order_date DATE DEFAULT CURRENT_DATE,
    
    -- Total de la orden con validación de no negativos
    total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
    
    -- Estado del proceso de la orden
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    -- Constraint de FK para integridad referencial
    CONSTRAINT fk_orders_customer 
        FOREIGN KEY (customer_id) 
        REFERENCES public.customers(id) 
        ON DELETE RESTRICT
);

-- Constraint para valores válidos de status
ALTER TABLE public.orders 
ADD CONSTRAINT chk_orders_status 
CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled'));

-- Comentarios de negocio para orders
COMMENT ON TABLE public.orders IS 'Órdenes de compra del e-commerce';
COMMENT ON COLUMN public.orders.id IS 'Identificador único de la orden';
COMMENT ON COLUMN public.orders.customer_id IS 'Cliente que realizó la compra';
COMMENT ON COLUMN public.orders.order_date IS 'Fecha en que se realizó la orden';
COMMENT ON COLUMN public.orders.total_amount IS 'Monto total de la orden';
COMMENT ON COLUMN public.orders.status IS 'Estado actual del proceso';
COMMENT ON CONSTRAINT fk_orders_customer ON public.orders IS 'Protege historial de órdenes contra eliminación de clientes';
COMMENT ON CONSTRAINT chk_orders_status ON public.orders IS 'Solo permite estados válidos del proceso';

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- ÍNDICES BÁSICOS (performance)
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- Índice para búsquedas por email (login)
CREATE INDEX IF NOT EXISTS idx_customers_email ON public.customers(email);

-- Índice para búsquedas de productos activos
CREATE INDEX IF NOT EXISTS idx_products_active ON public.products(is_active) WHERE is_active = true;

-- Índice para consultas de órdenes por cliente
CREATE INDEX IF NOT EXISTS idx_orders_customer ON public.orders(customer_id);

-- Índice para consultas de órdenes por estado
CREATE INDEX IF NOT EXISTS idx_orders_status ON public.orders(status);

-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- TRIGGER PARA updated_at (customers)
-- ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
-- Función para actualizar timestamp automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para customers.updated_at
CREATE TRIGGER update_customers_updated_at 
    BEFORE UPDATE ON public.customers 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();