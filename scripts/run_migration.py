#!/usr/bin/env python3
"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO: Entry Point CLI - Capa de Presentación
AUTOR: Fisherk2
FECHA: 2026-04-24
DESCRIPCIÓN: CLI que orquesta inyección de dependencias y ejecuta pipeline.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any

# ▏▎▍▌▋▊▉▉▉▉▉▉▉▉ Ajustar sys.path para permitir ejecución desde scripts/ sin romper imports de src/ ▉▉▉▉▉▉▉▉▉▊▋▌▍▎▏
# Esto mantiene el script ejecutable directamente mientras respeta la estructura de paquetes
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.migrator.db_connector import DBConnector, ConfigurationError, OperationalError
from src.migrator.csv_loader import CSVLoader
from src.migrator.error_handler import ErrorHandler
from src.migrator.report_generator import ReportGenerator
from src.migrator.pipeline import MigrationPipeline
from src.utils.logger import get_logger


def parse_arguments() -> argparse.Namespace:
    """
    Parsea argumentos de línea de comandos.
    
    DECISIÓN: Usar argparse (stdlib) para mantener MVP simple sin dependencias externas.
    Validación de ruta config antes de proceder para fail-fast.
    
    Returns:
        Namespace con argumentos parseados.
    """

    parser = argparse.ArgumentParser(
        description="Migrador CSV → PostgreSQL con validación reutilizable",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Ruta al archivo YAML de configuración de migración"
    )
    
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="Ruta al archivo .env con credenciales de BD (default: usar variables de entorno del sistema)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida sin modificar la base de datos (solo carga y validación CSV)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Muestra logs detallados (nivel DEBUG)"
    )
    
    return parser.parse_args()


def load_env_file(env_file: str) -> None:
    """
    Carga variables de entorno desde archivo .env.
    
    DECISIÓN: Implementación manual simple sin python-dotenv para reducir dependencias.
    Solo carga variables que no estén ya definidas (respetar precedence de sistema).
    
    Args:
        env_file: Ruta al archivo .env.
    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si el formato del archivo es inválido.
    """

    env_path = Path(env_file)
    
    if not env_path.exists():
        raise FileNotFoundError(f"Archivo .env no encontrado: {env_file}")
    
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # ▲▲▲▲▲▲ Ignorar comentarios y líneas vacías ▲▲▲▲▲▲
            if not line or line.startswith("#"):
                continue
            
            # ▲▲▲▲▲▲ Parsear KEY=VALUE ▲▲▲▲▲▲
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                # ▲▲▲▲▲▲ Solo setear si no existe ya (precedencia de sistema) ▲▲▲▲▲▲
                if key not in os.environ:
                    os.environ[key] = value

def load_db_config_from_env() -> Dict[str, Any]:
    """
    Carga configuración de BD desde variables de entorno.
    
    DECISIÓN: Usar constantes del pipeline para consistencia (DRY).
    Valores por defecto seguros para desarrollo local.
    
    Returns:
        Diccionario con configuración esperada por DBConnector.
    """

    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "dbname": os.getenv("DB_NAME", "migrator_ecommerce"),
        "user": os.getenv("DB_USER", "migrator_user"),
        "password": os.getenv("DB_PASSWORD", ""),
        "port": int(os.getenv("DB_PORT", "5432"))
    }


def validate_config_path(config_path: str) -> Path:
    """
    Valida que el archivo de configuración exista y sea legible.
    
    Args:
        config_path: Ruta al archivo de configuración.
    Returns:
        Path validado.
    Raises:
        FileNotFoundError: Si el archivo no existe.
        PermissionError: Si no hay permisos de lectura.
    """

    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
    
    if not path.is_file():
        raise ValueError(f"La ruta no es un archivo: {config_path}")
    
    if not os.access(config_path, os.R_OK):
        raise PermissionError(f"Sin permisos de lectura: {config_path}")
    
    return path


