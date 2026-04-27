# Configuración de PostgreSQL - Migrador CSV

---
metadata:
  tipo_documento: Guía de Configuración
  dominio: Infraestructura de Base de Datos
  estado: Aprobado
  fecha_creacion: 2026-04-27
  fecha_actualizacion: 2026-04-27
  autor: fisherk2, DBA Senior
  revisores: [Equipo de DevOps]
  stakeholders: [Desarrolladores, DBAs, Equipo QA]
  tags: [postgresql, docker, setup, infraestructura]
  version: 1.0
  relacionado_con: [[docker-compose.yml]], [[.env.example]], [[scripts/sql]]
---

## Introducción

Este documento proporciona instrucciones paso a paso para configurar PostgreSQL para el Migrador CSV, tanto en entorno nativo como mediante Docker Compose. Según *Systems Analysis & Design* (Cap. 11), la documentación de implementación debe reducir la curva de configuración y acelerar el diagnóstico de problemas.

**Propósito:**
- Configurar PostgreSQL para desarrollo y testing
- Ejecutar scripts SQL de inicialización
- Verificar salud de la base de datos
- Realizar teardown seguro del entorno

**Requisitos Previos:**
- Docker 20.10+ y Docker Compose 2.0+ (para setup Docker)
- PostgreSQL 15+ o psql client (para setup nativo)
- Python 3.9+ con psycopg2-binary (para scripts de inicialización)

---

## 📋 Tabla de Contenidos

