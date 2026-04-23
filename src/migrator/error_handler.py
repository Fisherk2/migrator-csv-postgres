"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO: Manejo de errores
AUTOR: Fisherk2
FECHA: 2026-04-23
DESCRIPCIÓN: Estructura centralizada de errores del pipeline de migración.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict

from src.utils.logger import get_logger


@dataclass(frozen=True)
class MigrationError:
    """
    Estructura inmutable para errores de migración.
    
    DECISIÓN: frozen=True garantiza inmutabilidad y previene efectos secundarios.
    El timestamp se genera automáticamente para trazabilidad completa.
    
    Attributes:
        row_num: Número de fila donde ocurrió el error (base 1).
        column: Nombre de la columna con el problema.
        field_type: Tipo de dato esperado (email, phone, integer, etc.).
        invalid_value: Valor que causó el error.
        reason: Descripción del error en español para reportes.
        suggestion: Sugerencia accionable o None si no aplica.
        timestamp: Momento exacto del error.
    """
    row_num: int
    column: str
    field_type: str
    invalid_value: str
    reason: str
    suggestion: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


def generate_correction_suggestion(field_type: str, invalid_value: str) -> Optional[str]:
    """
    Genera sugerencias heurísticas para corrección de errores comunes.
    
    DECISIÓN: Lógica determinista y segura. Si la sugerencia es incierta,
    retorna None para evitar información incorrecta.
    
    Args:
        field_type: Tipo de campo (email, phone, integer, float, etc.).
        invalid_value: Valor que causó el error.
    Returns:
        Sugerencia de corrección o None si no se puede inferir.
        
    Examples:
        >>> generate_correction_suggestion("email", "test.com")
        'Agregar @: test@test.com'
        >>> generate_correction_suggestion("phone", "555 123 4567")
        'Usar formato E.164: +15551234567'
    """
    if not field_type or not invalid_value:
        return None
    
    value = str(invalid_value).strip()
    
    if field_type == "email":
        if "@" not in value:
            return f"Agregar @: {value}@{value}.com" if "." in value else f"Agregar @: {value}@email.com"
        if "." not in value.split("@")[-1]:
            return f"Agregar dominio: {value}.com"
    
    elif field_type == "phone":

        # ■■■■■■■■■■■■■ Limpiar caracteres no numéricos ■■■■■■■■■■■■■
        digits = "".join(c for c in value if c.isdigit())
        if len(digits) == 10:
            return f"Usar formato E.164: +1{digits}"
        elif len(digits) > 10:
            return f"Usar formato E.164: +{digits}"
    
    elif field_type == "float":
        if "," in value and "." not in value:
            return f"Usar punto decimal: {value.replace(',', '.')}"
    
    elif field_type == "integer":
        if "." in value or "," in value:
            return f"Remover decimales: {value.replace('.', '').replace(',', '')}"
    
    return None


class ErrorHandler:
    """
    Gestiona acumulación, logging y umbrales de errores de migración.
    
    DECISIÓN: Separar acumulación de validación. Solo estructura y reporta.
    El logging usa el logger centralizado sin configurar handlers propios.
    
    Attributes:
        errors: Lista inmutable de errores acumulados.
        logger: Logger configurado para este módulo.
    """
    
    def __init__(self) -> None:
        """
        Inicializa el handler con logger y lista vacía.
        """
        self._errors: List[MigrationError] = []
        self._logger = get_logger(__name__)
    
    def add_error(self, error: MigrationError) -> None:
        """
        Agrega un error a la acumulación y registra el evento.
        
        Args:
            error: Instancia de MigrationError a agregar.
        """
        self._errors.append(error)
        self._logger.warning(
            f"Row {error.row_num}, {error.column} ({error.field_type}): {error.reason}"
        )
    
    def has_critical_errors(self, max_allowed: int) -> bool:
        """
        Verifica si se superó el umbral crítico de errores.
        
        Args:
            max_allowed: Número máximo de errores permitidos.
        Returns:
            True si se superó el umbral, False en caso contrario.
        """
        if len(self._errors) > max_allowed:
            self._logger.error(
                f"Umbral crítico superado: {len(self._errors)} > {max_allowed}"
            )
            return True
        return False
    
    def log_accumulated(self) -> None:
        """
        Registra un resumen de errores acumulados.
        """
        if not self._errors:
            return
        
        error_counts = {}
        for error in self._errors:
            key = f"{error.field_type}:{error.column}"
            error_counts[key] = error_counts.get(key, 0) + 1
        
        self._logger.info(f"Resumen de errores: {len(self._errors)} totales")
        for error_type, count in error_counts.items():
            self._logger.info(f"  {error_type}: {count}")
    
    def export_ready(self) -> List[Dict]:
        """
        Prepara errores para exportación JSON.
        
        Returns:
            Lista de diccionarios serializables por json.dumps().
        """
        return [
            {
                "row_num": error.row_num,
                "column": error.column,
                "field_type": error.field_type,
                "invalid_value": error.invalid_value,
                "reason": error.reason,
                "suggestion": error.suggestion,
                "timestamp": error.timestamp.isoformat()
            }
            for error in self._errors
        ]
    
    @property
    def error_count(self) -> int:
        """
        Número total de errores acumulados.
        """

        return len(self._errors)
    
    @property
    def errors(self) -> List[MigrationError]:
        """
        Retorna copia de la lista de errores.
        """
        return self._errors.copy()