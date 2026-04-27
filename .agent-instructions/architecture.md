# Architecture Guidelines

## 🏗️ Patrones Arquitectónicos

### Clean Architecture Implementation

El proyecto sigue una arquitectura de capas limpia con inversión de dependencias:

```mermaid
flowchart TB
    subgraph Presentation["🖥️ Presentation Layer"]
        CLI["CLI: run_migration.py<br/>• argparse<br/>• entrada/salida"]
    end
    
    subgraph Application["⚙️ Application Layer"]
        Pipeline["MigrationPipeline<br/>• Template Method<br/>• orquesta: load→validate→transfer→report"]
    end
    
    subgraph Domain["🧠 Domain Layer (Validations)"]
        Reused["Validators::Reused<br/>• import from auditor submodule<br/>• funciones puras: validate_*"]
        Custom["Validators::Custom<br/>• email_validator.py<br/>• phone_validator.py"]
        Strategy["Strategy Pattern<br/>• reglas cargadas desde YAML<br/>• abierto/cerrado"]
    end
    
    subgraph Infrastructure["🔌 Infrastructure Layer"]
        DB["DBConnector::Repository<br/>• psycopg2<br/>• COPY FROM, transacciones"]
        CSV["CSVLoader<br/>• stdlib csv + COPY<br/>• temp tables"]
        Utils["Utils<br/>• logger.py (stdlib)<br/>• helpers.py (puras)"]
    end

    CLI -->|invoca| Pipeline
    Pipeline -->|usa interfaz| Reused
    Pipeline -->|extiende| Custom
    Pipeline -->|configura| Strategy
    Pipeline -->|depende de| DB
    Pipeline -->|depende de| CSV
    Pipeline -->|usa| Utils

    classDef layer fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    class Presentation,Application,Domain,Infrastructure layer
```

### Matriz de Patrones

| Patrón | Componente | Implementación | Beneficio para MVP |
|--------|-----------|---------------|-------------------|
| **Strategy** | `validation_rules` en YAML | `if rule.type == 'email': apply_email_regex()` | Agregar reglas sin tocar pipeline |
| **Template Method** | `MigrationPipeline.execute()` | Pasos definidos: `_load() → _validate() → _transfer() → _report()` | Testing por etapa + extensibilidad |
| **Repository** | `DBConnector` | Interfaz: `ensure_table_exists()`, `execute_batch_insert()` | Cambiar DB engine sin tocar dominio |
| **Adapter** | `ValidatorAdapter` | Wrapper que unifica API del auditor + validadores custom | Reuso sin acoplamiento a implementación |

## 🏛️ Estructura de Capas

### 1. Presentation Layer
```
scripts/run_migration.py  # CLI principal
├── argparse parsing
├── env file loading
├── dependency injection
└── error handling
```

**Responsabilidades:**
- Parsear argumentos de línea de comandos
- Cargar variables de entorno
- Inyectar dependencias
- Manejar errores de alto nivel

### 2. Application Layer
```
src/migrator/
├── pipeline.py           # Orquestador principal (Template Method)
├── csv_loader.py         # Carga y validación CSV
├── db_connector.py       # Operaciones PostgreSQL
├── error_handler.py      # Manejo acumulado de errores
├── report_generator.py   # Generación de reportes
└── __init__.py
```

**Responsabilidades:**
- Orquestar el flujo de migración
- Coordinar componentes del dominio
- Generar reportes estructurados

### 3. Domain Layer
```
src/validators/
├── __init__.py          # Interfaz común
└── custom/              # Validadores específicos
    ├── email_validator.py
    ├── phone_validator.py
    └── __init__.py
```

**Responsabilidades:**
- Contener lógica de validación de negocio
- Definir reglas de dominio
- Mantener estado independiente de infraestructura

### 4. Infrastructure Layer
```
src/utils/
├── logger.py          # Logging estructurado
├── helpers.py         # Funciones auxiliares
└── __init__.py
```

**Responsabilidades:**
- Proporcionar utilidades compartidas
- Manejar logging estructurado
- Funciones auxiliares puras

## 🧩 Componentes Principales

### Integración con Submodule

