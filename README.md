# Plantilla de Proyecto - Sistema de Datos PostgreSQL

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)
![Shell](https://img.shields.io/badge/Shell-Bash-4EAA25.svg)

> 🚀 **Template completo para proyectos de base de datos PostgreSQL** con migraciones, seeds, documentación y validación automatizada.

---

## 📋 Tabla de Contenidos

- [Descripción del Proyecto](#descripción-del-proyecto)
- [Requisitos Previos](#requisitos-previos)
- [Inicio Rápido (Quick Start)](#inicio-rápido-quick-start)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Comandos Disponibles](#comandos-disponibles)
- [Documentación Relacionada](#documentación-relacionada)
- [Solución de Problemas](#solución-de-problemas)
- [Contribución](#contribución)
- [Licencia](#licencia)

---

## 📖 Descripción del Proyecto

Este template proporciona una estructura completa y replicable para proyectos de base de datos PostgreSQL, incluyendo:

### 🎯 Propósito Principal
- **Estandarización:** Base consistente para todos los proyectos de datos del equipo
- **Productividad:** Setup automático y validación de infraestructura
- **Documentación:** Completa con ERD, ADRs y convenciones
- **Onboarding:** Nuevo desarrollador productivo en <10 minutos

### 💡 Problemas que Resuelve
- ❌ **Inconsistencia:** Cada proyecto usa diferente estructura y nomenclatura
- ❌ **Configuración manual:** Setup repetitivo y propenso a errores
- ❌ **Documentación dispersa:** Falta de documentación centralizada
- ❌ **Validación manual:** Sin automatización para verificar configuración

### ✅ Beneficios para el Equipo
- 🚀 **Rapidez:** Setup completo en minutos, no horas
- 📚 **Conocimiento:** Documentación completa y accesible
- 🔧 **Consistencia:** Mismas convenciones en todos los proyectos
- 🛡️ **Calidad:** Validación automática de configuración

---

## ⚡ Requisitos Previos

### Software Obligatorio
- **PostgreSQL 15+** - Motor de base de datos principal
- **psql** - Cliente CLI para PostgreSQL (incluido con PostgreSQL)
- **Bash 4+** - Para ejecutar scripts de automatización
- **Git** - Control de versiones

### Software Recomendado
- **pgAdmin** - Interfaz gráfica para PostgreSQL
- **DBeaver** - Cliente SQL multiplataforma
- **Docker** - Para entornos de desarrollo aislados
- **VS Code** - Editor de código con extensiones SQL

### Verificación de Requisitos
```bash
# Verificar PostgreSQL
psql --version

# Verificar Bash
bash --version

# Verificar Git
git --version
```

---

## 🚀 Inicio Rápido (Quick Start)

> ⏱️ **Tiempo estimado:** 5-10 minutos para desarrolladores familiarizados con PostgreSQL

### Paso 1: Clonar el Proyecto
```bash
git clone https://github.com/Fisherk2/plantilla-proyecto-sistema-datos
cd plantilla-proyecto-sistema-datos
```

### Paso 2: Configurar Variables de Entorno
```bash
# Copiar archivo de ejemplo
cp connection_example.env .env

# Editar con tus credenciales
nano .env
```

### Paso 3: Crear Base de Datos
```bash
# Crear base de datos (idempotente)
psql -U postgres -d postgres -f create_database.sql
```

### Paso 4: Ejecutar Migraciones
```bash
# Crear tablas en orden correcto
psql -U postgres -d your_database_name -f migrations/001_create_users_table.sql
psql -U postgres -d your_database_name -f migrations/002_create_projects_table.sql
```

### Paso 5: Poblar Datos de Prueba
```bash
# Insertar datos seed
psql -U postgres -d your_database_name -f seeds/001_seed_users.sql
psql -U postgres -d your_database_name -f seeds/002_seed_projects.sql
```

### Paso 6: Validar Configuración
```bash
# Dar permisos de ejecución
chmod +x verify_setup.sh

# Ejecutar validación completa
./verify_setup.sh
```

### ✅ Verificación Final
Si todo está correcto, deberías ver:
```
🎉 ¡Todas las validaciones pasaron exitosamente!
✅ La base de datos está lista para uso
```

---

## 📁 Estructura del Proyecto

```
03-plantilla-proyecto-sistema-datos/
├── 📄 README.md                    # Documentación principal (este archivo)
├── 📄 .gitignore                   # Archivos ignorados por Git
├── 📄 connection_example.env         # Template de configuración
├── 📄 .env                        # Variables de entorno (crear desde ejemplo)
├── 📄 create_database.sql           # Script de creación de BD (idempotente)
├── 📄 drop_database.sql             # Script de eliminación segura de BD
├── 📄 verify_setup.sh               # Validación completa del setup
├── 📄 ADR.md                      # Decisiones arquitectónicas
├── 📄 naming_conventions.md         # Convenciones de nomenclatura
├── 📁 migrations/                   # Scripts de migración de estructura
│   ├── 📄 001_create_users_table.sql
│   └── 📄 002_create_projects_table.sql
├── 📁 seeds/                       # Datos de prueba
│   ├── 📄 001_seed_users.sql
│   └── 📄 002_seed_projects.sql
└── 📁 docs/                        # Documentación técnica
    └── 📄 ERD.md                    # Diagrama Entidad-Relación
```

### Descripción de Directorios
- **`migrations/`** - Scripts DDL para crear/modificar estructura de tablas
- **`seeds/`** - Datos de prueba para desarrollo y testing
- **`docs/`** - Documentación técnica (ERD, diagramas, etc.)
- **Raíz** - Scripts de configuración y automatización

---

## 🔧 Comandos Disponibles

### Scripts de Base de Datos
```bash
# Crear base de datos (idempotente)
psql -U postgres -d postgres -f create_database.sql

# Eliminar base de datos (con salvaguardas)
psql -U postgres -d postgres -f drop_database.sql

# Validar setup completo
./verify_setup.sh
```

### Migraciones (ejecutar en orden)
```bash
# Crear tabla de usuarios
psql -U postgres -d your_database_name -f migrations/001_create_users_table.sql

# Crear tabla de proyectos
psql -U postgres -d your_database_name -f migrations/002_create_projects_table.sql
```

### Datos de Prueba
```bash
# Poblar usuarios de prueba
psql -U postgres -d your_database_name -f seeds/001_seed_users.sql

# Poblar proyectos de prueba
psql -U postgres -d your_database_name -f seeds/002_seed_projects.sql
```

### Utilidades Adicionales
```bash
# Verificar estado de PostgreSQL
systemctl status postgresql

# Conectar a base de datos
psql -U postgres -d your_database_name

# Listar bases de datos
psql -U postgres -l
```

---

## 📚 Documentación Relacionada

### 📋 Decisiones Arquitectónicas
- **[ADR.md](ADR.md)** - Registro completo de decisiones arquitectónicas
  - Selección de PostgreSQL vs alternativas
  - Convenciones de nomenclatura
  - Estrategia de soft delete

### 🗺️ Modelo de Datos
- **[docs/ERD.md](docs/ERD.md)** - Diagrama Entidad-Relación completo
  - Visualización de tablas y relaciones
  - Diccionario de datos completo
  - Decisiones de diseño justificadas

### 📝 Convenciones
- **[naming_conventions.md](naming_conventions.md)** - Estándares de nomenclatura
  - Reglas para tablas, columnas, índices
  - Ejemplos de buenas y malas prácticas
  - Checklist de validación

---

## 🔧 Solución de Problemas

### ❓ FAQ - Preguntas Frecuentes

#### 1. Error: "FATAL: database does not exist"
**Causa:** La base de datos no ha sido creada  
**Solución:** Ejecuta primero `create_database.sql`
```bash
psql -U postgres -d postgres -f create_database.sql
```

#### 2. Error: "permission denied for relation users"
**Causa:** El usuario no tiene permisos en la base de datos  
**Solución:** Conéctate como superusuario o da permisos adecuados
```bash
# Como superusuario
psql -U postgres -d your_database_name

# O da permisos
GRANT ALL PRIVILEGES ON DATABASE your_database_name TO your_user;
```

#### 3. Error: "relation already exists"
**Causa:** Migración ejecutada múltiples veces sin idempotencia  
**Solución:** Los scripts son idempotentes, pero si fallan, limpia manualmente
```bash
# Eliminar tablas (cuidado con producción)
DROP TABLE IF EXISTS projects, users CASCADE;
```

#### 4. Error: "connection refused"
**Causa:** PostgreSQL no está corriendo o puerto incorrecto  
**Solución:** Verifica estado y configuración
```bash
# Verificar si PostgreSQL está corriendo
systemctl status postgresql

# Iniciar PostgreSQL
sudo systemctl start postgresql

# Verificar puerto
netstat -an | grep 5432
```

#### 5. Error: "FATAL: role "postgres" does not exist"
**Causa:** Configuración de usuario incorrecta en `.env`  
**Solución:** Crea el usuario o usa el usuario correcto
```bash
# Crear usuario postgres (si no existe)
sudo -u postgres createuser -s postgres

# O usa tu usuario actual
whoami  # y pon ese valor en DB_USER
```

### 🆘 Obtener Ayuda Adicional
- **Logs de PostgreSQL:** `/var/log/postgresql/`
- **Documentación oficial:** https://www.postgresql.org/docs/
- **Issues del proyecto:** Crear issue en el repositorio

---

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Por favor lee nuestra [guía de contribución](CONTRIBUTING.MD) para detalles sobre:

- Cómo reportar problemas y sugerir mejoras
- Flujo de trabajo para Pull Requests
- Estándares de código y convenciones
- Template para reporte de issues

### 📋 Checklist Rápido
- [ ] Lee la [guía completa](CONTRIBUTING.MD)
- [ ] Sigue las convenciones de [nomenclatura](naming_conventions.md)
- [ ] Ejecuta `./verify_setup.sh` antes de submit
- [ ] Actualiza documentación si aplica

---

## 📄 Licencia

Este proyecto está licenciado bajo **MIT License** - puedes ver el archivo [LICENSE](LICENSE) para detalles completos.

### 📋 Resumen de Licencia
- ✅ **Uso comercial:** Permitido
- ✅ **Modificación:** Permitida
- ✅ **Distribución:** Permitida
- ✅ **Uso privado:** Permitido
- ❌ **Responsabilidad:** Sin garantía
- ℹ️ **Atribución:** Requerida (mantener copyright)

---

## 🌟 Agradecimientos

Este template fue creado siguiendo principios de:
- **Clean Architecture** - Robert C. Martin
- **Clean Code** - Robert C. Martin  
- **Systems Analysis and Design** - Kendall & Kendall

---

> 💡 **Nota para Mantenedores:** Este README debe mantenerse sincronizado con los cambios en el proyecto. Cada nuevo script o modificación estructural debe reflejarse aquí para asegurar que el onboarding siga siendo efectivo.

---

**🚀 ¿Listo para comenzar?** Sigue el [Inicio Rápido](#inicio-rápido-quick-start) y tendrás tu base de datos funcionando en minutos!