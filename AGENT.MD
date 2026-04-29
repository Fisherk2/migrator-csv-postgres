# 🗂️ Migrador CSV → PostgreSQL con Validación Reutilizable
*Documentación modularizada para Cascade*

```yaml
# Frontmatter: Metadatos estructurados para procesamiento automático
project:
  name: "migrator-csv-postgres"
  version: "0.1.0"
  status: "active"
  created: "2026-04-15"
  updated: "2026-04-28T00:00:00Z"
  
dependencies:
  external:
    - name: "auditor-de-calidad-de-datos"
      type: "git_submodule"
      url: "https://github.com/Fisherk2/auditor-de-calidad-de-datos"
      integration: "import_functions"
      constraint: "read_only"
  
  python:
    runtime: ["psycopg2-binary>=2.9.0", "pyyaml>=6.0.0"]
    dev: ["pytest>=7.0.0", "pytest-cov>=4.0.0", "black>=23.0.0"]
  
  database:
    engine: "postgresql>=15"
    container: "postgres:15-alpine"
    schema: "e-commerce"
    
context:
  domain: "e-commerce"
  tables: ["customers", "products", "orders"]
  language:
    errors_human: "es"
    logs_tech: "en"
    
architecture:
  pattern: "layered_clean_architecture_lite"
  principles: ["SOLID", "DRY", "dependency_inversion"]
  layers:
    - name: "presentation"
      component: "CLI"
      tech: "argparse"
    - name: "application" 
      component: "MigrationPipeline"
      pattern: "template_method"
    - name: "domain"
      components: ["Validators::reused", "Validators::custom"]
      pattern: "strategy"
    - name: "infrastructure"
      components: ["DBConnector", "CSVLoader", "Utils"]
      pattern: "repository"
      
testing:
  strategy: "4_phase_testing"
  phases:
    - name: "environment_verification"
      script: "./scripts/verify_setup.sh"
    - name: "unit_tests"
      command: "python3 -m pytest tests/unit/ -v"
    - name: "integration_tests"
      command: "./scripts/run_schema.sh && pytest tests/integration/ -v -m integration"
    - name: "e2e_tests"
      script: "./scripts/run_integration_tests.sh"
```

---

## 🚀 Quick Start

**Propósito**: Herramienta CLI que migra datos CSV → PostgreSQL con validación reutilizable.

### Comandos Esenciales
```bash
# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos (Docker + PostgreSQL)
./scripts/run_schema.sh

# Ejecutar migración
python scripts/run_migration.py --config config/default_migration.yaml

# Ejecutar pruebas unitarias
python3 -m pytest tests/unit/ -v

# Ejecutar pruebas de integración (pytest)
./scripts/run_schema.sh && pytest tests/integration/ -v -m integration

# Ejecutar pruebas E2E completas
./scripts/run_integration_tests.sh --verbose

# Verificar entorno
./scripts/verify_setup.sh

# Formatear código
black src/ tests/
```