```mermaid
graph LR
    subgraph Main["🗂️ migrador-csv-postgres"]
        CLI[scripts/run_migration.py]
        Pipeline[src/migrator/pipeline.py]
        ValAdapter[src/validators/__init__.py]
        CustomVal[src/validators/custom/]
        Config[config/*.yaml]
    end

    subgraph Submodule["🔗 auditor-de-calidad-de-datos"]
        TypeVal[auditor/validators/type_validator.py]
        SchemaVal[auditor/validators/schema_validator.py]
        Rules[auditor/rules/]
    end

    CLI -->|argparse| Pipeline
    Pipeline -->|importa| ValAdapter
    ValAdapter -->|re-exporta| TypeVal
    ValAdapter -->|re-exporta| SchemaVal
    Pipeline -->|extiende| CustomVal
    Pipeline -->|carga| Config
    
    style Submodule fill:#fff3e0,stroke:#f57c00,stroke-dasharray:5
    style Main fill:#e8f5e9,stroke:#388e3c
```

> [!IMPORTANT]
> **Regla de integración**: El migrador **nunca** modifica código en `extern/auditor/`.  
> Para contribuir al auditor: fork → PR → actualizar submodule.

### Secuencia: Pipeline de Migración

```mermaid
sequenceDiagram
    autonumber
    participant User as Usuario/CLI
    participant Pipeline as MigrationPipeline
    participant CSV as CSVLoader
    participant Val as ValidatorAdapter
    participant DB as DBConnector
    participant Report as ReportGenerator

    User->>Pipeline: execute(config_path="config/default_migration.yaml")
    
    rect lightgreen
        Note right of Pipeline: FASE 1: SETUP
        Pipeline->>DB: create_connection(config.target)
        DB-->>Pipeline: conn_established ✅
        Pipeline->>CSV: load_csv_to_temp_table(csv_path)
        CSV-->>Pipeline: {temp_table: "tmp_customers", rows: 1000}
    end
    
    rect lightyellow
        Note right of Pipeline: FASE 2: VALIDACIÓN
        Pipeline->>Val: validate_schema_format(config.validation)
        Val-->>Pipeline: schema_valid ✅
        
        loop Por cada fila en temp_table
            Pipeline->>CSV: fetch_row(row_num)
            CSV-->>Pipeline: {email: "user@", phone: "123"}
            
            Pipeline->>Val: validate_email("user@")
            Val-->>Pipeline: {ok: false, reason: "invalid_format"}
            
            Pipeline->>Val: validate_required("user@", field="email")
            Val-->>Pipeline: {ok: true}
            
            alt Error crítico
                Pipeline->>Pipeline: mark_critical_error()
            else Error recuperable
                Pipeline->>Pipeline: collect_error(...)
            end
        end
    end
    
    rect lightblue
        Note right of Pipeline: FASE 3: TRANSFERENCIA
        alt critical_errors > 0
            Pipeline->>DB: rollback_temp_table("tmp_customers")
            DB-->>Pipeline: rollback_complete ✅
            Pipeline->>Report: generate_summary(status="failed")
        else all_valid
            Pipeline->>DB: validate_and_transfer("tmp_customers" → "customers")
            DB-->>Pipeline: {inserted: 987, skipped: 13}
            Pipeline->>Report: generate_summary(status="success")
        end
    end
    
    Report-->>Pipeline: {json_report: "...", text_report: "..."}
    Pipeline-->>User: ✅/❌ + paths a reportes
```

### Clases Principales

