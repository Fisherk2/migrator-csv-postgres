# Project Context: Migrador CSV → PostgreSQL

## 🎯 Propósito y Alcance

> [!SUMMARY]
> **Objetivo**: Herramienta CLI que migra datos CSV → PostgreSQL reutilizando validadores del proyecto `auditor-de-calidad-de-datos`, generando reportes de errores accionables.

**Entrada**: Archivos CSV con datos de customers/products/orders  
**Proceso**: Validación tipada + reglas de negocio + ingesta atómica  
**Salida**: Datos en PostgreSQL + reporte JSON/texto con errores y sugerencias

**Estado Actual**: Activo - MVP implementado con pruebas funcionando

**Criterios de éxito MVP**:
- [x] ✅ Migración de 1000 filas en <5 minutos
- [x] ✅ Reuso funcional de 3+ validadores del auditor
- [x] ✅ Reporte con conteo: importados/rechazados + sugerencias
- [x] ✅ Rollback automático ante errores críticos
- [x] ✅ Cero dependencias no-open-source

## 📋 Requisitos Modularizados

### Requisitos Funcionales (RF)

| ID | Módulo | Descripción | Criterio de Aceptación | Prioridad |
|----|--------|-------------|----------------------|-----------|
| **RF-001** | `csv_loader` | Ingesta eficiente vía `COPY FROM` | Temp table creada con encoding UTF-8 validado | 🔴 Alta |
| **RF-002** | `validators::reused` | Reuso de `validate_integer`, `validate_email` | Errores incluyen `row_num` y `field_name` | 🔴 Alta |
| **RF-003** | `validators::config` | Validación de campos obligatorios vía YAML | Mensaje: "Campo X requerido en fila Y" | 🔴 Alta |
| **RF-004** | `validators::custom` | Regex email (RFC 5322 simplificado) + teléfono | Sugerencia: "¿Quisiste decir user@domain.com?" | 🟡 Media |
| **RF-005** | `report_generator` | Reporte dual: JSON machine-readable + texto humano | Incluye: `{imported: N, rejected: M, errors: [...]}` | 🔴 Alta |
| **RF-006** | `db_connector` | Transacción atómica con rollback seguro | Log: "Rollback ejecutado: [motivo]" | 🔴 Alta |
| **RF-007** | `cli` | Flags: `--config`, `--dry-run`, `--verbose` | `--dry-run` no modifica BD, solo valida | 🟡 Media |
| **RF-008** | `config_loader` | Carga y validación de schema YAML al iniciar | Error claro si YAML no cumple schema esperado | 🟡 Media |
| **RF-009** | `tests::integration` | Fixtures: CSV válidos/inválidos + verificación de conteo | pytest pasa con BD de prueba en Docker | 🔴 Alta |
| **RF-010** | `docs::reuse` | `REUSE_STRATEGY.md` con comandos de submodule | Onboarding: nuevo dev puede extender validadores en <1h | 🟢 Baja |

### Requisitos No Funcionales (RNF)

| ID | Categoría | Especificación | Métrica de Verificación |
|----|-----------|---------------|------------------------|
| **RNF-001** | Performance | <5 min para 1000 filas | `time run_migration.py --config ...` |
| **RNF-002** | Licencias | 100% dependencias permisivas (MIT/BSD/Apache) | `pip-licenses --format=markdown` |
| **RNF-003** | Observabilidad | Logging estructurado: `INFO` para flujo, `ERROR` con contexto | Logs parseables por `jq` |
| **RNF-004** | Acoplamiento | Imports explícitos del auditor; sin herencia cruzada | `grep -r "from auditor" src/` muestra solo funciones |
| **RNF-005** | Internacionalización | Errores humanos en ES, logs técnicos en EN | `grep "Error:" logs/` vs `grep "Error:" report_*.txt` |

## 🌐 Dominio: Entidades y Relaciones

### Esquema E-Commerce (MVP)

```sql
-- customers
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- products  
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    is_active BOOLEAN DEFAULT true
);

-- orders
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled'))
);
```

### Entidades de Infraestructura

| Entidad | Propósito | Campos Clave | Persistencia |
|---------|-----------|-------------|-------------|
| `MigrationLog` | Auditoría del proceso | `id`, `timestamp`, `csv_file`, `target_table`, `status`, `error_count` | PostgreSQL (tabla `audit.migration_logs`) |
| `ValidationError` | Errores accionables | `row_num`, `field`, `invalid_value`, `reason`, `suggestion`, `is_critical` | Memoria → JSON/CSV (no se persiste en BD) |
| `ValidationRule` | Reglas configurables | `field`, `type`, `params`, `error_message`, `suggestion_template` | YAML en `config/validation_rules/` |

> [!NOTE]
> **Alcance MVP**: Migramos `customers`, `products`, `orders` de forma independiente.  
> La relación `Order`↔`Product` (N:M) requiere tabla `order_items` → **Fase 2**.

## 🚀 Orden de Implementación

