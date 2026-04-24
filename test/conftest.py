"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO: Fixtures centralizados de pytest
AUTOR: Fisherk2
FECHA: 2026-04-24
DESCRIPCIÓN: Inyección de dependencias para tests con scopes adecuados.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator
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
    mock.disconnect.return_value = None
    mock.begin_transaction.return_value = None
    mock.commit.return_value = None
    mock.rollback.return_value = None
    mock.execute_copy_from.return_value = 0
    mock.insert_batch.return_value = 0
    
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
def sample_valid_csv_data() -> str:
    """
    Datos CSV válidos de ejemplo para tests programáticos.
    
    Scope: function - Datos inmutables compartidos.
    
    Returns:
        String con contenido CSV válido (headers + 1 fila).
    """
    return "id,name,email,phone,created_at,updated_at\n1,Test User,test@example.com,+525512345678,2024-01-01 00:00:00,2024-01-01 00:00:00"


@pytest.fixture(scope="function")
def sample_invalid_csv_data() -> str:
    """
    Datos CSV inválidos de ejemplo para tests programáticos.
    
    Scope: function - Datos inmutables compartidos.
    
    Returns:
        String con contenido CSV inválido (email sin @).
    """
    return "id,name,email,phone,created_at,updated_at\n1,Test User,test.example.com,+525512345678,2024-01-01 00:00:00,2024-01-01 00:00:00"