```mermaid
classDiagram
    direction TB
    
    class MigrationConfig {
        +source: Dict[str, Any]
        +target: Dict[str, Any] 
        +validation: Dict[str, Any]
        +load_from_yaml(path: str) MigrationConfig
        +validate_schema() bool
    }
    
    class MigrationPipeline {
        -config: MigrationConfig
        -db: DBConnector
        -validator: ValidatorAdapter
        +execute() Dict[str, Any]
        -_load_csv() str
        -_validate_all() List[MigrationError]
        -_transfer_or_rollback() bool
        -_generate_report() Report
    }
    
    class DBConnector {
        -conn: psycopg2.connection
        +create_connection(config: Dict) bool
        +ensure_table_exists(table: str, schema: Dict) bool
        +execute_copy_from(csv_path: str, temp_table: str) int
        +execute_batch_transfer(temp: str, target: str) Dict[str, int]
        +rollback_temp_table(table: str) bool
    }
    
    class ValidatorAdapter {
        +validate_integer(value: Any, field: str) Tuple[bool, str]
        +validate_email(value: str) Tuple[bool, str, Optional[str]]
        +validate_required(value: Any, field: str) Tuple[bool, str]
        +apply_strategy(rules: List[Rule], row: Dict) List[MigrationError]
    }
    
    class MigrationError {
        +row_num: int
        +field: str
        +value: Any
        +reason: str
        +suggestion: Optional[str]
        +is_critical: bool
        +to_dict() Dict[str, Any]
        +__str__() str  # mensaje humano en ES
    }

    MigrationPipeline *-- MigrationConfig : configura
    MigrationPipeline *-- DBConnector : usa
    MigrationPipeline *-- ValidatorAdapter : delega
    MigrationPipeline o-- MigrationError : genera
    
    note for ValidatorAdapter "Adapta funciones del auditor + agrega custom"
    note for MigrationError "Diseñado para serialización JSON + legibilidad humana"
```

## 📁 Estructura de Directorios

```
migrador-csv-postgres/
├── src/                     # Código fuente
│   ├── migrator/           # Lógica principal
│   │   ├── pipeline.py
│   │   ├── csv_loader.py
│   │   ├── db_connector.py
│   │   ├── error_handler.py
│   │   ├── report_generator.py
│   │   └── __init__.py
│   ├── validators/         # Validadores
│   │   ├── __init__.py
│   │   └── custom/
│   │       ├── email_validator.py
│   │       ├── phone_validator.py
│   │       └── __init__.py
│   └── utils/              # Utilidades
│       ├── logger.py
│       ├── helpers.py
│       └── __init__.py
│
├── config/                 # Configuraciones
│   ├── default_migration.yaml
│   ├── schema_examples/
│   │   ├── customers_schema.yaml
│   │   ├── products_schema.yaml
│   │   └── orders_schema.yaml
│   └── validation_rules/
│       └── email_phone_rules.yaml
│
├── scripts/                # Scripts de utilidad
│   ├── init_db.py
│   ├── run_migration.py
│   ├── run_schema.sh
│   ├── update_submodule.sh
│   ├── verify_setup.sh
│   └── sql/
│       ├── 01_create_database.sql
│       ├── 02_create_schema.sql
│       ├── 03_create_indexes.sql
│       ├── drop_database.sql
│       └── test_schema_operations.sql
│
├── test/                   # Tests
│   ├── conftest.py
│   ├── fixtures/
│   │   ├── valid_customers.csv
│   │   ├── invalid_customers.csv
│   │   └── test_schema.yaml
│   ├── unit/
│   │   ├── test_csv_loader.py
│   │   ├── test_error_handler.py
│   │   └── test_validators_reuse.py
│   └── integration/
│       ├── test_db_connector.py
│       └── test_migration_flow.py
│
├── docs/                   # Documentación
│   ├── ADR.md
│   ├── ERD.md
│   ├── POSTGRES_SETUP.md
│   ├── REUSE_STRATEGY.md
│   └── TROUBLESHOOTING.md
│
├── extern/auditor/         # Git submodule (read-only)
├── .agent-instructions/    # Documentación para agentes
├── AGENT.MD               # System prompt para agentes
├── README.md              # Documentación principal
├── CONTRIBUTING.MD         # Guía de contribución
├── CHANGELOG.md           # Historial de cambios
├── requirements.txt       # Dependencias runtime
├── requirements-dev.txt    # Dependencias desarrollo
├── docker-compose.yml     # Configuración Docker
└── .env.example           # Ejemplo de variables de entorno
```

## 🎯 Contextos Específicos

### Cuando Modificar `src/migrator/pipeline.py`
- Mantener Template Method pattern
- No agregar lógica de negocio específica
- Preservar inyección de dependencias
- Mantener rollback transaccional

### Cuando Agregar Validadores
- Crear en `src/validators/custom/`
- Implementar interfaz común
- Registrar en configuración YAML
- Agregar tests unitarios

### Cuando Modificar CLI
- Mantener argparse simple
- No agregar lógica de negocio
- Preservar manejo de errores
- Mantener --dry-run y --verbose
