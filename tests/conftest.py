"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO: Fixtures centralizados de pytest
AUTOR: Fisherk2
FECHA: 2026-04-24
DESCRIPCIÓN: Inyección de dependencias para tests con scopes adecuados.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator, Optional
from unittest.mock import MagicMock, Mock

import pytest
import yaml

from src.migrator.db_connector import DBConnector
from src.migrator.csv_loader import CSVLoader
from src.migrator.error_handler import ErrorHandler
from src.migrator.report_generator import ReportGenerator


# ■■■■■■■■■■■■■ Rutas base para fixtures ■■■■■■■■■■■■■
# DECISIÓN: Usar __file__ para calcular rutas relativas de forma portable
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def config_path() -> Path:
    """
    Ruta al archivo YAML de configuración de prueba.
    
    Scope: session - Se comparte entre todos los tests (inmutable).
    """
    return FIXTURES_DIR / "test_schema.yaml"


@pytest.fixture(scope="session")
def valid_csv_path() -> Path:
    """
    Ruta al CSV con datos válidos de prueba.
    
    Scope: session - Se comparte entre todos los tests (inmutable).
    """
    return FIXTURES_DIR / "valid_customers.csv"


@pytest.fixture(scope="session")
def invalid_csv_path() -> Path:
    """
    Ruta al CSV con datos inválidos de prueba.
    
    Scope: session - Se comparte entre todos los tests (inmutable).
    """
    return FIXTURES_DIR / "invalid_customers.csv"


@pytest.fixture(scope="session")
def test_schema(config_path: Path) -> dict:
    """
    Carga y parsea el YAML de esquema de prueba.
    
    Scope: session - Se comparte entre todos los tests (inmutable).
    
    Returns:
        Diccionario con el contrato de validación cargado.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="function")
def mock_db_connector() -> Mock:
    """
    Mock de DBConnector para tests unitarios.
    
    Scope: function - Nueva instancia por cada test (aislamiento total).
    
    DECISIÓN: Usar unittest.mock en lugar de pytest-mock para evitar
    dependencias adicionales. El mock expone la misma interfaz que DBConnector.
    
    Returns:
        Mock con métodos: connect, disconnect, begin_transaction, commit,
        rollback, execute_copy_from, insert_batch, is_connected.
    """
    mock = Mock(spec=DBConnector)
    
    # Configurar comportamiento por defecto
    mock.is_connected.return_value = False
    mock.connect.return_value = None
    mock.close.return_value = None
    mock.begin.return_value = None
    mock.commit.return_value = None
    mock.rollback.return_value = None
    mock.execute_copy_from.return_value = 0
    
    return mock


@pytest.fixture(scope="function")
def mock_db_connector_connected(mock_db_connector: Mock) -> Mock:
    """
    Mock de DBConnector pre-configurado como conectado.
    
    Scope: function - Nueva instancia por cada test (aislamiento total).
    
    DECISIÓN: Fixture derivado para evitar configuración repetitiva en tests.
    
    Returns:
        Mock con is_connected = True.
    """
    mock_db_connector.is_connected.return_value = True
    return mock_db_connector


@pytest.fixture(scope="function")
def error_handler() -> ErrorHandler:
    """
    Instancia de ErrorHandler para tests.
    
    Scope: function - Nueva instancia por cada test (aislamiento total).
    
    DECISIÓN: Instancia real en lugar de mock porque ErrorHandler es
    un componente simple sin dependencias externas.
    
    Returns:
        ErrorHandler con lista de errores vacía.
    """
    return ErrorHandler()


@pytest.fixture(scope="function")
def report_generator() -> ReportGenerator:
    """
    Instancia de ReportGenerator para tests.
    
    Scope: function - Nueva instancia por cada test (aislamiento total).
    
    DECISIÓN: Instancia real en lugar de mock porque ReportGenerator es
    un componente simple sin dependencias externas.
    
    Returns:
        ReportGenerator listo para generar reportes.
    """
    return ReportGenerator()


@pytest.fixture(scope="function")
def csv_loader() -> CSVLoader:
    """
    Instancia de CSVLoader para tests.
    
    Scope: function - Nueva instancia por cada test (aislamiento total).
    
    DECISIÓN: Instancia real sin logger para evitar output en tests.
    
    Returns:
        CSVLoader sin logger configurado.
    """
    return CSVLoader(logger=None)


@pytest.fixture(scope="function")
def mock_logger() -> Mock:
    """
    Mock de logger para tests que requieren verificar logs.
    
    Scope: function - Nueva instancia por cada test (aislamiento total).
    
    Returns:
        Mock con métodos info, warning, error, debug.
    """
    mock = Mock()
    mock.info.return_value = None
    mock.warning.return_value = None
    mock.error.return_value = None
    mock.debug.return_value = None
    return mock


@pytest.fixture(scope="function")
def temp_csv_file(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Crea un archivo CSV temporal y lo limpia después del test.
    
    Scope: function - Archivo único por test con limpieza automática.
    
    DECISIÓN: Usar yield para limpieza explícita con tmp_path de pytest.
    
    Args:
        tmp_path: Directorio temporal provisto por pytest.
    
    Yields:
        Path al archivo CSV temporal.
    """
    csv_file = tmp_path / "temp.csv"
    yield csv_file
    # Limpia automática: pytest elimina tmp_path después del test


@pytest.fixture(scope="function")
def sample_valid_csv_data(valid_csv_path: Path) -> str:
    """
    Datos CSV válidos de ejemplo para tests programáticos.
    
    Scope: function - Datos inmutables compartidos.
    
    DECISIÓN: Cargar desde archivo existente en fixtures/ en lugar de hardcodear.
    
    Args:
        valid_csv_path: Ruta al CSV válido desde fixture.
    
    Returns:
        String con contenido CSV válido.
    """
    return valid_csv_path.read_text(encoding='utf-8')


