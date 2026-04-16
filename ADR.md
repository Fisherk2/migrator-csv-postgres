# Registro de Decisiones Arquitectónicas - Sistema de Datos

---
metadata:
  tipo_documento: Architecture Decision Record
  dominio: Ingeniería de Datos
  estado: Aprobado
  fecha_creacion: 2026-03-13
  fecha_actualizacion: 2026-03-13
  autor: fisherk2, Arquitecto de Base de Datos
  revisores: [Equipo de Desarrollo, Equipo de DevOps]
  stakeholders: [Desarrolladores, DBAs, Equipo de Producto]
  tags: [adr, arquitectura, datos, decision, documentación]
  version: 1.0
  relacionado_con: [[create_database.sql]], [[migrations]], [[seeds]]
---

## Introducción

Este documento registra las decisiones arquitectónicas clave tomadas durante el diseño e implementación del sistema de datos del proyecto. Cada decisión está documentada siguiendo el formato estándar ADR (Architecture Decision Record) para asegurar trazabilidad, consistencia y facilitar la toma de decisiones futuras.

**Propósito del documento:**
- Mantener un registro histórico de decisiones arquitectónicas
- Proporcionar contexto a nuevos miembros del equipo
- Facilitar la evaluación de decisiones existentes
- Evitar redescubrimiento de alternativas ya evaluadas

**Cómo usar este documento:**
1. Para nuevas decisiones: Copiar el formato ADR y completar cada sección
2. Para decisiones existentes: Revisar el contexto antes de proponer cambios
3. Para auditorías: Usar como referencia de decisiones pasadas

---

