"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO: Tests unitarios para validadores reusables
AUTOR: Fisherk2
FECHA: 2026-04-24
DESCRIPCIÓN: Tests para validate_integer, validate_string, validate_email, validate_phone.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

import pytest

from src.validators import (
    validate_integer,
    validate_string,
    validate_email_format,
    validate_phone_format,
)

# ■■■■■■■■■■■■■ Tests para validate_integer ■■■■■■■■■■■■■

class TestValidateInteger:
    """Tests para validación de enteros."""
    
    @pytest.mark.parametrize("value,expected_valid", [
        ("42", True),
        ("0", True),
        ("-100", True),
        ("1234567890", True),
    ])
    def test_validate_integer_succeeds_for_valid_inputs(self, value, expected_valid):
        """Valida que enteros válidos pasen la validación."""
        is_valid, message = validate_integer(value)
        assert is_valid == expected_valid
        assert message == ""
    
    @pytest.mark.parametrize("value,expected_error_msg", [
        (None, "El valor es requerido"),
        ("", "El valor es requerido"),
        ("abc", "'abc' no es un entero válido"),
        ("12.5", "'12.5' no es un entero válido"),
        ("123abc", "'123abc' no es un entero válido"),
    ])
    def test_validate_integer_fails_for_invalid_inputs(self, value, expected_error_msg):
        """Valida que inputs inválidos fallen con mensaje correcto."""
        is_valid, message = validate_integer(value)
        assert is_valid is False
        assert expected_error_msg in message


# ■■■■■■■■■■■■■ Tests para validate_string ■■■■■■■■■■■■■

class TestValidateString:
    """Tests para validación de strings."""
    
    @pytest.mark.parametrize("value,expected_valid", [
        ("hello", True),
        ("Hello World", True),
        ("áéíóú", True),
        ("123", True),
        ("  valid  ", True),
    ])
    def test_validate_string_succeeds_for_valid_inputs(self, value, expected_valid):
        """Valida que strings válidos pasen la validación."""
        is_valid, message = validate_string(value)
        assert is_valid == expected_valid
        assert message == ""
    
    @pytest.mark.parametrize("value,expected_error_msg", [
        (None, "El valor es requerido"),
        ("", "El string no puede estar vacío"),
        ("   ", "El string no puede estar vacío"),
        (123, "Se esperaba string, se recibió int"),
        (45.5, "Se esperaba string, se recibió float"),
    ])
    def test_validate_string_fails_for_invalid_inputs(self, value, expected_error_msg):
        """Valida que inputs inválidos fallen con mensaje correcto."""
        is_valid, message = validate_string(value)
        assert is_valid is False
        assert expected_error_msg in message


# ■■■■■■■■■■■■■ Tests para validate_email_format ■■■■■■■■■■■■■

class TestValidateEmailFormat:
    """Tests para validación de formato de email."""
    
    @pytest.mark.parametrize("value,expected_valid", [
        ("user@example.com", True),
        ("test.user@domain.co", True),
        ("user+tag@gmail.com", True),
        ("first.last@sub.domain.org", True),
    ])
    def test_validate_email_succeeds_for_valid_emails(self, value, expected_valid):
        """Valida que emails con formato correcto pasen la validación."""
        is_valid, message, suggestion = validate_email_format(value)
        assert is_valid == expected_valid
        assert message == ""
        assert suggestion is None
    
    def test_validate_email_fails_when_missing_at_symbol(self):
        """Valida que email sin @ falle."""
        is_valid, message, suggestion = validate_email_format("user.example.com")
        assert is_valid is False
        assert "inválido" in message.lower()
        assert suggestion is None
    
    def test_validate_email_generates_suggestion_for_common_typo(self):
        """Valida que se genere sugerencia para typo común de dominio."""
        is_valid, message, suggestion = validate_email_format("user@gmial.com")
        assert is_valid is False
        assert suggestion == "user@gmail.com"
        assert "gmail.com" in message
    
    @pytest.mark.parametrize("value,expected_error_msg", [
        (None, "Email es requerido"),
        ("", "Email no puede estar vacío"),
        (123, "Email debe ser texto"),
        ("@", "Formato de email inválido"),
        ("user@", "Formato de email inválido"),
        ("@domain.com", "Formato de email inválido"),
    ])
    def test_validate_email_fails_for_invalid_inputs(self, value, expected_error_msg):
        """Valida que inputs inválidos fallen con mensaje correcto."""
        is_valid, message, suggestion = validate_email_format(value)
        assert is_valid is False
        assert expected_error_msg in message
    
    def test_validate_email_rejects_consecutive_dots(self):
        """Valida que emails con puntos consecutivos sean rechazados."""
        is_valid, message, _ = validate_email_format("user..name@example.com")
        assert is_valid is False
        assert "puntos consecutivos" in message.lower()
    
    def test_validate_email_rejects_trailing_dot(self):
        """Valida que emails que terminan con punto sean rechazados."""
        is_valid, message, _ = validate_email_format("user@example.com.")
        assert is_valid is False
        assert "punto" in message.lower()


# ■■■■■■■■■■■■■ Tests para validate_phone_format ■■■■■■■■■■■■■

class TestValidatePhoneFormat:
    """Tests para validación de formato de teléfono."""
    
    @pytest.mark.parametrize("value,expected_valid", [
        ("+525512345678", True),
        ("+15551234567", True),
        ("+34912345678", True),
        ("+49123456789", True),
    ])
    def test_validate_phone_succeeds_for_valid_phones(self, value, expected_valid):
        """Valida que teléfonos con formato E.164 pasen la validación."""
        is_valid, message, suggestion = validate_phone_format(value)
        assert is_valid == expected_valid
        assert message == ""
        assert suggestion is None
    
    def test_validate_phone_allows_none_as_optional(self):
        """Valida que None sea aceptado como opcional."""
        is_valid, message, suggestion = validate_phone_format(None)
        assert is_valid is True
        assert "opcional" in message.lower()
        assert suggestion is None
    
    def test_validate_phone_allows_empty_string_as_optional(self):
        """Valida que string vacío sea aceptado como opcional."""
        is_valid, message, suggestion = validate_phone_format("")
        assert is_valid is True
        assert "opcional" in message.lower()
        assert suggestion is None
    
    def test_validate_phone_generates_suggestion_for_mx_format(self):
        """Valida que se genere sugerencia para formato MX sin código."""
        is_valid, message, suggestion = validate_phone_format("5551234567")
        assert is_valid is False
        assert suggestion == "+525551234567"
        assert "¿Quisiste decir" in message
    
    @pytest.mark.parametrize("value,expected_error_msg", [
        (123, "Teléfono debe ser texto"),  # type: ignore[arg-type]
        ("ABC-DEF-GHI", "inválido"),
        ("123", "demasiado corto"),
        ("+" + "9" * 20, "demasiado largo"),
    ])

    def test_validate_phone_fails_for_invalid_inputs(self, value, expected_error_msg):
        """Valida que inputs inválidos fallen con mensaje correcto."""
        is_valid, message, suggestion = validate_phone_format(value)
        assert is_valid is False
        assert expected_error_msg in message.lower()
