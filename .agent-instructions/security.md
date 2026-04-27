# Security Guidelines

## 🔒 Principios de Seguridad

### Confidencialidad de Datos
- **Nunca exponer credenciales** en logs, mensajes de error o código
- **Usar variables de entorno** para información sensible
- **Validar todos los inputs** antes de procesar
- **Sanitizar datos** antes de incluir en reportes

### Integridad de Datos
- **Transacciones atómicas** para operaciones de base de datos
- **Validación estricta** de formatos y tipos
- **Rollback automático** ante errores críticos
- **Auditoría completa** de operaciones realizadas

### Disponibilidad del Sistema
- **Manejo robusto de errores** sin exponer detalles internos
- **Recursos limitados** para prevenir agotamiento
- **Timeouts apropiados** para operaciones externas
- **Logging estructurado** para monitoreo y alertas

## 🚫 Prohibiciones de Seguridad

### NO Exponer Información Sensible

#### Credenciales y Configuración
```python
# ❌ MAL - Hardcodear credenciales
DB_PASSWORD = "admin123"
API_KEY = "sk-1234567890"

# ✅ BIEN - Usar variables de entorno
DB_PASSWORD = os.getenv("DB_PASSWORD")
API_KEY = os.getenv("API_KEY")
```

#### Mensajes de Error
```python
# ❌ MAL - Exponer detalles internos
except Exception as e:
    return f"Error en conexión a {db_host}: {str(e)}"

# ✅ BIEN - Mensaje genérico con logging interno
except Exception as e:
    logger.error(f"Database connection failed to {db_host}: {str(e)}")
    return "Error de conexión a la base de datos"
```

#### Paths del Sistema
```python
# ❌ MAL - Paths absolutos expuestos
CONFIG_PATH = "/etc/migrator/config.yaml"

# ✅ BIEN - Paths relativos validados
CONFIG_PATH = os.path.join(os.getcwd(), "config.yaml")
```

### NO Usar Funciones Inseguras

#### SQL Injection
```python
# ❌ MAL - Concatenación directa
query = f"SELECT * FROM users WHERE email = '{user_email}'"

# ✅ BIEN - Queries parametrizadas
query = "SELECT * FROM users WHERE email = %s"
cursor.execute(query, (user_email,))
```

#### Path Traversal
```python
# ❌ MAL - Sin validación de path
def read_csv_file(filename):
    return open(filename)  # Peligroso: ../../../etc/passwd

# ✅ BIEN - Validación de path
def read_csv_file(filename):
    safe_filename = os.path.basename(filename)
    full_path = os.path.join("data/", safe_filename)
    if not full_path.startswith("data/"):
        raise SecurityError("Invalid path")
    return open(full_path)
```

#### Code Injection
```python
# ❌ MAL - Eval dinámico
validation_rule = f"lambda x: {rule_expression}"
result = eval(validation_rule(user_input))

# ✅ BIEN - Validación segura
allowed_rules = {
    "email": lambda x: "@" in x and "." in x.split("@")[1],
    "phone": lambda x: x.replace("-", "").isdigit()
}
result = allowed_rules[rule_type](user_input)
```

## 🛡️ Validación de Inputs

### Validación de CSV
```python
def validate_csv_structure(csv_content: str) -> bool:
    """Valida estructura básica del CSV."""
    try:
        # Limitar tamaño del archivo
        if len(csv_content) > MAX_CSV_SIZE:
            raise SecurityError("CSV file too large")
        
        # Validar formato CSV
        csv.reader(StringIO(csv_content))
        return True
    except Exception as e:
        logger.error(f"CSV validation failed: {e}")
        return False
```

### Validación de Configuración YAML
```python
def validate_config_schema(config: Dict[str, Any]) -> bool:
    """Valida esquema de configuración YAML."""
    required_fields = ["source", "target", "validation"]
    
    for field in required_fields:
        if field not in config:
            raise ConfigurationError(f"Missing required field: {field}")
    
    # Validar tipos de datos
    if not isinstance(config["source"], dict):
        raise ConfigurationError("source must be a dictionary")
    
    return True
```

### Validación de Nombres de Tablas
```python
def validate_table_name(table_name: str) -> bool:
    """Valida nombres de tablas contra SQL injection."""
    # Solo permitir caracteres alfanuméricos y guiones bajos
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    
    if not re.match(pattern, table_name):
        raise SecurityError(f"Invalid table name: {table_name}")
    
    # Lista blanca de tablas permitidas
    allowed_tables = ["customers", "products", "orders"]
    if table_name not in allowed_tables:
        raise SecurityError(f"Table not allowed: {table_name}")
    
    return True
```

## 🔐 Manejo de Secretos

### Variables de Entorno
```python
class SecureConfig:
    """Manejo seguro de configuración."""
    
    def __init__(self):
        self.db_host = self._get_required_env("DB_HOST")
        self.db_port = self._get_required_env("DB_PORT")
        self.db_user = self._get_required_env("DB_USER")
        self.db_password = self._get_required_env("DB_PASSWORD")
        self.db_name = self._get_required_env("DB_NAME")
    
    def _get_required_env(self, key: str) -> str:
        """Obtiene variable de entorno requerida."""
        value = os.getenv(key)
        if not value:
            raise ConfigurationError(f"Required environment variable: {key}")
        return value
    
    def get_connection_string(self) -> str:
        """Genera string de conexión sin exponer credenciales."""
        return f"postgresql://{self.db_user}:***@{self.db_host}:{self.db_port}/{self.db_name}"
```

### Archivos de Configuración Seguros
```yaml
# .env.example - Template para desarrollo
DB_HOST=localhost
DB_PORT=5432
DB_USER=migrator_user
DB_PASSWORD=your_password_here
DB_NAME=migrator_db

# Archivos .env NUNCA se commitean
# .env.gitignore
.env
*.key
*.pem
secrets/
```

## 📝 Logging Seguro

### Estructura de Logs
```python
def setup_secure_logging():
    """Configura logging seguro sin información sensible."""
    
    # Formato sin datos sensibles
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para archivo
    file_handler = logging.FileHandler('migrator.log')
    file_handler.setFormatter(formatter)
    
    # Handler para consola (sin detalles en producción)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger('migrator')
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
```

### Mensajes de Error Seguros
```python
class SecureErrorHandler:
    """Manejo seguro de errores."""
    
    @staticmethod
    def handle_database_error(error: Exception) -> str:
        """Maneja errores de base de datos de forma segura."""
        error_id = str(uuid.uuid4())[:8]
        
        # Log completo para debugging (interno)
        logger.error(f"[{error_id}] Database error: {type(error).__name__}: {str(error)}")
        
        # Mensaje genérico para usuario
        return f"Error de base de datos (ID: {error_id}). Contacte al administrador."
    
    @staticmethod
    def handle_validation_error(field: str, value: str, reason: str) -> str:
        """Maneja errores de validación sin exponer datos."""
        # No loggear el valor completo, solo longitud y tipo
        logger.warning(f"Validation failed for field '{field}': {reason}")
        
        return f"Error de validación en campo '{field}': {reason}"
```

## 🔍 Auditoría y Monitoreo

### Logs de Auditoría
```python
class AuditLogger:
    """Logging especializado para auditoría."""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
        
    def log_migration_start(self, csv_file: str, target_table: str):
        """Registra inicio de migración."""
        self.logger.info(f"MIGRATION_START: file={csv_file}, table={target_table}")
    
    def log_migration_complete(self, csv_file: str, imported: int, rejected: int):
        """Registra finalización de migración."""
        self.logger.info(f"MIGRATION_COMPLETE: file={csv_file}, imported={imported}, rejected={rejected}")
    
    def log_security_event(self, event_type: str, details: str):
        """Registra eventos de seguridad."""
        self.logger.warning(f"SECURITY_EVENT: type={event_type}, details={details}")
```

### Métricas de Seguridad
```python
class SecurityMetrics:
    """Métricas de seguridad para monitoreo."""
    
    def __init__(self):
        self.failed_logins = 0
        self.validation_errors = 0
        self.suspicious_files = 0
    
    def record_failed_login(self, username: str):
        """Registra intento de login fallido."""
        self.failed_logins += 1
        logger.warning(f"SECURITY: Failed login attempt for user: {username}")
    
    def record_validation_error(self, field: str, pattern: str):
        """Registra error de validación sospechoso."""
        self.validation_errors += 1
        if self.validation_errors > MAX_VALIDATION_ERRORS:
            logger.error("SECURITY: Too many validation errors - possible attack")
```

## 🚀 Checklist de Seguridad

### Antes de Deploy
- [ ] Variables de entorno configuradas correctamente
- [ ] Archivos .env en .gitignore
- [ ] Validación de inputs implementada
- [ ] Queries parametrizadas en todo el código
- [ ] Logging seguro configurado
- [ ] Auditoría habilitada

### Durante Desarrollo
- [ ] Nunca commitear credenciales
- [ ] Validar todos los inputs externos
- [ ] Usar conexiones seguras (SSL/TLS)
- [ ] Implementar timeouts para operaciones externas
- [ ] Revisar logs por información sensible

### En Producción
- [ ] Monitorear logs de seguridad
- [ ] Rotar credenciales regularmente
- [ ] Revisar accesos y permisos
- [ ] Actualizar dependencias
- [ ] Realizar auditorías periódicas

## 📚 Referencias de Seguridad

- **OWASP Python Security**: https://owasp.org/www-project-cheat-sheets/cheatsheets/Python_Security_Cheat_Sheet.html
- **PostgreSQL Security**: https://www.postgresql.org/docs/current/security.html
- **Python Logging Best Practices**: https://docs.python.org/3/howto/logging.html
- **Secure Coding Guidelines**: NIST SP 800-64
