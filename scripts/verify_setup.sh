#!/bin/bash

# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘
# SCRIPT DE AUTOMATIZACIÓN DE TESTS - MIGRATOR CSV POSTGRES
# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘
# Propósito: Ejecutar ciclo completo de pruebas con cleanup automático
# Author: fisherk2
# Version: 1.0 - Versión inicial
# Date: 2026-04-20
# 
# Principios Aplicados:
# - Fail-Fast (Clean Code Cap. 19): Detenerse al primer error
# - Automated Testing (Software Development Cap. 18): Tests reproducibles
# - Resource Cleanup (DevOps Best Practices): Limpieza automática INCONDICIONAL
# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘

# Modo estricto para fail-fast (Clean Code Cap. 19)
set -euo pipefail

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# CONFIGURACIÓN INICIAL
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

# Colores para output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Variables de entorno
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
readonly CONTAINER_NAME="migrator_postgres_dev"
readonly COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
readonly CONFIG_FILE="$PROJECT_DIR/.env"

# Contadores para estadísticas
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNINGS=0

# Tiempo de inicio
readonly START_TIME=$(date +%s)

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIONES DE LOGGING
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

# Función de timestamp
timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

# Funciones de logging con colores y timestamps (corregidas para set -euo pipefail)
log_info() {
    echo -e "${BLUE}[$(timestamp)] INFO:${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(timestamp)] SUCCESS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(timestamp)] WARNING:${NC} $1"
    # Incremento seguro con manejo de errores
    TESTS_WARNINGS=$((TESTS_WARNINGS + 1)) || true
}

log_error() {
    echo -e "${RED}[$(timestamp)] ERROR:${NC} $1"
}

log_test() {
    echo -e "${BLUE}[$(timestamp)] TEST:${NC} $1"
    # Incremento seguro con manejo de errores
    TESTS_TOTAL=$((TESTS_TOTAL + 1)) || true
}

log_debug() {
    echo -e "${YELLOW}[$(timestamp)] DEBUG:${NC} $1" >&2
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIÓN DE CLEANUP - CRÍTICA (DevOps Best Practices)
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# Esta función se ejecuta SIEMPRE gracias a trap cleanup EXIT
# No hay forma de omitirla, incluso con Ctrl+C o errores

cleanup() {
    log_info " Iniciando cleanup del entorno..."
    
    # Determinar el tipo de limpieza basado en el resultado de los tests
    local cleanup_type="full"  # Por defecto: limpieza completa
    
    # Verificar si los tests pasaron exitosamente (solo verificar que no haya fallidos y que haya pasados)
    if [[ ${TESTS_FAILED:-0} -eq 0 && ${TESTS_PASSED:-0} -gt 0 ]]; then
        cleanup_type="success"  # Tests exitosos: limpieza completa
        log_info "  Tests exitosos detectados - aplicando limpieza completa..."
    elif [[ ${TESTS_FAILED:-0} -gt 0 ]]; then
        cleanup_type="failed"  # Tests fallaron: limpieza parcial
        log_info "  Tests fallaron detectados - aplicando limpieza parcial..."
    else
        cleanup_type="partial"  # Ejecución incompleta: limpieza parcial
        log_info "  Ejecución incompleta - aplicando limpieza parcial..."
    fi
    
    # Detener y eliminar contenedores y volúmenes
    if docker-compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
        log_info " Deteniendo contenedores activos..."
        docker-compose -f "$COMPOSE_FILE" down -v
        log_success "✅ Contenedores y volúmenes eliminados"
    else
        log_info "ℹ️ No hay contenedores activos para eliminar"
        # Asegurar eliminación de contenedores incluso si no están activos
        log_info "🧹 Eliminando contenedores residuales..."
        docker-compose -f "$COMPOSE_FILE" down -v 2>/dev/null || true
        log_success "✅ Contenedores residuales eliminados"
    fi
    
    # Limpieza condicional de imágenes según el tipo
    case "$cleanup_type" in
        "success")
            # Tests exitosos: eliminar imagen completamente para liberar espacio
            log_info "🗑️ Eliminando imagen completamente (tests exitosos)..."
            if docker images -q "postgres:15-alpine" | grep -q .; then
                docker rmi postgres:15-alpine 2>/dev/null || true
                log_success "✅ Imagen PostgreSQL eliminada (espacio liberado)"
            fi
            
            # Eliminar imágenes huérfanas
            log_info "🧹 Limpiando imágenes huérfanas..."
            if docker images -f "dangling=true" -q | grep -q .; then
                docker rmi $(docker images -f "dangling=true" -q) 2>/dev/null || true
                log_success "✅ Imágenes huérfanas eliminadas"
            else
                log_info "ℹ️ No hay imágenes huérfanas para eliminar"
            fi
            ;;
            
        "failed")
            # Tests fallaron: eliminar solo caché para reconstrucción rápida
            log_info "🔄 Eliminando caché de imagen (tests fallaron)..."
            if docker images -q "postgres:15-alpine" | grep -q .; then
                # Forzar reconstrucción sin descargar nuevamente
                docker builder prune -f 2>/dev/null || true
                log_success "✅ Caché de Docker eliminado (reconstrucción rápida)"
            fi
            ;;
            
        "partial")
            # Ejecución incompleta: limpieza básica
            log_info "🧹 Aplicando limpieza básica (ejecución parcial)..."
            # Solo limpiar contenedores y volúmenes, mantener imagen
            ;;
    esac
    
    log_success "✅ Cleanup completado ($cleanup_type)"
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# CONFIGURACIÓN DE TRAP - GARANTIZA LIMPIEZA INCONDICIONAL
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# trap cleanup EXIT se ejecuta:
# - Al final normal del script
# - Con exit 1, 2, etc.
# - Con Ctrl+C (SIGINT)
# - Con kill (SIGTERM)
# - Con cualquier error no manejado

