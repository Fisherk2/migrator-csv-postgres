#!/bin/bash

# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙 
# Script de Verificación End-to-End con Zero Tolerance
# Propósito: Validación completa del entorno, contenedor y migración
# Autor: fisherk2
# Versión: 1.0
# Fecha: 2026-04-17
# Requisitos: Docker, Docker Compose v2, Python 3.10+, .env
# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙 


# ■■■■■■■■■■■■■ Zero tolerance: cualquier error detiene ejecución inmediatamente ■■■■■■■■■■■■■
set -euo pipefail

# ▁▂▃▄▅▆▇███████ Configuración de colores y timestamps ███████▇▆▅▄▃▂▁
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ▁▂▃▄▅▆▇███████ Variables globales para tracking  ███████▇▆▅▄▃▂▁
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# ■■■■■■■■■■■■■ Función para imprimir mensajes con timestamp ■■■■■■■■■■■■■ 
print_message() {
    local color=$1
    local symbol=$2
    local message=$3
    echo -e "${color}[$TIMESTAMP]${symbol} ${message}${NC}"
}

# ■■■■■■■■■■■■■ Verificación de dependencias críticas ■■■■■■■■■■■■■ 
check_deps() {
    print_message $BLUE " " "Verificando dependencias del sistema..."
    
    local deps=("docker" "docker" "python3" "pip")
    local missing_deps=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing_deps+=("$dep")
        else
            print_message $GREEN " " " $dep encontrado"
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_message $RED " " "Dependencias faltantes: ${missing_deps[*]}"
        print_message $YELLOW " " "Instala las dependencias y reintenta"
        exit 1
    fi
    
    # Verificar Docker Compose v2
    if ! docker compose version &> /dev/null; then
        print_message $RED " " "Docker Compose v2 no encontrado"
        print_message $YELLOW " " "Actualiza a Docker Compose v2 nativo"
        exit 1
    fi
    
    # Verificar archivo .env
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        print_message $RED " " "Archivo .env no encontrado en $PROJECT_ROOT"
        print_message $YELLOW " " "Crea .env desde .env.example"
        exit 1
    fi
    
    print_message $GREEN " " "Todas las dependencias verificadas"
}

# ■■■■■■■■■■■■■ Levantar stack Docker con healthcheck ■■■■■■■■■■■■■ 
start_stack() {
    print_message $BLUE " " "Levantando stack Docker..."
    
    cd "$PROJECT_ROOT"
    
    # Verificar si ya está corriendo
    if docker compose ps -q | grep -q .; then
        print_message $YELLOW " " "Stack ya corriendo, deteniendo primero..."
        docker compose down
    fi
    
    # Levantar en modo detached
    docker compose up -d
    
    print_message $GREEN " " "Stack levantado exitosamente"
}

# ■■■■■■■■■■■■■ Esperar healthcheck de PostgreSQL con timeout ■■■■■■■■■■■■■ 
wait_db() {
    print_message $BLUE " " "Esperando healthcheck de PostgreSQL..."
    
    local timeout=30
    local interval=2
    local elapsed=0
    
    while [ $elapsed -lt $timeout ]; do
        if docker compose exec -T postgres pg_isready -U "${DB_USER:-migrator_user}" &> /dev/null; then
            print_message $GREEN " " "PostgreSQL está healthy"
            return 0
        fi
        
        print_message $YELLOW " " "Esperando PostgreSQL... (${elapsed}s/${timeout}s)"
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    print_message $RED " " "Timeout esperando PostgreSQL healthcheck"
    return 1
}

# ■■■■■■■■■■■■■ Ejecutar inicialización de base de datos ■■■■■■■■■■■■■ 
run_init_db() {
    print_message $BLUE " " "Ejecutando inicialización de base de datos..."
    
    cd "$PROJECT_ROOT"
    
    if python3 scripts/init_db.py; then
        print_message $GREEN " " "Base de datos inicializada exitosamente"
        return 0
    else
        print_message $RED " " "Error en inicialización de base de datos"
        return 1
    fi
}

