# Testing Guidelines

## 🧪 Estrategia de Testing

### Pirámide de Testing

```
    🔺 E2E Tests (Integration)
       - Tests completos del pipeline
       - Base de datos real (Docker)
       - Archivos CSV reales
    
    🔺🔺 Integration Tests  
       - Tests de componentes con BD
       - Fixtures compartidas
       - Rollback automático
    
    🔺🔺🔺 Unit Tests
       - Tests de funciones puras
       - Mocks para dependencias externas
       - Rápida ejecución
```

### Frameworks y Herramientas

- **pytest 7.0+**: Framework principal
- **pytest-cov 4.0+**: Cobertura de código
- **testcontainers-postgres**: BD real para tests de integración
- **unittest.mock**: Para aislar dependencias

## 📋 Tipos de Tests

### Unit Tests
**Ubicación**: `test/unit/`
**Propósito**: Verificar lógica de negocio aislada

```python
class TestValidatorAdapter:
    """Tests de ValidatorAdapter."""
    
    def test_validate_email_valid_format(
        self,
        valid_email_validator: ValidatorAdapter
    ) -> None:
        """
        ARRANGE: Validador configurado con reglas de email.
        ACT: Validar email con formato correcto.
        ASSERT: Retorna éxito sin errores.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        validator = valid_email_validator
        test_email = "user@domain.com"
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        result = validator.validate_email(test_email)
        
        # ■■■■■■■■■■■■■ ASSERT ■■■■■■■■■■■■■
        assert result[0] is True  # is_valid
        assert result[1] == ""   # no error message
        assert result[2] is None  # no suggestion
```

### Integration Tests
**Ubicación**: `test/integration/`
**Propósito**: Verificar interacción entre componentes

```python
class TestDBConnector:
    """Tests de integración con PostgreSQL."""
    
    def test_copy_from_with_real_database(
        self,
        db_connection: psycopg2.extensions.connection,
        temp_csv_file: str
    ) -> None:
        """
        ARRANGE: Conexión real a BD + CSV temporal.
        ACT: Ejecutar COPY FROM.
        ASSERT: Datos insertados correctamente.
        """
        # ■■■■■■■■■■■■■ ARRANGE: Ya conectado por fixture ■■■■■■■■■■■■■
        connector = DBConnector(db_connection)
        temp_table = "test_copy_table"
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        rows_inserted = connector.execute_copy_from(temp_csv_file, temp_table)
        
        # ■■■■■■■■■■■■■ ASSERT ■■■■■■■■■■■■■
        assert rows_inserted == 3
        # Verificar que los datos existen en la tabla temporal
        with db_connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {temp_table}")
            count = cursor.fetchone()[0]
            assert count == 3
```

### End-to-End Tests
**Ubicación**: `test/integration/test_migration_flow.py`
**Propósito**: Verificar flujo completo

```python
class TestMigrationFlow:
    """Tests del pipeline completo de migración."""
    
    def test_successful_migration_with_valid_csv(
        self,
        db_connection: psycopg2.extensions.connection,
        valid_customers_csv: str,
        migration_config: Dict[str, Any]
    ) -> None:
        """
        ARRANGE: CSV válido + configuración completa.
        ACT: Ejecutar pipeline completo.
        ASSERT: Migración exitosa con reporte correcto.
        """
        # ■■■■■■■■■■■■■ ARRANGE: Ya conectado por fixture ■■■■■■■■■■■■■
        pipeline = MigrationPipeline(migration_config, db_connection)
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        result = pipeline.execute(valid_customers_csv)
        
        # ■■■■■■■■■■■■■ ASSERT ■■■■■■■■■■■■■
        assert result["status"] == "success"
        assert result["imported"] > 0
        assert result["rejected"] == 0
        assert "report_path" in result
```

## 🎯 Fixtures y Datos de Prueba

### Fixtures Principales (conftest.py)

```python
@pytest.fixture
def db_connection() -> psycopg2.extensions.connection:
    """Proporciona conexión real a PostgreSQL para tests."""
    # Usar testcontainers o BD de prueba
    pass

@pytest.fixture
def valid_customers_csv() -> str:
    """CSV válido con datos de prueba."""
    return "test/fixtures/valid_customers.csv"

@pytest.fixture
def invalid_customers_csv() -> str:
    """CSV inválido con errores intencionados."""
    return "test/fixtures/invalid_customers.csv"

@pytest.fixture
def test_schema_yaml() -> str:
    """Esquema YAML de prueba."""
    return "test/fixtures/test_schema.yaml"

@pytest.fixture
def migration_config() -> Dict[str, Any]:
    """Configuración completa para migración."""
    return {
        "source": {"csv_path": "test.csv"},
        "target": {"table": "customers"},
        "validation": {"max_errors": 10}
    }
```

### Datos de Prueba

**CSV Válido**:
```csv
id,name,email,phone
1,John Doe,john@example.com,555-1234
2,Jane Smith,jane@example.com,555-5678
3,Bob Johnson,bob@example.com,555-9012
```

**CSV Inválido**:
```csv
id,name,email,phone
1,John Doe,john@,555-1234
2,Jane Smith,,555-5678
3,Bob Johnson,bob@example.com,invalid-phone
```

## 🔧 Configuración de Tests

### pytest.ini
```ini
[tool:pytest]
testpaths = test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    -v
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Tests that take more than 1 second
```

### Docker Compose para Tests
```yaml
version: '3.8'
services:
  test_db:
    image: postgres:15
    environment:
      POSTGRES_DB: test_migrator
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user -d test_migrator"]
      interval: 1s
      timeout: 5s
      retries: 5
```

## 📊 Métricas de Cobertura

### Objetivos
- **Cobertura total**: >80%
- **Cobertura de rama**: >75%
- **Cobertura de línea**: >85%

### Comandos
```bash
# Ejecutar todos los tests con cobertura
pytest --cov=src --cov-report=html

# Ver cobertura por módulo
pytest --cov=src.migrator --cov=src.validators

# Generar reporte para CI
pytest --cov=src --cov-report=xml --cov-report=term
```

## 🚨 Manejo de Errores en Tests

### Estrategia de Rollback Automático

```python
@pytest.fixture(autouse=True)
def transaction_rollback(db_connection):
    """Rollback automático después de cada test."""
    transaction = None
    try:
        transaction = db_connection.begin()
        yield
    finally:
        if transaction:
            transaction.rollback()
```

### Aislamiento de Tests

- Cada test usa su propia transacción
- Rollback automático después de cada test
- Tablas temporales con nombres únicos
- Limpieza de archivos temporales

## 📋 Checklist de Testing

### Antes de Escribir Tests
- [ ] Identificar tipo de test (unit/integration/e2e)
- [ ] Definir fixtures necesarias
- [ ] Establecer criterios de aceptación claros
- [ ] Considerar casos límite y errores

### Durante la Escritura
- [ ] Usar patrón AAA (Arrange, Act, Assert)
- [ ] Nombres descriptivos de tests
- [ ] Mock solo dependencias externas
- [ ] Verificar comportamiento, no implementación

### Después de Escribir Tests
- [ ] Verificar que el test falla inicialmente
- [ ] Corregir código para que pase el test
- [ ] Ejecutar suite completa
- [ ] Revisar cobertura

## 🔄 Integración Continua

### GitHub Actions Workflow
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 📚 Referencias de Testing

- **pytest Documentation**: https://docs.pytest.org/
- **Testcontainers**: https://www.testcontainers.org/
- **Python Testing with pytest**: Gerardo Meszi
- **Effective Testing**: Robert C. Martin
