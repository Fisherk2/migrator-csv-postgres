"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO:      Utilidades puras y reutilizables.
AUTOR:       Fisherk2
FECHA:       2026-04-22
DESCRIPCIÓN: Funciones stateless para YAML, rutas, strings y CSV.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """
    Carga segura de configuración YAML.
    
    Usa yaml.safe_load para prevenir RCE y valida existencia del archivo.
    
    Args:
        file_path: Ruta al archivo YAML de configuración.
    Returns:
        Diccionario con la configuración cargada.
    Raises:
        FileNotFoundError: Si el archivo no existe.
        yaml.YAMLError: Si el YAML es inválido o malformado.
        ValueError: Si el archivo está vacío o no contiene un diccionario.
    Examples:
        >>> config = load_yaml_config("config/default_migration.yaml")
        >>> csv_path = config["source"]["csv_path"]
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {file_path}")
    
    if not path.is_file():
        raise ValueError(f"La ruta no es un archivo válido: {file_path}")
    
    try:
        with open(path, "r", encoding="utf-8") as file:
            content = yaml.safe_load(file)
            
        if content is None:
            raise ValueError(f"El archivo YAML está vacío: {file_path}")
            
        if not isinstance(content, dict):
            raise ValueError(
                f"El archivo YAML debe contener un diccionario raíz, "
                f"se encontró: {type(content).__name__}"
            )
            
        return content
        
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error al parsear YAML en {file_path}: {e}") from e


def validate_file_path(
    file_path: str, 
    extensions: Tuple[str, ...] = (".csv", ".yaml", ".yml")
) -> Path:
    """
    Valida existencia, permisos y extensión de archivo.
    
    Realiza validaciones completas antes de retornar el Path normalizado.
    
    Args:
        file_path: Ruta al archivo a validar.
        extensions: Tupla de extensiones permitidas (con punto).
    Returns:
        Objeto Path validado y normalizado.
    Raises:
        FileNotFoundError: Si el archivo no existe.
        PermissionError: Si no hay permisos de lectura.
        ValueError: Si la extensión no está permitida o la ruta es inválida.
    Examples:
        >>> path = validate_file_path("data/customers.csv", (".csv",))
        >>> print(path.suffix)  # .csv
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError("file_path debe ser un string no vacío")
    
    path = Path(file_path).resolve()
    
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    
    if not path.is_file():
        raise ValueError(f"La ruta no corresponde a un archivo: {path}")
    
    if not os.access(path, os.R_OK):
        raise PermissionError(f"Sin permisos de lectura: {path}")
    
    if path.suffix.lower() not in [ext.lower() for ext in extensions]:
        raise ValueError(
            f"Extensión no permitida. Se esperaba una de: {extensions}, "
            f"se encontró: {path.suffix}"
        )
    
    return path

def normalize_string(
    value: Optional[str], 
    case: str = "lower", 
    strip_spaces: bool = True
) -> Optional[str]:
    """
    Normaliza strings eliminando caracteres invisibles y normalizando caso.
    
    Función pura que maneja None y strings vacíos de forma explícita.
    
    Args:
        value: String a normalizar o None.
        case: "lower", "upper", "title" o "preserve" (default: "lower").
        strip_spaces: Si se deben eliminar espacios en blanco (default: True).
    Returns:
        String normalizado o None si la entrada era None.
    Raises:
        ValueError: Si case no es un valor válido.
    Examples:
        >>> normalize_string("  HOLA  MUNDO  ")
        'hola mundo'
        >>> normalize_string(None)
        None
        >>> normalize_string("  Hola Mundo  ", case="title")
        'Hola Mundo'
    """
    if value is None:
        return None
    
    if not isinstance(value, str):
        raise ValueError(f"value debe ser string o None, se encontró: {type(value)}")
    
    # ■■■■■■■■■■■■■ Manejar strings vacíos explícitamente ■■■■■■■■■■■■■
    if value == "":
        return ""
    
    # ■■■■■■■■■■■■■ Eliminar caracteres invisibles (excepto espacios normales y newlines) ■■■■■■■■■■■■■
    cleaned = re.sub(r"[^\x20\x21-\x7E\r\n\t]", "", value)
    
    if strip_spaces:
        cleaned = cleaned.strip()
        # ▲▲▲▲▲▲ Normalizar múltiples espacios a uno solo ▲▲▲▲▲▲
        cleaned = re.sub(r"\s+", " ", cleaned)
    
    if case == "lower":
        return cleaned.lower()
    elif case == "upper":
        return cleaned.upper()
    elif case == "title":
        return cleaned.title()
    elif case == "preserve":
        return cleaned
    else:
        raise ValueError(f"case inválido: {case}. Usar 'lower', 'upper', 'title' o 'preserve'")


def sanitize_csv_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitiza una fila CSV convirtiendo strings vacíos a None y aplicando strip.
    
    Función pura que retorna una copia sin mutar el diccionario original.
    
    Args:
        row: Diccionario representando una fila CSV.
    Returns:
        Nuevo diccionario con valores sanitizados.
    Raises:
        ValueError: Si row no es un diccionario.
    Examples:
        >>> original = {"name": "  Juan  ", "email": "", "age": 25}
        >>> sanitized = sanitize_csv_row(original)
        >>> print(sanitized)  # {'name': 'Juan', 'email': None, 'age': 25}
        >>> print(original)     # {'name': '  Juan  ', 'email': '', 'age': 25}
    """
    if not isinstance(row, dict):
        raise ValueError(f"row debe ser un diccionario, se encontró: {type(row)}")
    
    sanitized = {}
    
    for key, value in row.items():
        if isinstance(value, str):
            if value.strip() == "":
                sanitized[key] = None
            else:
                sanitized[key] = value.strip()
        else:
            # ▲▲▲▲▲▲ Mantener valores no-string como están (números, booleanos, etc.) ▲▲▲▲▲▲
            sanitized[key] = value
    
    return sanitized


# ▏▎▍▌▋▊▉▉▉▉▉▉▉▉ Importar os aquí para evitar dependencia circular ▉▉▉▉▉▉▉▉▉▊▋▌▍▎▏
import os

# ▁▂▃▄▅▆▇███████ Exportación pública ███████▇▆▅▄▃▂▁
__all__ = [
    "load_yaml_config",
    "validate_file_path", 
    "normalize_string",
    "sanitize_csv_row"
]