## Tabla de Contenidos
- [ADR-DAT-001: Selección de PostgreSQL como Base de Datos Principal](#adr-dat-001-selección-de-postgresql-como-base-de-datos-principal)
- [ADR-DAT-002: Convención de Nomenclatura Snake Case](#adr-dat-002-convención-de-nomenclatura-snake-case)
- [ADR-DAT-003: Estrategia de Soft Delete](#adr-dat-003-estrategia-de-soft-delete)
- [Historial de Cambios](#historial-de-cambios)

---

# ADR-DAT-001: Selección de PostgreSQL como Base de Datos Principal

## Estado y Contexto

**Estado:** Aprobado  
**Fecha:** 2026-03-13  
**Autor:** fisherk2

**Contexto del Problema:**
El proyecto requiere un sistema de gestión de datos que soporte transacciones ACID, relaciones complejas entre usuarios y proyectos, y escalabilidad para crecimiento futuro. Se necesita una base de datos relacional robusta con buen soporte para JSON, timestamps con zona horaria, y migraciones estructuradas.

**Requisitos:**
- Transacciones ACID completas
- Soporte para foreign keys y constraints complejas
- Migraciones estructuradas controladas
- Timestamps con zona horaria
- JSON para datos flexibles futuros
- Código abierto con comunidad activa

**Restricciones:**
- Presupuesto limitado (sin licencias comerciales)
- Expertise del equipo en SQL tradicional
- Requerimiento de deployment local y cloud

---

## Decisión Arquitectónica

**Decisión:** Se selecciona **PostgreSQL 15+** como sistema principal de almacenamiento transaccional para el proyecto.

**Justificación:**
PostgreSQL ofrece el mejor balance entre madurez, características enterprise y costo cero. Su soporte nativo para JSON, timestamps con zona horaria, y migraciones controladas lo hacen ideal para nuestro caso de uso.

**Componentes seleccionados:**
- PostgreSQL 15+ (motor principal)
- psql (cliente CLI)
- pgAdmin (herramienta de gestión)
- pg_dump/pg_restore (backup/restore)

---

## Alternativas Consideradas

| Alternativa | Costo | Madurez | Expertise Equipo | Veredicto | Razón de Rechazo |
|-------------|-------|---------|------------------|-----------|------------------|
| **PostgreSQL 15+** | Gratis | Alta | Alta | ✅ Seleccionada | Mejor balance general |
| MySQL 8.0 | Gratis | Alta | Media | ❌ Rechazada | JSON menos robusto |
| SQLite | Gratis | Media | Alta | ❌ Rechazada | No soporta concurrencia |
| SQL Server | $$ | Alta | Baja | ❌ Rechazada | Costo de licencias |

---

## Consecuencias y Trade-offs

### Beneficios
- **Costo cero:** Sin licencias ni restricciones
- **Características enterprise:** ACID completo, JSON avanzado
- **Comunidad activa:** Amplia documentación y soporte
- **Portabilidad:** Disponible en todas las plataformas

### Trade-offs
- **Complejidad operativa:** Requiere más configuración que NoSQL
- **Escalabilidad vertical:** Limitada a un solo servidor por instancia
- **Learning curve:** Más complejo que soluciones simples

---

# ADR-DAT-002: Convención de Nomenclatura Snake Case

## Estado y Contexto

**Estado:** Aprobado  
**Fecha:** 2026-03-13  
**Autor:** fisherk2

**Contexto del Problema:**
El equipo necesita una convención de nomenclatura consistente para tablas, columnas, y otros objetos de base de datos. Sin estándares claros, el código se vuelve difícil de mantener y leer. Se busca un balance entre legibilidad y consistencia.

**Requisitos:**
- Nombres legibles y descriptivos
- Consistencia entre base de datos y código
- Facilidad de escritura y lectura
- Compatibilidad con herramientas ORM

**Restricciones:**
- PostgreSQL es case-insensitive por defecto
- Herramientas de generación de código prefieren ciertos formatos
- Equipo familiarizado con diferentes convenciones

---

## Decisión Arquitectónica

**Decisión:** Se adopta **snake_case** como convención estándar para todos los objetos de base de datos.

**Reglas específicas:**
- Tablas en plural: `users`, `projects`
- Columnas en singular: `username`, `email`
- Primary keys siempre `id`
- Foreign keys formato `tabla_id`: `user_id`
- Timestamps con sufijo `_at`: `created_at`

**Justificación:**
Snake_case es legible, ampliamente soportado por PostgreSQL y herramientas ORM, y mantiene consistencia con convenciones de Python y Ruby.

---

## Alternativas Consideradas

| Alternativa | Legibilidad | Herramientas | Consistencia | Veredicto | Razón de Rechazo |
|-------------|-------------|--------------|--------------|-----------|------------------|
| **snake_case** | Alta | Excelente | Alta | ✅ Seleccionada | Balance óptimo |
| camelCase | Media | Media | Media | ❌ Rechazada | PostgreSQL case-insensitive |
| PascalCase | Baja | Baja | Baja | ❌ Rechazada | Difícil de leer |
| kebab-case | Media | Baja | Media | ❌ Rechazada | Requiere quotes |

---

## Consecuencias y Trade-offs

### Beneficios
- **Legibilidad:** Fácil de leer y entender
- **Consistencia:** Ampliamente soportado por herramientas
- **Estándar:** Usado por muchos frameworks populares

### Trade-offs
- **Verbosidad:** Nombres más largos que camelCase
- **Migración:** Requiere conversión desde otros formatos

---

# ADR-DAT-003: Estrategia de Soft Delete

## Estado y Contexto

**Estado:** Aprobado  
**Fecha:** 2026-03-13  
**Autor:** fisherk2

**Contexto del Problema:**
El sistema necesita manejar eliminación de usuarios y proyectos sin perder historial ni romper integridad referencial. DELETE físico elimina datos permanentemente y puede causar problemas de auditoría y recuperación.

**Requisitos:**
- Preservar historial de datos
- Permitir recuperación de eliminaciones accidentales
- Mantener integridad referencial
- Soportar auditoría y compliance

**Restricciones:**
- Las consultas deben filtrar registros eliminados
- El storage adicional debe ser mínimo
- El rendimiento no debe verse afectado significativamente

---

## Decisión Arquitectónica

**Decisión:** Se implementa **soft delete** mediante campo booleano `is_active` en todas las tablas principales.

**Implementación:**
- Campo `is_active BOOLEAN DEFAULT true`
- Índices parciales para rendimiento
- Queries automáticas con filtro `WHERE is_active = true`
- Procedimientos de cleanup manual para datos antiguos

**Justificación:**
Soft delete preserva datos para auditoría, permite recuperación accidental, y mantiene integridad referencial sin complejidad adicional.

---

## Alternativas Consideradas

| Alternativa | Storage | Complejidad | Rendimiento | Veredicto | Razón de Rechazo |
|-------------|---------|-------------|-------------|-----------|------------------|
| **Soft Delete** | Medio | Baja | Alto | ✅ Seleccionada | Balance óptimo |
| DELETE Físico | Mínimo | Mínima | Excelente | ❌ Rechazada | Pérdida de datos |
| Tabla de Auditoría | Alto | Alta | Medio | ❌ Rechazada | Complejidad alta |
| Archivo Histórico | Variable | Alta | Medio | ❌ Rechazada | Complejo de gestionar |

---

## Consecuencias y Trade-offs

### Beneficios
- **Recuperación:** Datos pueden ser restaurados
- **Auditoría:** Historial completo preservado
- **Integridad:** No rompe foreign keys

### Trade-offs
- **Storage:** Mayor uso de espacio en disco
- **Queries:** Requiere filtros adicionales
- **Complejidad:** Lógica de negocio más compleja

---

## Historial de Cambios

| Versión | Fecha | Cambios | Autor | Estado |
|---------|-------|---------|-------|---------|
| 1.0 | 2026-03-13 | Creación inicial con 3 ADRs | fisherk2 | Activo |

---

## Mantenimiento del Documento

**Propietario:** fisherk2  
**Frecuencia de revisión:** Trimestral  
**Proceso de cambios:**
1. Proponer nuevo ADR o modificación
2. Revisión por equipo técnico
3. Aprobación por arquitecto principal
4. Actualización del documento

---

> **Nota sobre importancia de ADRs:** Documentar decisiones arquitectónicas evita que el equipo "redescubra" soluciones, proporciona contexto para decisiones futuras, y facilita el onboarding de nuevos miembros. Un ADR bien mantenido es un activo estratégico para el equipo.