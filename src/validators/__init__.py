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

# ■■■■■■■■■■■■■ Intentar importar desde el auditor externo con manejo de errores robusto ■■■■■■■■■■■■■
try:
    # ▲▲▲▲▲▲ Importar funciones de validación de tipos del auditor ▲▲▲▲▲▲
    from extern.auditor.src.validators.type_validator import (
        validate_integer,
        validate_float,
        validate_string,
        validate_boolean,
    )
    
    # ▲▲▲▲▲▲ Importar funciones de validación de esquemas del auditor ▲▲▲▲▲▲
    from extern.auditor.src.validators.schema_validator import (
        load_schema_from_yaml,
        validate_schema_format,
    )
    
except ImportError as e:
    # ▲▲▲▲▲▲ Si el submodule no está inicializado, proporcionar mensaje claro ▲▲▲▲▲▲
    raise ImportError(
        f"No se pudo importar desde extern.auditor. "
        f"Ejecuta: git submodule update --init --recursive\n"
        f"Error original: {e}"
    ) from e

# ■■■■■■■■■■■■■ Espacio preparado para validadores custom futuros ■■■■■■■■■■■■■
# TODO: Implementar validadores específicos del dominio cuando sea necesario
# try:
#     from .custom import (
#         validate_email_format,
#         validate_phone_number,
#         validate_date_range,
#     )
# except ImportError:
#     # Los validadores custom son opcionales
#     pass

# ▏▎▍▌▋▊▉▉▉▉▉▉▉▉ Exportación pública de la API del Facade ▉▉▉▉▉▉▉▉▉▊▋▌▍▎▏
__all__ = [
    # ▲▲▲▲▲▲ Validadores de tipos (re-exportados del auditor) ▲▲▲▲▲▲
    "validate_integer",
    "validate_float", 
    "validate_string",
    "validate_boolean",
    
    # ▲▲▲▲▲▲ Validadores de esquemas (re-exportados del auditor) ▲▲▲▲▲▲
    "load_schema_from_yaml",
    "validate_schema_format",
]

# ▁▂▃▄▅▆▇███████ Metadatos del módulo para debugging y versionado ███████▇▆▅▄▃▂▁
__version__ = "1.0.0"
__author__ = "Fisherk2"
__purpose__ = "Facade Layer for External Validators"