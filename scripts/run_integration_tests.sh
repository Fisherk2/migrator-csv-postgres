#!/bin/bash

# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘
# SCRIPT DE PRUEBAS DE INTEGRACIÓN E2E - MIGRATOR CSV POSTGRES
# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘
# Propósito: Ejecutar pruebas de integración end-to-end con base de datos real
# Author: fisherk2
# Version: 1.0 - Versión inicial
# Date: 2026-04-27
#
# Principios Aplicados:
# - YAGNI: Reutilizar contenedor existente con aislamiento lógico (TEST_DB_NAME)
# - F.I.R.S.T.: Tests Fast, Independent, Repeatable, Self-validating, Timely
# - Zero Tolerance: set -euo pipefail para fail-fast
# - Aislamiento Transaccional: ROLLBACK garantizado en teardown
# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘

# Modo estricto para fail-fast (Clean Code Cap. 19)
set -euo pipefail

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# CONFIGURACIÓN INICIAL
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

# Configuración de colores y logging
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Variables globales
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
readonly CONFIG_FILE="$PROJECT_DIR/.env"
readonly COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
readonly CONTAINER_NAME="migrator_postgres_dev"
readonly PYTHON_SCRIPT="$PROJECT_DIR/tests/integration/test_integration.py"

# Variables de contadores
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0
START_TIME=$(date +%s)

# Flags de línea de comandos
VERBOSE=false
KEEP_DATA=false

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIONES DE LOGGING
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
timestamp() { date '+%Y-%m-%d %H:%M:%S'; }
log_info() { echo -e "${BLUE}[INFO]${NC} $*" >&2; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*" >&2; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_test() { echo -e "${BLUE}[TEST]${NC} $*" >&2; }

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIÓN DE PARSEO DE ARGUMENTOS
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --keep-data|-k)
                KEEP_DATA=true
                shift
                ;;
            --help|-h)
                echo "Uso: $0 [--verbose] [--keep-data]"
                echo "  --verbose, -v    Modo verboso"
                echo "  --keep-data, -k  Mantener datos de prueba para debugging"
                exit 0
                ;;
            *)
                log_error "Opción desconocida: $1"
                exit 2
                ;;
        esac
    done
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIÓN DE VERIFICACIÓN DE PREREQUISITOS
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

