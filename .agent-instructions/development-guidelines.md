# Development Guidelines

## 🔧 Reglas de Generación de Código

### Principios SOLID Aplicados

#### S - Single Responsibility
- Cada clase tiene UNA razón para cambiar
- `MigrationPipeline`: solo orquesta flujo
- `CSVLoader`: solo carga/valida CSV
- `DBConnector`: solo operaciones PostgreSQL

#### O - Open/Closed
- Extensible sin modificación
- Nuevos validadores via Strategy pattern
- Nuevos formatos de reporte via ReportGenerator

#### L - Liskov Substitution
- Subtipos reemplazables por base
- Validadores específicos intercambiables

#### I - Interface Segregation
- Interfaces específicas por cliente
- No forzar dependencias no usadas

#### D - Dependency Inversion
- High-level modules dependen de abstracciones
- Pipeline depende de interfaces, no implementaciones

### Clean Architecture Rules

#### Dependencias Permitidas
```
Presentation → Application → Domain ← Infrastructure
```

#### Prohibiciones Estrictas
- ❌ Domain depende de Infrastructure
- ❌ Presentation accede directamente a Database
- ❌ Lógica de negocio en CLI
- ❌ Dependencies ciclicas

### Manejo de Errores

#### Jerarquía de Excepciones
```python
class MigrationError(Exception):
    """Base exception for migration operations."""

class ConfigurationError(MigrationError):
    """Invalid configuration or missing files."""

class OperationalError(MigrationError):
    """Database operations failures."""

class ValidationError(MigrationError):
    """Data validation failures."""
```

#### Strategy de Manejo
1. **Captura en capa apropiada**
2. **Logging con contexto**
3. **Propagación con tipo específico**
4. **Rollback transaccional si aplica**

## 📝 Formato de Respuesta Esperado

### Para Generación de Código

#### Formato de Docstrings (Google Style con Ejemplos)

**Módulos:**
```python
"""Descripción clara del propósito del módulo.

Este módulo proporciona [funcionalidad principal] con las siguientes características:
- Característica 1: descripción
- Característica 2: descripción
- Característica 3: descripción

Example:
    >>> from [package.module] import [function]
    >>>
    >>> # Ejemplo básico de uso
    >>> result = [function](param1, param2)
    >>> print(result)
"""
```

**Clases:**
```python
class ClassName:
    """Descripción clara de la clase y su propósito.

    Explica el rol de la clase en la arquitectura y patrones utilizados.
    Menciona si sigue algún patrón específico (Strategy, Facade, etc.).

    Attributes:
        _attr1: Descripción del atributo privado.
        _attr2: Descripción del atributo privado.

    Example:
        >>> instance = ClassName(param1, param2)
        >>> result = instance.method()
        >>> print(result)
    """
    
    def __init__(self, param1: type, param2: type) -> None:
        """Inicializa la clase con los parámetros necesarios.

        Args:
            param1: Descripción del primer parámetro.
            param2: Descripción del segundo parámetro.

        Example:
            >>> instance = ClassName("value1", "value2")
            >>> assert instance is not None
        """
        pass
```

**Funciones/Métodos:**
```python
def method_name(
    param1: type,
    param2: type,
    optional_param: type = "default"
) -> return_type:
    """Descripción clara del método y su propósito.

    Explica el algoritmo o lógica implementada, decisiones de diseño
    importantes y casos de uso típicos.

    Args:
        param1: Descripción del primer parámetro.
        param2: Descripción del segundo parámetro.
        optional_param: Descripción del parámetro opcional.

    Returns:
        Descripción detallada del valor retornado, incluyendo estructura
        y posibles valores.

    Raises:
        ValueError: Cuándo se lanza esta excepción.
        TypeError: Cuándo se lanza esta excepción.

    Example:
        >>> result = method_name("value1", "value2")
        >>> print(result)
        >>> 
        >>> # Con parámetro opcional
        >>> result = method_name("value1", "value2", optional_param="custom")
        >>> print(result)
    """
    pass
```

