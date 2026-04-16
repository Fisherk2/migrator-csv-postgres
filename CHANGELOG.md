# Registro de Cambios (Changelog)

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Sin Lanzar]

### Agregado
- Marcador de posición para cambios futuros

## [1.0.0] - 2026-03-16

### Agregado

#### Infraestructura de Base de Datos
- **Configuración completa de PostgreSQL** con scripts de creación, migración y seeding
- **Suite de pruebas automatizada** con 7 pruebas unitarias comprehensivas usando patrón AAA (Arrange-Act-Assert)
- **Ejecución zero-tolerant** - las pruebas se detienen inmediatamente en el primer fallo para depuración limpia
- **Soporte de autenticación peer** para desarrollo local seguro sin prompts de contraseña
- **Automatización de limpieza de base de datos** - limpieza automática del entorno en fallos de pruebas

#### Scripts Principales
- **`create_database.sql`** - Creación de base de datos con codificación UTF-8 y propiedad adecuadas
- **`drop_database.sql`** - Terminación segura de base de datos con limpieza de conexiones
- **Scripts de migración** (`001_create_users_table.sql`, `002_create_projects_table.sql`) con definiciones completas de esquema
- **Scripts de seed** (`001_seed_users.sql`, `002_seed_projects.sql`) con datos de prueba e integridad referencial
- **`verify_setup.sh`** - Validación completa del entorno con reporte detallado

#### Framework de Pruebas
- **Suite de pruebas unitarias** (`test/test_scripts.sh`) con manejo comprehensivo de errores y depuración
- **Implementación del patrón Arrange-Act-Assert** para todas las operaciones de base de datos
- **Depuración en tiempo real** con registros paso a paso detallados
- **Limpieza automatizada** en fallos de pruebas para mantener entorno de desarrollo limpio
- **Seguimiento de resultados de pruebas** con estadísticas de paso/fallo y códigos de salida para integración CI/CD

#### Herramientas de Desarrollo
- **Configuración de entorno** (soporte `.env`) con gestión segura de credenciales
- **Ejemplos de conexión** (`connection_example.env`) para configuración fácil
- **Estándares de scripts shell** con manejo apropiado de errores y documentación
- **Compatibilidad multiplataforma** (Linux, macOS, WSL) soporte

#### Documentación
- **README comprehensivo** con instrucciones de configuración y ejemplos de uso
- **Registros de Decisiones de Arquitectura** (ADR.md) para decisiones de diseño
- **Diagrama de Entidad-Relación** (docs/ERD.md) con visualización Mermaid
- **Documentación de API** para esquema de base de datos y operaciones
- **Guías de desarrollador** y estándares de contribución

### Cambiado

#### Esquema de Base de Datos
- **Estructuras de tabla optimizadas** con indexación y restricciones adecuadas
- **Integridad de datos mejorada** con relaciones de clave foránea y reglas de validación
- **Seguridad mejorada** con permisos de usuario adecuados y controles de acceso

#### Flujo de Desarrollo
- **Manejo de errores estandarizado** a través de todos los scripts shell
- **Capacidades de depuración mejoradas** con opciones de registro verbose
- **Aislamiento de pruebas mejorado** para ejecución independiente de pruebas

### Deprecado

- **Configuración manual de base de datos** - reemplazado con scripts automatizados
- **Autenticación basada en contraseña** para desarrollo local (reemplazado con autenticación peer)

### Removido

- **Archivos de configuración heredados** - consolidados en formato estandarizado `.env`
- **Procedimientos de prueba obsoletos** - reemplazados con suite de pruebas unitarias comprehensiva

### Corregido

#### Problemas de Autenticación
- **Configuración de autenticación peer** para desarrollo local sin problemas
- **Errores de conexión de base de datos** con manejo apropiado de errores y lógica de reintento
- **Conflictos de permisos** entre roles de superusuario y usuario de aplicación

#### Confiabilidad de Pruebas
- **Ejecución zero-tolerant** previene fallos en cascada de pruebas
- **Limpieza de entorno** asegura estado limpio entre ejecuciones de pruebas
- **Operaciones idempotentes** para ejecución repetible de pruebas

#### Integridad de Datos
- **Detección y prevención de registros huérfanos** en datos seed
- **Manejo de transacciones** para operaciones atómicas de base de datos
- **Validación de restricciones** con mensajes de error apropiados

### Seguridad

#### Control de Acceso
- **Principio de menor privilegio** implementado para usuarios de base de datos
- **Gestión segura de credenciales** sin contraseñas codificadas
- **Autenticación peer** elimina exposición de contraseñas en registros

#### Protección de Datos
- **Validación de entrada** en todas las operaciones de base de datos
- **Prevención de inyección SQL** a través de consultas parametrizadas
- **Registro de auditoría** para operaciones y cambios de base de datos

---

## Información del Proyecto

### Repositorio
- **Nombre**: Plantilla de Base de Datos PostgreSQL
- **Descripción**: Plantilla completa de infraestructura de base de datos con pruebas automatizadas y despliegue
- **Repositorio**: https://github.com/Fisherk2/plantilla-proyecto-sistema-datos
- **Licencia**: MIT License

### Stack Tecnológico
- **Base de Datos**: PostgreSQL 15+
- **Scripting**: Scripts Bash/Shell
- **Pruebas**: Framework de pruebas unitarias personalizado con patrón AAA
- **Documentación**: Markdown con diagramas Mermaid
- **Control de Versiones**: Git

### Documentación Relacionada

- **[README.md](README.md)** - Guía completa de configuración y uso
- **[ADR.md](ADR.md)** - Registros de Decisiones de Arquitectura
- **[docs/ERD.md](docs/ERD.md)** - Diagrama de Entidad-Relación
- **[test/test_scripts.sh](test/test_scripts.sh)** - Documentación de suite de pruebas

### Instrucciones de Actualización

#### Desde Versiones Anteriores
Este es el lanzamiento inicial (1.0.0). No se requiere ruta de actualización.

#### Para Versiones Futuras
Al actualizar desde 1.0.0 a versiones futuras:

1. **Respalda tu base de datos** antes de actualizar
2. **Revisa el CHANGELOG** para cambios rupturantes
3. **Prueba scripts de migración** en entorno de desarrollo primero
4. **Actualiza variables de entorno** como se especifica en notas de lanzamiento
5. **Ejecuta suite de verificación** para asegurar compatibilidad

### Contribuyendo al CHANGELOG

Al contribuir a este proyecto:

1. **Agrega entradas** a la sección `[Sin Lanzar]`
2. **Sigue versionado semántico** para cambios rupturantes
3. **Usa categorías apropiadas** (Agregado, Cambiado, Deprecado, Removido, Corregido, Seguridad)
4. **Incluye fechas** en formato `YYYY-MM-DD`
5. **Proporciona descripciones claras** explicando el impacto de los cambios
6. **Referencia issues relacionados** o pull requests cuando aplique

### Por Qué Este CHANGELOG Importa

Este CHANGELOG sirve como documentación viva que:

- **Rastrea la evolución** de la plantilla de base de datos a través del tiempo
- **Comunica cambios rupturantes** a usuarios y desarrolladores
- **Proporciona guía de actualización** para lanzamientos futuros
- **Documenta decisiones arquitectónicas** y su racional
- **Habilita procesos de lanzamiento automatizados** con seguimiento estructurado de cambios
- **Soporta requisitos de cumplimiento** con trails de auditoría detallados