#!/usr/bin/env python3
"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO:      Orquestador de Pruebas de Integración E2E
AUTOR:       Fisherk2
FECHA:       2026-04-27
DESCRIPCIÓN: Ejecuta migraciones reales contra PostgreSQL con rollback transaccional.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# DECISIÓN: Agregar src al path para importar módulos del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.migrator.db_connector import DBConnector
from src.migrator.csv_loader import CSVLoader
from src.migrator.error_handler import ErrorHandler, MigrationError
from src.migrator.report_generator import ReportGenerator
from src.validators.custom.email_validator import validate_email_format
from src.validators.custom.phone_validator import validate_phone_format


# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# CONFIGURACIÓN DE LOGGING
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# CLASE DE CONFIGURACIÓN DE PRUEBAS
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

class TestConfig:
    """Configuración de pruebas desde variables de entorno TEST_*."""
    
    def __init__(self) -> None:
        # DECISIÓN: Usar TEST_* con fallback a valores seguros
        self.host = os.getenv('TEST_DB_HOST', 'localhost')
        self.port = int(os.getenv('TEST_DB_PORT', '5432'))
        self.dbname = os.getenv('TEST_DB_NAME', 'migrator_test')
        self.user = os.getenv('TEST_DB_USER', 'test_user')
        self.password = os.getenv('TEST_DB_PASSWORD', 'test_password')
        
        # DECISIÓN DE DISEÑO: Validar que no apunte a producción
        if self.dbname == 'migrator_ecommerce':
            raise ValueError(
                f"TEST_DB_NAME apunta a producción: {self.dbname}. "
                "Usar base de datos separada para pruebas."
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para DBConnector."""
        return {
            'host': self.host,
            'port': self.port,
            'dbname': self.dbname,
            'user': self.user,
            'password': self.password
        }


# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# ORQUESTADOR DE PRUEBAS DE INTEGRACIÓN
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

class IntegrationTestRunner:
    """
    Ejecuta pruebas de integración E2E con rollback transaccional garantizado.
    
    DECISIÓN: Usar transacción explícita con ROLLBACK en finally.
    Esto garantiza que ningún dato de prueba persista, incluso si hay excepciones.
    """
    
    def __init__(self, config: TestConfig, verbose: bool = False, keep_data: bool = False) -> None:
        """
        Inicializa el runner con configuración de pruebas.
        
        Args:
            config: Configuración de conexión a base de datos de prueba.
            verbose: Si True, muestra logs detallados.
            keep_data: Si True, no hace ROLLBACK (para debugging).
        """
        self.config = config
        self.verbose = verbose
        self.keep_data = keep_data
        
        # DECISIÓN: Instanciar componentes reales, no mocks
        # Estas son pruebas de integración, validan comportamiento real
        self.db_connector = DBConnector(config.to_dict())
        self.csv_loader = CSVLoader(logger=logger if verbose else None)
        self.error_handler = ErrorHandler()
        self.report_generator = ReportGenerator()
        
        # DECISIÓN: Usar fixtures desde test/fixtures/
        self.fixtures_dir = Path(__file__).parent.parent / 'fixtures'
        
        # DECISIÓN: Usar schema YAML existente
        self.schema_dir = Path(__file__).parent.parent.parent / 'config' / 'schema_examples'
    
    def _load_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Carga esquema YAML para una tabla.
        
        Args:
            table_name: Nombre de la tabla (ej: 'customers').
            
        Returns:
            Diccionario con definición de esquema.
        """
        schema_path = self.schema_dir / f'{table_name}_schema.yaml'
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema no encontrado: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _get_validators(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construye diccionario de validadores desde schema.
        
        Args:
            schema: Diccionario de esquema YAML.
            
        Returns:
            Diccionario {columna: validador_func}.
        """
        validators = {}
        
        for col_name, col_def in schema.get('columns', {}).items():
            col_type = col_def.get('type')
            
            if col_type == 'email':
                validators[col_name] = validate_email_format
            elif col_type == 'phone':
                validators[col_name] = validate_phone_format
        
        return validators
    
    def _run_single_test(
        self,
        csv_file: str,
        table_name: str,
        expected_imported: int,
        expected_rejected: int
    ) -> Dict[str, Any]:
        """
        Ejecuta una prueba de integración individual.
        
        Args:
            csv_file: Nombre del archivo CSV en fixtures/.
            table_name: Nombre de la tabla destino.
            expected_imported: Número esperado de filas importadas.
            expected_rejected: Número esperado de filas rechazadas.
            
        Returns:
            Diccionario con resultados de la prueba.
        """
        csv_path = self.fixtures_dir / csv_file
        schema = self._load_schema(table_name)
        validators = self._get_validators(schema)
        
        result = {
            'csv_file': csv_file,
            'table_name': table_name,
            'expected_imported': expected_imported,
            'expected_rejected': expected_rejected,
            'actual_imported': 0,
            'actual_rejected': 0,
            'errors': [],
            'success': False
        }
        
        # DECISIÓN: Usar transacción explícita con ROLLBACK garantizado
        self.db_connector.connect()
        
        try:
            # BEGIN transacción
            self.db_connector.connection.autocommit = False
            
            # Ejecutar migración
            temp_table = self.csv_loader.load_csv_to_temp_table(
                csv_path=str(csv_path),
                schema=schema,
                validators=validators,
                db_connector=self.db_connector,
                config={'validation': {'max_errors_before_rollback': 100}}
            )
            
            # Verificar resultados en tabla temporal
            with self.db_connector.connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {temp_table}")
                result['actual_imported'] = cursor.fetchone()[0]
            
            # Validar resultados
            result['success'] = (
                result['actual_imported'] == expected_imported and
                result['actual_rejected'] == expected_rejected
            )
            
            if not result['success']:
                result['errors'].append(
                    f"Expected {expected_imported} imported, got {result['actual_imported']}"
                )
            
            # DECISIÓN: ROLLBACK siempre en pruebas (a menos que keep_data=True)
            if not self.keep_data:
                self.db_connector.rollback()
                logger.info(f"ROLLBACK ejecutado para {csv_file}")
            else:
                self.db_connector.commit()
                logger.warning(f"COMMIT ejecutado para {csv_file} (keep_data=True)")
                
        except Exception as e:
            # ROLLBACK en caso de error
            if not self.keep_data:
                self.db_connector.rollback()
            result['errors'].append(str(e))
            result['success'] = False
            logger.error(f"Error en prueba {csv_file}: {e}")
            
        finally:
            # Cerrar conexión
            self.db_connector.close()
        
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Ejecuta todas las pruebas de integración.
        
        Returns:
            Diccionario con resultados agregados:
                - imported: Total de filas importadas exitosamente
                - rejected: Total de filas rechazadas
                - errors: Lista de errores encontrados
                - success: True si todas las pruebas pasaron
        """
        logger.info("=== INICIANDO PRUEBAS DE INTEGRACIÓN E2E ===")
        
        # DECISIÓN: Definir casos de prueba deterministas
        test_cases = [
            # (csv_file, table_name, expected_imported, expected_rejected)
            ('customers_valid.csv', 'customers', 10, 0),
            ('customers_invalid_email.csv', 'customers', 0, 5),
            ('customers_invalid_phone.csv', 'customers', 0, 5),
            ('customers_mixed.csv', 'customers', 8, 4),
        ]
        
        results = []
        total_imported = 0
        total_rejected = 0
        all_errors = []
        
        for csv_file, table_name, expected_imported, expected_rejected in test_cases:
            logger.info(f"Ejecutando prueba: {csv_file}")
            
            result = self._run_single_test(csv_file, table_name, expected_imported, expected_rejected)
            results.append(result)
            
            total_imported += result['actual_imported']
            total_rejected += result['actual_rejected']
            all_errors.extend(result['errors'])
            
            if result['success']:
                logger.success(f"✅ {csv_file}: PASSED")
            else:
                logger.error(f"❌ {csv_file}: FAILED")
                for error in result['errors']:
                    logger.error(f"   - {error}")
        
        # Agregar resultados
        all_success = all(r['success'] for r in results)
        
        logger.info("=== RESUMEN DE PRUEBAS DE INTEGRACIÓN ===")
        logger.info(f"Total importadas: {total_imported}")
        logger.info(f"Total rechazadas: {total_rejected}")
        logger.info(f"Pruebas pasadas: {sum(1 for r in results if r['success'])}/{len(results)}")
        
        return {
            'imported': total_imported,
            'rejected': total_rejected,
            'errors': all_errors,
            'success': all_success,
            'test_results': results
        }


# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# FUNCIÓN PRINCIPAL
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

def parse_arguments() -> argparse.Namespace:
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description='Orquestador de pruebas de integración E2E',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verboso (DEBUG logging)'
    )
    
    parser.add_argument(
        '--keep-data', '-k',
        action='store_true',
        help='Mantener datos de prueba (no hacer ROLLBACK)'
    )
    
    return parser.parse_args()


def main() -> int:
    """Función principal del orquestador."""
    try:
        args = parse_arguments()
        
        # Configurar nivel de logging
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Cargar configuración de pruebas
        config = TestConfig()
        
        # Ejecutar pruebas
        runner = IntegrationTestRunner(
            config=config,
            verbose=args.verbose,
            keep_data=args.keep_data
        )
        
        results = runner.run_all_tests()
        
        # Exit code basado en resultados
        if results['success']:
            logger.success("🎉 TODAS LAS PRUEBAS DE INTEGRACIÓN PASARON")
            return 0
        else:
            logger.error("💥 HAY PRUEBAS DE INTEGRACIÓN FALLIDAS")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Pruebas canceladas por usuario")
        return 130
    except Exception as e:
        logger.error(f"Error no manejado: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
