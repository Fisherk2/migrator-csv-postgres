"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO:      Configuración centralizada de logging.
AUTOR:       Fisherk2
FECHA:       2026-04-22
DESCRIPCIÓN: Este módulo provee una fábrica thread-safe de loggers configurados
para toda la aplicación, siguiendo principios de Clean Architecture.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
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
    """
    Normaliza y valida el nivel de logging.
    Args:
        level: Nivel de log como string.
    Returns:
        Nivel de logging normalizado (int).
    Raises:
        ValueError: Si el nivel no es válido.
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
    """
    Crea y configura el handler para stderr.
    Args:
        level: Nivel de logging para el handler.
    Returns:
        Handler configurado con formato estructurado.
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
    handler.setFormatter(formatter)
    
    return handler


def get_logger(module_name: str, level: str = "INFO") -> logging.Logger:
    """
    Fábrica thread-safe de loggers configurados.
    
    Crea o retorna un logger con configuración consistente para toda
    la aplicación. Usa stderr para evitar interferencia con stdout del CLI.
    Args:
        module_name: Nombre del módulo (usualmente __name__).
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    Returns:
        Logger configurado y listo para uso.
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Iniciando migración")
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
    """
    with _logger_lock:
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        _cache.clear()


# ▁▂▃▄▅▆▇███████ Exportación pública ███████▇▆▅▄▃▂▁
__all__ = ["get_logger", "reset_logging"]