#!/bin/bash

# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘
# SCRIPT DE AUTOMATIZACIÓN DE CONFIGURACIÓN DE ESQUEMA - MIGRATOR CSV POSTGRES
# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘
# Propósito: Ejecutar configuración de esquema
# Author: fisherk2
# Version: 1.0 - Versión inicial
# Date: 2026-04-21
# 🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘🮙🮘🮙🮙🮘

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
readonly SQL_SCRIPTS_DIR="$PROJECT_DIR/scripts/sql"

# Variables de contadores
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_WARNINGS=0
START_TIME=$(date +%s)

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
# FUNCIÓN DE VERIFICACIÓN
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

# Verificar prerequisitos
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
# PASO 1: CREAR CONTENEDOR
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

create_container() {
    log_test "🐳 Creando contenedor Docker..."
    
    # Verificar variables críticas
    log_info "📋 COMPOSE_FILE = $COMPOSE_FILE"
    log_info "📋 Directorio actual = $(pwd)"
    
    # Verificar que el archivo docker-compose.yml existe
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "❌ Archivo docker-compose.yml no encontrado: $COMPOSE_FILE"
        exit 1
    fi
    
    # Verificar que Docker está disponible
    if ! command -v docker &> /dev/null; then
        log_error "❌ Docker no está disponible"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "❌ Docker Compose no está disponible"
        exit 1
    fi
    
    # Reconstruir imagen y crear contenedor con captura de errores
    log_info "🔨 Reconstruyendo imagen PostgreSQL (sin caché)..."
    if docker-compose -f "$COMPOSE_FILE" build --no-cache 2>&1; then
        log_success "✅ Imagen reconstruida exitosamente"
    else
        log_error "❌ Error al reconstruir imagen"
        log_info "📋 Verificando logs de construcción..."
        docker-compose -f "$COMPOSE_FILE" build --no-cache 2>&1
        exit 1
    fi
    
    log_info "🐳 Creando contenedor Docker..."
    if docker-compose -f "$COMPOSE_FILE" up -d 2>&1; then
        log_success "✅ Contenedor creado exitosamente"
        # Incremento seguro
        TESTS_PASSED=$((TESTS_PASSED + 1)) || true
        
        # Verificar que el contenedor está corriendo
        if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
            log_success "✅ Contenedor está corriendo"
        else
            log_error "❌ Contenedor no está corriendo después de creación"
            docker-compose -f "$COMPOSE_FILE" ps
            exit 1
        fi
    else
        log_error "❌ Error al crear contenedor"
        log_info "📋 Verificando logs de Docker Compose..."
        docker-compose -f "$COMPOSE_FILE" logs --tail=20
        exit 1
    fi
    
    # Esperar a que PostgreSQL inicie
    wait_for_postgres
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
# PASO 3: APLICAR MIGRACIONES
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

apply_migrations() {
    log_info "📦 Aplicando migraciones con init_db.py..."
    
    # Verificar que el script init_db.py existe
    if [[ ! -f "$PROJECT_DIR/scripts/init_db.py" ]]; then
        log_error "❌ Script init_db.py no encontrado en: $PROJECT_DIR/scripts/"
        exit 1
    fi
    
    # Verificar y activar entorno virtual si existe
    local venv_path="$PROJECT_DIR/.venv"
    if [[ -d "$venv_path" ]]; then
        log_info "🐍 Entorno virtual detectado, activando..."
        if [[ -f "$venv_path/bin/activate" ]]; then
            source "$venv_path/bin/activate"
            log_success "✅ Entorno virtual activado"
        elif [[ -f "$venv_path/bin/activate.fish" ]]; then
            source "$venv_path/bin/activate.fish"
            log_success "✅ Entorno virtual (fish) activado"
        else
            log_warning "⚠️ Entorno virtual encontrado pero no hay script de activación"
        fi
    else
        log_info "ℹ️ No se encontró entorno virtual, usando Python global"
    fi
    
    # Verificar dependencias de Python
    log_test "🔍 Verificando dependencias de Python..."
    if ! python3 -c "import psycopg2; print('psycopg2 disponible')" 2>/dev/null; then
        log_error "❌ psycopg2 no está disponible. Instala con: pip install psycopg2-binary"
        exit 1
    fi
    log_success "✅ Dependencias de Python verificadas"
    
    # Ejecutar script init_db.py con variables de entorno exportadas
    log_test "▶️ Ejecutando scripts/init_db.py..."
    
    # Asegurar que las variables de entorno estén disponibles para el script Python
    export DB_HOST="$DB_HOST"
    export DB_PORT="$DB_PORT"
    export DB_NAME="$DB_NAME"
    export DB_USER="$DB_USER"
    export DB_PASSWORD="$DB_PASSWORD"
    
    # Ejecutar el script Python desde el directorio del proyecto
    cd "$PROJECT_DIR"
    if python3 scripts/init_db.py; then
        log_success "✅ Migraciones aplicadas exitosamente via init_db.py"
        ((TESTS_PASSED++))
    else
        log_error "❌ Error al ejecutar scripts/init_db.py"
        exit 1
    fi
}

# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIÓN PRINCIPAL - ORQUESTACIÓN
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

main() {
    echo "============================================================================"
    log_info " INICIANDO CONFIGURACIÓN DE ENTORNO - MIGRATION CSV POSTGRES"
    echo "============================================================================"
    
    # Ejecutar pasos en orden
    check_prerequisites
    load_config
    create_container
    verify_connection
    apply_migrations
    
    echo "============================================================================"
    log_success " ENTORNO CONFIGURADO EXITOSAMENTE"
    echo "============================================================================"
    log_info " Contenedor: $CONTAINER_NAME"
    log_info " Base de datos: $DB_NAME"
    log_info " Conexión: ${DB_USER}@${DB_HOST}:${DB_PORT}"
    echo "============================================================================"
}

# Ejecutar función principal
log_info " Iniciando configuración del entorno..."
main "$@"

# Asegurar terminación exitosa explícita
exit 0
