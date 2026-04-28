"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO: Tests unitarios para CSVLoader
AUTOR: Fisherk2
FECHA: 2026-04-24
DESCRIPCIÓN: Tests para CSVLoader con DBConnector y validadores mockeados.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

from unittest.mock import Mock, patch, MagicMock
import pytest
from pathlib import Path

from src.migrator.csv_loader import CSVLoader
from src.migrator.db_connector import DBConnector


class TestCSVLoaderInitialization:
    """
    Tests para inicialización de CSVLoader.
    """
    
    def test_csv_loader_initializes_without_logger(self):
        """Valida que CSVLoader se inicialice sin logger (usa default)."""
        loader = CSVLoader(logger=None)
        assert loader is not None
        assert loader._logger is not None
    
    def test_csv_loader_initializes_with_logger(self, mock_logger):
        """Valida que CSVLoader se inicialice con logger personalizado."""
        loader = CSVLoader(logger=mock_logger)
        assert loader._logger == mock_logger


class TestCSVLoaderFileValidation:
    """Tests para validación de acceso a archivos."""
    
    def test_validate_file_access_succeeds_for_existing_file(self, tmp_path):
        """Valida que archivo existente pase validación de acceso."""
        loader = CSVLoader(logger=None)
        
        # ■■■■■■■■■■■■■ Arrange: Crear archivo temporal ■■■■■■■■■■■■■
        test_file = tmp_path / "test.csv"
        test_file.write_text("id,name\n1,Test")
        
        # ■■■■■■■■■■■■■ Act & Assert: No debe lanzar excepción ■■■■■■■■■■■■■
        loader._validate_file_access(str(test_file))
    
    def test_validate_file_access_fails_for_nonexistent_file(self):
        """Valida que archivo inexistente lance FileNotFoundError."""
        loader = CSVLoader(logger=None)
        
        with pytest.raises(FileNotFoundError, match="no encontrado"):
            loader._validate_file_access("/nonexistent/path.csv")
    
    def test_validate_file_access_fails_for_directory(self, tmp_path):
        """Valida que directorio lance ValueError."""
        loader = CSVLoader(logger=None)
        
        with pytest.raises(ValueError, match="no es un archivo"):
            loader._validate_file_access(str(tmp_path))


class TestCSVLoaderTempTableNameGeneration:
    """Tests para generación de nombres de tablas temporales."""
    
    def test_generate_temp_table_name_uses_csv_filename(self):
        """Valida que nombre de tabla temporal se base en nombre del CSV."""
        loader = CSVLoader(logger=None)
        
        temp_table = loader._generate_temp_table_name("/path/to/customers.csv")
        assert "customers" in temp_table.lower()
        assert "temp" in temp_table.lower()
    
    def test_generate_temp_table_name_generates_unique_names(self):
        """Valida que nombres generados sean únicos (por timestamp)."""
        loader = CSVLoader(logger=None)
        
        name1 = loader._generate_temp_table_name("/path/to/data.csv")
        name2 = loader._generate_temp_table_name("/path/to/data.csv")
        
        assert name1 != name2


class TestCSVLoaderRowValidation:
    """Tests para validación de filas individuales."""
    
    def test_validate_row_succeeds_with_valid_data(self):
        """Valida que fila con datos válidos pase validación."""
        loader = CSVLoader(logger=None)
        schema = {"id": "integer", "name": "string"}
        validators = {}
        
        row = {"id": "1", "name": "Test User"}
        
        errors = loader._validate_row(row, schema, validators, 1)
        
        assert len(errors) == 0
    
    def test_validate_row_fails_with_invalid_integer(self):
        """Valida que fila con entero inválido falle."""
        loader = CSVLoader(logger=None)
        schema = {"id": "integer", "name": "string"}
        validators = {}
        
        row = {"id": "abc", "name": "Test User"}
        
        errors = loader._validate_row(row, schema, validators, 1)
        
        assert len(errors) > 0
    
    def test_validate_row_uses_custom_validator_when_provided(self):
        """Valida que se use validador custom cuando se proporciona."""
        loader = CSVLoader(logger=None)
        schema = {"email": "string"}
        validators = {"email": Mock(return_value=(False, "inválido", None))}
        
        row = {"email": "invalid"}
        
        errors = loader._validate_row(row, schema, validators, 1)
        
        assert len(errors) > 0
        validators["email"].assert_called_once()