# ■■■■■■■■■■■■■ Ejecutar migración de prueba (dry-run) ■■■■■■■■■■■■■ 
run_migration_test() {
    print_message $BLUE " " "Ejecutando migración de prueba..."
    
    cd "$PROJECT_ROOT"
    
    # Crear CSV de prueba pequeño
    echo "id,name,email,phone
1,Test User,test@example.com,+1-555-0123" > test_migration.csv
    
    # Verificar si existe script de migración
    if [ -f "scripts/run_migration.py" ]; then
        if python3 scripts/run_migration.py --dry-run --source test_migration.csv; then
            print_message $GREEN " " "Migración de prueba exitosa"
            rm -f test_migration.csv
            return 0
        else
            print_message $RED " " "Error en migración de prueba"
            rm -f test_migration.csv
            return 1
        fi
    else
        print_message $YELLOW " " "Script run_migration.py no encontrado, omitiendo prueba"
        rm -f test_migration.csv
        return 0
    fi
}

# ■■■■■■■■■■■■■ Validar outputs esperados ■■■■■■■■■■■■■ 
validate_outputs() {
    print_message $BLUE " " "Validando outputs esperados..."
    
    cd "$PROJECT_ROOT"
    
    # Verificar logs limpios (sin errores críticos)
    if docker compose logs postgres | grep -qi "error\|fatal\|failed"; then
        print_message $RED " " "Se encontraron errores en logs de PostgreSQL"
        return 1
    fi
    
    # Verificar que las tablas existen
    local db_name="${DB_NAME:-migrator_ecommerce}"
    local tables=("customers" "products" "orders")
    
    for table in "${tables[@]}"; do
        if ! docker compose exec -T postgres psql -U "${DB_USER:-migrator_user}" -d "$db_name" -c "SELECT 1 FROM information_schema.tables WHERE table_name='$table';" | grep -q 1; then
            print_message $RED " " "Tabla '$table' no encontrada"
            return 1
        fi
    done
    
    print_message $GREEN " " "Todas las validaciones de outputs pasaron"
    return 0
}

# ■■■■■■■■■■■■■ Limpieza en caso de fallo (mantener imagen para debugging) ■■■■■■■■■■■■■ 
cleanup_on_fail() {
    print_message $RED " " "Ejecutando limpieza por fallo..."
    
    cd "$PROJECT_ROOT"
    
    # Detener y eliminar contenedor y volumen, mantener imagen para depuración
    docker compose down
    docker rm -f migrator_postgres_dev 2>/dev/null || true
    
    print_message $YELLOW " " "Contenedor y volumen eliminados, imagen conservada para debugging"
}

# ■■■■■■■■■■■■■ Limpieza en caso de éxito (eliminar todo incluyendo imagen) ■■■■■■■■■■■■■ 
cleanup_on_success() {
    print_message $GREEN " " "Ejecutando limpieza exitosa..."
    
    cd "$PROJECT_ROOT"
    
    # Eliminar todo incluyendo contenedor, volúmenes e imagen
    docker compose down -v
    docker rmi migrator_postgres_dev:latest 2>/dev/null || true
    
    print_message $GREEN " " "Limpieza completa exitosa (imagen eliminada)"
}

# ■■■■■■■■■■■■■ Función principal con zero tolerance ■■■■■■■■■■■■■ 
main() {
    print_message $BLUE " " "Iniciando verificación end-to-end..."
    echo
    
    # Trap global para limpieza en caso de interrupción
    trap cleanup_on_fail EXIT
    
    # Ejecutar pasos secuenciales con validación explícita
    check_deps || { cleanup_on_fail; exit 1; }
    echo
    
    start_stack || { cleanup_on_fail; exit 1; }
    echo
    
    wait_db || { cleanup_on_fail; exit 1; }
    echo
    
    run_init_db || { cleanup_on_fail; exit 1; }
    echo
    
    run_migration_test || { cleanup_on_fail; exit 1; }
    echo
    
    validate_outputs || { cleanup_on_fail; exit 1; }
    echo
    
    # Éxito: cambiar trap y limpiar completamente
    trap - EXIT
    cleanup_on_success
    echo
    
    print_message $GREEN " " " Verificación completada exitosamente!"
    print_message $GREEN " " "Todos los componentes funcionan correctamente"
    exit 0
}

# ■■■■■■■■■■■■■ Ejecutar si se llama directamente ■■■■■■■■■■■■■ 
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi