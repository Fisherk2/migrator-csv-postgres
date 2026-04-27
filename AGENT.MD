# 🗂️ Migrador CSV → PostgreSQL con Validación Reutilizable
*Documentación modularizada para Cascade*

```yaml
# Frontmatter: Metadatos estructurados para procesamiento automático
project:
  name: "migrador-csv-postgres"
  version: "0.1.0-mvp"
  status: "planning"
  created: "2026-04-15"
  updated: "2026-04-16T01:23:00Z"
  duration_estimate: "40-60h"
  
dependencies:
  external:
    - name: "auditor-de-calidad-de-datos"
      type: "git_submodule"
      url: "https://github.com/Fisherk2/auditor-de-calidad-de-datos"
      integration: "import_functions"
      constraint: "read_only"
  
  python:
    runtime: ["psycopg2-binary>=2.9", "pyyaml>=6.0"]
    dev: ["pytest>=7.0", "pytest-cov>=4.0", "black>=23.0"]
  
  database:
    engine: "postgresql>=14"
    schema: "e-commerce-mvp"
    
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
```

---

## 🚀 Quick Start

**Propósito**: Herramienta CLI que migra datos CSV → PostgreSQL con validación reutilizable.

### Comandos Esenciales
```bash
# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos
./scripts/init_db.py

# Ejecutar migración
python scripts/run_migration.py --config config/default_migration.yaml

# Ejecutar tests
pytest

# Formatear código
black src/ test/
```

### Estructura del Proyecto
```
src/migrator/          # Lógica principal del migrador
├── pipeline.py         # Orquestador del flujo
├── csv_loader.py       # Carga y validación CSV
├── db_connector.py    # Operaciones PostgreSQL
├── error_handler.py    # Manejo de errores
├── report_generator.py # Generación de reportes
└── __init__.py

src/validators/         # Validadores reutilizables
├── __init__.py        # Interfaz con submodule auditor
└── custom/            # Validadores específicos del proyecto

src/utils/             # Utilidades compartidas
├── logger.py          # Logging estructurado
├── helpers.py         # Funciones auxiliares
└── __init__.py

config/                # Configuraciones YAML
├── default_migration.yaml
├── schema_examples/    # Ejemplos de esquemas
└── validation_rules/   # Reglas de validación

scripts/               # Scripts de utilidad
├── init_db.py         # Inicialización de BD
├── run_migration.py   # CLI principal
├── run_schema.sh      # Ejecución de scripts SQL
├── update_submodule.sh # Actualización de submodule
├── verify_setup.sh    # Verificación de entorno
└── sql/               # Scripts SQL

test/                  # Tests unitarios e integración
├── conftest.py        # Configuración pytest
├── fixtures/         # Datos de prueba
├── unit/             # Tests de componentes aislados
└── integration/       # Tests con base de datos real

docs/                  # Documentación del proyecto
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
- [Testing Guidelines](.agent-instructions/testing.md) - Estrategia, fixtures, integración continua

### 🔒 **Seguridad y Prohibiciones**
- [Security Guidelines](.agent-instructions/security.md) - Validación de inputs, manejo de secretos

---

## 🎯 Para Agentes de IA

Este archivo sirve como **system prompt** para asegurar comprensión correcta del proyecto.

### Información Crítica
- **Stack**: Python 3.11+, PostgreSQL 15+, psycopg2, PyYAML
- **Patrón**: Clean Architecture con Template Method y Strategy
- **Submodule**: `extern/auditor/` (read-only, no modificar)
- **Testing**: pytest con fixtures y rollback automático

### Reglas Fundamentales
1. **NO hardcodear** credenciales, paths o configuración
2. **USAR stdlib** sobre dependencias externas cuando sea posible
3. **MANTENER** patrones SOLID y separación de capas
4. **SEGUIR** Template Method en pipeline.py
5. **VALIDAR** todos los inputs externos

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