- [Opción 1: Setup con Docker Compose (Recomendado)](#opción-1-setup-con-docker-compose-recomendado)
- [Opción 2: Setup Nativo PostgreSQL](#opción-2-setup-nativo-postgresql)
- [Ejecución de Scripts SQL](#ejecución-de-scripts-sql)
- [Verificación de Salud](#verificación-de-salud)
- [Teardown Seguro](#teardown-seguro)
- [Script Automatizado](#script-automatizado)

---

## Opción 1: Setup con Docker Compose (Recomendado)

### Por qué Docker Compose

Docker Compose es la opción recomendada para desarrollo porque:
- **Reproducibilidad:** Mismo entorno en todas las máquinas
- **Aislamiento:** No afecta PostgreSQL nativo del sistema
- **Cleanup Fácil:** Eliminar contenedores y volúmenes con un comando
- **Health Checks:** `pg_isready` integrado para verificar disponibilidad

### Paso 1: Configurar Variables de Entorno

> [!WARNING]
> **NUNCA** commits el archivo `.env` real. Solo `.env.example` debe estar en el repositorio.

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

Variables mínimas requeridas en `.env`:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=migrator_ecommerce
DB_USER=migrator_user
DB_PASSWORD=tu_contraseña_secreta_aqui
```

### Paso 2: Iniciar Contenedor PostgreSQL

```bash
# Iniciar contenedor en background
docker compose up -d

# Ver logs de inicio
docker compose logs -f postgres
```

**¿Qué hace este comando?**
- `up -d`: Crea e inicia contenedores en modo detached (background)
- `docker compose` lee `docker-compose.yml` para configuración
- Imagen `postgres:15-alpine` se descarga si no existe localmente

### Paso 3: Esperar a que PostgreSQL esté Listo

PostgreSQL requiere ~10-30 segundos para inicializar. El healthcheck automático en `docker-compose.yml` verifica esto.

```bash
# Verificar healthcheck
docker compose ps

# Output esperado:
# NAME                    STATUS          PORTS
# migrator_postgres_dev   Up (healthy)   0.0.0.0:5432->5432/tcp
```

**Healthcheck configurado:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U migrator_user -d migrator_ecommerce"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s
```

### Paso 4: Verificar Conexión

```bash
# Usar psql desde el host
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -c "SELECT version();"

# Output esperado:
# PostgreSQL 15.x on x86_64-pc-linux-gnu...
```

**¿Por qué `PGPASSWORD`?**
- Evita prompt interactivo de contraseña
- Permite automatización en scripts
- **NO** almacenar en historial de shell (usar `unset HISTFILE` o `set +o history`)

### Paso 5: Ejecutar Scripts de Inicialización

```bash
# Usar script automatizado (recomendado)
bash scripts/run_schema.sh

# O ejecutar scripts SQL manualmente
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -f scripts/sql/01_create_database.sql
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -f scripts/sql/02_create_schema.sql
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -f scripts/sql/03_create_indexes.sql
```

**Scripts SQL en orden:**
1. `01_create_database.sql`: Crea base de datos si no existe
2. `02_create_schema.sql`: Crea tablas (customers, products, orders)
3. `03_create_indexes.sql`: Crea índices para performance

### Paso 6: Verificar Tablas Creadas

```bash
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -c "\dt"

# Output esperado:
# Schema |   Name    | Type  |  Owner
#--------+-----------+-------+-------------
# public | customers | table | migrator_user
# public | orders    | table | migrator_user
# public | products  | table | migrator_user
```

---

## Opción 2: Setup Nativo PostgreSQL

### Paso 1: Instalar PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql-15 postgresql-client-15
```

**macOS (Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Windows:**
- Descargar installer desde https://www.postgresql.org/download/windows/
- Seguir wizard de instalación

### Paso 2: Crear Usuario y Base de Datos

```bash
# Conectar como usuario postgres
sudo -u postgres psql

# En psql:
CREATE USER migrator_user WITH PASSWORD 'tu_contraseña_secreta';
CREATE DATABASE migrator_ecommerce OWNER migrator_user;
GRANT ALL PRIVILEGES ON DATABASE migrator_ecommerce TO migrator_user;
\q
```

**¿Por qué `sudo -u postgres`?**
- Usuario `postgres` es superuser por defecto
- Solo puede crear usuarios y bases de datos
- Evita usar `sudo` para operaciones normales de aplicación

### Paso 3: Configurar pg_hba.conf (si es necesario)

Si obtienes error "connection refused" o "authentication failed":

```bash
# Ubicación de pg_hba.conf:
# Ubuntu/Debian: /etc/postgresql/15/main/pg_hba.conf
# macOS: /usr/local/var/postgres@15/pg_hba.conf

# Agregar línea para autenticación md5:
host    migrator_ecommerce    migrator_user    127.0.0.1/32    md5

# Recargar configuración
sudo systemctl reload postgresql
```

### Paso 4: Ejecutar Scripts SQL

```bash
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -f scripts/sql/01_create_database.sql
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -f scripts/sql/02_create_schema.sql
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -f scripts/sql/03_create_indexes.sql
```

---

## Ejecución de Scripts SQL

### Orden de Ejecución

Los scripts SQL deben ejecutarse en este orden específico:

| Script | Propósito | Dependencias |
|--------|-----------|--------------|
| `01_create_database.sql` | Crea BD y usuario | Ninguna |
| `02_create_schema.sql` | Crea tablas y constraints | BD debe existir |
| `03_create_indexes.sql` | Crea índices y triggers | Tablas deben existir |
| `test_schema_operations.sql` | Tests unitarios de schema | Todo anterior |

### Ejecución Manual con psql

```bash
# Ejecutar un solo script
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -f scripts/sql/02_create_schema.sql

# Ejecutar todos los scripts en orden
for script in scripts/sql/0{1,2,3}_*.sql; do
    echo "Ejecutando $script..."
    PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -f "$script"
done
```

### Ejecución con Docker Exec

```bash
# Ejecutar desde dentro del contenedor
docker exec -i migrator_postgres_dev psql -U migrator_user -d migrator_ecommerce < scripts/sql/02_create_schema.sql
```

**¿Por qué `-i`?**
- `-i`: Modo interactivo (necesario para input de stdin)
- Sin `-i`, psql puede fallar con pipe desde archivo

---

## Verificación de Salud

### Verificar Conexión

```bash
# Método 1: psql directo
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -c "SELECT 1;"

# Método 2: pg_isready (Docker)
docker exec migrator_postgres_dev pg_isready -U migrator_user -d migrator_ecommerce

# Output esperado:
# migrator_ecommerce:5432 - accepting connections
```

### Verificar Tablas y Constraints

```bash
# Listar tablas
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -c "\dt"

# Ver estructura de tabla específica
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -c "\d customers"

# Ver constraints
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -c "\d+ orders"
```

### Verificar Índices

```bash
# Listar índices
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -c "\di"

# Ver tamaño de índices
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -c "SELECT indexname, pg_size_pretty(pg_relation_size(indexname)) FROM pg_indexes WHERE schemaname = 'public';"
```

### Ejecutar Tests de Schema

```bash
# Script automatizado de verificación
bash scripts/verify_setup.sh

# O ejecutar tests SQL manualmente
PGPASSWORD="tu_contraseña" psql -h localhost -p 5432 -U migrator_user -d migrator_ecommerce -f scripts/sql/test_schema_operations.sql
```

**Salida esperada de tests:**
```
NOTICE:  TEST PASSED: Tabla customers existe
NOTICE:  TEST PASSED: Tabla products existe
NOTICE:  TEST PASSED: Tabla orders existe
NOTICE:  TEST PASSED: FK orders.customer_id existe
NOTICE:  TEST PASSED: Constraint chk_orders_status existe
```

---

## Teardown Seguro

### Docker Compose

```bash
# Detener contenedores (mantener volúmenes)
docker compose down

# Detener y eliminar volúmenes (datos perdidos)
docker compose down -v

# Detener, eliminar volúmenes e imágenes
docker compose down -v --rmi all
```

> [!WARNING]
> **`docker compose down -v` elimina todos los datos.** Úsalo solo en desarrollo o testing.

### PostgreSQL Nativo

```bash
# Eliminar base de datos
sudo -u postgres psql -c "DROP DATABASE migrator_ecommerce;"

# Eliminar usuario
sudo -u postgres psql -c "DROP USER migrator_user;"

# O usar script SQL
PGPASSWORD="postgres_password" psql -h localhost -U postgres -f scripts/sql/drop_database.sql
```

> [!WARNING]
> **`DROP DATABASE` es irreversible.** Asegúrate de tener backup si necesitas datos.

### Limpieza Completa (Docker)

```bash
# Eliminar contenedores, volúmenes, imágenes huérfanas
docker compose down -v
docker system prune -a --volumes

# Verificar limpieza
docker ps -a
docker volume ls
docker images
```

---

## Script Automatizado

### scripts/run_schema.sh

Este script automatiza todo el proceso de configuración:

```bash
# Ejecutar configuración completa
bash scripts/run_schema.sh
```

**Qué hace el script:**
1. Verifica prerequisitos (Docker, Docker Compose, psql)
2. Carga configuración desde `.env`
3. Crea contenedor Docker
4. Espera a que PostgreSQL esté listo (healthcheck)
5. Verifica conexión
6. Ejecuta `scripts/init_db.py` (aplica migraciones)

**Ventajas:**
- Fail-fast: Detiene al primer error
- Logging estructurado con colores
- Manejo robusto de errores
- Compatible con entornos virtuales Python

### scripts/verify_setup.sh

Este script ejecuta tests de verificación con cleanup automático:

```bash
# Ejecutar ciclo completo de tests
bash scripts/verify_setup.sh
```

**Qué hace el script:**
1. Configura entorno (si es necesario)
2. Verifica conexión
3. Ejecuta tests unitarios de schema
4. Muestra resumen de resultados
5. **Cleanup automático incondicional** (trap EXIT)

**Cleanup inteligente:**
- Tests exitosos: Elimina imagen completamente
- Tests fallados: Elimina solo caché para reconstrucción rápida
- Ejecución incompleta: Limpieza básica

---

## Troubleshooting Rápido

| Error | Causa | Solución |
|-------|-------|----------|
| `No module named 'psycopg2'` | Falta dependencia Python | `pip install psycopg2-binary` |
| `connection refused` | PostgreSQL no iniciado | `docker compose up -d` o `sudo systemctl start postgresql` |
| `authentication failed` | Contraseña incorrecta | Verificar `.env` y `pg_hba.conf` |
| `database does not exist` | BD no creada | Ejecutar `01_create_database.sql` |
| `port already in use` | Puerto 5432 ocupado | Cambiar `DB_PORT` en `.env` |

Para troubleshooting detallado, ver [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## Referencias

- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [ADR-MIG-001: Clean Architecture](ADR.md#adr-mig-001-clean-architecture-sobre-mvcmonolito)
- [ERD del Sistema](ERD.md)

---

> **Nota de Seguridad:** Nunca hardcode credenciales en código. Usa variables de entorno o secretos management (Vault, AWS Secrets Manager) en producción.