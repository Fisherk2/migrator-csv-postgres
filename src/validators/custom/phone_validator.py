"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO:      Validador de Formato Teléfono - Dominio Específico E-commerce.
AUTOR:       Fisherk2
FECHA:       2026-04-23
DESCRIPCIÓN: Módulo de validación pura de formato telefónico según E.164 flexible.
Independiente de infraestructura, optimizado para validación fila-a-fila.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

# ▏▎▍▌▋▊▉▉▉▉▉▉▉▉ Regex compilado a nivel de módulo para optimización ▉▉▉▉▉▉▉▉▉▊▋▌▍▎▏
# E.164 flexible: +[código_país][número] con formato básico
_PHONE_REGEX = re.compile(
    r"^\+?[1-9]\d{1,14}$"
)

# ▏▎▍▌▋▊▉▉▉▉▉▉▉▉ Regex para detectar formatos comunes que necesitan limpieza ▉▉▉▉▉▉▉▉▉▊▋▌▍▎▏
_PHONE_CLEANUP_REGEX = re.compile(
    r"[^\d+]"  # Eliminar excepto dígitos y +
)

# ▏▎▍▌▋▊▉▉▉▉▉▉▉▉ Códigos de país comunes para validación básica ▉▉▉▉▉▉▉▉▉▊▋▌▍▎▏
_COUNTRY_CODES = {
    "1": "US/CA",     # Estados Unidos/Canadá
    "52": "MX",       # México
    "54": "AR",       # Argentina
    "55": "BR",       # Brasil
    "56": "CL",       # Chile
    "57": "CO",       # Colombia
    "58": "VE",       # Venezuela
    "34": "ES",       # España
    "44": "GB",       # Reino Unido
    "49": "DE",       # Alemania
    "33": "FR",       # Francia
    "39": "IT",       # Italia
}

# ◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤ ⎡ DECISIÓN DE DISEÑO ⎦ ◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤
# Aceptar formatos flexibles pero sugerir estandarización a E.164
# para consistencia en la base de datos

def _clean_phone_number(phone: str) -> str:
    """
    Limpia número telefónico eliminando caracteres no numéricos.
    
    Args:
        phone: Número telefónico original.
    Returns:
        Número limpio con solo dígitos y posible + inicial.
    """

    # ■■■■■■■■■■■■■ Eliminar espacios, guiones, paréntesis y otros caracteres ■■■■■■■■■■■■■
    cleaned = _PHONE_CLEANUP_REGEX.sub("", phone)
    
    # ■■■■■■■■■■■■■ Asegurar que + solo esté al inicio si existe ■■■■■■■■■■■■■
    if cleaned.startswith("+"):
        return "+" + cleaned[1:].lstrip("0")
    else:
        return cleaned.lstrip("0")


def _generate_phone_suggestion(phone: str) -> Optional[str]:
    """
    Genera sugerencia de formato E.164 basada en el número limpio.
    
    Args:
        phone: Número telefónico limpio.
    Returns:
        Sugerencia en formato E.164 o None si no es posible.
    """

    # ■■■■■■■■■■■■■ Si ya tiene + y es válido, no sugerir cambios ■■■■■■■■■■■■■
    if phone.startswith("+") and _PHONE_REGEX.match(phone):
        return None
    
    # ■■■■■■■■■■■■■ Si no tiene +, intentar inferir código de país ■■■■■■■■■■■■■
    if not phone.startswith("+") and len(phone) >= 10:

        # ▲▲▲▲▲▲ Intentar con código de México (52) como default para LATAM ▲▲▲▲▲▲
        if len(phone) == 10:  # Formato MX sin código
            return f"+52{phone}"

        elif len(phone) == 11 and phone.startswith("1"):  # Formato US
            return f"+1{phone[1:]}"
        elif len(phone) >= 11:  # Intentar extraer código de país
            for code_len in [1, 2, 3]:
                if len(phone) > code_len:
                    potential_code = phone[:code_len]
                    if potential_code in _COUNTRY_CODES:
                        return f"+{potential_code}{phone[code_len:]}"
    
    return None