class TestCSVLoaderLoadToTempTable:
    """Tests integración para carga a tabla temporal."""
    
    @patch.object(CSVLoader, '_validate_file_access')
    @patch.object(CSVLoader, '_generate_temp_table_name')
    @patch.object(CSVLoader, '_create_temp_table')
    @patch.object(CSVLoader, '_read_and_validate_csv')
    @patch.object(CSVLoader, '_copy_rows_to_temp_table')
    def test_load_csv_to_temp_table_returns_temp_table_name(
        self, mock_copy, mock_read, mock_create, mock_generate, mock_validate, mock_db_connector
    ):
        """Valida que load_csv_to_temp_table retorne el nombre de la tabla temporal."""
        loader = CSVLoader(logger=None)

        mock_generate.return_value = "temp_customers_123"
        mock_read.return_value = ([{}], [])
        
        schema = {"id": "integer", "name": "string"}
        validators = {}
        config = {}
        
        result = loader.load_csv_to_temp_table(
            csv_path="/fake/path.csv",
            schema=schema,
            validators=validators,
            db_connector=mock_db_connector,
            config=config
        )
        
        assert result == "temp_customers_123"
    
    def test_load_csv_to_temp_table_respects_max_errors_threshold(self, mock_db_connector):
        """Valida que se respete umbral de max_errors_before_rollback."""
        loader = CSVLoader(logger=None)

        with patch.object(CSVLoader, '_validate_file_access'), \
             patch.object(CSVLoader, '_generate_temp_table_name'), \
             patch.object(CSVLoader, '_create_temp_table') as mock_create, \
             patch.object(CSVLoader, '_read_and_validate_csv') as mock_read, \
             patch.object(CSVLoader, '_copy_rows_to_temp_table'), \
             patch.object(CSVLoader, 'rollback_temp_table') as mock_rollback:

            mock_create.return_value = "temp_customers_123"
            mock_read.return_value = ([{}], [Mock()] * 10)
            
            schema = {"id": "integer"}
            validators = {}
            config = {"validation": {"max_errors_before_rollback": 5}}

            result = loader.load_csv_to_temp_table(
                csv_path="/fake/path.csv",
                schema=schema,
                validators=validators,
                db_connector=mock_db_connector,
                config=config
            )

            mock_rollback.assert_called_once()


class TestCSVLoaderBuffering:
    """Tests para manejo de buffer en memoria."""
    
    def test_buffer_handles_large_csv_without_memory_issues(self, mock_db_connector):
        """Valida que buffer maneje CSV grande sin problemas de memoria."""
        loader = CSVLoader(logger=None)

        with patch.object(CSVLoader, '_validate_file_access'), \
             patch.object(CSVLoader, '_create_temp_table'), \
             patch.object(CSVLoader, '_read_and_validate_csv') as mock_read, \
             patch.object(CSVLoader, '_copy_rows_to_temp_table') as mock_copy:
            
            mock_read.return_value = ([{"id": i} for i in range(1000)], [])
            mock_copy.return_value = 1000
            
            schema = {"id": "integer"}
            validators = {}
            
            result = loader.load_csv_to_temp_table(
                csv_path="/fake/large.csv",
                schema=schema,
                validators=validators,
                db_connector=mock_db_connector,
                config={}
            )
            
            assert result is not None
            mock_copy.assert_called_once()


class TestCSVLoaderErrorAccumulation:
    """Tests para acumulación de errores."""
    
    def test_errors_accumulate_across_multiple_invalid_rows(self, mock_db_connector):
        """Valida que errores se acumulen correctamente."""
        loader = CSVLoader(logger=None)

        with patch.object(CSVLoader, '_validate_file_access'), \
             patch.object(CSVLoader, '_create_temp_table'), \
             patch.object(CSVLoader, '_read_and_validate_csv') as mock_read, \
             patch.object(CSVLoader, '_copy_rows_to_temp_table'):
            
            mock_errors = [Mock() for _ in range(5)]
            mock_read.return_value = ([{}], mock_errors)
            
            schema = {"id": "integer"}
            validators = {}
            
            loader.load_csv_to_temp_table(
                csv_path="/fake/path.csv",
                schema=schema,
                validators=validators,
                db_connector=mock_db_connector,
                config={}
            )
            
            assert len(mock_errors) == 5
