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
```python
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# MÓDULO: [Nombre del Módulo]
# AUTOR: [Agente IA]
# FECHA: [YYYY-MM-DD]
# DESCRIPCIÓN: [Breve descripción del propósito]
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

from __future__ import annotations

# Stdlib imports
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
    """
    [Descripción clara de la clase].
    
    Attributes:
        [atributo]: [descripción]
    """
    
    def __init__(self, param: type) -> None:
        """Inicializa [clase]."""
        pass
    
    def method_name(self, param: type) -> return_type:
        """
        [Descripción del método].
        
        Args:
            param: [descripción]
            
        Returns:
            [descripción del retorno]
            
        Raises:
            [Exception]: [cuándo se lanza]
        """
        pass
```

### Para Tests
```python
import pytest
from unittest.mock import Mock
from src.migrator.module import ClassName

class TestClassName:
    """Tests de [ClassName]."""
    
    def test_method_succeeds(
        self,
        fixture_name: type
    ) -> None:
        """
        ARRANGE: [configuración del test].
        ACT: [acción a probar].
        ASSERT: [verificación del resultado].
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        
        # ■■■■■■■■■■■■■ ASSERT ■■■■■■■■■■■■■
        pass
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