def validate_phone_format(value: Optional[str]) -> Tuple[bool, str, Optional[str]]:
    """
    Valida formato de teléfono E.164 flexible con sugerencias.
    
    Función pura que valida formato y proporciona feedback accionable.
    
    Args:
        value: Teléfono a validar o None.
    Returns:
        Tupla (es_válido, mensaje_error, sugerencia_o_None):
        - es_válido: True si el formato es correcto
        - mensaje_error: Mensaje descriptivo en español
        - sugerencia_o_None: Sugerencia específica o None
    Examples:
        >>> result = validate_phone_format("555-123-4567")
        >>> print(result)  # (False, "Formato de teléfono inválido", "+15551234567")
        
        >>> result = validate_phone_format("+525551234567")
        >>> print(result)  # (True, "", None)
    """

    # ■■■■■■■■■■■■■ Manejo defensivo de valores nulos/vacíos ■■■■■■■■■■■■■
    if value is None:
        return True, "Teléfono es opcional", None
    
    if not isinstance(value, str):
        return False, "Teléfono debe ser texto", None
    
    # ■■■■■■■■■■■■■ Eliminar whitespace y verificar resultado ■■■■■■■■■■■■■
    phone = value.strip()
    if not phone:
        return True, "Teléfono es opcional", None
    
    # ■■■■■■■■■■■■■ Limpiar número de caracteres no numéricos ■■■■■■■■■■■■■
    cleaned_phone = _clean_phone_number(phone)

    # ■■■■■■■■■■■■■ Validar que tenga dígitos después de limpieza ■■■■■■■■■■■■■
    if not cleaned_phone or cleaned_phone == "+":
        return (
            False,
            "Formato de telefono inválido: debe contener al menos un dígito",
            None
        )

    # ■■■■■■■■■■■■■ Validar longitud mínima después de limpieza ■■■■■■■■■■■■■
    if len(cleaned_phone.replace("+", "")) < 7:
        return (
            False,
            "Teléfono demasiado corto (mínimo 7 dígitos)",
            None
        )
    
    # ■■■■■■■■■■■■■ Validar longitud máxima ■■■■■■■■■■■■■
    if len(cleaned_phone) > 15:
        return (
            False,
            "Teléfono demasiado largo (máximo 15 dígitos)",
            None
        )

    # ■■■■■■■■■■■■■ Si no tiene + y tiene 10 dígitos, sugerir formato MX ■■■■■■■■■■■■■
    if not cleaned_phone.startswith("+") and len(cleaned_phone) == 10:
        suggestion = f"+52{cleaned_phone}"
        return (
            False,
            f"Formato de teléfono inválido. ¿Quisiste decir '{suggestion}'?",
            suggestion
        )

    # ■■■■■■■■■■■■■ Validación principal con regex compilado ■■■■■■■■■■■■■
    if not _PHONE_REGEX.match(cleaned_phone):

        # ▲▲▲▲▲▲ Generar sugerencia de formato E.164 ▲▲▲▲▲▲
        suggestion = _generate_phone_suggestion(cleaned_phone)
        
        if suggestion:
            return (
                False,
                f"Formato de teléfono inválido. ¿Quisiste decir '{suggestion}'?",
                suggestion
            )
        else:
            return (
                False,
                "Formato de teléfono inválido. Se espera formato: +[código_país][número]",
                None
            )
    
    # ■■■■■■■■■■■■■ Validaciones adicionales de negocio ■■■■■■■■■■■■■
    if cleaned_phone.startswith("+"):
        digits_only = cleaned_phone[1:]
        country_code = ""
        
        # ▲▲▲▲▲▲ Extraer código de país para validación ▲▲▲▲▲▲
        for code_len in [1, 2, 3]:
            if len(digits_only) >= code_len:
                potential_code = digits_only[:code_len]
                if potential_code in _COUNTRY_CODES:
                    country_code = potential_code
                    break
        
        if country_code and len(digits_only) - len(country_code) < 7:
            return (
                False,
                f"Número de teléfono demasiado corto para código +{country_code}",
                None
            )
    
    # ■■■■■■■■■■■■■ Éxito: formato válido ■■■■■■■■■■■■■
    return True, "", None


# ▁▂▃▄▅▆▇███████ Exportación pública ███████▇▆▅▄▃▂▁
__all__ = ["validate_phone_format"]