#### Formato de Archivo Completo
```python
"""Descripción del módulo con características principales.

Example:
    >>> from [package.module] import [main_class]
    >>>
    >>> instance = [main_class](param)
    >>> result = instance.method()
"""

from __future__ import annotations

# Standard library imports
import os
import sys
from typing import Dict, List, Optional

# Third-party imports
import psycopg2
import yaml

# Local imports
from src.migrator.db_connector import DBConnector
from src.utils.logger import get_logger

class ClassName:
    """Descripción clara de la clase.

    Attributes:
        _logger: Logger configurado para este módulo.
        _config: Configuración de la instancia.

    Example:
        >>> instance = ClassName(config)
        >>> result = instance.process_data()
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Inicializa la clase con configuración.

        Args:
            config: Diccionario con configuración necesaria.

        Example:
            >>> config = {"key": "value"}
            >>> instance = ClassName(config)
        """
        self._logger = get_logger(__name__)
        self._config = config
    
    def method_name(self, data: List[str]) -> Dict[str, int]:
        """Procesa los datos y retorna estadísticas.

        Args:
            data: Lista de elementos a procesar.

        Returns:
            Diccionario con conteos: {"processed": int, "errors": int}.

        Raises:
            ValueError: Si data está vacío.

        Example:
            >>> instance = ClassName({})
            >>> stats = instance.method_name(["a", "b", "c"])
            >>> print(stats["processed"])  # 3
        """
        pass
```

### Para Tests
```python
import pytest
from unittest.mock import Mock
from src.migrator.module import ClassName

class TestClassName:
    """Tests de ClassName cubriendo casos principales y edge cases."""
    
    def test_method_succeeds_with_valid_data(
        self,
        fixture_name: type
    ) -> None:
        """Verifica que el método funciona correctamente con datos válidos.

        ARRANGE: Configurar instancia con datos válidos.
        ACT: Ejecutar método con parámetros válidos.
        ASSERT: Verificar resultado esperado y sin errores.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        instance = ClassName(valid_config)
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        result = instance.method(valid_data)
        
        # ■■■■■■■■■■■■■ ASSERT ■■■■■■■■■■■■■
        assert result["success"] is True
        assert result["count"] > 0
    
    def test_method_raises_error_with_invalid_data(
        self
    ) -> None:
        """Verifica que el método lanza excepción con datos inválidos.

        ARRANGE: Configurar instancia con datos inválidos.
        ACT: Ejecutar método que debe fallar.
        ASSERT: Verificar que se lanza la excepción correcta.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        instance = ClassName(valid_config)
        
        # ■■■■■■■■■■■■■ ACT & ASSERT ■■■■■■■■■■■■■
        with pytest.raises(ValueError, match="mensaje esperado"):
            instance.method(invalid_data)
```

### Para Configuración YAML
```yaml
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# [NOMBRE]: [Descripción]
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

table: nombre_tabla
description: "Descripción del propósito"

columns:
  nombre_columna:
    type: tipo_dato
    required: boolean
    validation_message: "Mensaje de error"

validation:
  max_errors_before_rollback: number
  strict_mode: boolean
```

## 🚫 Prohibiciones Explícitas

### NO Hardcodear
- ❌ Credenciales de base de datos
- ❌ Paths absolutos (usar pathlib)
- ❌ Configuración de producción
- ❌ Datos de prueba en código

### NO Usar Dependencias Prohibidas
- ❌ `pandas` (usar csv stdlib + psycopg2 COPY)
- ❌ `sqlalchemy` (psycopg2 es más directo)
- ❌ `click` (usar argparse stdlib)
- ❌ `loguru` (logging stdlib es suficiente)
- ❌ `python-dotenv` (os.getenv() stdlib)

### NO Romper Patrones
- ❌ Lógica de negocio en CLI
- ❌ Acceso directo a BD desde Presentation
- ❌ Validadores sin estrategia
- ❌ Clases con múltiples responsabilidades

### NO Comprometer Seguridad
- ❌ Exponer credenciales en logs
- ❌ SQL injection (siempre usar parameterized queries)
- ❌ Paths relativos sin validación
- ❌ Información sensible en mensajes de error

## 🔍 Checklist de Validación