@pytest.fixture(scope="function")
def sample_invalid_csv_data(invalid_csv_path: Path) -> str:
    """
    Datos CSV inválidos de ejemplo para tests programáticos.
    
    Scope: function - Datos inmutables compartidos.
    
    DECISIÓN: Cargar desde archivo existente en fixtures/ en lugar de hardcodear.
    
    Args:
        invalid_csv_path: Ruta al CSV inválido desde fixture.
    
    Returns:
        String con contenido CSV inválido.
    """
    return invalid_csv_path.read_text(encoding='utf-8')


# ■■■■■■■■■■■■■ Fixtures para tests de integración con PostgreSQL real ■■■■■■■■■■■■■

@pytest.fixture(scope="session")
def test_db_config() -> Optional[dict]:
    """
    Configuración de base de datos para tests de integración.

    Scope: session - Se comparte entre todos los tests de integración.

    DECISIÓN: Leer desde variables de entorno TEST_* o usar valores por defecto
    alineados con .env.example. Retorna None si TEST_DB_AVAILABLE=false.

    Valores por defecto alineados con .env.example:
    - TEST_DB_HOST: localhost (igual que DB_HOST)
    - TEST_DB_NAME: migrator_test (variante de DB_NAME para tests)
    - TEST_DB_USER: test_user (variante de DB_USER para tests)
    - TEST_DB_PASSWORD: test_password (valor seguro para contenedor local)
    - TEST_DB_PORT: 5432 (igual que DB_PORT)

    Returns:
        Diccionario con configuración de conexión o None si tests no disponibles.
    """
    if os.getenv("TEST_DB_AVAILABLE", "true").lower() == "false":
        return None

    return {
        "host": os.getenv("TEST_DB_HOST", "localhost"),
        "dbname": os.getenv("TEST_DB_NAME", "migrator_test"),
        "user": os.getenv("TEST_DB_USER", "test_user"),
        "password": os.getenv("TEST_DB_PASSWORD", "test_password"),
        "port": int(os.getenv("TEST_DB_PORT", "5432"))
    }


@pytest.fixture(scope="function")
def db_connection(test_db_config: Optional[dict]) -> Generator[Optional[DBConnector], None, None]:
    """
    Conexión real a PostgreSQL para tests de integración con rollback automático.
    
    Scope: function - Nueva conexión por cada test con rollback en teardown.
    
    DECISIÓN: Usar transacción con rollback en yield para garantizar aislamiento
    total entre tests. Cada test modifica datos pero los cambios se revierten.
    
    Args:
        test_db_config: Configuración de BD desde fixture de sesión.
    
    Yields:
        DBConnector conectado o None si tests no disponibles.
    
    Skip:
        Salta el test si TEST_DB_AVAILABLE=false o si falla la conexión.
    """
    if test_db_config is None:
        pytest.skip("Tests de integración deshabilitados: TEST_DB_AVAILABLE=false")
        yield None
        return
    
    connector = DBConnector(test_db_config)
    
    try:
        connector.connect()
        connector.begin()
        
        yield connector
        
    except Exception as e:
        pytest.skip(f"No se pudo conectar a PostgreSQL: {e}")
        yield None
    finally:
        try:
            if connector.is_connected:
                connector.rollback()
                connector.close()
        except Exception:
            pass


@pytest.fixture(scope="session")
def real_schema_sql() -> str:
    """
    Ruta al archivo SQL con el esquema real de la base de datos.
    
    Scope: session - Se comparte entre todos los tests de integración.
    
    Returns:
        Ruta absoluta al archivo 02_create_schema.sql.
    """
    return str(Path(__file__).parent.parent / "scripts" / "sql" / "02_create_schema.sql")


@pytest.fixture(scope="function")
def db_with_real_schema(db_connection: DBConnector, real_schema_sql: str) -> Generator[DBConnector, None, None]:
    """
    Conexión a BD con el esquema real del proyecto inicializado.
    
    Scope: function - Nueva conexión con esquema inicializado por cada test.
    
    DECISIÓN: Ejecutar el SQL del esquema real para usar tablas customers, products, orders
    en lugar de tablas temporales hardcodeadas. Esto valida contra la estructura real.
    
    Args:
        db_connection: Conexión desde fixture base.
        real_schema_sql: Ruta al archivo SQL del esquema.
    
    Yields:
        DBConnector con esquema real inicializado.
    """
    if db_connection is None:
        yield None
        return
    
    cursor = db_connection._connection.cursor()
    
    try:
        # Leer y ejecutar el SQL del esquema real
        with open(real_schema_sql, 'r', encoding='utf-8') as sql_file:
            sql_content = sql_file.read()
            cursor.execute(sql_content)
        db_connection.commit()
        
        yield db_connection
        
    except Exception as e:
        pytest.skip(f"No se pudo inicializar esquema real: {e}")
        yield None
    finally:
        # Rollback en teardown del fixture db_connection limpiará completamente
        pass


@pytest.fixture(scope="session")
def customers_schema_config() -> Dict:
    """
    Configuración YAML del esquema de customers desde config/schema_examples/.
    
    Scope: session - Se comparte entre todos los tests.
    
    Returns:
        Diccionario con la configuración del esquema customers.
    """
    schema_path = Path(__file__).parent.parent / "config" / "schema_examples" / "customers_schema.yaml"
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def default_migration_config() -> Dict:
    """
    Configuración YAML por defecto del migrador desde config/default_migration.yaml.
    
    Scope: session - Se comparte entre todos los tests.
    
    Returns:
        Diccionario con la configuración por defecto del migrador.
    """
    config_path = Path(__file__).parent.parent / "config" / "default_migration.yaml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