### Estructura del Proyecto
```
src/migrator/          # Lógica principal del migrador
├── pipeline.py         # Orquestador del flujo (Template Method)
├── csv_loader.py       # Carga y validación CSV con COPY FROM
├── db_connector.py    # Operaciones PostgreSQL con transacciones
├── error_handler.py    # Manejo acumulado de errores
├── report_generator.py # Generación de reportes JSON/texto
└── __init__.py

src/validators/         # Validadores reutilizables
├── __init__.py        # Interfaz con submodule auditor
└── custom/            # Validadores específicos del proyecto
    ├── email_validator.py
    ├── phone_validator.py
    └── __init__.py

src/utils/             # Utilidades compartidas
├── logger.py          # Logging estructurado (stdlib)
├── helpers.py         # Funciones auxiliares puras
└── __init__.py

config/                # Configuraciones YAML
├── default_migration.yaml  # Configuración de migración
├── schema_examples/        # Esquemas de validación por tabla
│   ├── customers_schema.yaml
│   ├── products_schema.yaml
│   └── orders_schema.yaml
└── validation_rules/       # Reglas de validación

scripts/               # Scripts de utilidad
├── init_db.py         # Inicialización de BD (Python)
├── run_migration.py   # CLI principal
├── run_schema.sh      # Ejecución de scripts SQL (Docker)
├── run_integration_tests.sh  # Orquestador de pruebas E2E
├── verify_setup.sh    # Verificación de entorno
├── update_submodule.sh # Actualización de submodule
└── sql/               # Scripts SQL
    ├── 01_create_database.sql
    ├── 02_create_schema.sql
    ├── 03_create_indexes.sql
    ├── drop_database.sql
    └── test_schema_operations.sql

tests/                 # Tests unitarios e integración
├── conftest.py        # Configuración pytest con fixtures
├── fixtures/          # Datos de prueba CSV
│   ├── customers_valid.csv
│   ├── customers_invalid_email.csv
│   ├── customers_invalid_phone.csv
│   └── customers_mixed.csv
├── unit/              # Tests de componentes aislados
│   ├── test_error_handler.py
│   ├── test_validators_reuse.py
│   └── test_csv_loader.py
├── integration/       # Tests con base de datos real
│   ├── test_db_connector.py
│   └── test_migration_flow.py
└── test_integration.py  # Orquestador E2E (Python)

docs/                  # Documentación del proyecto
├── TESTING_STRATEGY.md  # Estrategia de pruebas en 4 fases
├── ADR.md             # Architecture Decision Records
├── ERD.md             # Entity Relationship Diagram
├── POSTGRES_SETUP.md  # Configuración de PostgreSQL
├── REUSE_STRATEGY.md  # Estrategia de reuso del auditor
└── TROUBLESHOOTING.md # Solución de problemas

extern/auditor/       # Git submodule (read-only)
└── auditor-de-calidad-de-datos
```

---

## 📚 Documentación Detallada

Para guías específicas y reglas completas, consulta:

### 🎯 **Contexto del Proyecto**
- [Project Context](.agent-instructions/project-context.md) - Propósito, requisitos, dominio e implementación

### 🏗️ **Arquitectura y Diseño**  
- [Architecture Guidelines](.agent-instructions/architecture.md) - Patrones, capas, componentes y flujos

### 🔧 **Guías de Desarrollo**
- [Development Guidelines](.agent-instructions/development-guidelines.md) - Principios SOLID, formatos, checklists

### 🧪 **Testing y Calidad**
- [Testing Strategy](docs/TESTING_STRATEGY.md) - Estrategia de pruebas en 4 fases (verificación, unitarias, integración, E2E)
- [Testing Guidelines](.agent-instructions/testing.md) - Frameworks, fixtures, patrones de testing

### 🔒 **Seguridad y Prohibiciones**
- [Security Guidelines](.agent-instructions/security.md) - Validación de inputs, manejo de secretos

---

## 🎯 Para Agentes de IA

Este archivo sirve como **system prompt** para asegurar comprensión correcta del proyecto.

### Información Crítica
- **Stack**: Python 3.11+, PostgreSQL 15 (Docker), psycopg2-binary>=2.9.0, PyYAML>=6.0.0
- **Patrón**: Clean Architecture con Template Method y Strategy
- **Submodule**: `extern/auditor/` (read-only, no modificar)
- **Testing**: Estrategia en 4 fases (verificación, unitarias, integración, E2E)
- **Scripts**: run_schema.sh, verify_setup.sh, run_integration_tests.sh

### Reglas Fundamentales
1. **NO hardcodear** credenciales, paths o configuración (usar .env y YAML)
2. **USAR stdlib** sobre dependencias externas cuando sea posible
3. **MANTENER** patrones SOLID y separación de capas
4. **SEGUIR** Template Method en pipeline.py
5. **VALIDAR** todos los inputs externos
6. **EJECUTAR** pruebas en orden: verificación → unitarias → integración → E2E

### Para Empezar a Trabajar
1. Revisa el contexto específico en los archivos enlazados arriba
2. Identifica la capa/componente que modificarás
3. Sigue las guías de desarrollo y seguridad correspondientes
4. Usa las fixtures existentes para testing

---

> 💡 **Nota**: Esta documentación sigue principios de **divulgación progresiva**.  
> Lo esencial está aquí; lo detallado está en los archivos especializados enlazados.

> [!SUCCESS]
> ✅ **Documentación refactorizada lista para agentes**
> 
> - Archivo raíz minimalista (<50 líneas esenciales)
> - Contenido organizado por temas específicos
> - Enlaces claros a documentación detallada
> - Sin redundancia ni contradicciones
> - Estructura navegable y mantenible