```yaml
phases:
  - name: "foundation"
    duration: "8-10h"
    tasks:
      - id: "F-001"
        name: "Configurar submodule del auditor"
        files: [".gitmodules", "extern/auditor/", "src/validators/__init__.py"]
        acceptance: "import validate_integer from validators; assert callable(validate_integer)"
        
      - id: "F-002" 
        name: "Definir schema de BD + scripts de inicialización"
        files: ["domain/e-commerce/schema.sql", "scripts/sql/", "scripts/init_db.py"]
        acceptance: "docker compose up -d db && ./scripts/init_db.py --verify"
        
      - id: "F-003"
        name: "Configurar logging estructurado + helpers"
        files: ["src/utils/logger.py", "src/utils/helpers.py"]
        acceptance: "logger.info('test') produce JSON parseable en stdout"

  - name: "core"
    duration: "20-25h" 
    tasks:
      - id: "C-001"
        name: "Implementar DBConnector (Repository)"
        files: ["src/migrator/db_connector.py"]
        depends_on: ["F-002"]
        acceptance: "DBConnector.ensure_table_exists('customers', schema) == True"
        
      - id: "C-002"
        name: "Implementar CSVLoader con COPY FROM"
        files: ["src/migrator/csv_loader.py"] 
        depends_on: ["C-001"]
        acceptance: "load_csv_to_temp_table('test.csv') returns temp_table_name + row_count"
        
      - id: "C-003"
        name: "Adapter para validadores reutilizados + custom"
        files: ["src/validators/custom/", "src/validators/__init__.py"]
        depends_on: ["F-001"]
        acceptance: "ValidatorAdapter.validate_email('bad@') returns (False, reason, suggestion)"

  - name: "orchestration"
    duration: "10-12h"
    tasks:
      - id: "O-001"
        name: "MigrationPipeline con Template Method"
        files: ["src/migrator/pipeline.py"]
        depends_on: ["C-001", "C-002", "C-003"]
        acceptance: "Pipeline.execute() returns {status: 'success', imported: N, rejected: M}"
        
      - id: "O-002"
        name: "ReportGenerator: JSON + texto humano"
        files: ["src/migrator/report_generator.py"]
        acceptance: "Report incluye conteo + errores con sugerencias en ES"

  - name: "delivery"
    duration: "6-8h"
    tasks:
      - id: "D-001"
        name: "CLI entry point con argparse"
        files: ["scripts/run_migration.py"]
        depends_on: ["O-001"]
        acceptance: "--dry-run valida sin modificar BD; --verbose muestra logs detallados"
        
      - id: "D-002"
        name: "Tests de integración + fixtures"
        files: ["test/integration/", "test/fixtures/"]
        acceptance: "pytest test/integration/ pasa con BD de prueba"
        
      - id: "D-003"
        name: "Documentación mínima viable"
        files: ["README.md", "docs/TROUBLESHOOTING.md"]
        acceptance: "Nuevo dev puede ejecutar migración de ejemplo en <15 min"
```

## 🔗 Referencias Curated

```yaml
references:
  architecture:
    - title: "Clean Architecture Lite"
      url: "https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html"
      relevance: "Separación de capas + inversión de dependencias"
      
  patterns:
    - title: "Strategy Pattern in Python"
      url: "https://refactoring.guru/design-patterns/strategy/python"
      relevance: "Validaciones configurables vía YAML"
      
  postgres:
    - title: "COPY Command Best Practices"
      url: "https://www.postgresql.org/docs/current/sql-copy.html"
      relevance: "RF-001: ingesta eficiente de CSV"
      
  testing:
    - title: "Testing with PostgreSQL in Docker"
      url: "https://www.testcontainers.org/modules/databases/postgres/"
      relevance: "RF-009: tests de integración reproducibles"
      
  submodule:
    - title: "Git Submodules: A Survival Guide"
      url: "https://git-scm.com/book/en/v2/Git-Tools-Submodules"
      relevance: "Integración segura con auditor-de-calidad-de-datos"
```

## 🔄 Guía de Actualización

> [!CASCADE]
> **Cómo procesar esta documentación**:

1. **Inicio**: Leer `metadata/project.yaml` para contexto global
2. **Requisitos**: Procesar `requirements/functional.md` para entender RFs
3. **Arquitectura**: Consultar `architecture/layers.md` para dependencias entre módulos
4. **Implementación**: Seguir `implementation/tasks.yaml` en orden (respeta `depends_on`)
5. **Validación**: Usar `testing/suites/` para verificar aceptación de cada tarea

**Convenciones**:
- `[[enlace]]` = referencia cruzada a otro archivo en este árbol
- `✅` = criterio de aceptación verificable automáticamente
- `🔴/🟡/🟢` = prioridad para planificación de sprints

**Actualizaciones**:
- Modificar solo archivos en `src/`, `config/`, `docs/`, `scripts/`, `test/`
- Para cambios en arquitectura: actualizar `.agent-instructions/architecture.md` + notificar en `CHANGELOG.md`
- Para extender validadores: seguir `docs/REUSE_STRATEGY.md`
