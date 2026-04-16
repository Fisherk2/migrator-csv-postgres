# 📋 Guía Detallada de Setup - Sistema de Datos PostgreSQL

---
**Documento:** Guía de Instalación y Configuración  
**Versión:** 1.0.0  
**Fecha:** 2026-03-13  
**Autor:** fisherk2  
**Relación:** Complemento detallado de [README.md](../README.md)  
**Tiempo estimado:** 5-10 minutos para desarrolladores familiarizados con PostgreSQL  
---

## 📖 Propósito del Documento

Esta guía proporciona instrucciones paso a paso para configurar el entorno de desarrollo del sistema de datos PostgreSQL. Mientras que el [README.md](../README.md) ofrece un resumen rápido, este documento incluye detalles de instalación, troubleshooting avanzado y mejores prácticas para asegurar una configuración exitosa.

---

## ⚡ Prerrequisitos Detallados

### Software Obligatorio

| Software | Versión Mínima | Verificación | Instalación |
|-----------|----------------|---------------|-------------|
| **PostgreSQL** | 15.0+ | `psql --version` | Ver sección instalación |
| **psql** | 15.0+ | `which psql` | Incluido con PostgreSQL |
| **Bash** | 4.0+ | `bash --version` | Preinstalado en Linux/macOS |
| **Git** | 2.30+ | `git --version` | `sudo apt install git` |

### Verificación de Prerrequisitos

```bash
# Verificar PostgreSQL
psql --version
# Salida esperada: psql (PostgreSQL) 15.x

# Verificar cliente psql
which psql
# Salida esperada: /usr/bin/psql

# Verificar Bash
bash --version
# Salida esperada: GNU bash, version 4.x.x

# Verificar Git
git --version
# Salida esperada: git version 2.x.x
```

> ⚠️ **Importante:** Si alguno de estos comandos no funciona, instala el software faltante antes de continuar.

---

## 🛠️ Instalación de PostgreSQL

### Linux (Ubuntu/Debian)

```bash
# Actualizar paquetes
sudo apt update

# Instalar PostgreSQL 15
sudo apt install postgresql-15 postgresql-contrib-15

# Iniciar servicio
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verificar estado
sudo systemctl status postgresql
# Salida esperada: Active: active (exited)
```

### macOS

```bash
# Usar Homebrew
brew install postgresql@15

# Iniciar servicio
brew services start postgresql@15

# Verificar estado
brew services list
# Salida esperada: postgresql@15 started
```

### Windows

1. Descargar desde https://www.postgresql.org/download/windows/
2. Ejecutar instalador
3. Anotar contraseña del usuario `postgres`
4. Marcar "Install Stack Builder" (opcional)

---

## 🔧 Configuración del Entorno

### 1. Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp connection_example.env .env

# Editar archivo de configuración
nano .env
```

> ⚠️ **Seguridad:** Nunca commitees el archivo `.env` al repositorio. Ya está incluido en `.gitignore`.

### 2. Configuración de PostgreSQL

```bash
# Cambiar al usuario postgres
sudo -u postgres psql

# Crear usuario de desarrollo (reemplaza 'tu_usuario')
CREATE USER tu_usuario WITH PASSWORD 'tu_password';

# Crear base de datos
CREATE DATABASE your_database_name OWNER tu_usuario;

# Conceder permisos
GRANT ALL PRIVILEGES ON DATABASE your_database_name TO tu_usuario;

# Salir de psql
\q
```

### 3. Verificar Conexión

```bash
# Probar conexión
psql -U tu_usuario -d your_database_name -h localhost

# Deberías ver:
# your_database_name=#
```

---

## 🚀 Ejecución Paso a Paso

### Paso 1: Clonar el Proyecto

```bash
git clone https://github.com/Fisherk2/plantilla-proyecto-sistema-datos
cd plantilla-proyecto-sistema-datos
```

**Salida esperada:**
```
Cloning into 'plantilla-proyecto-sistema-datos'...
remote: Enumerating objects: 50, done.
remote: Counting objects: 100% (50/50), done.
remote: Compressing objects: 100% (30/30), done.
```

### Paso 2: Configurar Variables de Entorno

```bash
# Copiar y editar configuración
cp connection_example.env .env
nano .env
```

**Configuración típica en `.env`:**
```bash
# PostgreSQL Connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=tu_usuario
DB_PASSWORD=tu_password

# Pool Settings
DB_POOL_MIN=5
DB_POOL_MAX=20
```

### Paso 3: Crear Base de Datos

```bash
# Crear base de datos (idempotente)
psql -U postgres -d postgres -f create_database.sql
```

**Salida esperada:**
```
CREATE DATABASE
Base de datos 'your_database_name' creada exitosamente.
```

### Paso 4: Ejecutar Migraciones

```bash
# Crear tabla de usuarios
psql -U tu_usuario -d your_database_name -f migrations/001_create_users_table.sql