check_prerequisites() {
    log_info "🔍 Verificando prerequisitos..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        log_error "❌ Docker no está instalado"
        exit 2
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "❌ Docker Compose no está instalado"
        exit 2
    fi
    
    # Verificar Python 3
    if ! command -v python3 &> /dev/null; then
        log_error "❌ Python 3 no está instalado"
        exit 2
    fi
    
    # Verificar archivo de configuración
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "❌ Archivo de configuración no encontrado: $CONFIG_FILE"
        log_info "💡 Copia .env.example a .env"
        exit 2
    fi
    
    # Verificar script Python de integración
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        log_error "❌ Script de integración no encontrado: $PYTHON_SCRIPT"
        exit 2
    fi
    
    log_success "✅ Prerequisitos verificados"
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIÓN DE CARGA DE CONFIGURACIÓN TEST_*
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

load_test_config() {
    log_info "📋 Cargando configuración de pruebas desde $CONFIG_FILE"
    
    # Cargar variables de entorno
    set -a
    if ! source "$CONFIG_FILE" 2>/dev/null; then
        log_error "❌ Error al cargar archivo de configuración: $CONFIG_FILE"
        exit 2
    fi
    set +a
    
    # DECISIÓN: Usar TEST_* con fallback a DB_* para pruebas
    # Esto permite reutilizar contenedor existente con aislamiento lógico
    TEST_DB_HOST="${TEST_DB_HOST:-${DB_HOST:-localhost}}"
    TEST_DB_PORT="${TEST_DB_PORT:-${DB_PORT:-5432}}"
    TEST_DB_NAME="${TEST_DB_NAME:-migrator_test}"
    TEST_DB_USER="${TEST_DB_USER:-${DB_USER:-migrator_user}}"
    TEST_DB_PASSWORD="${TEST_DB_PASSWORD:-${DB_PASSWORD:-dev_password_123}}"
    
    # DECISIÓN DE DISEÑO: Validar que TEST_DB_NAME no sea producción
    # Evitar accidentalmente ejecutar pruebas contra base de datos de producción
    if [[ "$TEST_DB_NAME" == "migrator_ecommerce" ]] || [[ "$TEST_DB_NAME" == "${DB_NAME:-}" ]]; then
        log_error "❌ TEST_DB_NAME apunta a base de datos de producción: $TEST_DB_NAME"
        log_error "❌ Por seguridad, las pruebas deben usar una base de datos separada"
        exit 2
    fi
    
    # Validar variables críticas
    local required_vars=("TEST_DB_HOST" "TEST_DB_PORT" "TEST_DB_NAME" "TEST_DB_USER" "TEST_DB_PASSWORD")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "❌ Variable requerida no configurada: $var"
            exit 2
        fi
    done
    
    log_success "✅ Configuración de pruebas cargada"
    log_info "📋 Conectando a: ${TEST_DB_USER}@${TEST_DB_HOST}:${TEST_DB_PORT}/${TEST_DB_NAME}"
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIÓN DE ESPERA Y HEALTH CHECK
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

wait_for_postgres() {
    log_info "⏳ Esperando a que PostgreSQL inicie..."
    
    # Verificar que el contenedor existe y está corriendo
    if ! docker-compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
        log_error "❌ Contenedor $CONTAINER_NAME no encontrado o no corriendo"
        log_info "💡 Ejecuta: docker-compose -f $COMPOSE_FILE up -d"
        exit 2
    fi
    
    local timeout=60
    local count=0
    
    while [[ $count -lt $timeout ]]; do
        if docker exec "$CONTAINER_NAME" pg_isready -U "$DB_USER" -d "$DB_NAME" &>/dev/null; then
            log_success "✅ PostgreSQL está listo"
            return 0
        fi
        
        echo -n "."
        sleep 1
        count=$((count + 1))
    done
    
    echo
    log_error "❌ Timeout esperando a PostgreSQL"
    exit 2
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIÓN DE CREACIÓN DE BASE DE DATOS DE PRUEBA
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

create_test_database() {
    log_info "🗄️ Preparando base de datos de prueba: $TEST_DB_NAME"

    # DECISIÓN: Eliminar base de datos de prueba si existe para garantizar limpieza
    # Esto hace el proceso idempotente y reproducible
    log_info "🧹 Eliminando base de datos de prueba previa (si existe)..."
    cd "$PROJECT_DIR"
    if python3 scripts/init_db.py --drop "$TEST_DB_NAME" > /dev/null 2>&1; then
        log_success "✅ Limpieza de base de datos de prueba completada"
    else
        log_warning "⚠️ No se pudo eliminar base de datos (puede no existir)"
    fi

    # DECISIÓN: Usar init_db.py con DB_NAME=TEST_DB_NAME para crear BD de prueba
    # Esto aplica el esquema automáticamente
    log_info "📦 Creando base de datos de prueba y aplicando esquema..."
    cd "$PROJECT_DIR"
    if DB_NAME="$TEST_DB_NAME" python3 scripts/init_db.py --verbose > /dev/null 2>&1; then
        log_success "✅ Base de datos de prueba creada con esquema"
    else
        log_error "❌ Error al crear base de datos de prueba"
        exit 2
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIÓN DE EJECUCIÓN DE PRUEBAS DE INTEGRACIÓN
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

run_integration_tests() {
    log_test "🧪 Ejecutando pruebas de integración..."
    
    # Exportar variables TEST_* para el script Python
    export TEST_DB_HOST
    export TEST_DB_PORT
    export TEST_DB_NAME
    export TEST_DB_USER
    export TEST_DB_PASSWORD
    
    # Ejecutar script Python con flags apropiados
    local python_args=""
    if [[ "$VERBOSE" == true ]]; then
        python_args="--verbose"
    fi
    if [[ "$KEEP_DATA" == true ]]; then
        python_args="$python_args --keep-data"
    fi
    
    cd "$PROJECT_DIR"
    if python3 "$PYTHON_SCRIPT" $python_args; then
        log_success "✅ Pruebas de integración pasadas"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "❌ Pruebas de integración fallaron"
        ((TESTS_FAILED++))
        return 1
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIÓN DE LIMPIEZA DE BASE DE DATOS DE PRUEBA
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

cleanup_test_database() {
    if [[ "$KEEP_DATA" == true ]]; then
        log_warning "⚠️ Manteniendo base de datos de prueba para debugging: $TEST_DB_NAME"
        log_info "💡 Para limpiar manualmente: psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c \"DROP DATABASE $TEST_DB_NAME;\""
        return 0
    fi
    
    log_info "🧹 Limpiando base de datos de prueba: $TEST_DB_NAME"
    
    # DECISIÓN: Terminar conexiones activas antes de DROP
    # Evita "database is being accessed by other users"
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "
        SELECT pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname = '$TEST_DB_NAME' AND pid <> pg_backend_pid();
    " 2>/dev/null || true
    
    # Eliminar base de datos
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE $TEST_DB_NAME;" 2>&1; then
        log_success "✅ Base de datos de prueba eliminada"
    else
        log_warning "⚠️ No se pudo eliminar base de datos de prueba (puede no existir)"
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIÓN PRINCIPAL - ORQUESTACIÓN
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

main() {
    echo "============================================================================"
    log_info " INICIANDO PRUEBAS DE INTEGRACIÓN E2E - MIGRATION CSV POSTGRES"
    echo "============================================================================"
    
    # Parsear argumentos
    parse_arguments "$@"
    
    # Ejecutar pasos en orden
    check_prerequisites
    load_test_config
    wait_for_postgres
    create_test_database
    run_integration_tests
    
    # Limpieza siempre se ejecuta (incluso si tests fallan)
    cleanup_test_database
    
    echo "============================================================================"
    
    # Exit code basado en resultados
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "🎉 PRUEBAS DE INTEGRACIÓN PASARON"
        exit 0
    else
        log_error "💥 PRUEBAS DE INTEGRACIÓN FALLARON"
        exit 1
    fi
}

# Ejecutar función principal
main "$@"
