"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO: Tests unitarios para ErrorHandler y MigrationError
AUTOR: Fisherk2
FECHA: 2026-04-24
DESCRIPCIÓN: Tests para inmutabilidad, acumulación de errores y serialización JSON.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

import json
from datetime import datetime
import pytest
from dataclasses import FrozenInstanceError

from src.migrator.error_handler import MigrationError, ErrorHandler, generate_correction_suggestion


class TestMigrationError:
    """Tests para dataclass MigrationError."""
    
    def test_migration_error_is_immutable(self):
        """Valida que MigrationError sea inmutable (frozen=True)."""
        error = MigrationError(
            row_num=1,
            column="email",
            field_type="email",
            invalid_value="invalid",
            reason="Formato inválido",
            suggestion="user@example.com"
        )

        # ■■■■■■■■■■■■■ Lanzamiento de asignación al Data class congelado ■■■■■■■■■■■■■
        with pytest.raises(FrozenInstanceError):
            error.row_num = 2
    
    def test_migration_error_generates_timestamp_by_default(self):
        """Valida que timestamp se genere automáticamente si no se proporciona."""
        before = datetime.now()
        error = MigrationError(
            row_num=1,
            column="email",
            field_type="email",
            invalid_value="invalid",
            reason="Formato inválido"
        )
        after = datetime.now()
        
        assert before <= error.timestamp <= after
    
    def test_migration_error_accepts_custom_timestamp(self):
        """Valida que timestamp personalizado sea aceptado."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        error = MigrationError(
            row_num=1,
            column="email",
            field_type="email",
            invalid_value="invalid",
            reason="Formato inválido",
            timestamp=custom_time
        )
        
        assert error.timestamp == custom_time
    
    def test_migration_error_suggestion_defaults_to_none(self):
        """Valida que suggestion sea None por defecto."""
        error = MigrationError(
            row_num=1,
            column="email",
            field_type="email",
            invalid_value="invalid",
            reason="Formato inválido"
        )
        
        assert error.suggestion is None


class TestGenerateCorrectionSuggestion:
    """Tests para función generate_correction_suggestion."""
    
    def test_generate_suggestion_for_email_typo(self):
        """Valida sugerencia para typo común de dominio de email."""
        suggestion = generate_correction_suggestion("email", "user@gmial.com")
        assert "gmail.com" in suggestion.lower()
    
    def test_generate_suggestion_for_missing_at_in_email(self):
        """Valida sugerencia para email sin @."""
        suggestion = generate_correction_suggestion("email", "userdomain.com")
        assert "@" in suggestion
    
    def test_generate_suggestion_returns_none_for_unknown_pattern(self):
        """Valida que retorne None para patrón desconocido."""
        suggestion = generate_correction_suggestion("phone", "xyz")
        assert suggestion is None
    
    def test_generate_suggestion_for_integer_field(self):
        """Valida sugerencia para campo entero."""
        suggestion = generate_correction_suggestion("integer", "abc")

        # ■■■■■■■■■■■■■ Para enteros, la sugerencia puede ser None o un mensaje genérico ■■■■■■■■■■■■■
        assert suggestion is None or isinstance(suggestion, str)


class TestErrorHandlerInitialization:
    """Tests para inicialización de ErrorHandler."""
    
    def test_error_handler_initializes_with_empty_errors_list(self):
        """Valida que ErrorHandler se inicialice con lista de errores vacía."""
        handler = ErrorHandler()
        assert len(handler.errors) == 0
    
    def test_error_handler_has_logger_configured(self):
        """Valida que ErrorHandler tenga logger configurado."""
        handler = ErrorHandler()
        assert handler._logger is not None


class TestErrorHandlerAddError:
    """Tests para función add_error."""
    
    def test_add_error_increments_error_count(self):
        """Valida que add_error incremente contador de errores."""
        handler = ErrorHandler()
        
        error = MigrationError(
            row_num=1,
            column="email",
            field_type="email",
            invalid_value="invalid",
            reason="Formato inválido"
        )
        
        handler.add_error(error)
        assert len(handler.errors) == 1
    
    def test_add_error_logs_warning(self, mock_logger):
        """Valida que add_error registre advertencia."""
        handler = ErrorHandler()
        handler._logger = mock_logger
        
        error = MigrationError(
            row_num=1,
            column="email",
            field_type="email",
            invalid_value="invalid",
            reason="Formato inválido"
        )
        
        handler.add_error(error)
        mock_logger.warning.assert_called_once()
    
    def test_add_error_accumulates_multiple_errors(self):
        """Valida que múltiples errores se acumulen correctamente."""
        handler = ErrorHandler()
        
        for i in range(5):
            error = MigrationError(
                row_num=i + 1,
                column="email",
                field_type="email",
                invalid_value=f"invalid{i}",
                reason="Formato inválido"
            )
            handler.add_error(error)
        
        assert len(handler.errors) == 5
    
    def test_add_error_preserves_error_order(self):
        """Valida que errores se preserven en orden de inserción."""
        handler = ErrorHandler()
        
        error1 = MigrationError(1, "col1", "type1", "val1", "reason1")
        error2 = MigrationError(2, "col2", "type2", "val2", "reason2")
        error3 = MigrationError(3, "col3", "type3", "val3", "reason3")
        
        handler.add_error(error1)
        handler.add_error(error2)
        handler.add_error(error3)
        
        assert handler.errors[0].row_num == 1
        assert handler.errors[1].row_num == 2
        assert handler.errors[2].row_num == 3


class TestErrorHandlerHasCriticalErrors:
    """Tests para función has_critical_errors."""
    
    def test_has_critical_errors_returns_false_when_no_errors(self):
        """Valida que retorne False cuando no hay errores."""
        handler = ErrorHandler()
        assert handler.has_critical_errors(max_allowed=5) is False
    
    def test_has_critical_errors_returns_true_when_threshold_exceeded(self):
        """Valida que retorne True cuando se supera umbral."""
        handler = ErrorHandler()
        threshold = 3
        
        for i in range(threshold + 1):
            error = MigrationError(i, "col", "type", "val", "reason")
            handler.add_error(error)
        
        assert handler.has_critical_errors(max_allowed=threshold) is True
    
    def test_has_critical_errors_returns_false_when_below_threshold(self):
        """Valida que retorne False cuando está por debajo del umbral."""
        handler = ErrorHandler()
        threshold = 5
        
        for i in range(threshold - 1):
            error = MigrationError(i, "col", "type", "val", "reason")
            handler.add_error(error)
        
        assert handler.has_critical_errors(max_allowed=threshold) is False
    
    def test_has_critical_errors_returns_true_at_threshold_boundary(self):
        """Valida comportamiento en el límite del umbral."""
        handler = ErrorHandler()
        threshold = 5
        
        # ■■■■■■■■■■■■■ Agregar exactamente threshold errores ■■■■■■■■■■■■■
        for i in range(threshold):
            error = MigrationError(i, "col", "type", "val", "reason")
            handler.add_error(error)
        
        # ■■■■■■■■■■■■■ FIX: Aislamiento mejorado - verificar comportamiento esperado ■■■■■■■■■■■■■
        # El comportamiento debe ser: >= threshold es crítico
        result = handler.has_critical_errors(max_allowed=threshold)
        assert result is True


class TestErrorHandlerExportReady:
    """Tests para función export_ready (serialización JSON)."""
    
    def test_export_ready_returns_list_of_dicts(self):
        """Valida que export_ready retorne lista de diccionarios."""
        handler = ErrorHandler()
        
        error = MigrationError(
            row_num=1,
            column="email",
            field_type="email",
            invalid_value="invalid",
            reason="Formato inválido"
        )
        handler.add_error(error)
        
        export_data = handler.export_ready()
        assert isinstance(export_data, list)
        assert len(export_data) == 1
        assert isinstance(export_data[0], dict)
    
    def test_export_ready_includes_all_error_fields(self):
        """Valida que export_ready incluya todos los campos del error."""
        handler = ErrorHandler()
        
        error = MigrationError(
            row_num=1,
            column="email",
            field_type="email",
            invalid_value="invalid",
            reason="Formato inválido",
            suggestion="user@example.com"
        )
        handler.add_error(error)
        
        export_data = handler.export_ready()
        error_dict = export_data[0]
        
        assert error_dict["row_num"] == 1
        assert error_dict["column"] == "email"
        assert error_dict["field_type"] == "email"
        assert error_dict["invalid_value"] == "invalid"
        assert error_dict["reason"] == "Formato inválido"
        assert error_dict["suggestion"] == "user@example.com"
        assert "timestamp" in error_dict
    
    def test_export_ready_serializes_datetime_to_string(self):
        """Valida que datetime se serialice a string."""
        handler = ErrorHandler()
        
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        error = MigrationError(
            row_num=1,
            column="email",
            field_type="email",
            invalid_value="invalid",
            reason="Formato inválido",
            timestamp=custom_time
        )
        handler.add_error(error)
        
        export_data = handler.export_ready()
        error_dict = export_data[0]
        
        assert isinstance(error_dict["timestamp"], str)
    
    def test_export_ready_is_json_serializable(self):
        """Valida que export_ready sea serializable a JSON."""
        handler = ErrorHandler()
        
        error = MigrationError(
            row_num=1,
            column="email",
            field_type="email",
            invalid_value="invalid",
            reason="Formato inválido"
        )
        handler.add_error(error)
        
        export_data = handler.export_ready()
        
        # ■■■■■■■■■■■■■ No debe lanzar excepción ■■■■■■■■■■■■■
        json_str = json.dumps(export_data)
        assert json_str is not None
        assert len(json_str) > 0
    
    def test_export_ready_handles_suggestion_none(self):
        """Valida que suggestion None se maneje correctamente."""
        handler = ErrorHandler()
        
        error = MigrationError(
            row_num=1,
            column="email",
            field_type="email",
            invalid_value="invalid",
            reason="Formato inválido",
            suggestion=None
        )
        handler.add_error(error)
        
        export_data = handler.export_ready()
        error_dict = export_data[0]
        
        assert error_dict["suggestion"] is None


class TestErrorHandlerClear:
    """Tests para función clear."""
    
    def test_clear_resets_error_list(self):
        """Valida que clear resetee la lista de errores."""
        handler = ErrorHandler()
        
        error = MigrationError(1, "col", "type", "val", "reason")
        handler.add_error(error)
        
        assert len(handler.errors) == 1
        
        handler.clear()
        
        assert len(handler.errors) == 0
    
    def test_clear_can_be_called_multiple_times(self):
        """Valida que clear pueda llamarse múltiples veces sin error."""
        handler = ErrorHandler()
        
        handler.clear()
        handler.clear()
        handler.clear()
        
        assert len(handler.errors) == 0