# Crear tabla de proyectos
psql -U tu_usuario -d your_database_name -f migrations/002_create_projects_table.sql
```

**Salida esperada:**
```
CREATE TABLE
CREATE TRIGGER
Tabla 'users' creada exitosamente.
CREATE TABLE
CREATE TRIGGER
Tabla 'projects' creada exitosamente.
```

### Paso 5: Poblar Datos de Prueba

```bash
# Insertar usuarios
psql -U tu_usuario -d your_database_name -f seeds/001_seed_users.sql

# Insertar proyectos
psql -U tu_usuario -d your_database_name -f seeds/002_seed_projects.sql
```

**Salida esperada:**
```
INSERT 0 5
Usuarios seed insertados exitosamente.
INSERT 0 10
Proyectos seed insertados exitosamente.
```

### Paso 6: Validar Configuración

```bash
# Dar permisos de ejecución
chmod +x verify_setup.sh

# Ejecutar validación completa
./verify_setup.sh
```

**Salida esperada:**
```
🔍 Verificando conexión a PostgreSQL...
✅ Conexión exitosa a PostgreSQL

🗄️ Verificando base de datos...
✅ Base de datos 'your_database_name' existe

📋 Verificando tablas...
✅ Tabla 'users' existe
✅ Tabla 'projects' existe

📊 Verificando datos seed...
✅ Datos seed de usuarios: 5 registros
✅ Datos seed de proyectos: 10 registros

🎉 ¡Todas las validaciones pasaron exitosamente!
✅ La base de datos está lista para uso
```

---

## ✅ Validación del Setup

### Verificación Manual

```bash
# Conectar a la base de datos
psql -U tu_usuario -d your_database_name

# Verificar tablas
\dt
# Salida esperada:
#          List of relations
#  Schema |  Name   | Type  | Owner
# --------+---------+-------+----------
#  public | users   | table | tu_usuario
#  public | projects| table | tu_usuario

# Verificar datos
SELECT COUNT(*) FROM users;
# Salida esperada: 5

SELECT COUNT(*) FROM projects;
# Salida esperada: 10

# Salir
\q
```

### Verificación con Script

```bash
# Ejecutar script de validación
./verify_setup.sh

# Deberías ver el mensaje de éxito
echo $?
# Salida esperada: 0
```

---

## 🔧 Troubleshooting Avanzado

### Error 1: "FATAL: database does not exist"

**Causa:** La base de datos no ha sido creada  
**Solución:**
```bash
# Verificar bases de datos existentes
psql -U postgres -l

# Crear base de datos manualmente
createdb -U postgres your_database_name

# O usar el script
psql -U postgres -d postgres -f create_database.sql
```

### Error 2: "FATAL: password authentication failed for user"

**Causa:** Contraseña incorrecta o usuario no existe  
**Solución:**
```bash
# Conectar como postgres
sudo -u postgres psql

# Verificar usuarios
\du

# Crear o resetear usuario
CREATE USER tu_usuario WITH PASSWORD 'nueva_contraseña';
GRANT ALL PRIVILEGES ON DATABASE your_database_name TO tu_usuario;
```

### Error 3: "permission denied for relation"

**Causa:** El usuario no tiene permisos en la tabla  
**Solución:**
```bash
# Conectar como superusuario
psql -U postgres -d your_database_name

# Dar permisos
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO tu_usuario;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO tu_usuario;
```

### Error 4: "connection refused"

**Causa:** PostgreSQL no está corriendo o puerto incorrecto  
**Solución:**
```bash
# Verificar si PostgreSQL está corriendo
sudo systemctl status postgresql

# Iniciar PostgreSQL
sudo systemctl start postgresql

# Verificar puerto
netstat -an | grep 5432
# Salida esperada: tcp 0 0 127.0.0.1:5432
```

### Error 5: "role 'postgres' does not exist"

**Causa:** Configuración incorrecta de usuario  
**Solución:**
```bash
# Crear usuario postgres
sudo -u postgres createuser -s postgres

# O usar tu usuario actual
whoami
# Y poner ese valor en DB_USER en .env
```

### Error 6: "syntax error at or near"

**Causa:** Error de sintaxis en SQL  
**Solución:**
```bash
# Verificar sintaxis del script
psql -U postgres -d your_database_name -f migrations/001_create_users_table.sql

