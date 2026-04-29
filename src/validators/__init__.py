"""Facade de Validadores - Boundary Layer para el Migrador CSV.

Este módulo actúa como un patrón Facade que expone una API limpia y estable
de validaciones del auditor externo, protegiendo al dominio de cambios en la
estructura interna de dependencias externas según Clean Architecture.

El dominio (src.migrator) depende de esta abstracción, no del detalle de
implementación del auditor externo, aplicando el Principio de Inversión
de Dependencias (DIP).

Validadores disponibles:
- validate_integer: Validación de enteros usando TypeValidator del auditor
- validate_float: Validación de flotantes usando TypeValidator del auditor
- validate_string: Validación de strings usando TypeValidator del auditor
- validate_boolean: Validación de booleanos usando TypeValidator del auditor
- validate_email_format: Validador custom de formato de email
- validate_phone_format: Validador custom de formato de teléfono

Example:
    >>> from src.validators import validate_email_format, validate_integer
    >>>
    >>> # Validar email
    >>> is_valid, error = validate_email_format("user@example.com")
    >>> print(is_valid)  # True
    >>>
    >>> # Validar entero
    >>> is_valid, error = validate_integer("123")
    >>> print(is_valid)  # True
    >>>
    >>> # Validar con valor inválido
    >>> is_valid, error = validate_integer("abc")
    >>> print(is_valid)  # False
    >>> print(error)     # "abc no es un entero válido"
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

# ■■■■■■■■■■■■■ Agregar path del submodule al sys.path para importaciones directas ■■■■■■■■■■■■■
_auditor_path = Path(__file__).parent.parent.parent / "extern" / "auditor" / "src"
if str(_auditor_path) not in sys.path:
    sys.path.insert(0, str(_auditor_path))

# ■■■■■■■■■■■■■ Intentar importar desde el auditor externo con manejo de errores robusto ■■■■■■■■■■■■■
try:
    # ▲▲▲▲▲▲ Importar clase TypeValidator del auditor ▲▲▲▲▲▲
    from validators.type_validator import TypeValidator
    
    # ▲▲▲▲▲▲ Instancia singleton para wrappers ▲▲▲▲▲▲
    _type_validator = TypeValidator()
    
    # ▲▲▲▲▲▲ Wrappers para exponer funciones en lugar de métodos ▲▲▲▲▲▲
    def validate_integer(value: Any) -> tuple[bool, str]:
        """Wrapper para validación de enteros usando TypeValidator del auditor.

        Args:
            value: Valor a validar como entero.

        Returns:
            Tupla (is_valid, error_message) donde is_valid es True si el valor
            es un entero válido, y error_message contiene el mensaje de error.

        Example:
            >>> validate_integer("123")
            (True, '')
            >>> validate_integer("abc")
            (False, "'abc' no es un entero válido")
            >>> validate_integer("")
            (False, 'El valor es requerido')
        """
        if value is None or value == "":
            return False, "El valor es requerido"
        is_valid = _type_validator.validate_type(value, "entero")
        if is_valid:
            return True, ""
        return False, f"'{value}' no es un entero válido"
    
    def validate_float(value: Any) -> tuple[bool, str]:
        """Wrapper para validación de flotantes usando TypeValidator del auditor.

        Args:
            value: Valor a validar como flotante.

        Returns:
            Tupla (is_valid, error_message) donde is_valid es True si el valor
            es un flotante válido, y error_message contiene el mensaje de error.

        Example:
            >>> validate_float("123.45")
            (True, '')
            >>> validate_float("abc")
            (False, "'abc' no es un flotante válido")
            >>> validate_float("")
            (False, 'El valor es requerido')
        """
        if value is None or value == "":
            return False, "El valor es requerido"
        is_valid = _type_validator.validate_type(value, "flotante")
        if is_valid:
            return True, ""
        return False, f"'{value}' no es un flotante válido"
    
    def validate_string(value: Any) -> tuple[bool, str]:
        """Wrapper para validación de strings usando TypeValidator del auditor.

        Args:
            value: Valor a validar como string.

        Returns:
            Tupla (is_valid, error_message) donde is_valid es True si el valor
            es un string válido no vacío, y error_message contiene el mensaje de error.

        Example:
            >>> validate_string("Hola mundo")
            (True, '')
            >>> validate_string("")
            (False, 'El string no puede estar vacío')
            >>> validate_string(None)
            (False, 'El valor es requerido')
            >>> validate_string(123)
            (False, 'Se esperaba string, se recibió int')
        """
        if value is None:
            return False, "El valor es requerido"
        if not isinstance(value, str):
            return False, f"Se esperaba string, se recibió {type(value).__name__}"
        if not value.strip():
            return False, "El string no puede estar vacío"
        # TypeValidator acepta cualquier valor como cadena, solo verificamos tipo y vacío aquí
        return True, ""
    
    def validate_boolean(value: Any) -> tuple[bool, str]:
        """Wrapper para validación de booleanos usando TypeValidator del auditor.

        Args:
            value: Valor a validar como booleano.

        Returns:
            Tupla (is_valid, error_message) donde is_valid es True si el valor
            es un booleano válido, y error_message contiene el mensaje de error.

        Example:
            >>> validate_boolean("true")
            (True, '')
            >>> validate_boolean("false")
            (True, '')
            >>> validate_boolean("abc")
            (False, "'abc' no es un booleano válido")
            >>> validate_boolean("")
            (False, 'El valor es requerido')
        """
        if value is None or value == "":
            return False, "El valor es requerido"
        is_valid = _type_validator.validate_type(value, "booleano")
        if is_valid:
            return True, ""
        return False, f"'{value}' no es un booleano válido"
    
except ImportError as e:

    # ■■■■■■■■■■■■■ Si el submodule no está inicializado, proporcionar mensaje claro ■■■■■■■■■■■■■
    raise ImportError(
        f"No se pudo importar desde extern.auditor. "
        f"Ejecuta: git submodule update --init --recursive\n"
        f"Error original: {e}"
    ) from e

# ▼△▼△△▼△▼△▼△▼△▼△▼△ Validadores custom específicos del dominio △▼△▼△▼△▼△▼△▼△▼△▼△▼
from .custom.email_validator import validate_email_format
from .custom.phone_validator import validate_phone_format

# ▏▎▍▌▋▊▉▉▉▉▉▉▉▉ Exportación pública de la API del Facade ▉▉▉▉▉▉▉▉▉▊▋▌▍▎▏
__all__ = [
    # ▲▲▲▲▲▲ Validadores de tipos (wrappers usando TypeValidator del auditor) ▲▲▲▲▲▲
    "validate_integer",
    "validate_float",
    "validate_string",
    "validate_boolean",
    
    # ▲▲▲▲▲▲ Validadores custom específicos del dominio ▲▲▲▲▲▲
    "validate_email_format",
    "validate_phone_format",
]

# ▁▂▃▄▅▆▇███████ Metadatos del módulo para debugging y versionado ███████▇▆▅▄▃▂▁
__version__ = "1.0.0"
__author__ = "Fisherk2"
__purpose__ = "Facade Layer for External Validators"