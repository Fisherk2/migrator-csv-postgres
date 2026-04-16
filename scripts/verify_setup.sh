#!/bin/bash

# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙
# Database Setup Verification Script
# Purpose: Validación completa de configuración de base de datos
# Author: fisherk2
# Version: 1.0
# Date: 2026-03-13
# Requirements: PostgreSQL 15+, psql client, .env file con parámetros de conexión
# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙🮙🮘🮙

# ■■■■■■■■■■■■■ Configuración de colores para salida legible ■■■■■■■■■■■■■ 
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ■■■■■■■■■■■■■ Variables globales para tracking de validaciones ■■■■■■■■■■■■■ 
VALIDATION_ERRORS=0
TOTAL_TESTS=0

# ■■■■■■■■■■■■■ Función para imprimir mensajes con formato ■■■■■■■■■■■■■ 
print_message() {
    local color=$1
    local symbol=$2
    local message=$3
    echo -e "${color}${symbol} ${message}${NC}"
}

# ■■■■■■■■■■■■■ Función para validar conexión a PostgreSQL ■■■■■■■■■■■■■
# Por qué es crítica: Sin conexión, no se puede validar nada más
validate_connection() {
    print_message $BLUE "🔍" "Validando conexión a PostgreSQL..."
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Intentar conexión básica sin mostrar credenciales
    if PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
        print_message $GREEN "✅" "Conexión a PostgreSQL exitosa"
        return 0
    else
        print_message $RED "❌" "Error: No se puede conectar a PostgreSQL"
        print_message $YELLOW "💡" "Verifica que PostgreSQL esté corriendo y las credenciales en .env"
        VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
        return 1
    fi
}

# ■■■■■■■■■■■■■ Función para validar que la base de datos existe ■■■■■■■■■■■■■ 
# Por qué es crítica: Sin BD, no hay tablas ni datos que validar
validate_database() {
    print_message $BLUE "🔍" "Validando existencia de la base de datos..."
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    local db_name="${DB_NAME:-your_database_name}"
    
    # Verificar si la BD existe
    if PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db_name';" | grep -q 1; then
        print_message $GREEN "✅" "Base de datos '$db_name' existe"
        return 0
    else
        print_message $RED "❌" "Error: Base de datos '$db_name' no existe"
        print_message $YELLOW "💡" "Ejecuta: psql -f create_database.sql"
        VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
        return 1
    fi
}

# ■■■■■■■■■■■■■ Función para validar que las tablas existen ■■■■■■■■■■■■■ 
# Por qué es crítica: Sin tablas, no se puede almacenar ni validar datos
validate_tables() {
    print_message $BLUE "🔍" "Validando existencia de tablas..."
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    local db_name="${DB_NAME:-your_database_name}"
    local tables=("users" "projects")
    local missing_tables=()
    
    # Verificar cada tabla requerida
    for table in "${tables[@]}"; do
        if PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "$db_name" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name='$table';" | grep -q 1; then
            print_message $GREEN "✅" "Tabla '$table' existe"
        else
            print_message $RED "❌" "Tabla '$table' no existe"
            missing_tables+=("$table")
        fi
    done
    
    # Si faltan tablas, mostrar error y sugerencia
    if [ ${#missing_tables[@]} -gt 0 ]; then
        print_message $RED "❌" "Tablas faltantes: ${missing_tables[*]}"
        print_message $YELLOW "💡" "Ejecuta las migraciones: psql -f migrations/*.sql"
        VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
        return 1
    else
        print_message $GREEN "✅" "Todas las tablas requeridas existen"
        return 0
    fi
}

# ■■■■■■■■■■■■■ Función para validar que hay datos seed en las tablas ■■■■■■■■■■■■■ 
# Por qué es crítica: Sin datos, no se puede probar funcionalidad
validate_data() {
    print_message $BLUE "🔍" "Validando datos seed en tablas..."
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    local db_name="${DB_NAME:-your_database_name}"
    local data_valid=true
    
    # Validar datos en tabla users
    local user_count=$(PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "$db_name" -tAc "SELECT COUNT(*) FROM users;" 2>/dev/null)
    if [ "$user_count" -gt 0 ]; then
        print_message $GREEN "✅" "Tabla users contiene $user_count registros"
    else
        print_message $RED "❌" "Tabla users está vacía"
        data_valid=false
    fi
    
    # Validar datos en tabla projects
    local project_count=$(PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "$db_name" -tAc "SELECT COUNT(*) FROM projects;" 2>/dev/null)
    if [ "$project_count" -gt 0 ]; then
        print_message $GREEN "✅" "Tabla projects contiene $project_count registros"
    else
        print_message $RED "❌" "Tabla projects está vacía"
        data_valid=false
    fi
    
    # Validar integridad referencial (proyectos huérfanos)
    local orphaned_projects=$(PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" -d "$db_name" -tAc "SELECT COUNT(*) FROM projects p LEFT JOIN users u ON p.user_id = u.id WHERE u.id IS NULL;" 2>/dev/null)
    if [ "$orphaned_projects" -eq 0 ]; then
        print_message $GREEN "✅" "Integridad referencial correcta (no hay proyectos huérfanos)"
    else
        print_message $RED "❌" "Se encontraron $orphaned_projects proyectos huérfanos"
        data_valid=false
    fi
    
    if [ "$data_valid" = false ]; then
        print_message $YELLOW "💡" "Ejecuta los seeds: psql -f seeds/*.sql"
        VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
        return 1
    else
        print_message $GREEN "✅" "Validación de datos completada exitosamente"
        return 0
    fi
}

# ■■■■■■■■■■■■■ Función para cargar variables de entorno desde .env ■■■■■■■■■■■■■ 
# Por qué es crítica: Sin configuración, el script no puede conectarse
load_env_file() {
    print_message $BLUE "🔍" "Cargando configuración desde .env..."
    
    if [ -f ".env" ]; then
        # Cargar variables de entorno (ignorar líneas con # y vacías)
        export $(grep -v '^#' .env | grep -v '^$' | xargs)
        print_message $GREEN "✅" "Archivo .env cargado"
    else
        print_message $YELLOW "⚠️" "Archivo .env no encontrado, usando valores por defecto"
        print_message $YELLOW "💡" "Crea .env desde connection_example.env"
    fi
}

# ■■■■■■■■■■■■■ Función principal de validación ■■■■■■■■■■■■■ 
main() {
    print_message $BLUE "🚀" "Iniciando validación completa de base de datos..."
    echo
    
    # Cargar configuración
    load_env_file
    echo
    
    # Ejecutar todas las validaciones en orden
    validate_connection
    echo
    
    validate_database
    echo
    
    validate_tables
    echo
    
    validate_data
    echo
    
    # Resumen final
    print_message $BLUE "📊" "Resumen de validación:"
    print_message $BLUE "📊" "Total de pruebas: $TOTAL_TESTS"
    print_message $BLUE "📊" "Errores encontrados: $VALIDATION_ERRORS"
    echo
    
    if [ $VALIDATION_ERRORS -eq 0 ]; then
        print_message $GREEN "🎉" "¡Todas las validaciones pasaron exitosamente!"
        print_message $GREEN "✅" "La base de datos está lista para uso"
        exit 0
    else
        print_message $RED "💥" "Se encontraron $VALIDATION_ERRORS errores"
        print_message $RED "❌" "Por favor, corrige los problemas antes de continuar"
        exit 1
    fi
}

# ■■■■■■■■■■■■■ Ejecutar función principal si el script se ejecuta directamente ■■■■■■■■■■■■■ 
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi