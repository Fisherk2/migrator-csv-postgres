# Registro de Decisiones Arquitectónicas - Migrador CSV → PostgreSQL

---
metadata:
  tipo_documento: Architecture Decision Record
  dominio: Migración de Datos
  estado: Aprobado
  fecha_creacion: 2026-04-27
  fecha_actualizacion: 2026-04-27
  autor: fisherk2, Arquitecto de Software
  revisores: [Equipo de Desarrollo]
  stakeholders: [Desarrolladores, Arquitectos]
  tags: [adr, arquitectura, clean-architecture, git-submodule, patrones]
  version: 2.0
  relacionado_con: [[REUSE_STRATEGY.md]], [[AGENT.MD]]
---

## Introducción

Este documento registra las decisiones arquitectónicas clave del Migrador CSV → PostgreSQL. Cada decisión captura el "por qué" detrás del "qué", siguiendo principios de *Clean Architecture* (Cap. 30: "The Database is a Detail", Cap. 10: "Configuration") y *Software Development, Design, and Coding* (Cap. 20).

**Propósito:**
- Mantener registro histórico de decisiones arquitectónicas
- Prevenir el "Morning After Syndrome" (decisiones sin contexto)
- Facilitar auditoría técnica futura
- Evitar redescubrimiento de alternativas evaluadas

**Cómo usar este documento:**
1. Para nuevas decisiones: Copiar formato ADR y completar cada sección
2. Para decisiones existentes: Revisar contexto antes de proponer cambios
3. Para auditorías: Usar como referencia de decisiones pasadas

---

