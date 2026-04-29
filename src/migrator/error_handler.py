"""Estructura centralizada de errores del pipeline de migración.

Este módulo proporciona componentes para gestionar errores de migración
de manera estructurada, incluyendo:

- MigrationError: Dataclass inmutable para representar errores individuales
- generate_correction_suggestion: Función heurística para sugerir correcciones
- ErrorHandler: Gestor para acumular, registrar y reportar errores

El diseño separa la acumulación de errores de la validación, permitiendo
que el ErrorHandler solo se encargue de estructura y reporte.

Example:
    >>> from src.migrator.error_handler import ErrorHandler, MigrationError
    >>>
    >>> handler = ErrorHandler()
    >>> error = MigrationError(
    ...     row_num=1,
    ...     column="email",
    ...     field_type="email",
    ...     invalid_value="test.com",
    ...     reason="Formato de email inválido",
    ...     suggestion="Agregar @: test@test.com"
    ... )
    >>> handler.add_error(error)
    >>> assert handler.error_count == 1
    >>> assert handler.has_critical_errors(100) == False
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict

from src.utils.logger import get_logger


@dataclass(frozen=True)
class MigrationError:
    """Estructura inmutable para errores de migración.

    frozen=True garantiza inmutabilidad y previene efectos secundarios.
    El timestamp se genera automáticamente para trazabilidad completa.

    Attributes:
        row_num: Número de fila donde ocurrió el error (base 1).
        column: Nombre de la columna con el problema.
        field_type: Tipo de dato esperado (email, phone, integer, etc.).
        invalid_value: Valor que causó el error.
        reason: Descripción del error en español para reportes.
        suggestion: Sugerencia accionable o None si no aplica.
        timestamp: Momento exacto del error (generado automáticamente).

    Example:
        >>> error = MigrationError(
        ...     row_num=1,
        ...     column="email",
        ...     field_type="email",
        ...     invalid_value="test.com",
        ...     reason="Formato de email inválido",
        ...     suggestion="Agregar @: test@test.com"
        ... )
        >>> assert error.row_num == 1
        >>> assert error.column == "email"
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

    # ■■■■■■■■■■■■■ Typos comunes de dominio de email ■■■■■■■■■■■■■
    _COMMON_DOMAIN_TYPOS = {
        "gmial.com": "gmail.com",
        "gmial.es": "gmail.com",
        "gamil.com": "gmail.com",
        "hotmal.com": "hotmail.com",
        "hotmial.com": "hotmail.com",
        "yahooo.com": "yahoo.com",
        "outlok.com": "outlook.com",
        "outlook.co": "outlook.com",
        "proton.com": "proton.me",
        "porton.me": "proton.me",
    }

    if field_type == "email":
        if "@" not in value:
            return f"Agregar @: {value}@{value}.com" if "." in value else f"Agregar @: {value}@email.com"

        # ■■■■■■■■■■■■■ Detectar typos comunes de dominio ■■■■■■■■■■■■■
        if "@" in value:
            local, domain = value.split("@", 1)
            domain_lower = domain.lower()
            if domain_lower in _COMMON_DOMAIN_TYPOS:
                correction = _COMMON_DOMAIN_TYPOS[domain_lower]
                return f"¿Quisiste decir: {local}@{correction}?"

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
    """Gestiona acumulación, logging y umbrales de errores de migración.

    Separa la acumulación de errores de la validación, permitiendo que
    el ErrorHandler solo se encargue de estructura y reporte. El logging
    usa el logger centralizado sin configurar handlers propios.

    Attributes:
        _errors: Lista interna de errores acumulados.
        _logger: Logger configurado para este módulo.

    Example:
        >>> handler = ErrorHandler()
        >>> error = MigrationError(1, "email", "email", "test.com", "Inválido", "Agregar @")
        >>> handler.add_error(error)
        >>> assert handler.error_count == 1
        >>> handler.clear()
        >>> assert handler.error_count == 0
    """
    
    def __init__(self) -> None:
        """Inicializa el handler con logger y lista vacía.

        Example:
            >>> handler = ErrorHandler()
            >>> assert handler.error_count == 0
        """
        self._errors: List[MigrationError] = []
        self._logger = get_logger(__name__)
    
    def add_error(self, error: MigrationError) -> None:
        """Agrega un error a la acumulación y registra el evento.

        Args:
            error: Instancia de MigrationError a agregar.

        Example:
            >>> handler = ErrorHandler()
            >>> error = MigrationError(1, "email", "email", "test.com", "Inválido")
            >>> handler.add_error(error)
            >>> assert handler.error_count == 1
        """
        self._errors.append(error)
        self._logger.warning(
            f"Row {error.row_num}, {error.column} ({error.field_type}): {error.reason}"
        )
    
    def has_critical_errors(self, max_allowed: int) -> bool:
        """Verifica si se superó el umbral crítico de errores.

        Args:
            max_allowed: Número máximo de errores permitidos.

        Returns:
            True si se superó el umbral, False en caso contrario.

        Example:
            >>> handler = ErrorHandler()
            >>> for i in range(50):
            ...     handler.add_error(MigrationError(i, "col", "type", "val", "reason"))
            >>> assert handler.has_critical_errors(100) == False
            >>> assert handler.has_critical_errors(40) == True
        """
        if len(self._errors) >= max_allowed:
            self._logger.error(
                f"Umbral crítico superado: {len(self._errors)} >= {max_allowed}"
            )
            return True
        return False
    
    def log_accumulated(self) -> None:
        """Registra un resumen de errores acumulados.

        Agrupa errores por tipo (field_type:column) y registra el conteo
        de cada categoría para facilitar el análisis de problemas.

        Example:
            >>> handler = ErrorHandler()
            >>> handler.add_error(MigrationError(1, "email", "email", "val", "reason"))
            >>> handler.add_error(MigrationError(2, "email", "email", "val", "reason"))
            >>> handler.log_accumulated()  # Registra resumen
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
        """Prepara errores para exportación JSON.

        Convierte la lista de MigrationError a diccionarios serializables
        por json.dumps(), incluyendo todos los campos con timestamps en formato ISO.

        Returns:
            Lista de diccionarios serializables por json.dumps().

        Example:
            >>> handler = ErrorHandler()
            >>> handler.add_error(MigrationError(1, "email", "email", "val", "reason"))
            >>> export_data = handler.export_ready()
            >>> assert isinstance(export_data, list)
            >>> assert "timestamp" in export_data[0]
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
        """Número total de errores acumulados.

        Returns:
            Número de errores en la acumulación.

        Example:
            >>> handler = ErrorHandler()
            >>> assert handler.error_count == 0
            >>> handler.add_error(MigrationError(1, "col", "type", "val", "reason"))
            >>> assert handler.error_count == 1
        """

        return len(self._errors)
    
    @property
    def errors(self) -> List[MigrationError]:
        """Retorna copia de la lista de errores.

        Retorna una copia para prevenir mutación externa de la lista interna.

        Returns:
            Copia de la lista de MigrationError acumulados.

        Example:
            >>> handler = ErrorHandler()
            >>> error = MigrationError(1, "col", "type", "val", "reason")
            >>> handler.add_error(error)
            >>> errors = handler.errors
            >>> assert len(errors) == 1
        """
        return self._errors.copy()

    def clear(self) -> None:
        """Limpia la lista de errores acumulados.

        Útil para reutilizar la misma instancia de ErrorHandler en múltiples
        migraciones o para pruebas.

        Example:
            >>> handler = ErrorHandler()
            >>> handler.add_error(MigrationError(1, "col", "type", "val", "reason"))
            >>> assert handler.error_count == 1
            >>> handler.clear()
            >>> assert handler.error_count == 0
        """
        self._errors.clear()