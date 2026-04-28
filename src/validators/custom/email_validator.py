"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO:      Validador de Formato Email - Dominio Específico E-commerce.
AUTOR:       Fisherk2
FECHA:       2026-04-22
DESCRIPCIÓN: Módulo de validación pura de formato de email según RFC 5322 simplificado.
Independiente de infraestructura, optimizado para validación fila-a-fila.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

# ▏▎▍▌▋▊▉▉▉▉▉▉▉▉ Regex compilado a nivel de módulo para optimización ▉▉▉▉▉▉▉▉▉▊▋▌▍▎▏
# RFC 5322 simplificado: local@domain con validación básica
_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

# ▏▎▍▌▋▊▉▉▉▉▉▉▉▉ Patrones comunes de errores para sugerencias ▉▉▉▉▉▉▉▉▉▊▋▌▍▎▏
_COMMON_TYPOS = {
    "gmial.com": "gmail.com",
    "gmial.es": "gmail.com", 
    "gamil.com": "gmail.com",
    "hotmal.com": "hotmail.com",
    "hotmial.com": "hotmail.com",
    "yahooo.com": "yahoo.com",
    "outlok.com": "outlook.com",
    "outlook.co": "outlook.com",
    "proton.com":"proton.me",
    "porton.me":"proton.me",
}

# ◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤ ⎡ DECISIÓN DE DISEÑO ⎦ ◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤
# Solo sugerir correcciones de dominio comunes,
# no intentar corregir la parte local (username) por privacidad


def _generate_email_suggestion(email: str) -> Optional[str]:
    """
    Genera sugerencia basada en patrones comunes de error.
    
    Args:
        email: Email original con posible error.
    Returns:
        Sugerencia corregida o None si no hay patrón claro.
    """
    if "@" not in email:
        return None
    
    local, domain = email.split("@", 1)
    domain_lower = domain.lower()
    
    # ■■■■■■■■■■■■■ Buscar typos comunes en dominio ■■■■■■■■■■■■■
    for typo, correction in _COMMON_TYPOS.items():
        if domain_lower == typo:
            return f"{local}@{correction}"
    
    # ■■■■■■■■■■■■■ Sugerir agregar .com si falta TLD común ■■■■■■■■■■■■■
    if "." not in domain and len(domain) > 3:
        return f"{local}@{domain}.com"
    
    return None


def validate_email_format(value: Optional[str]) -> Tuple[bool, str, Optional[str]]:
    """
    Valida formato de email RFC 5322 simplificado con sugerencias.
    
    Función pura que valida formato y proporciona feedback accionable.
    
    Args:
        value: Email a validar o None.
    Returns:
        Tupla (es_válido, mensaje_error, sugerencia_o_None):
        - es_válido: True si el formato es correcto
        - mensaje_error: Mensaje descriptivo en español
        - sugerencia_o_None: Sugerencia específica o None
    Examples:
        >>> result = validate_email_format("usuario@gmial.com")
        >>> print(result)  # (False, "Formato de email inválido", "usuario@gmail.com")
        
        >>> result = validate_email_format("usuario@dominio.com")
        >>> print(result)  # (True, "", None)
    """
    # ■■■■■■■■■■■■■ Manejo defensivo de valores nulos/vacíos ■■■■■■■■■■■■■
    if value is None:
        return False, "Email es requerido", None
    
    if not isinstance(value, str):
        return False, "Email debe ser texto", None
    
    # ■■■■■■■■■■■■■ Eliminar whitespace y verificar resultado ■■■■■■■■■■■■■
    email = value.strip()
    if not email:
        return False, "Email no puede estar vacío", None

    # ■■■■■■■■■■■■■ Validación de caracteres problemáticos antes del regex ■■■■■■■■■■■■■
    if email.startswith(".") or email.endswith("."):
        return False, "Email no puede empezar o terminar con un punto", None

    if ".." in email:
        return False, "Email no puede contener puntos consecutivos", None

    # ■■■■■■■■■■■■■ Validación principal con regex compilado ■■■■■■■■■■■■■
    if not _EMAIL_REGEX.match(email):

        # ▲▲▲▲▲▲ Generar sugerencia si hay patrón reconocible ▲▲▲▲▲▲
        suggestion = _generate_email_suggestion(email)

        if suggestion:
            return (
                False,
                f"Formato de email inválido. ¿Quisiste decir '{suggestion}'?",
                suggestion
            )
        else:
            return (
                False,
                "Formato de email inválido. Se espera formato: usuario@dominio.com",
                None
            )

    # ■■■■■■■■■■■■■ Verificar typos comunes de dominio aunque el formato sea válido ■■■■■■■■■■■■■
    if "@" in email:
        local, domain = email.split("@", 1)
        domain_lower = domain.lower()
        for typo, correction in _COMMON_TYPOS.items():
            if domain_lower == typo:
                suggestion = f"{local}@{correction}"
                return (
                    False,
                    f"Posible error en dominio. ¿Quisiste decir '{suggestion}'?",
                    suggestion
                )
    
    # ■■■■■■■■■■■■■ Validaciones adicionales de negocio ■■■■■■■■■■■■■
    if email.count("@") != 1:
        return False, "Email debe contener exactamente un @", None
    
    local, domain = email.split("@", 1)
    
    # ■■■■■■■■■■■■■ Validaciones de longitud razonables ■■■■■■■■■■■■■
    if len(local) > 64:
        return False, "Parte local del email demasiado larga (máx 64 caracteres)", None
    
    if len(domain) > 253:
        return False, "Dominio del email demasiado largo (máx 253 caracteres)", None

    # ■■■■■■■■■■■■■ Éxito: formato válido ■■■■■■■■■■■■■
    return True, "", None


# ▁▂▃▄▅▆▇███████ Exportación pública ███████▇▆▅▄▃▂▁
__all__ = ["validate_email_format"]