## Tabla de Contenidos
- [ADR-MIG-001: Clean Architecture sobre MVC/Monolito](#adr-mig-001-clean-architecture-sobre-mvcmonolito)
- [ADR-MIG-002: Git Submodule vs Pip Package vs Vendor](#adr-mig-002-git-submodule-vs-pip-package-vs-vendor)
- [ADR-MIG-003: Repository + Template Method para Pipeline](#adr-mig-003-repository--template-method-para-pipeline)
- [ADR-MIG-004: Separación YAML (Dominio) vs SQL (Infraestructura)](#adr-mig-004-separación-yaml-dominio-vs-sql-infraestructura)
- [ADR-MIG-005: psycopg2 + copy_expert sobre SQLAlchemy/pandas](#adr-mig-005-psycopg2--copy_expert-sobre-sqlalchemypandas)
- [Resumen de ADRs](#resumen-de-adrs)
- [Historial de Cambios](#historial-de-cambios)

---

# ADR-MIG-001: Clean Architecture sobre MVC/Monolito

## Estado y Contexto

**Estado:** Aceptado  
**Fecha:** 2026-04-27  
**Autor:** fisherk2

**Contexto del Problema:**
El proyecto requiere una arquitectura que soporte cambios en la base de datos sin afectar el dominio de negocio, permita testing de componentes aislados, y facilite la integración con el auditor externo. MVC tradicional acopla lógica de negocio con infraestructura.

**Requisitos:**
- Independencia de la base de datos (PostgreSQL es un detalle)
- Testing de componentes aislados sin BD real
- Integración controlada con dependencias externas
- Extensibilidad sin modificar código existente

**Restricciones:**
- MVP con timeline limitado (40-60h)
- Equipo familiarizado con MVC tradicional
- Necesidad de rápida iteración

---

## Decisión Arquitectónica

**Decisión:** Se adopta **Clean Architecture (Lite)** con separación estricta de capas: Presentation → Application → Domain ← Infrastructure.

**Justificación:**
Según *Clean Architecture* Cap. 30, "The Database is a Detail". La base de datos es un detalle de implementación, no el centro del sistema. Clean Architecture permite cambiar el motor de BD sin tocar el dominio.

**Estructura de Capas:**
```
Presentation Layer (CLI)
    ↓
Application Layer (Pipeline, CSVLoader, ReportGenerator)
    ↓
Domain Layer (Validators, Schema Definitions)
    ↑
Infrastructure Layer (DBConnector, Logger, FileSystem)
```

**Principios Aplicados:**
- **DIP (Dependency Inversion):** High-level modules dependen de abstracciones
- **OCP (Open/Closed):** Extensible sin modificación (Strategy pattern)
- **SRP (Single Responsibility):** Cada clase tiene una razón para cambiar

---

## Alternativas Consideradas

| Alternativa | Acoplamiento BD | Testing | Extensibilidad | Veredicto | Razón de Rechazo |
|-------------|----------------|---------|----------------|-----------|------------------|
| **Clean Architecture** | Bajo | Excelente | Alta | ✅ Seleccionada | Independencia máxima |
| MVC Tradicional | Alto | Medio | Media | ❌ Rechazada | Acoplamiento fuerte |
| Monolito Simple | Alto | Bajo | Baja | ❌ Rechazada | Difícil de mantener |
| Hexagonal | Bajo | Excelente | Alta | ❌ Rechazada | Overhead para MVP |

---

## Consecuencias y Trade-offs

### Beneficios
- **Independencia:** Cambiar BD (PostgreSQL → MySQL) sin tocar dominio
- **Testing:** Unit tests sin dependencias externas
- **Extensibilidad:** Agregar validadores sin modificar pipeline
- **Mantenibilidad:** Cambios localizados a capas específicas

### Trade-offs
- **Complejidad inicial:** Curva de aprendizaje para equipo MVC
- **Overhead:** Más archivos y abstracciones que monolito
- **Boilerplate:** Interfaces y adaptadores adicionales
<!-- CONSIDERACIÓN: Para MVP, podría parecer overengineering, pero ahorra deuda técnica a largo plazo -->

---

# ADR-MIG-002: Git Submodule vs Pip Package vs Vendor

## Estado y Contexto

**Estado:** Aceptado  
**Fecha:** 2026-04-27  
**Autor:** fisherk2

**Contexto del Problema:**
El proyecto necesita reutilizar validadores del proyecto `auditor-de-calidad-de-datos`. Se requiere control sobre versiones, capacidad de contribuir upstream, y aislamiento de cambios sin permisos de escritura en el repo original.

**Requisitos:**
- Control explícito de versiones del auditor
- Capacidad de contribuir cambios upstream (fork → PR)
- Aislamiento: cambios en migrador no afectan auditor
- Read-only para este repo (sin permisos de escritura)

**Restricciones:**
- No tenemos permisos de escritura en el repo del auditor
- Necesitamos rastrear qué versión del auditor usamos
- El auditor evoluciona independientemente

---

## Decisión Arquitectónica

**Decisión:** Se usa **git submodule** en `extern/auditor/` con patrón Facade en `src/validators/__init__.py`.

**Justificación:**
Git submodule permite versionado explícito (commit SHA), contribución upstream controlada, y aislamiento completo. El Facade (`src/validators/__init__.py`) aplica DIP: el dominio depende de la abstracción, no del detalle del auditor.

**Implementación:**
```python
# src/validators/__init__.py (Facade)
from extern.auditor.src.validators.type_validator import TypeValidator

def validate_integer(value: Any) -> tuple[bool, str]:
    """Wrapper que aísla cambios internos del auditor."""
    # Lógica de adaptación aquí
```

**Workflow de Submodule:**
```bash
# Inicializar
git submodule update --init --recursive

# Actualizar a versión específica
cd extern/auditor
git checkout <commit-sha>
cd ../..
git add extern/auditor
git commit -m "Pin auditor to commit <sha>"

# Contribuir upstream (si tenemos permisos)
cd extern/auditor
git checkout -b feature/new-validator
# ... hacer cambios ...
git push origin feature/new-validator
# Crear PR en repo del auditor
```

---

## Alternativas Consideradas

| Alternativa | Versionado | Contribución | Aislamiento | Veredicto | Razón de Rechazo |
|-------------|------------|-------------|-------------|-----------|------------------|
| **Git Submodule** | Commit SHA | Fork → PR | Completo | ✅ Seleccionada | Control máximo |
| Pip Package | SemVer | Directa | Medio | ❌ Rechazada | No tenemos permisos |
| vendor/ | Manual | Difícil | Completo | ❌ Rechazada | Duplicación de código |
| Copy-Paste | Ninguno | Ninguna | Completo | ❌ Rechazada | Sin rastreo de cambios |

---

## Consecuencias y Trade-offs

### Beneficios
- **Versionado explícito:** Commit SHA garantiza reproducibilidad
- **Contribución controlada:** Fork → PR sin acceso directo
- **Aislamiento:** Cambios en migrador no afectan auditor
- **Transparencia:** Git rastrea qué versión usamos

### Trade-offs
- **Complejidad git:** Comandos adicionales para desarrolladores
- **Detached HEAD:** Submodule en estado detached por defecto
- **Setup inicial:** Requiere `git submodule update --init`
- **Sync manual:** Actualizar versión requiere pasos explícitos
<!-- CONSIDERACIÓN: Equipo nuevo puede confundirse con detached HEAD, pero script `update_submodule.sh` mitiga esto -->

---

# ADR-MIG-003: Repository + Template Method para Pipeline

## Estado y Contexto

**Estado:** Aceptado  
**Fecha:** 2026-04-27  
**Autor:** fisherk2

**Contexto del Problema:**
El pipeline de migración requiere orquestación de pasos (load → validate → transfer → report) con rollback automático ante errores. Se necesita testing por etapa y extensibilidad para agregar nuevos pasos sin modificar el flujo principal.

**Requisitos:**
- Orquestación de flujo estándar con rollback transaccional
- Testing de cada etapa independientemente
- Extensibilidad para agregar pasos (ej: data transformation)
- Rollback automático ante umbrales de error

**Restricciones:**
- MVP con funcionalidad básica primero
- Necesidad de logging estructurado por etapa
- Transacciones atómicas obligatorias

---

## Decisión Arquitectónica

**Decisión:** Se aplica **Template Method** en `MigrationPipeline.execute()` y **Repository** en `DBConnector`.

**Justificación:**
Template Method (GoF) define el esqueleto del algoritmo, permitiendo que subclases redefinan ciertos pasos sin cambiar la estructura. Repository abstrae operaciones de BD, facilitando testing y cambio de motor.

**Implementación:**
```python
# Template Method
class MigrationPipeline:
    def execute(self, config: Dict) -> Dict:
        self._load_config(config)      # Paso 1
        self._establish_connection()  # Paso 2
        self._load_and_validate()      # Paso 3 (abstract)
        self._transfer_or_rollback()   # Paso 4 (abstract)
        self._generate_report()        # Paso 5
        return self._stats

# Repository
class DBConnector:
    def ensure_table_exists(self, table: str, schema: Dict) -> bool:
        """Abstracción sobre psycopg2."""
        pass
```

**Principios Aplicados:**
- **Template Method:** Flujo estándar, pasos variables
- **Repository:** Abstracción sobre operaciones BD
- **SRP:** Pipeline orquesta, DBConnector opera BD

---

## Alternativas Consideradas

| Alternativa | Testing | Extensibilidad | Rollback | Veredicto | Razón de Rechazo |
|-------------|---------|----------------|----------|-----------|------------------|
| **Template + Repository** | Excelente | Alta | Automático | ✅ Seleccionada | Balance óptimo |
| Script Lineal | Bajo | Baja | Manual | ❌ Rechazada | Difícil de testear |
| Chain of Responsibility | Medio | Alta | Manual | ❌ Rechazada | Complejidad alta |
| State Machine | Medio | Alta | Manual | ❌ Rechazada | Overhead para MVP |

---

## Consecuencias y Trade-offs

### Beneficios
- **Testing por etapa:** Cada paso testable independientemente
- **Extensibilidad:** Agregar pasos sin modificar flujo principal
- **Rollback automático:** Transacción atómica en DBConnector
- **Clarity:** Flujo visible en un método (`execute()`)

### Trade-offs
- **Rigidez:** Cambiar orden de pasos requiere modificación
- **Overhead:** Clases adicionales (Repository)
- **Learning curve:** Equipo debe entender patrones GoF
<!-- CONSIDERACIÓN: Para MVP, podría parecer overengineering, pero facilita agregar data transformation en Fase 2 -->

---

# ADR-MIG-004: Separación YAML (Dominio) vs SQL (Infraestructura)

## Estado y Contexto

**Estado:** Aceptado  
**Fecha:** 2026-04-27  
**Autor:** fisherk2

**Contexto del Problema:**
El proyecto necesita definir esquemas de datos (tipos, validaciones) y estructura física de BD (tablas, índices). Mezclar ambos conceptos viola Clean Architecture: el dominio no debe conocer detalles de infraestructura.

**Requisitos:**
- Definición de esquemas en lenguaje de dominio (YAML)
- Scripts SQL para estructura física (DDL)
- Independencia: cambiar YAML no afecta SQL y viceversa
- Validación de esquemas sin conexión a BD

**Restricciones:**
- MVP con 3 tablas (customers, products, orders)
- Necesidad de validación declarativa
- Scripts SQL idempotentes

---

## Decisión Arquitectónica

**Decisión:** Se separa **esquema YAML (dominio)** en `config/schema_examples/` y **scripts SQL (infraestructura)** en `scripts/sql/`.

**Justificación:**
Según *Clean Architecture* Cap. 10, "Configuration", la configuración debe estar separada de la lógica. YAML define contratos de dominio (tipos, validaciones), SQL define detalles de implementación (tablas, índices).

**Implementación:**
```yaml
# config/schema_examples/customers_schema.yaml (Dominio)
table: customers
columns:
  email:
    type: string
    required: true
    validation: email_format
```

```sql
-- scripts/sql/02_create_schema.sql (Infraestructura)
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    -- ... índices, constraints
);
```

**Principios Aplicados:**
- **Separation of Concerns:** Dominio vs Infraestructura
- **Configuration as Code:** YAML versionado
- **Idempotency:** Scripts SQL re-ejecutables

---

## Alternativas Consideradas

| Alternativa | Validación | Independencia | Mantenibilidad | Veredicto | Razón de Rechazo |
|-------------|------------|----------------|----------------|-----------|------------------|
| **YAML + SQL separados** | Declarativa | Alta | Alta | ✅ Seleccionada | Clean Architecture |
| Solo SQL | Imperativa | Baja | Media | ❌ Rechazada | Acopla dominio a BD |
| ORM (Python) | Programática | Media | Media | ❌ Rechazada | Overhead para MVP |
| JSON Schema | Declarativa | Alta | Alta | ❌ Rechazada | YAML más legible |

---

## Consecuencias y Trade-offs

### Beneficios
- **Independencia:** Cambiar estructura BD sin afectar validaciones
- **Validación offline:** Validar esquemas sin conexión a BD
- **Legibilidad:** YAML más legible que DDL para no-DBAs
- **Versionado:** Ambos archivos versionados en git

### Trade-offs
- **Duplicación:** Esquema definido en YAML y SQL
- **Sync manual:** Cambios en uno requieren actualización del otro
- **Complejidad:** Dos sistemas de definición que mantener
<!-- CONSIDERACIÓN: Herramienta de generación SQL desde YAML podría mitigar duplicación en Fase 2 -->

---

# ADR-MIG-005: psycopg2 + copy_expert sobre SQLAlchemy/pandas

## Estado y Contexto

**Estado:** Aceptado  
**Fecha:** 2026-04-27  
**Autor:** fisherk2

**Contexto del Problema:**
El MVP requiere ingesta eficiente de CSV a PostgreSQL (<5 min para 1000 filas). Se necesita balance entre rendimiento, simplicidad, y dependencias. Pandas es popular pero agrega overhead innecesario para CSV simple.

**Requisitos:**
- Ingesta eficiente vía `COPY FROM` de PostgreSQL
- Mínimas dependencias externas
- Control transaccional explícito
- Performance sin sacrificio de claridad

**Restricciones:**
- MVP con timeline limitado
- Equipo familiarizado con Python stdlib
- Requisito de 100% dependencias open-source

---

## Decisión Arquitectónica

**Decisión:** Se usa **psycopg2-binary + copy_expert** directamente, sin ORM ni pandas.

**Justificación:**
`copy_expert` de psycopg2 es el método más eficiente para CSV → PostgreSQL (usa protocolo binario de PostgreSQL). Pandas agrega overhead innecesario para CSV simple. SQLAlchemy es excesivo para MVP sin necesidad de ORM.

**Implementación:**
```python
# src/migrator/db_connector.py
import psycopg2
from io import StringIO

def execute_copy_from(self, csv_path: str, temp_table: str) -> int:
    """Usa COPY FROM nativo de PostgreSQL."""
    with open(csv_path, 'r') as f:
        cursor.copy_expert(f"COPY {temp_table} FROM STDIN WITH CSV HEADER", f)
    return cursor.rowcount
```

**Principios Aplicados:**
- **KISS (Keep It Simple, Stupid):** Herramienta mínima para el trabajo
- **Performance:** Uso de protocolo nativo de PostgreSQL
- **Fail-Fast:** Errores visibles inmediatamente

---

## Alternativas Consideradas

| Alternativa | Performance | Dependencias | Simplicidad | Veredicto | Razón de Rechazo |
|-------------|-------------|--------------|-------------|-----------|------------------|
| **psycopg2 + copy_expert** | Excelente | Mínimas | Alta | ✅ Seleccionada | Balance óptimo |
| pandas + to_sql | Medio | Alta | Alta | ❌ Rechazada | Overhead innecesario |
| SQLAlchemy ORM | Medio | Alta | Media | ❌ Rechazada | Excesivo para MVP |
| csv stdlib + INSERT | Bajo | Mínimas | Alta | ❌ Rechazada | Performance pobre |

---

## Consecuencias y Trade-offs

### Beneficios
- **Performance:** `COPY FROM` es 10-100x más rápido que INSERT
- **Dependencias mínimas:** Solo psycopg2 (ya requerido)
- **Control explícito:** Transacciones y rollback visibles
- **Simplicidad:** Código directo sin abstracciones ORM

### Trade-offs
- **Sin ORM:** Queries SQL manuales (pero simples para MVP)
- **Sin pandas:** Sin funcionalidades de data manipulation (no necesarias)
- **PostgreSQL-specific:** `COPY FROM` no portable a otros motores
<!-- CONSIDERACIÓN: Si MVP requiere multi-DB en Fase 2, considerar wrapper sobre COPY FROM -->

---

# Resumen de ADRs

| ADR # | Principio Aplicado | Alternativa Descartada | Impacto en MVP |
|-------|-------------------|------------------------|----------------|
| ADR-MIG-001 | DIP, OCP, SRP | MVC Tradicional | +Complejidad inicial, -Deuda técnica |
| ADR-MIG-002 | DIP, Facade | Pip Package | +Control versionado, -Complejidad git |
| ADR-MIG-003 | Template Method, Repository | Script Lineal | +Testing por etapa, -Rigidez |
| ADR-MIG-004 | Separation of Concerns | Solo SQL | +Independencia, -Duplicación |
| ADR-MIG-005 | KISS, Performance | pandas + to_sql | +Performance, -Sin ORM |

---

## Prevención del "Morning After Syndrome"

Los ADRs y la estrategia de reuso previenen el "Morning After Syndrome" (decisiones sin contexto que generan deuda técnica) mediante:

1. **Captura explícita de trade-offs:** Cada ADR documenta consecuencias negativas, no solo beneficios
2. **Vinculación a principios SOLID:** Cada decisión se justifica con principios arquitectónicos
3. **Workflow de git submodule documentado:** Evita confusiones con detached HEAD y versioning
4. **Separación dominio/infraestructura:** Cambios futuros en BD no rompen validaciones
5. **Auditoría técnica facilitada:** ADRs proporcionan contexto para decisiones pasadas

---

## Historial de Cambios

| Versión | Fecha | Cambios | Autor | Estado |
|---------|-------|---------|-------|---------|
| 1.0 | 2026-03-13 | Creación inicial con 3 ADRs de BD | fisherk2 | Reemplazado |
| 2.0 | 2026-04-27 | 5 ADRs de arquitectura del migrador | fisherk2 | Activo |

---

## Mantenimiento del Documento

**Propietario:** fisherk2  
**Frecuencia de revisión:** Trimestral  
**Proceso de cambios:**
1. Proponer nuevo ADR o modificación en issue
2. Revisión por equipo técnico
3. Aprobación por arquitecto principal
4. Actualización del documento con trade-offs explícitos

---

> **Nota sobre importancia de ADRs:** Documentar decisiones arquitectónicas evita que el equipo "redescubra" soluciones, proporciona contexto para decisiones futuras, y facilita el onboarding de nuevos miembros. Un ADR bien mantenido es un activo estratégico para el equipo.