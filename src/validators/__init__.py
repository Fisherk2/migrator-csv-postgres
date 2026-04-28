"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO:      Facade de Validadores - Boundary Layer para el Migrador CSV.
AUTOR:       Fisherk2
FECHA:       2026-04-22
DESCRIPCIÓN: Expone una API limpia y estable de validaciones del auditor externo.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

Este módulo actúa como un patrón Facade que expone una API limpia y estable
de validaciones del auditor externo, protegiendo al dominio de cambios en la
estructura interna de dependencias externas según Clean Architecture.

El dominio (src.migrator) depende de esta abstracción, no del detalle de
implementación del auditor externo, aplicando el Principio de Inversión
de Dependencias (DIP).
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
        """Wrapper para validación de enteros usando TypeValidator del auditor."""
        if value is None or value == "":
            return False, "El valor es requerido"
        is_valid = _type_validator.validate_type(value, "entero")
        if is_valid:
            return True, ""
        return False, f"'{value}' no es un entero válido"
    
    def validate_float(value: Any) -> tuple[bool, str]:
        """Wrapper para validación de flotantes usando TypeValidator del auditor."""
        if value is None or value == "":
            return False, "El valor es requerido"
        is_valid = _type_validator.validate_type(value, "flotante")
        if is_valid:
            return True, ""
        return False, f"'{value}' no es un flotante válido"
    
    def validate_string(value: Any) -> tuple[bool, str]:
        """Wrapper para validación de strings usando TypeValidator del auditor."""
        if value is None:
            return False, "El valor es requerido"
        if not isinstance(value, str):
            return False, f"Se esperaba string, se recibió {type(value).__name__}"
        if not value.strip():
            return False, "El string no puede estar vacío"
        # TypeValidator acepta cualquier valor como cadena, solo verificamos tipo y vacío aquí
        return True, ""
    
    def validate_boolean(value: Any) -> tuple[bool, str]:
        """Wrapper para validación de booleanos usando TypeValidator del auditor."""
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