### Antes de Generar Código
- [ ] Entiendo el patrón arquitectónico requerido
- [ ] Sé qué capa estoy modificando
- [ ] Conozco las dependencias permitidas
- [ ] Sé qué prohibiciones aplicar

### Después de Generar Código
- [ ] Sigue principios SOLID
- [ ] Tiene type hints adecuados
- [ ] Maneja errores correctamente
- [ ] No hardcodea valores sensibles
- [ ] Es testable y mantenible
- [ ] **Docstrings en formato Google con ejemplos**
- [ ] **Ejemplos ejecutables en docstrings**
- [ ] **Imports organizados: stdlib, third-party, local**
- [ ] **Atributos privados con _prefix**
- [ ] **Nombres descriptivos y claros**

### Para Tests
- [ ] Usan fixtures existentes
- [ ] Tienen nombres descriptivos
- [ ] Verifican comportamiento, no implementación
- [ ] Mantienen aislamiento

## 🚀 Directivas Finales

### Prioridades
1. **Correctitud**: El código debe funcionar correctamente
2. **Claridad**: Código legible y auto-documentado
3. **Mantenibilidad**: Fácil de modificar y extender
4. **Performance**: Eficiente sin sacrificar claridad

### Decisiones de Diseño
- Siempre preferir stdlib sobre dependencias externas
- Usar composición sobre herencia cuando sea posible
- Mantener clases pequeñas (< 100 líneas)
- Prefieren funciones puras cuando sea aplicable
- **Documentar TODOs con formato específico**
- **Usar logging estructurado con get_logger()**
- **Validar argumentos al inicio de funciones**
- **Retornar tuplas (bool, str) para validaciones**

### Comunicación
- Ser explícito sobre decisiones arquitectónicas
- Documentar trade-offs cuando sea relevante
- Mantener consistencia con código existente

## 📚 Referencias Bibliográficas

### Clean Architecture
- Robert C. Martin - "Clean Architecture: A Craftsman's Guide"
- Principios de dependencia y separación de capas

### SOLID Principles
- Robert C. Martin - "Clean Code: A Handbook of Agile Software Craftsmanship"
- Principios de diseño orientado a objetos

### Testing Patterns
- Kent Beck - "Test-Driven Development: By Example"
- Gerardo Meszi - "Python Testing with pytest"

### Database Design
- C.J. Date - "An Introduction to Database Systems"
- Patrones de transacción y concurrencia

### Documentation Standards
- Google Python Style Guide - Docstring conventions
- PEP 257 - Docstring conventions
- Sphinx - Python documentation generation

## 📋 Formatos Específicos del Proyecto

### Comentarios de Código
```python
# ■■■■■■■■■■■■■ Sección principal del algoritmo ■■■■■■■■■■■■■
# ▲▲▲▲▲▲ Subsección específica ▲▲▲▲▲▲
# ▼▼▼▼▼▼ Decisión de diseño importante ▼▼▼▼▼▼
# ▏▎▍▌▋▊▉▉▉▉▉▉▉▉ Configuracion ▉▉▉▉▉▉▉▉▉▊▋▌▍▎▏
# ▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣  Separador ▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣ 
# Comentarios de una línea para explicaciones breves
```

### Naming Conventions
```python
# Variables y funciones: snake_case descriptivo
def validate_email_format(email: str) -> Tuple[bool, str, Optional[str]]:
    pass

# Clases: PascalCase
class EmailValidator:
    pass

# Constantes: SCREAMING_SNAKE_CASE
MAX_EMAIL_LENGTH = 254

# Atributos privados: _prefix
self._logger = get_logger(__name__)
self._config = {}
```

### Estructura de Archivos
```python
"""Docstring del módulo con ejemplo."""

from __future__ import annotations

# Standard library imports
import os
import sys
from typing import Dict, List, Optional

# Third-party imports
import psycopg2
import yaml

# Local imports
from src.migrator.db_connector import DBConnector
from src.utils.logger import get_logger

# ▁▂▃▄▅▆▇███████ Exportación pública ███████▇▆▅▄▃▂▁
__all__ = ["ClassName", "helper_function"]
```