trap cleanup EXIT

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIONES DE VERIFICACIÓN
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
    
    # Verificar archivo de configuración
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "❌ Archivo de configuración no encontrado: $CONFIG_FILE"
        log_info "💡 Copia .env.example a .env"
        exit 2
    fi
    
    # Verificar psql
    if ! command -v psql &> /dev/null; then
        log_error "❌ psql no está instalado"
        exit 2
    fi
    
    log_success "✅ Prerequisitos verificados"
    
    # Verificar si contenedor está corriendo
    log_info " Verificando si contenedor PostgreSQL ya está corriendo..."
    
    # Verificar que el archivo docker-compose.yml existe
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_warning " Archivo docker-compose.yml no encontrado: $COMPOSE_FILE"
        return 1
    fi
    
    # Verificar si el contenedor está corriendo
    if docker-compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
        log_success " Contenedor $CONTAINER_NAME encontrado y corriendo"
        return 0
    else
        log_info " Contenedor $CONTAINER_NAME no está corriendo"
        return 1
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIÓN DE CARGA DE CONFIGURACIÓN
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

load_config() {
    log_info "📋 Cargando configuración desde $CONFIG_FILE"
    
    # Verificar que el archivo existe
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "❌ Archivo de configuración no encontrado: $CONFIG_FILE"
        log_info "💡 Copia .env.example a .env"
        exit 2
    fi
    
    # Cargar variables de entorno con manejo de errores
    if ! bash -n "$CONFIG_FILE" 2>/dev/null; then
        log_error "❌ Error de sintaxis en archivo de configuración: $CONFIG_FILE"
        exit 2
    fi
    
    set -a
    if ! source "$CONFIG_FILE" 2>/dev/null; then
        log_error "❌ Error al cargar archivo de configuración: $CONFIG_FILE"
        exit 2
    fi
    set +a
    
    # Validar variables críticas con valores por defecto
    DB_HOST="${DB_HOST:-localhost}"
    DB_PORT="${DB_PORT:-5432}"
    DB_NAME="${DB_NAME:-migrator_ecommerce}"
    DB_USER="${DB_USER:-migrator_user}"
    DB_PASSWORD="${DB_PASSWORD:-pimpumpapas}"
    
    # Validar variables críticas con valores por defecto
    local required_vars=("DB_HOST" "DB_PORT" "DB_NAME" "DB_USER" "DB_PASSWORD")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "❌ Variable requerida no configurada: $var"
            exit 2
        fi
    done
    
    log_success "✅ Configuración cargada"
    log_info "📋 Conectando a: ${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIÓN DE ESPERA Y HEALTH CHECK
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

wait_for_postgres() {
    log_info "⏳ Esperando a que PostgreSQL inicie..."
    
    echo "🔍 DEBUG: Variables en wait_for_postgres:"
    echo "   CONTAINER_NAME = $CONTAINER_NAME"
    echo "   DB_USER = $DB_USER"
    echo "   DB_NAME = $DB_NAME"
    
    # Verificar que el contenedor existe y está corriendo
    echo "🔍 DEBUG: Verificando contenedor..."
    if ! docker-compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
        echo "❌ ERROR: Contenedor $CONTAINER_NAME no encontrado o no corriendo"
        echo "🔍 DEBUG: Contenedores activos:"
        docker-compose -f "$COMPOSE_FILE" ps
        exit 1
    fi
    echo "✅ Contenedor $CONTAINER_NAME encontrado y corriendo"
    
    # Probar pg_isready directamente
    echo "🔍 DEBUG: Probando pg_isready..."
    echo "🔍 DEBUG: Probando pg_isready..."
    if docker exec "$CONTAINER_NAME" pg_isready --help &>/dev/null; then
        echo "✅ pg_isready disponible en el contenedor"
    else
        echo "❌ ERROR: pg_isready no disponible en el contenedor"
        echo "🔍 DEBUG: Probando conexión alternativa..."
        # Alternativa: intentar conexión directa
        if docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &>/dev/null; then
            echo "✅ Conexión directa funciona"
            log_success "✅ PostgreSQL está listo (verificación directa)"
            return 0
        else
            echo "❌ ERROR: Ni pg_isready ni conexión directa funcionan"
            exit 1
        fi
    fi
    
    local timeout=60
    local count=0
    
    echo "🔍 DEBUG: Iniciando bucle de espera..."
    while [[ $count -lt $timeout ]]; do
        echo -n "🔍 DEBUG: Intento $((count + 1))/$timeout - "
        if docker exec "$CONTAINER_NAME" pg_isready -U "$DB_USER" -d "$DB_NAME" 2>&1; then
            echo "✅ PostgreSQL está listo"
            log_success "✅ PostgreSQL está listo"
            return 0
        else
            echo "❌ PostgreSQL no listo aún"
        fi
        
        echo -n "."
        sleep 1
        count=$((count + 1))
    done
    
    echo
    log_error "❌ Timeout esperando a PostgreSQL"
    exit 1
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# PASO 1: CONFIGURACIÓN DE ENTORNO
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

setup_environment() {
    # log_debug "🔍 DEBUG: Iniciando setup_environment"
    
    # Verificar prerequisitos básicos y estado del contenedor
    local container_running=false
    local run_schema_exists=false
    
    # Verificar prerequisitos y estado del contenedor en una sola función
    if check_prerequisites; then
        container_running=true
    else
        container_running=false
    fi
    
    # Verificar si run_schema.sh existe
    if [[ -f "$SCRIPT_DIR/run_schema.sh" ]]; then
        run_schema_exists=true
        log_info "📋 Script run_schema.sh encontrado"
    else
        log_info "📋 Script run_schema.sh no encontrado - usando modo independiente"
    fi
    
    # Lógica de bajo acoplamiento
    if [[ "$container_running" == true ]] && [[ "$run_schema_exists" == true ]]; then
        log_info "🚀 FASE 1: Contenedor ya corriendo - omitiendo run_schema.sh"
        log_success "✅ Entorno ya configurado (contenedor existente)"
        ((TESTS_PASSED++))
        # log_debug "🔍 DEBUG: setup_environment completado - contenedor existente"
        return 0
    elif [[ "$run_schema_exists" == true ]] && [[ "$container_running" == false ]]; then
        log_info "🚀 FASE 1: Ejecutando configuración completa con run_schema.sh..."
        # log_debug "🔍 DEBUG: Ejecutando bash '$SCRIPT_DIR/run_schema.sh'"
        # log_debug "🔍 DEBUG: A punto de ejecutar run_schema.sh"
        
        # Ejecutar run_schema.sh con manejo robusto de errores
        # Mantenemos trap cleanup pero usamos subshell para aislar la ejecución
        # log_debug "🔍 DEBUG: Ejecutando run_schema.sh en subshell para mantener trap cleanup"
        
        local run_schema_result=0
        if output=$(bash "$SCRIPT_DIR/run_schema.sh" 2>&1); then
            run_schema_result=0
            echo "$output"
            # log_debug "🔍 DEBUG: run_schema.sh ejecutado, código de salida: $?"
            log_success "✅ Entorno configurado exitosamente"
            ((TESTS_PASSED++))
            # log_debug "🔍 DEBUG: run_schema.sh completado exitosamente, continuando a FASE 2"
            # log_debug "🔍 DEBUG: setup_environment completado - run_schema.sh ejecutado"
            return 0
        else
            run_schema_result=$?
            echo "$output"
            # log_debug "🔍 DEBUG: run_schema.sh ejecutado, código de salida: $run_schema_result"
            log_error "❌ Error en configuración del entorno"
            ((TESTS_FAILED++))
            # log_debug "🔍 DEBUG: run_schema.sh falló, saliendo con exit 1"
            return 1
        fi
    else
        log_info "🚀 FASE 1: Modo independiente - verificando conexión directamente"
        # log_debug "🔍 DEBUG: Ejecutando verify_connection en modo independiente"
        # Intentar verificar conexión directamente
        if verify_connection; then
            log_success "✅ Conexión verificada exitosamente"
            ((TESTS_PASSED++))
            # log_debug "🔍 DEBUG: verify_connection completado, continuando a FASE 2"
            # log_debug "🔍 DEBUG: setup_environment completado - modo independiente"
            return 0
        else
            log_error "❌ No se pudo establecer conexión a la base de datos"
            ((TESTS_FAILED++))
            # log_debug "🔍 DEBUG: verify_connection falló, saliendo con exit 1"
            return 1
        fi
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# PASO 2: VERIFICAR CONEXIÓN
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

verify_connection() {
    log_test "🔌 Verificando conexión a PostgreSQL..."
    
    echo "🔍 DEBUG: Variables de conexión:"
    echo "   DB_HOST = $DB_HOST"
    echo "   DB_PORT = $DB_PORT"
    echo "   DB_USER = $DB_USER"
    echo "   DB_NAME = $DB_NAME"
    echo "   DB_PASSWORD = [OCULTA]"
    
    # Verificar que el contenedor está corriendo
    echo " DEBUG: Verificando estado del contenedor..."
    if docker-compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
        echo " Contenedor está corriendo"
        docker-compose -f "$COMPOSE_FILE" ps
    else
        echo "❌ Contenedor no está corriendo"
        exit 1
    fi
    
    # Verificar que el puerto está mapeado
    echo " DEBUG: Verificando mapeo de puertos..."
    echo "🔍 DEBUG: Verificando mapeo de puertos..."
    local port_mapping
    port_mapping=$(docker port "$CONTAINER_NAME" 5432 2>/dev/null || echo "NO_MAPEADO")
    echo "   Port mapping 5432: $port_mapping"
    
    # Intentar conexión con detalles
    echo "🔍 DEBUG: Intentando conexión psql..."
    echo "   Comando: PGPASSWORD=\"*****\" psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \"SELECT 1;\""
    
    # Probar conexión con output visible para debugging
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" 2>&1; then
        echo "✅ Comando psql ejecutado exitosamente"
        log_success "✅ Conexión exitosa a PostgreSQL"
        TESTS_PASSED=$((TESTS_PASSED + 1)) || true
    else
        echo "❌ ERROR: Comando psql falló"
        echo "🔍 DEBUG: Probando conexión alternativa con docker exec..."
        
        # Alternativa: probar conexión desde dentro del contenedor
        if docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &>/dev/null; then
            echo "✅ Conexión desde dentro del contenedor funciona"
            echo "❌ ERROR: El problema es la conexión desde el host (posible problema de puerto o red)"
        else
            echo "❌ ERROR: Ni siquiera funciona desde dentro del contenedor"
        fi
        
        log_error "❌ Error de conexión a PostgreSQL"
        exit 1
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# PASO 3: TESTS UNITARIOS DEL SCHEMA
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

run_schema_tests() {
    log_test "🧪 Ejecutando tests unitarios del schema con test_schema_operations.sql..."
    
    # Verificar que el script de tests existe
    local test_script="$PROJECT_DIR/scripts/sql/test_schema_operations.sql"
    if [[ ! -f "$test_script" ]]; then
        log_error "❌ Script de tests no encontrado: $test_script"
        exit 1
    fi
    
    # Ejecutar tests unitarios usando psql (compatible con RAISE NOTICE)
    log_info "  Ejecutando tests unitarios con rollback automático..."
    
    # Capturar salida para analizar resultados de tests
    local test_output
    test_output=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$test_script" 2>&1)
    local exit_code=$?
    
    # Mostrar salida completa
    echo "$test_output"
    
    # Analizar salida para detectar tests fallidos y rollback parcial
    local failed_tests
    failed_tests=$(echo "$test_output" | grep -c "TEST FAILED" || true)
    local passed_tests
    passed_tests=$(echo "$test_output" | grep -c "TEST PASSED" || true)
    local rollback_partial
    rollback_partial=$(echo "$test_output" | grep -c "rollback parcial" || true)
    
    # Actualizar contadores según resultados
    if [[ $failed_tests -gt 0 ]]; then
        log_error "  Se detectaron $failed_tests tests fallidos"
        ((TESTS_FAILED += failed_tests))
        # Solo sumar los que realmente pasaron (no contar fallidos)
        ((TESTS_PASSED += passed_tests - failed_tests))
        return 1
    elif [[ $rollback_partial -gt 0 ]]; then
        log_warning "  Tests pasaron pero hay rollback parcial - datos persistieron"
        ((TESTS_PASSED += passed_tests))
        ((TESTS_WARNINGS++))
        return 1  # Tratar rollback parcial como fallo para limpieza parcial
    elif [[ $exit_code -eq 0 && $passed_tests -gt 0 ]]; then
        log_success "  Tests unitarios ejecutados exitosamente ($passed_tests tests pasaron)"
        ((TESTS_PASSED += passed_tests))
    else
        log_error "  Error en ejecución de tests unitarios (código: $exit_code)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# PASO 4: RESUMEN FINAL
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

show_summary() {
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))
    
    echo
    echo "============================================================================"
    log_info "📊 RESUMEN FINAL DE TESTS"
    echo "============================================================================"
    log_info "⏱️ Tiempo total de ejecución: ${duration}s"
    log_info "📈 Total de tests ejecutados: $TESTS_TOTAL"
    log_success "✅ Tests pasados: $TESTS_PASSED"
    
    if [[ $TESTS_FAILED -gt 0 ]]; then
        log_error "❌ Tests fallidos: $TESTS_FAILED"
    fi
    
    if [[ $TESTS_WARNINGS -gt 0 ]]; then
        log_warning "⚠️ Advertencias: $TESTS_WARNINGS"
    fi
    
    echo "============================================================================"
    
    # Exit code basado en resultados
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_success "🎉 TODOS LOS TESTS PASARON - SISTEMA FUNCIONAL"
        exit 0
    else
        log_error "💥 HAY TESTS FALLIDOS - REVISAR EL SISTEMA"
        exit 1
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIÓN PRINCIPAL - ORQUESTACIÓN
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

main() {
    echo "============================================================================"
    log_info " INICIANDO CICLO COMPLETO DE TESTS - MIGRATION CSV POSTGRES"
    echo "============================================================================"
    
    # Cargar configuración primero (necesario para setup_environment)
    load_config
    
    # FASE 1: Configurar entorno con bajo acoplamiento
    # log_debug "🔍 DEBUG: Iniciando FASE 1 - Configuración de entorno"
    if setup_environment; then
        # log_debug "🔍 DEBUG: FASE 1 completada exitosamente"
        true  # No-op for readability
    else
        log_error "❌ Error en FASE 1 - Configuración del entorno"
        exit 1
    fi
    
    # Punto de control antes de FASE 2
    # log_debug "🔍 DEBUG: Antes de FASE 2 - TESTS_PASSED=$TESTS_PASSED, TESTS_FAILED=$TESTS_FAILED"
    
    # FASE 2: Ejecutar pruebas de schema
    log_info "🚀 FASE 2: Ejecutando pruebas de schema..."
    # log_debug "🔍 DEBUG: Llamando a run_schema_tests"
    run_schema_tests
    # log_debug "🔍 DEBUG: run_schema_tests completado"
    
    # Mostrar resumen final
    show_summary
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# EJECUCIÓN
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

# Ejecutar función principal
log_info "🚀 Iniciando ejecución principal..."
main "$@"