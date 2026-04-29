# Contributing to Migrador CSV → PostgreSQL

Gracias por tu interés en contribuir! Esta guía establece el flujo de trabajo, estándares y requisitos para mantener la calidad y consistencia del proyecto.

---

## 📋 Tabla de Contenidos

- [Flujo de Trabajo](#flujo-de-trabajo)
- [Configuración del Entorno](#configuración-del-entorno)
- [Estándares de Código](#estándares-de-código)
- [Requisitos de Testing](#requisitos-de-testing)
- [Proceso de Review](#proceso-de-review)
- [Guía de Commits](#guía-de-commits)
- [Reporte de Issues](#reporte-de-issues)

---

## 🔄 Flujo de Trabajo

### 1. Fork y Clone
```bash
# Fork en GitHub UI

# Clonar tu fork
git clone https://github.com/TU_USERNAME/migrator-csv-postgres
cd migrator-csv-postgres

# Agregar upstream
git remote add upstream https://github.com/Fisherk2/migrator-csv-postgres
```

### 2. Rama de Desarrollo
```bash
# Sincronizar con upstream
git fetch upstream
git checkout main
git merge upstream/main

# Crear rama feature
git checkout -b feature/nombre-de-tu-feature
```

### 3. Desarrollo y Testing
```bash
# Instalar dependencias de desarrollo
pip install -r requirements.txt

# Ejecutar tests locales (estrategia en 4 fases)
./scripts/verify_setup.sh
python3 -m pytest tests/unit/ -v
./scripts/run_schema.sh && pytest tests/integration/ -v -m integration
./scripts/run_integration_tests.sh --verbose

# Formatear código
black src/ tests/
```

### 4. Pull Request
```bash
# Push a tu fork
git push origin feature/nombre-de-tu-feature

# Crear PR en GitHub UI
```

---

## 🛠️ Configuración del Entorno

### Requisitos
- Python 3.11+
- PostgreSQL 15+
- Docker (opcional, para desarrollo)

### Entorno Virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Base de Datos para Tests
```bash
# Usar script automatizado (recomendado)
./scripts/run_schema.sh

# Verificar entorno
./scripts/verify_setup.sh

# O configurar PostgreSQL local manualmente
export TEST_DB_AVAILABLE=true
export TEST_DB_HOST=localhost
export TEST_DB_NAME=migrator_test
export TEST_DB_USER=test_user
export TEST_DB_PASSWORD=test_password
```

### Pre-commit Hooks (Opcional)
```bash
# Instalar hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

---

## 📝 Estándares de Código

### Python Code Style
- **PEP 8**: Seguir estándar de estilo Python
- **Black**: Formateo automático con config preestablecido
- **Type Hints**: Obligatorios para funciones públicas
- **Docstrings**: Google Style para clases y funciones públicas

### Ejemplo de Código
```python
from typing import Dict, List, Optional
import logging

class CSVLoader:
    """
    Carga y valida archivos CSV para migración a PostgreSQL.
    
    Attributes:
        logger: Logger para registro de operaciones.
        _temp_table_counter: Contador para nombres de tablas temporales.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Inicializa el cargador CSV."""
        self.logger = logger or logging.getLogger(__name__)
        self._temp_table_counter = 0
    
    def load_csv_to_temp_table(
        self, 
        csv_path: str, 
        schema: Dict[str, Any],
        validators: Dict[str, Any],
        db_connector: "DBConnector",
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Carga CSV a tabla temporal con validación.
        
        Args:
            csv_path: Ruta al archivo CSV.
            schema: Esquema de validación YAML.
            validators: Validadores configurados.
            db_connector: Conector a PostgreSQL.
            config: Configuración adicional.
            
        Returns:
            Nombre de la tabla temporal creada.
            
        Raises:
            FileNotFoundError: Si el CSV no existe.
            ValidationError: Si los datos no cumplen el esquema.
        """
        # Implementación...
        pass
```

### Nomenclatura
- **Variables/Funciones**: `snake_case`
- **Clases**: `PascalCase`
- **Constantes**: `UPPER_SNAKE_CASE`
- **Privados**: Prefijo `_` (ej: `_validate_row()`)

### Imports
```python
# Stdlib primero
import os
import sys
from typing import Dict, List, Optional

# Third-party después
import psycopg2
import yaml

# Local imports al final
from src.migrator.db_connector import DBConnector
from src.utils.logger import get_logger
```

---

## 🧪 Requisitos de Testing

### Cobertura Mínima
- **Unit Tests**: 90% cobertura
- **Integration Tests**: 80% cobertura
- **Total**: 85% cobertura mínimo

### Estructura de Tests
```bash
tests/
├── conftest.py              # Fixtures compartidos
├── test_integration.py      # Orquestador E2E (Python)
├── unit/                    # Tests unitarios
│   ├── test_error_handler.py
│   ├── test_validators_reuse.py
│   └── test_csv_loader.py
├── integration/             # Tests de integración
│   ├── test_db_connector.py
│   └── test_migration_flow.py
└── fixtures/                # Datos de prueba
    ├── customers_valid.csv
    ├── customers_invalid_email.csv
    ├── customers_invalid_phone.csv
    └── customers_mixed.csv
```

### Ejemplo de Test
```python
import pytest
from src.migrator.csv_loader import CSVLoader

class TestCSVLoader:
    """Tests unitarios de CSVLoader."""
    
    def test_load_valid_csv_succeeds(
        self, 
        valid_csv_path: Path,
        mock_db_connector: Mock
    ) -> None:
        """
        ARRANGE: CSV válido y mock de BD.
        ACT: Cargar CSV.
        ASSERT: Tabla temporal creada exitosamente.
        """
        loader = CSVLoader(logger=None)
        
        temp_table = loader.load_csv_to_temp_table(
            csv_path=str(valid_csv_path),
            schema={},
            validators={},
            db_connector=mock_db_connector
        )
        
        assert temp_table.startswith("temp_csv_")
        mock_db_connector.execute_copy_from.assert_called_once()
```

### Ejecución de Tests
```bash
# Estrategia en 4 fases (recomendado)
./scripts/verify_setup.sh
python3 -m pytest tests/unit/ -v
./scripts/run_schema.sh && pytest tests/integration/ -v -m integration
./scripts/run_integration_tests.sh --verbose

# Unit tests solamente
python3 -m pytest tests/unit/ -v

# Integration tests
./scripts/run_schema.sh && pytest tests/integration/ -v -m integration

# Con cobertura
pytest --cov=src --cov-report=html --cov-fail-under=85

# Tests específicos
pytest tests/unit/test_csv_loader.py::TestCSVLoader::test_load_valid_csv_succeeds -v
```

---

## 👀 Proceso de Review

### Checklist Pre-PR
- [ ] Código sigue PEP 8 y está formateado con Black
- [ ] Type hints en funciones públicas
- [ ] Docstrings en Google Style
- [ ] Tests unitarios e integración pasan
- [ ] Cobertura mínima alcanzada
- [ ] No hardcoded credentials o paths
- [ ] Commits siguen formato semántico
- [ ] Documentación actualizada si aplica

### Review Guidelines
1. **Funcionalidad**: El código resuelve el problema propuesto
2. **Calidad**: Sigue estándares del proyecto
3. **Testing**: Tests adecuados y cobertura suficiente
4. **Performance**: No introduce regresiones de rendimiento
5. **Seguridad**: No expone credenciales o datos sensibles

### Merge Criteria
- ✅ Aprobación de al menos 1 maintainer
- ✅ Todos los checks de CI pasan
- ✅ Sin conflictos con main
- ✅ Documentación actualizada

---

## 📝 Guía de Commits

### Formato Semántico
```
<tipo>(<alcance>): <descripción>

[opcional: cuerpo]

[opcional: footer]
```

### Tipos
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Documentación
- `style`: Formato, sin cambios lógicos
- `refactor`: Refactorización
- `test`: Tests
- `chore**: Mantenimiento, dependencias

### Ejemplos
```bash
feat(csv): add email validation with RFC 5322

Implement regex-based email validation using Python's re module.
Add unit tests for valid and invalid email formats.

Closes #123

fix(db): handle connection timeout gracefully

Add retry logic for PostgreSQL connection timeouts.
Implement exponential backoff with max 3 attempts.

docs(readme): update installation instructions

Add Docker Compose setup for local development.
Update Python version requirements.

refactor(pipeline): extract validation logic to separate class

Create DataValidator class to improve testability.
Reduce MigrationPipeline complexity by 30%.
```

---

## 🐛 Reporte de Issues

### Bug Report Template
```markdown
## Descripción
Breve descripción del problema.

## Pasos para Reproducir
1. Ejecutar `python scripts/run_migration.py --config X`
2. Con archivo CSV adjunto
3. Observar error Y

## Comportamiento Esperado
Describir qué debería pasar.

## Comportamiento Actual
Describir qué está pasando.

## Entorno
- OS: Ubuntu 22.04
- Python: 3.11.5
- PostgreSQL: 15.2
- Versión del proyecto: v1.2.0

## Logs Adjuntos
```

### Feature Request Template
```markdown
## Título
Breve título de la funcionalidad solicitada.

## Problema a Resolver
Describir el problema que esta funcionalidad resolvería.

## Solución Propuesta
Descripción detallada de la solución propuesta.

## Alternativas Consideradas
Otras soluciones que se evaluaron y por qué no se eligieron.

## Casos de Uso
Ejemplos de cómo se usaría esta funcionalidad.
```

---

## 🏆 Contribuidores

Agradecemos a todos los contribuidores que han hecho este proyecto posible:

- [@Fisherk2](https://github.com/Fisherk2) - Creador y maintainer principal

---

## 📞 Contacto

- **Issues**: [GitHub Issues](https://github.com/Fisherk2/migrator-csv-postgres/issues)
- **Discusiones**: [GitHub Discussions](https://github.com/Fisherk2/migrator-csv-postgres/discussions)
- **Email**: fisherk2@example.com

---

> 💡 **Nota**: Esta guía evoluciona con el proyecto. Si algo no está claro, abre un issue para mejorarla.