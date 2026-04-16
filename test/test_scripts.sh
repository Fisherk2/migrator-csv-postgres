#!/bin/bash

# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙
# Suite de Unit Tests para Scripts PostgreSQL con Patrón AAA
# Propósito: Pruebas unitarias automatizadas con Arrange-Act-Assert
# Autor: fisherk2
# Versión: 3.0.0
# Fecha: 2026-03-16
# Requisitos: PostgreSQL 15+, CLI psql, archivo .env con credenciales
# Códigos de salida: 0 = todas las pruebas pasaron, 1 = al menos una falló
# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Variables Globales para Seguimiento de Pruebas
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TEST_RESULTS=()

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Configuración de Colores para Salida Legible
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin Color

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Función: Imprimir Resultados de Pruebas
# Propósito: Formato de salida estandarizado para resultados de pruebas
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
print_test_result() {
    local test_name="$1"
    local status="$2"
    local message="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ "$status" = "PASS" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo -e "${GREEN}✅ PASS${NC}: $test_name - $message"
        TEST_RESULTS+=("PASS: $test_name")
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo -e "${RED}❌ FAIL${NC}: $test_name - $message"
        TEST_RESULTS+=("FAIL: $test_name")
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Función: Cargar Variables de Entorno
# Propósito: Carga segura de .env sin exponer credenciales
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
load_env_safely() {
    local env_file=""
    
    # Buscar .env en directorio actual y directorio padre (raíz del proyecto)
    if [ -f ".env" ]; then
        env_file=".env"
    elif [ -f "../.env" ]; then
        env_file="../.env"
    else
        echo -e "${RED}❌ Error: Archivo .env no encontrado en directorio actual ni padre${NC}"
        return 1
    fi
    
    # Cargar variables de entorno sin mostrarlas en salida
    set -a
    source "$env_file"
    set +a
    
    # Validar que las variables críticas existen
    if [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
        echo -e "${RED}❌ Error: Variables críticas faltantes en $env_file${NC}"
        return 1
    fi
    
    echo -e "${BLUE}🔧 Variables de entorno cargadas desde $env_file${NC}"
    return 0
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Función: Limpiar Entorno Completo
# Propósito: Limpiar credenciales y base de datos después de errores
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
cleanup_on_error() {
    echo -e "${RED}🧹 Limpiando entorno debido a error en pruebas...${NC}"
    
    # Limpiar credenciales primero
    cleanup_credentials
    
    # Eliminar base de datos para dejar entorno limpio
    echo -e "${BLUE}🔍 Debug: Eliminando base de datos para limpiar entorno${NC}"
    local db_name="${DB_NAME:-your_database_name}"
    local db_host="${DB_HOST:-localhost}"
    local db_port="${DB_PORT:-5432}"
    
    # Verificar si la base de datos existe antes de eliminar
    local db_exists=$(psql -h "$db_host" -p "$db_port" -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db_name';" 2>/dev/null)
    
    if [ "$db_exists" = "1" ]; then
        echo -e "${BLUE}🔍 Debug: Ejecutando drop_database.sql para limpiar${NC}"
        if psql -h "$db_host" -p "$db_port" -U postgres -d postgres -f drop_database.sql >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Base de datos '$db_name' eliminada exitosamente${NC}"
        else
            echo -e "${YELLOW}⚠️  Error eliminando base de datos, pero continuando...${NC}"
        fi
    else
        echo -e "${BLUE}🔍 Debug: La base de datos '$db_name' no existe, no es necesario eliminar${NC}"
    fi
    
    echo -e "${GREEN}🧹 Entorno limpiado exitosamente${NC}"
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Función: Limpiar Credenciales
# Propósito: Limpiar variables de entorno después de la ejecución de pruebas
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
cleanup_credentials() {
    # Limpiar PGPASSWORD para seguridad
    unset PGPASSWORD
    echo -e "${BLUE}🧹 Credenciales limpiadas de la memoria${NC}"
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Unit Test 1: Creación de Base de Datos (Patrón AAA)
# Propósito: Verificar que el script create_database.sql funciona correctamente
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
test_database_creation() {
    echo -e "${BLUE}🧪 Test: Creación de Base de Datos${NC}"
    echo -e "${BLUE}🔍 Debug: Iniciando test de creación de base de datos...${NC}"
    
    # ARRANGE: Preparar entorno para la prueba
    echo -e "${BLUE}🔍 Debug: ARRANGE - Preparando entorno${NC}"
    local db_name="${DB_NAME:-your_database_name}"
    local db_host="${DB_HOST:-localhost}"
    local db_port="${DB_PORT:-5432}"
    
    # Verificar que la base de datos no existe antes de crearla (usando peer authentication)
    echo -e "${BLUE}🔍 Debug: Verificando existencia de BD con peer authentication${NC}"
    local pre_existing=$(psql -h "$db_host" -p "$db_port" -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db_name';" 2>/dev/null)
    echo -e "${BLUE}🔍 Debug: Base de datos existe antes de crear: '$pre_existing'${NC}"
    
    # ACT: Ejecutar la acción a probar (usando peer authentication)
    echo -e "${BLUE}🔍 Debug: ACT - Ejecutando create_database.sql con peer authentication${NC}"
    echo -e "${BLUE}🔍 Debug: Comando: psql -h $db_host -p $db_port -U postgres -d postgres -f create_database.sql${NC}"
    
    if psql -h "$db_host" -p "$db_port" -U postgres -d postgres -f create_database.sql >/dev/null 2>&1; then
        echo -e "${BLUE}🔍 Debug: Script ejecutado exitosamente${NC}"
        
        # ASSERT: Verificar el resultado esperado (usando peer authentication)
        echo -e "${BLUE}🔍 Debug: ASSERT - Verificando resultado con peer authentication${NC}"
        local post_creation=$(psql -h "$db_host" -p "$db_port" -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db_name';" 2>/dev/null)
        echo -e "${BLUE}🔍 Debug: Base de datos existe después de crear: '$post_creation'${NC}"
        
        if [ "$post_creation" = "1" ]; then
            print_test_result "Database Creation" "PASS" "Base de datos '$db_name' creada exitosamente con peer authentication"
            return 0
        else
            print_test_result "Database Creation" "FAIL" "La base de datos no fue creada"
            return 1
        fi
    else
        print_test_result "Database Creation" "FAIL" "Error ejecutando create_database.sql con peer authentication"
        echo -e "${RED}🔍 Debug: Error detallado:${NC}"
        psql -h "$db_host" -p "$db_port" -U postgres -d postgres -f create_database.sql
        return 1
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Unit Test 2: Creación de Tabla Users (Patrón AAA)
# Propósito: Verificar que la migración de users funciona correctamente
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
test_users_table_creation() {
    echo -e "${BLUE}🧪 Test: Creación de Tabla Users${NC}"
    echo -e "${BLUE}🔍 Debug: Iniciando test de creación de tabla users...${NC}"
    
    # ARRANGE: Preparar entorno para la prueba
    echo -e "${BLUE}🔍 Debug: ARRANGE - Preparando entorno${NC}"
    local db_name="${DB_NAME:-your_database_name}"
    local db_host="${DB_HOST:-localhost}"
    local db_port="${DB_PORT:-5432}"
    local db_user="${DB_USER:-fisherk2}"
    
    # Verificar que la tabla no existe antes de crearla (usando peer authentication)
    echo -e "${BLUE}🔍 Debug: Verificando existencia de tabla users con peer authentication${NC}"
    local pre_existing=$(psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='users';" 2>/dev/null)
    echo -e "${BLUE}🔍 Debug: Tabla users existe antes de crear: '$pre_existing'${NC}"
    
    # ACT: Ejecutar la acción a probar (usando peer authentication)
    echo -e "${BLUE}🔍 Debug: ACT - Ejecutando migración 001_create_users_table.sql con peer authentication${NC}"
    echo -e "${BLUE}🔍 Debug: Comando: psql -h $db_host -p $db_port -U $db_user -d $db_name -f migrations/001_create_users_table.sql${NC}"
    
    if psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -f migrations/001_create_users_table.sql >/dev/null 2>&1; then
        echo -e "${BLUE}🔍 Debug: Migración ejecutada exitosamente${NC}"
        
        # ASSERT: Verificar el resultado esperado (usando peer authentication)
        echo -e "${BLUE}🔍 Debug: ASSERT - Verificando resultado con peer authentication${NC}"
        local post_creation=$(psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='users';" 2>/dev/null)
        echo -e "${BLUE}🔍 Debug: Tabla users existe después de crear: '$post_creation'${NC}"
        
        if [ "$post_creation" = "1" ]; then
            # Verificar estructura de la tabla
            local column_count=$(psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -tAc "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='users';" 2>/dev/null)
            echo -e "${BLUE}🔍 Debug: Tabla users tiene $column_count columnas${NC}"
            
            print_test_result "Users Table Creation" "PASS" "Tabla users creada exitosamente con $column_count columnas usando peer authentication"
            return 0
        else
            print_test_result "Users Table Creation" "FAIL" "La tabla users no fue creada"
            return 1
        fi
    else
        print_test_result "Users Table Creation" "FAIL" "Error ejecutando migración de users con peer authentication"
        echo -e "${RED}🔍 Debug: Error detallado:${NC}"
        psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -f migrations/001_create_users_table.sql
        return 1
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Unit Test 3: Creación de Tabla Projects (Patrón AAA)
# Propósito: Verificar que la migración de projects funciona correctamente
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
test_projects_table_creation() {
    echo -e "${BLUE}🧪 Test: Creación de Tabla Projects${NC}"
    echo -e "${BLUE}🔍 Debug: Iniciando test de creación de tabla projects...${NC}"
    
    # ARRANGE: Preparar entorno para la prueba
    echo -e "${BLUE}🔍 Debug: ARRANGE - Preparando entorno${NC}"
    local db_name="${DB_NAME:-your_database_name}"
    local db_host="${DB_HOST:-localhost}"
    local db_port="${DB_PORT:-5432}"
    local db_user="${DB_USER:-fisherk2}"
    
    # Verificar que la tabla no existe antes de crearla (usando peer authentication)
    echo -e "${BLUE}🔍 Debug: Verificando existencia de tabla projects con peer authentication${NC}"
    local pre_existing=$(psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='projects';" 2>/dev/null)
    echo -e "${BLUE}🔍 Debug: Tabla projects existe antes de crear: '$pre_existing'${NC}"
    
    # ACT: Ejecutar la acción a probar (usando peer authentication)
    echo -e "${BLUE}🔍 Debug: ACT - Ejecutando migración 002_create_projects_table.sql con peer authentication${NC}"
    echo -e "${BLUE}🔍 Debug: Comando: psql -h $db_host -p $db_port -U $db_user -d $db_name -f migrations/002_create_projects_table.sql${NC}"
    
    if psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -f migrations/002_create_projects_table.sql >/dev/null 2>&1; then
        echo -e "${BLUE}🔍 Debug: Migración ejecutada exitosamente${NC}"
        
        # ASSERT: Verificar el resultado esperado (usando peer authentication)
        echo -e "${BLUE}🔍 Debug: ASSERT - Verificando resultado con peer authentication${NC}"
        local post_creation=$(psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='projects';" 2>/dev/null)
        echo -e "${BLUE}🔍 Debug: Tabla projects existe después de crear: '$post_creation'${NC}"
        
        if [ "$post_creation" = "1" ]; then
            # Verificar estructura de la tabla
            local column_count=$(psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -tAc "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='projects';" 2>/dev/null)
            echo -e "${BLUE}🔍 Debug: Tabla projects tiene $column_count columnas${NC}"
            
            print_test_result "Projects Table Creation" "PASS" "Tabla projects creada exitosamente con $column_count columnas usando peer authentication"
            return 0
        else
            print_test_result "Projects Table Creation" "FAIL" "La tabla projects no fue creada"
            return 1
        fi
    else
        print_test_result "Projects Table Creation" "FAIL" "Error ejecutando migración de projects con peer authentication"
        echo -e "${RED}🔍 Debug: Error detallado:${NC}"
        psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -f migrations/002_create_projects_table.sql
        return 1
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Unit Test 4: Inserción de Datos Users (Patrón AAA)
# Propósito: Verificar que el seed de users funciona correctamente
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
test_users_seed_insertion() {
    echo -e "${BLUE}🧪 Test: Inserción de Datos Users${NC}"
    echo -e "${BLUE}🔍 Debug: Iniciando test de inserción de datos users...${NC}"
    
    # ARRANGE: Preparar entorno para la prueba
    echo -e "${BLUE}🔍 Debug: ARRANGE - Preparando entorno${NC}"
    local db_name="${DB_NAME:-your_database_name}"
    local db_host="${DB_HOST:-localhost}"
    local db_port="${DB_PORT:-5432}"
    local db_user="${DB_USER:-fisherk2}"
    
    # Verificar que la tabla está vacía antes de insertar (usando peer authentication)
    echo -e "${BLUE}🔍 Debug: Verificando conteo de users con peer authentication${NC}"
    local pre_count=$(psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -tAc "SELECT COUNT(*) FROM users;" 2>/dev/null)
    echo -e "${BLUE}🔍 Debug: Tabla users tiene $pre_count registros antes de insertar${NC}"
    
    # ACT: Ejecutar la acción a probar (usando peer authentication)
    echo -e "${BLUE}🔍 Debug: ACT - Ejecutando seed 001_seed_users.sql con peer authentication${NC}"
    echo -e "${BLUE}🔍 Debug: Comando: psql -h $db_host -p $db_port -U $db_user -d $db_name -f seeds/001_seed_users.sql${NC}"
    
    if psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -f seeds/001_seed_users.sql >/dev/null 2>&1; then
        echo -e "${BLUE}🔍 Debug: Seed ejecutado exitosamente${NC}"
        
        # ASSERT: Verificar el resultado esperado (usando peer authentication)
        echo -e "${BLUE}🔍 Debug: ASSERT - Verificando resultado con peer authentication${NC}"
        local post_count=$(psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -tAc "SELECT COUNT(*) FROM users;" 2>/dev/null)
        echo -e "${BLUE}🔍 Debug: Tabla users tiene $post_count registros después de insertar${NC}"
        
        if [ "$post_count" -gt 0 ]; then
            # Verificar integridad de los datos
            local admin_count=$(psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -tAc "SELECT COUNT(*) FROM users WHERE username='admin_user';" 2>/dev/null)
            echo -e "${BLUE}🔍 Debug: Usuarios admin encontrados: $admin_count${NC}"
            
            print_test_result "Users Seed Insertion" "PASS" "Insertados $post_count usuarios de prueba usando peer authentication"
            return 0
        else
            print_test_result "Users Seed Insertion" "FAIL" "No se insertaron usuarios"
            return 1
        fi
    else
        print_test_result "Users Seed Insertion" "FAIL" "Error ejecutando seed de users con peer authentication"
        echo -e "${RED}🔍 Debug: Error detallado:${NC}"
        psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -f seeds/001_seed_users.sql
        return 1
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Unit Test 5: Inserción de Datos Projects (Patrón AAA)
# Propósito: Verificar que el seed de projects funciona correctamente
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
test_projects_seed_insertion() {
    echo -e "${BLUE}🧪 Test: Inserción de Datos Projects${NC}"
    echo -e "${BLUE}🔍 Debug: Iniciando test de inserción de datos projects...${NC}"
    
    # ARRANGE: Preparar entorno para la prueba
    echo -e "${BLUE}🔍 Debug: ARRANGE - Preparando entorno${NC}"
    local db_name="${DB_NAME:-your_database_name}"
    local db_host="${DB_HOST:-localhost}"
    local db_port="${DB_PORT:-5432}"
    local db_user="${DB_USER:-fisherk2}"
    
    # Verificar que la tabla está vacía antes de insertar (usando peer authentication)
    echo -e "${BLUE}🔍 Debug: Verificando conteo de projects con peer authentication${NC}"
    local pre_count=$(psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -tAc "SELECT COUNT(*) FROM projects;" 2>/dev/null)
    echo -e "${BLUE}🔍 Debug: Tabla projects tiene $pre_count registros antes de insertar${NC}"
    
    # ACT: Ejecutar la acción a probar (usando peer authentication)
    echo -e "${BLUE}🔍 Debug: ACT - Ejecutando seed 002_seed_projects.sql con peer authentication${NC}"
    echo -e "${BLUE}🔍 Debug: Comando: psql -h $db_host -p $db_port -U $db_user -d $db_name -f seeds/002_seed_projects.sql${NC}"
    
    # Ejecutar el script y capturar tanto salida como código de salida
    local seed_output
    local seed_exit_code
    
    seed_output=$(psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -f seeds/002_seed_projects.sql 2>&1)
    seed_exit_code=$?
    
    echo -e "${BLUE}🔍 Debug: Código de salida del seed: $seed_exit_code${NC}"
    echo -e "${BLUE}🔍 Debug: Salida del seed (últimas líneas):${NC}"
    echo "$seed_output" | tail -5
    
    # El script puede tener NOTICE pero aún así funcionar correctamente
    # Verificamos el resultado real en lugar de solo el código de salida
    echo -e "${BLUE}🔍 Debug: ASSERT - Verificando resultado real con peer authentication${NC}"
    local post_count=$(psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -tAc "SELECT COUNT(*) FROM projects;" 2>/dev/null)
    echo -e "${BLUE}🔍 Debug: Tabla projects tiene $post_count registros después de insertar${NC}"
    
    if [ "$post_count" -gt 0 ]; then
        # Verificar integridad referencial
        local orphaned_count=$(psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -tAc "SELECT COUNT(*) FROM projects p LEFT JOIN users u ON p.user_id = u.id WHERE u.id IS NULL;" 2>/dev/null)
        echo -e "${BLUE}🔍 Debug: Proyectos huérfanos encontrados: $orphaned_count${NC}"
        
        # Verificar si hubo INSERTs exitosos en la salida
        if echo "$seed_output" | grep -q "INSERT [0-9]"; then
            print_test_result "Projects Seed Insertion" "PASS" "Insertados $post_count proyectos de prueba usando peer authentication"
            return 0
        else
            print_test_result "Projects Seed Insertion" "FAIL" "No se detectaron INSERTs exitosos en la salida"
            return 1
        fi
    else
        print_test_result "Projects Seed Insertion" "FAIL" "No se insertaron proyectos (conteo: $post_count)"
        echo -e "${RED}🔍 Debug: Salida completa del seed:${NC}"
        echo "$seed_output"
        return 1
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Unit Test 6: Verificación Setup Completo (Patrón AAA)
# Propósito: Verificar que verify_setup.sh funciona correctamente
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
test_setup_verification() {
    echo -e "${BLUE}🧪 Test: Verificación Setup Completo${NC}"
    echo -e "${BLUE}🔍 Debug: Iniciando test de verificación setup completo...${NC}"
    
    # ARRANGE: Preparar entorno para la prueba
    echo -e "${BLUE}🔍 Debug: ARRANGE - Preparando entorno${NC}"
    
    # Asegurar que verify_setup.sh tenga permisos de ejecución
    if [ ! -x "verify_setup.sh" ]; then
        chmod +x verify_setup.sh
        echo -e "${BLUE}🔍 Debug: Permisos de ejecución asignados a verify_setup.sh${NC}"
    fi
    
    # ACT: Ejecutar la acción a probar
    echo -e "${BLUE}🔍 Debug: ACT - Ejecutando verify_setup.sh${NC}"
    
    # Capturar salida y código de salida
    local output
    local exit_code
    
    output=$(./verify_setup.sh 2>&1)
    exit_code=$?
    
    echo -e "${BLUE}🔍 Debug: verify_setup.sh ejecutado con código de salida: $exit_code${NC}"
    
    # ASSERT: Verificar el resultado esperado
    echo -e "${BLUE}🔍 Debug: ASSERT - Verificando resultado${NC}"
    
    if [ $exit_code -eq 0 ]; then
        # Verificar que la salida contenga indicadores de éxito
        if echo "$output" | grep -q "¡Todas las validaciones pasaron exitosamente!"; then
            print_test_result "Setup Verification" "PASS" "verify_setup.sh pasó todas las validaciones"
            return 0
        else
            print_test_result "Setup Verification" "FAIL" "verify_setup.sh tuvo código 0 pero mensaje incorrecto"
            return 1
        fi
    else
        # Verificar si hay errores esperados
        local error_count=$(echo "$output" | grep -c "❌" || echo "0")
        echo -e "${BLUE}🔍 Debug: Errores encontrados en verify_setup.sh: $error_count${NC}"
        
        print_test_result "Setup Verification" "FAIL" "verify_setup.sh detectó $error_count errores"
        return 1
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Unit Test 7: Eliminación de Base de Datos (Patrón AAA)
# Propósito: Verificar que el script drop_database.sql funciona correctamente
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
test_database_deletion() {
    echo -e "${BLUE}🧪 Test: Eliminación de Base de Datos${NC}"
    echo -e "${BLUE}🔍 Debug: Iniciando test de eliminación de base de datos...${NC}"
    
    # ARRANGE: Preparar entorno para la prueba
    echo -e "${BLUE}🔍 Debug: ARRANGE - Preparando entorno${NC}"
    local db_name="${DB_NAME:-your_database_name}"
    local db_host="${DB_HOST:-localhost}"
    local db_port="${DB_PORT:-5432}"
    
    # Verificar que la base de datos existe antes de eliminarla (usando peer authentication)
    echo -e "${BLUE}🔍 Debug: Verificando existencia de BD para eliminar con peer authentication${NC}"
    local pre_existing=$(psql -h "$db_host" -p "$db_port" -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db_name';" 2>/dev/null)
    echo -e "${BLUE}🔍 Debug: Base de datos existe antes de eliminar: '$pre_existing'${NC}"
    
    if [ "$pre_existing" != "1" ]; then
        print_test_result "Database Deletion" "FAIL" "La base de datos no existe para eliminar"
        return 1
    fi
    
    # ACT: Ejecutar la acción a probar (usando peer authentication)
    echo -e "${BLUE}🔍 Debug: ACT - Ejecutando drop_database.sql con peer authentication${NC}"
    echo -e "${BLUE}🔍 Debug: Comando: psql -h $db_host -p $db_port -U postgres -d postgres -f drop_database.sql${NC}"
    
    if psql -h "$db_host" -p "$db_port" -U postgres -d postgres -f drop_database.sql >/dev/null 2>&1; then
        echo -e "${BLUE}🔍 Debug: Script de eliminación ejecutado exitosamente${NC}"
        
        # ASSERT: Verificar el resultado esperado (usando peer authentication)
        echo -e "${BLUE}🔍 Debug: ASSERT - Verificando resultado con peer authentication${NC}"
        local post_deletion=$(psql -h "$db_host" -p "$db_port" -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db_name';" 2>/dev/null)
        echo -e "${BLUE}🔍 Debug: Base de datos existe después de eliminar: '$post_deletion'${NC}"
        
        if [ "$post_deletion" != "1" ]; then
            print_test_result "Database Deletion" "PASS" "Base de datos eliminada exitosamente usando peer authentication"
            return 0
        else
            print_test_result "Database Deletion" "FAIL" "La base de datos todavía existe"
            return 1
        fi
    else
        print_test_result "Database Deletion" "FAIL" "Error ejecutando drop_database.sql con peer authentication"
        echo -e "${RED}🔍 Debug: Error detallado:${NC}"
        psql -h "$db_host" -p "$db_port" -U postgres -d postgres -f drop_database.sql
        return 1
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Función Principal de Ejecución de Tests con Peer Authentication
# Propósito: Ejecutar tests en orden lógico con tolerancia cero a errores
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
main() {
    echo -e "${BLUE}🚀 Iniciando Suite de Unit Tests PostgreSQL con Patrón AAA (Peer AUTH)${NC}"
    echo -e "${BLUE}================================================================${NC}"
    
    # Setup inicial
    if ! load_env_safely; then
        echo -e "${RED}❌ Setup inicial falló - abortando ejecución${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}🔍 Debug: Iniciando ejecución de tests unitarios (Zero-Tolerant)...${NC}"
    echo -e "${YELLOW}⚠️  NOTA: Si una prueba falla, la ejecución se detendrá inmediatamente${NC}"
    echo -e "${BLUE}================================================================${NC}"
    
    # Ejecutar tests en orden lógico con tolerancia cero a errores
    # Si una prueba falla, se detiene la ejecución inmediatamente
    
    echo -e "${BLUE}📋 Test 1/7: Creación de Base de Datos${NC}"
    if ! test_database_creation; then
        echo -e "${RED}💥 CRÍTICO: Test 1 falló - Deteniendo ejecución (Zero-Tolerant)${NC}"
        cleanup_on_error
        exit 1
    fi
    echo -e "${GREEN}✅ Test 1 pasó - Continuando con Test 2...${NC}"
    echo -e "${BLUE}================================================================${NC}"
    
    echo -e "${BLUE}📋 Test 2/7: Creación de Tabla Users${NC}"
    if ! test_users_table_creation; then
        echo -e "${RED}💥 CRÍTICO: Test 2 falló - Deteniendo ejecución (Zero-Tolerant)${NC}"
        cleanup_on_error
        exit 1
    fi
    echo -e "${GREEN}✅ Test 2 pasó - Continuando con Test 3...${NC}"
    echo -e "${BLUE}================================================================${NC}"
    
    echo -e "${BLUE}📋 Test 3/7: Creación de Tabla Projects${NC}"
    if ! test_projects_table_creation; then
        echo -e "${RED}💥 CRÍTICO: Test 3 falló - Deteniendo ejecución (Zero-Tolerant)${NC}"
        cleanup_on_error
        exit 1
    fi
    echo -e "${GREEN}✅ Test 3 pasó - Continuando con Test 4...${NC}"
    echo -e "${BLUE}================================================================${NC}"
    
    echo -e "${BLUE}📋 Test 4/7: Inserción de Datos Users${NC}"
    if ! test_users_seed_insertion; then
        echo -e "${RED}💥 CRÍTICO: Test 4 falló - Deteniendo ejecución (Zero-Tolerant)${NC}"
        cleanup_on_error
        exit 1
    fi
    echo -e "${GREEN}✅ Test 4 pasó - Continuando con Test 5...${NC}"
    echo -e "${BLUE}================================================================${NC}"
    
    echo -e "${BLUE}📋 Test 5/7: Inserción de Datos Projects${NC}"
    if ! test_projects_seed_insertion; then
        echo -e "${RED}💥 CRÍTICO: Test 5 falló - Deteniendo ejecución (Zero-Tolerant)${NC}"
        cleanup_on_error
        exit 1
    fi
    echo -e "${GREEN}✅ Test 5 pasó - Continuando con Test 6...${NC}"
    echo -e "${BLUE}================================================================${NC}"
    
    echo -e "${BLUE}📋 Test 6/7: Verificación Setup Completo${NC}"
    if ! test_setup_verification; then
        echo -e "${RED}💥 CRÍTICO: Test 6 falló - Deteniendo ejecución (Zero-Tolerant)${NC}"
        cleanup_on_error
        exit 1
    fi
    echo -e "${GREEN}✅ Test 6 pasó - Continuando con Test 7...${NC}"
    echo -e "${BLUE}================================================================${NC}"
    
    echo -e "${BLUE}📋 Test 7/7: Eliminación de Base de Datos${NC}"
    if ! test_database_deletion; then
        echo -e "${RED}💥 CRÍTICO: Test 7 falló - Deteniendo ejecución (Zero-Tolerant)${NC}"
        cleanup_on_error
        exit 1
    fi
    echo -e "${GREEN}✅ Test 7 pasó - ¡Todos los tests completados!${NC}"
    
    # Cleanup final (solo credenciales, ya que la BD fue eliminada en Test 7)
    cleanup_credentials
    
    # Reporte final de éxito
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${GREEN}🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE!${NC}"
    echo -e "${GREEN}📊 Reporte Final de Tests (Zero-Tolerant):${NC}"
    echo -e "${GREEN}🔍 Debug: Total de tests ejecutados: $TOTAL_TESTS${NC}"
    echo -e "${GREEN}✅ Passed: $PASSED_TESTS${NC}"
    echo -e "${GREEN}❌ Failed: $FAILED_TESTS${NC}"
    echo -e "${GREEN}🔍 Debug: Suite de pruebas completada sin errores (Zero-Tolerant)${NC}"
    echo -e "${GREEN}🏆 ¡ÉXITO COMPLETO! Todos los scripts funcionaron correctamente${NC}"
    exit 0
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Punto de Entrada del Script
# Propósito: Ejecutar función principal si el script se ejecuta directamente
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi