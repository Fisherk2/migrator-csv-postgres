#!/usr/bin/env python3
"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO:      Inicializador de Base de Datos
AUTOR:       Fisherk2
FECHA:       2026-04-17
DESCRIPCIÓN: Orquesta la aplicación secuencial de scripts SQL 
para configurar la base de datos del migrador 
usando el patrón dual-connection.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import psycopg2
from psycopg2 import DatabaseError, OperationalError
from psycopg2.extensions import connection


# ■■■■■■■■■■■■■ Configuración de logging estructurado ■■■■■■■■■■■■■
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Configuración de conexión a base de datos desde .env o CLI."""
    
    def __init__(self, env_file: Optional[str] = None) -> None:
        self.host: str = os.getenv('DB_HOST', 'localhost')
        self.port: int = int(os.getenv('DB_PORT', '5432'))
        self.db_name: str = os.getenv('DB_NAME', 'migrator_ecommerce')
        self.user: str = os.getenv('DB_USER', 'migrator_user')
        self.password: str = os.getenv('DB_PASSWORD', '')
        
        # ■■■■■■■■■■■■■ Validación de credenciales obligatorias ■■■■■■■■■■■■■
        if not self.user or not self.password:
            raise ValueError("DB_USER y DB_PASSWORD son obligatorios")
    
    def get_connection_string(self, dbname: str) -> str:
        """Genera string de conexión sin exponer credenciales en logs."""
        return (
            f"host={self.host} port={self.port} dbname={dbname} "
            f"user={self.user} password={self.password}"
        )


class DatabaseInitializer:
    """Orquestador de inicialización de base de datos con dual-connection."""
    
    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self.sql_scripts_dir = Path(__file__).parent / "sql"
        self.scripts = [
            "01_create_database.sql",
            "02_create_schema.sql", 
            "03_create_indexes.sql",
            "04_seed_sample_data.sql"
        ]
    
    def _execute_sql_file(
        self, 
        conn: connection, 
        script_name: str,
        description: str
    ) -> bool:
        """
        Ejecuta un archivo SQL dentro de una transacción explícita.
        
        Returns:
            True si éxito, False si fallo
        """
        script_path = self.sql_scripts_dir / script_name
        if not script_path.exists():
            logger.error(f"Script no encontrado: {script_path}")
            return False
        
        try:
            with conn.cursor() as cursor:
                
                # ■■■■■■■■■■■■■ Iniciar transacción explícita ■■■■■■■■■■■■■
                conn.autocommit = False
                
                logger.info(f"Ejecutando {description} desde {script_name}")
                
                # ■■■■■■■■■■■■■ Leer y ejecutar script SQL ■■■■■■■■■■■■■
                with open(script_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                cursor.execute(sql_content)
                
                # ■■■■■■■■■■■■■ Confirmar transacción ■■■■■■■■■■■■■
                conn.commit()
                logger.info(f"Completado: {description}")
                return True
                
        except DatabaseError as e:
            # ■■■■■■■■■■■■■ Rollback en error ■■■■■■■■■■■■■
            conn.rollback()
            logger.error(f"Error en {description}: {e}")
            return False
        except Exception as e:
            conn.rollback()
            logger.error(f"Error inesperado en {description}: {e}")
            return False
        finally:
            # ■■■■■■■■■■■■■ Restaurar autocommit ■■■■■■■■■■■■■
            conn.autocommit = True
    
    def _create_connection(self, dbname: str) -> connection:
        """Crea conexión a base de datos con manejo de errores."""
        try:
            conn_string = self.config.get_connection_string(dbname)
            logger.info(f"Conectando a PostgreSQL en {self.config.host}:{self.config.port}/{dbname}")
            return psycopg2.connect(conn_string)
        except OperationalError as e:
            logger.error(f"No se puede conectar a {dbname}: {e}")
            raise
    
    def initialize_database(self) -> bool:
        """
        Orquesta la inicialización completa usando dual-connection pattern.
        
        Returns:
            True si todos los scripts se ejecutaron correctamente
        """
        conn_maintenance = None
        conn_target = None
        
        try:
            # ■■■■■■■■■■■■■ PASO 1: Conectar a BD mantenimiento para crear BD ■■■■■■■■■■■■■
            logger.info("=== FASE 1: Creación de base de datos ===")
            conn_maintenance = self._create_connection("postgres")
            
            # ▲▲▲▲▲▲ Ejecutar script 01_create_database.sql ▲▲▲▲▲▲
            if not self._execute_sql_file(
                conn_maintenance, 
                self.scripts[0],
                "creación de base de datos"
            ):
                return False
            
            # ▲▲▲▲▲▲ Cerrar conexión de mantenimiento ▲▲▲▲▲▲
            conn_maintenance.close()
            conn_maintenance = None
            
            # ■■■■■■■■■■■■■ PASO 2: Conectar a BD target para schema y datos ■■■■■■■■■■■■■
            logger.info("=== FASE 2: Configuración de esquema y datos ===")
            conn_target = self._create_connection(self.config.db_name)
            
            # ▲▲▲▲▲▲ Ejecutar scripts restantes en secuencia ▲▲▲▲▲▲
            remaining_scripts = [
                (self.scripts[1], "creación de esquema"),
                (self.scripts[2], "creación de índices"),
                (self.scripts[3], "datos de prueba")
            ]
            
            for script_name, description in remaining_scripts:
                if not self._execute_sql_file(conn_target, script_name, description):
                    return False
            
            logger.info("=== Inicialización completada exitosamente ===")
            return True
            
        except Exception as e:
            logger.error(f"Error fatal en inicialización: {e}")
            return False
        finally:
            
            # ▲▲▲▲▲▲ Asegurar cierre de conexiones ▲▲▲▲▲▲
            if conn_maintenance:
                conn_maintenance.close()
            if conn_target:
                conn_target.close()


def parse_arguments() -> argparse.Namespace:
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Inicializador de base de datos para migrador CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s                          # Usa .env por defecto
  %(prog)s --env-file .env.local     # Archivo .env específico
  %(prog)s --config config/dev.yaml # Configuración YAML (futuro)
        """
    )
    
    parser.add_argument(
        '--env-file',
        type=str,
        help='Archivo .env con variables de conexión (default: .env)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Archivo YAML de configuración (no implementado aún)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verboso (DEBUG logging)'
    )
    
    return parser.parse_args()


def load_env_file(env_file: Optional[str]) -> None:
    """Carga variables desde archivo .env si existe."""
    if env_file and Path(env_file).exists():
        logger.info(f"Cargando variables desde: {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    elif Path('.env').exists():
        logger.info("Cargando variables desde: .env (default)")
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value


def main() -> int:
    """Función principal del inicializador."""
    try:
        args = parse_arguments()
        
        # ■■■■■■■■■■■■■ Configurar nivel de logging ■■■■■■■■■■■■■
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # ■■■■■■■■■■■■■ Cargar variables de entorno ■■■■■■■■■■■■■
        load_env_file(args.env_file)
        
        # ■■■■■■■■■■■■■ Validar configuración ■■■■■■■■■■■■■
        config = DatabaseConfig()
        
        # ■■■■■■■■■■■■■ Ejecutar inicialización ■■■■■■■■■■■■■
        initializer = DatabaseInitializer(config)
        success = initializer.initialize_database()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Inicialización cancelada por usuario")
        return 130
    except Exception as e:
        logger.error(f"Error no manejado: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())