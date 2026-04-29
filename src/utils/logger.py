"""Configuración centralizada de logging para la aplicación.

Este módulo provee una fábrica thread-safe de loggers configurados
para toda la aplicación, siguiendo principios de Clean Architecture.

Características principales:
- Fábrica thread-safe con cache para evitar configuraciones duplicadas
- Formato estructurado y consistente para todos los logs
- Configuración automática de handlers y formatters
- Prevención de propagación a librerías externas
- Función de reset para testing

Example:
    >>> from src.utils.logger import get_logger
    >>>
    >>> logger = get_logger(__name__)
    >>> logger.info("Iniciando migración")
    >>> logger.error("Error en conexión")
    >>>
    >>> # Para testing
    >>> from src.utils.logger import reset_logging
    >>> reset_logging()  # Limpia configuración
"""

from __future__ import annotations

import logging
import sys
from threading import Lock
from typing import Dict

# ▏▎▍▌▋▊▉▉▉▉▉▉▉▉ Lock thread-safe para configuración concurrente ▉▉▉▉▉▉▉▉▉▊▋▌▍▎▏
_logger_lock: Lock = Lock()
_cache: Dict[str, logging.Logger] = {}

# ▏▎▍▌▋▊▉▉▉▉▉▉▉▉ Formato estructurado y consistente para todos los logs ▉▉▉▉▉▉▉▉▉▊▋▌▍▎▏
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ▏▎▍▌▋▊▉▉▉▉▉▉▉▉ Niveles de log válidos con fallback seguro ▉▉▉▉▉▉▉▉▉▊▋▌▍▎▏
_VALID_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

def _normalize_level(level: str) -> int:
    """Normaliza y valida el nivel de logging.

    Convierte el nivel a mayúsculas, elimina espacios y valida contra
    los niveles permitidos. Si el nivel no es válido, usa INFO como fallback
    y registra una advertencia.

    Args:
        level: Nivel de log como string (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        Nivel de logging normalizado (int) correspondiente a logging.DEBUG, etc.

    Example:
        >>> _normalize_level("debug")
        10
        >>> _normalize_level("invalid")  # Usa INFO como fallback
        20
    """
    level_upper = level.upper().strip()
    
    if level_upper not in _VALID_LEVELS:
        logging.warning(
            "Nivel de log inválido '%s'. Usando INFO como fallback.",
            level
        )
        return logging.INFO
        
    return _VALID_LEVELS[level_upper]


def _create_handler(level: int) -> logging.StreamHandler:
    """Crea y configura el handler para stderr.

    Usa stderr para evitar interferencia con stdout del CLI. Configura
    el handler con el nivel especificado y un formatter estructurado.

    Args:
        level: Nivel de logging para el handler (logging.DEBUG, etc.).

    Returns:
        Handler configurado con formato estructurado y listo para usar.

    Example:
        >>> handler = _create_handler(logging.INFO)
        >>> assert isinstance(handler, logging.StreamHandler)
        >>> assert handler.level == logging.INFO
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
    handler.setFormatter(formatter)
    
    return handler


def get_logger(module_name: str, level: str = "INFO") -> logging.Logger:
    """Fábrica thread-safe de loggers configurados.

    Crea o retorna un logger con configuración consistente para toda
    la aplicación. Usa stderr para evitar interferencia con stdout del CLI.
    Implementa cache para evitar configuraciones duplicadas y es thread-safe.

    Args:
        module_name: Nombre del módulo (usualmente __name__).
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        Logger configurado y listo para uso.

    Raises:
        ValueError: Si module_name no es un string no vacío.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Iniciando migración")
        >>> logger.error("Error en conexión")
        >>>
        >>> # Con nivel personalizado
        >>> debug_logger = get_logger(__name__, "DEBUG")
        >>> debug_logger.debug("Información detallada")
    """

    # ■■■■■■■■■■■■■ Validación de entrada ■■■■■■■■■■■■■
    if not module_name or not isinstance(module_name, str):
        raise ValueError("module_name debe ser un string no vacío")
    
    # ■■■■■■■■■■■■■ Cache para evitar configuraciones duplicadas ■■■■■■■■■■■■■
    cache_key = f"{module_name}:{level}"
    
    with _logger_lock:
        if cache_key in _cache:
            return _cache[cache_key]
        
        # ▲▲▲▲▲▲ Normalización segura del nivel ▲▲▲▲▲▲
        normalized_level = _normalize_level(level)
        
        # ▲▲▲▲▲▲ Creación del logger con configuración específica ▲▲▲▲▲▲
        logger = logging.getLogger(module_name)
        logger.setLevel(normalized_level)
        
        # ▲▲▲▲▲▲ Evitar duplicación de handlers ▲▲▲▲▲▲
        if not logger.handlers:
            handler = _create_handler(normalized_level)
            logger.addHandler(handler)
        
        # ▲▲▲▲▲▲ Prevenir propagación a librerías externas ▲▲▲▲▲▲
        logger.propagate = False
        
        # ▲▲▲▲▲▲ Cache para uso futuro ▲▲▲▲▲▲
        _cache[cache_key] = logger
        
        return logger


def reset_logging() -> None:
    """Reseta la configuración de logging (útil para testing).

    Elimina todos los handlers del logger raíz y limpia el cache.
    Es útil para tests que necesitan un entorno de logging limpio.

    Example:
        >>> logger = get_logger(__name__)
        >>> reset_logging()  # Limpia configuración
        >>> assert len(_cache) == 0
    """
    with _logger_lock:
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        _cache.clear()


# ▁▂▃▄▅▆▇███████ Exportación pública ███████▇▆▅▄▃▂▁
__all__ = ["get_logger", "reset_logging"]