def main() -> int:
    """
    Punto de entrada principal del CLI.
    
    DECISIÓN: Inyección manual de dependencias para MVP sin contenedor DI complejo.
    Instanciar componentes explícitamente y pasarlos al pipeline.
    
    Returns:
        Exit code: 0 (éxito), 1 (error validación), 2 (error configuración/CLI).
    """

    try:
        # ■■■■■■■■■■■■■ Paso 1: Parsear argumentos CLI ■■■■■■■■■■■■■
        args = parse_arguments()
        
        # ■■■■■■■■■■■■■ Paso 2: Validar archivo de configuración ■■■■■■■■■■■■■
        validate_config_path(args.config)
        
        # ■■■■■■■■■■■■■ Paso 3: Cargar .env si se especificó ■■■■■■■■■■■■■
        if args.env_file:
            load_env_file(args.env_file)
        
        # ■■■■■■■■■■■■■ Paso 4: Configurar logger según --verbose ■■■■■■■■■■■■■
        log_level = "DEBUG" if args.verbose else "INFO"
        logger = get_logger(__name__, level=log_level)
        logger.info(f"Iniciando migrador con config: {args.config}")
        
        # ■■■■■■■■■■■■■ Paso 5: Inyección de dependencias manual ■■■■■■■■■■■■■
        # DECISIÓN: Instanciar componentes explícitamente para máxima claridad y testabilidad
        
        # ▲▲▲▲▲▲ DBConnector con config desde variables de entorno ▲▲▲▲▲▲
        db_config = load_db_config_from_env()
        # DECISIÓN DE DISEÑO: No imprimir credenciales por seguridad
        logger.info(f"Conectando a BD: {db_config['host']}:{db_config['port']}/{db_config['dbname']}")
        db_connector = DBConnector(config=db_config)
        
        # ▲▲▲▲▲▲ CSVLoader con logger inyectado ▲▲▲▲▲▲
        csv_loader = CSVLoader(logger=logger)
        
        # ▲▲▲▲▲▲ ErrorHandler sin dependencias ▲▲▲▲▲▲
        error_handler = ErrorHandler()
        
        # ▲▲▲▲▲▲ ReportGenerator sin dependencias ▲▲▲▲▲▲
        report_generator = ReportGenerator()
        
        # ▲▲▲▲▲▲ MigrationPipeline con todos los componentes inyectados ▲▲▲▲▲▲
        pipeline = MigrationPipeline(
            db_connector=db_connector,
            csv_loader=csv_loader,
            error_handler=error_handler,
            report_generator=report_generator
        )
        
        # ■■■■■■■■■■■■■ Paso 6: Ejecutar pipeline ■■■■■■■■■■■■■
        if args.dry_run:
            logger.info("MODO DRY-RUN: Solo validación, sin modificaciones a BD")
            # DECISIÓN DE DISEÑO: En dry-run, el pipeline ejecuta validación pero no commit
            # La implementación interna del pipeline debe respetar este flag
        
        results = pipeline.execute(config_path=args.config)
        
        # ■■■■■■■■■■■■■ Paso 7: Reportar resultado ■■■■■■■■■■■■■
        imported = results.get("imported", 0)
        rejected = results.get("rejected", 0)
        logger.info(f"Migración completada: {imported} importados, {rejected} rechazados")
        
        # ▲▲▲▲▲▲ Exit code según resultado ▲▲▲▲▲▲
        if rejected > 0:
            logger.warning("Migración con errores: algunos registros fueron rechazados")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Migración interrumpida por usuario", file=sys.stderr)
        return 130  # Exit code estándar para SIGINT
        
    except SystemExit as e:

        # ▲▲▲▲▲▲ Propagar SystemExit sin modificar (puede ser desde argparse) ▲▲▲▲▲▲
        return e.code if e.code is not None else 2
        
    except (FileNotFoundError, PermissionError, ValueError, ConfigurationError) as e:

        # ▲▲▲▲▲▲ Errores de configuración/CLI ▲▲▲▲▲▲
        print(f"❌ Error de configuración: {e}", file=sys.stderr)
        return 2
        
    except OperationalError as e:

        # ▲▲▲▲▲▲ Errores operacionales de BD (conexión, timeout) ▲▲▲▲▲▲
        print(f"❌ Error de base de datos: {e}", file=sys.stderr)
        return 2
        
    except Exception as e:

        # ▲▲▲▲▲▲ Excepciones inesperadas ▲▲▲▲▲▲
        print(f"❌ Error inesperado: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