# Revisar línea específica del error
# Comúnmente es por falta de punto y coma o comillas
```

### Error 7: "database is being accessed by other users"

**Causa:** Hay conexiones activas al eliminar/modificar  
**Solución:**
```bash
# Terminar conexiones activas
psql -U postgres -d postgres -c "
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'your_database_name'
  AND pid <> pg_backend_pid();
"
```

### Error 8: "could not connect to server"

**Causa:** Problemas de red o configuración de host  
**Solución:**
```bash
# Verificar configuración de PostgreSQL
sudo nano /etc/postgresql/15/main/postgresql.conf

# Buscar y modificar:
# listen_addresses = 'localhost'

# Reiniciar PostgreSQL
sudo systemctl restart postgresql
```

### Error 9: "FATAL: sorry, too many clients already"

**Causa:** Límite de conexiones alcanzado  
**Solución:**
```bash
# Verificar conexiones activas
psql -U postgres -d postgres -c "
SELECT count(*) FROM pg_stat_activity;
"

# Aumentar límite en postgresql.conf
# max_connections = 100
```

### Error 10: "ERROR: relation already exists"

**Causa:** Migración ejecutada múltiples veces  
**Solución:**
```bash
# Limpiar tablas (solo desarrollo)
psql -U postgres -d your_database_name -c "
DROP TABLE IF EXISTS projects, users CASCADE;
"

# O usar scripts idempotentes (recomendado)
# Los scripts ya incluyen IF NOT EXISTS
```

---

## 💡 Mejores Prácticas

### Desarrollo en Equipo

1. **Versiones consistentes:** Asegúrate que todo el equipo use PostgreSQL 15+
2. **Variables de entorno:** Nunca commitear `.env` al repositorio
3. **Scripts idempotentes:** Los scripts pueden ejecutarse múltiples veces
4. **Validación automática:** Siempre ejecutar `verify_setup.sh` después de cambios

### Seguridad

```bash
# Usar conexiones SSL
psql "host=localhost dbname=your_database_name user=tu_usuario sslmode=require"

# Limitar permisos de usuario
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO tu_usuario;
```

### Performance

```bash
# Verificar índices
psql -U tu_usuario -d your_database_name -c "\di"

# Analizar consultas lentas
psql -U tu_usuario -d your_database_name -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"
```

### Backup y Recovery

```bash
# Crear backup
pg_dump -U tu_usuario your_database_name > backup.sql

# Restaurar backup
psql -U tu_usuario your_database_name < backup.sql

# Backup comprimido
pg_dump -U tu_usuario your_database_name | gzip > backup.sql.gz
```

---

## 🎯 Próximos Pasos

### Inmediato (Después del Setup)

1. **Explorar el modelo de datos:**
   ```bash
   psql -U tu_usuario -d your_database_name
   \d users
   \d projects
   ```

2. **Revisar documentación:**
   - [ERD.md](ERD.md) - Diagrama Entidad-Relación
   - [ADR.md](../ADR.md) - Decisiones arquitectónicas
   - [naming_conventions.md](../naming_conventions.md) - Convenciones

3. **Probar queries básicos:**
   ```sql
   -- Ver usuarios activos
   SELECT username, email FROM users WHERE is_active = true;
   
   -- Ver proyectos por usuario
   SELECT p.name, p.status FROM projects p 
   JOIN users u ON p.user_id = u.id 
   WHERE u.username = 'admin';
   ```

### Desarrollo Continuo

1. **Agregar nuevas migraciones:** Crear archivos `003_*.sql`, `004_*.sql`, etc.
2. **Extender datos seed:** Agregar nuevos archivos seed según necesidad
3. **Actualizar documentación:** Mantener ERD y ADRs sincronizados
4. **Validar cambios:** Siempre ejecutar `verify_setup.sh` después de modificaciones

### Producción

1. **Configurar backups automáticos:** Usar pg_cron o scripts cron
2. **Monitor performance:** Configurar pg_stat_statements
3. **Security hardening:** Configurar SSL, limitar accesos
4. **Documentation:** Mantener actualizada para el equipo de operaciones

---

## 📚 Recursos Adicionales

- **Documentación oficial PostgreSQL:** https://www.postgresql.org/docs/15/
- **psql cheat sheet:** https://postgrescheatsheet.com/
- **Best practices:** https://wiki.postgresql.org/wiki/Performance_Optimization

---

> 💡 **Nota para Mantenedores:** Esta guía debe mantenerse sincronizada con los cambios en el proyecto. Cada nuevo script o modificación estructural debe reflejarse aquí para asegurar que el setup siga siendo reproducible.

---

**🚀 ¡Setup completado!** Ahora puedes comenzar a desarrollar con tu base de datos PostgreSQL configurada y validada.