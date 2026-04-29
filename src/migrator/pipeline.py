"""Orquestador de migración con patrón Template Method.

Este módulo implementa el patrón Template Method para definir el esqueleto
algorítmico de la migración de datos CSV a PostgreSQL, delegando la
implementación concreta de cada paso a componentes inyectados.

El pipeline garantiza:
- Transacciones atómicas con rollback automático
- Validación de datos configurable
- Reporting estructurado de resultados
- Extensibilidad mediante hooks de ciclo de vida

Example:
    >>> from src.migrator.db_connector import DBConnector
    >>> from src.migrator.csv_loader import CSVLoader
    >>> from src.migrator.error_handler import ErrorHandler
    >>> from src.migrator.report_generator import ReportGenerator
    >>>
    >>> db = DBConnector(host="localhost", user="postgres", password="secret", database="mydb")
    >>> loader = CSVLoader()
    >>> handler = ErrorHandler()
    >>> reporter = ReportGenerator()
    >>>
    >>> pipeline = MigrationPipeline(db, loader, handler, reporter)
    >>> results = pipeline.execute("config/migration.yaml")
    >>> print(f"Importados: {results['imported']}, Rechazados: {results['rejected']}")
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from src.migrator.csv_loader import CSVLoader
from src.migrator.db_connector import DBConnector
from src.migrator.error_handler import ErrorHandler
from src.migrator.report_generator import ReportGenerator
from src.utils.logger import get_logger


class MigrationPipeline:
    """Orquestador de migración con patrón Template Method.

    Define el esqueleto algorítmico inmutable para garantizar consistencia
    operativa. Los pasos concretos se delegan a componentes inyectados,
    permitiendo testing aislado y extensibilidad mediante hooks.

    El flujo del pipeline es:
    1. Cargar configuración YAML
    2. Establecer conexión a base de datos
    3. Iniciar transacción
    4. Cargar y validar CSV
    5. Finalizar transacción (commit/rollback)
    6. Generar reporte
    7. Limpiar recursos

    Attributes:
        _db_connector: Conector a base de datos inyectado.
        _csv_loader: Cargador CSV inyectado.
        _error_handler: Gestor de errores inyectado.
        _report_generator: Generador de reportes inyectado.
        _config: Configuración de migración cargada desde YAML.
        _logger: Logger configurado para este módulo.

    Example:
        >>> pipeline = MigrationPipeline(db, loader, handler, reporter)
        >>> results = pipeline.execute("config/default_migration.yaml")
        >>> assert results['imported'] >= 0
        >>> assert results['rejected'] >= 0
    """
    
    def __init__(
        self,
        db_connector: DBConnector,
        csv_loader: CSVLoader,
        error_handler: ErrorHandler,
        report_generator: ReportGenerator
    ) -> None:
        """Inicializa el pipeline con componentes inyectados.

        Args:
            db_connector: Conector a base de datos PostgreSQL.
            csv_loader: Cargador de archivos CSV con validación.
            error_handler: Gestor de errores de migración.
            report_generator: Generador de reportes en JSON/CLI.

        Example:
            >>> db = DBConnector(host="localhost", user="postgres", password="secret", database="mydb")
            >>> loader = CSVLoader()
            >>> handler = ErrorHandler()
            >>> reporter = ReportGenerator()
            >>> pipeline = MigrationPipeline(db, loader, handler, reporter)
        """
        self._db_connector = db_connector
        self._csv_loader = csv_loader
        self._error_handler = error_handler
        self._report_generator = report_generator
        self._config: Optional[Dict] = None
        self._logger = get_logger(__name__)
    
    def execute(self, config_path: str) -> Dict:
        """Ejecuta el pipeline completo de migración.

        Implementa el Template Method con esqueleto fijo try/except/finally
        para garantizar rollback y cleanup incluso en fallos inesperados.

        Args:
            config_path: Ruta al archivo de configuración YAML. El archivo
                debe contener secciones para 'source', 'target', 'validation',
                y 'reporting'.

        Returns:
            Diccionario con métricas finales del proceso:
                - 'imported': Número de filas importadas exitosamente.
                - 'rejected': Número de filas rechazadas por validación.
                - 'errors': Lista de errores encontrados.

        Raises:
            FileNotFoundError: Si el archivo de configuración no existe.
            yaml.YAMLError: Si el archivo YAML tiene sintaxis inválida.
            Exception: Si falla el pipeline de forma crítica.

        Example:
            >>> pipeline = MigrationPipeline(db, loader, handler, reporter)
            >>> results = pipeline.execute("config/default_migration.yaml")
            >>> print(f"Importados: {results['imported']}")
            >>> print(f"Rechazados: {results['rejected']}")
        """
        try:
            # ■■■■■■■■■■■■■ Paso 1: Cargar configuración ■■■■■■■■■■■■■
            self._config = self._load_config(config_path)
            self._logger.info(f"Configuración cargada desde: {config_path}")
            
            # ■■■■■■■■■■■■■ Hook pre-conexión (extensibilidad) ■■■■■■■■■■■■■
            self._pre_connection_hook()
            
            # ■■■■■■■■■■■■■ Paso 2: Establecer conexión ■■■■■■■■■■■■■
            self._establish_connection()
            self._logger.info("Conexión a base de datos establecida")
            
            # ■■■■■■■■■■■■■ Hook pre-transacción (extensibilidad) ■■■■■■■■■■■■■
            self._pre_transaction_hook()
            
            # ■■■■■■■■■■■■■ Paso 3: Iniciar transacción ■■■■■■■■■■■■■
            self._db_connector.begin_transaction()
            self._logger.info("Transacción iniciada")
            
            # ■■■■■■■■■■■■■ Paso 4: Cargar y validar CSV ■■■■■■■■■■■■■
            stats = self._load_and_validate_csv()
            self._logger.info(f"CSV procesado: {stats}")
            
            # ■■■■■■■■■■■■■ Paso 5: Finalizar transacción ■■■■■■■■■■■■■
            self._finalize_transaction()
            
            # ■■■■■■■■■■■■■ Paso 6: Generar reporte ■■■■■■■■■■■■■
            report_data = self._generate_report(stats)
            
            # ■■■■■■■■■■■■■ Hook post-reporte (extensibilidad) ■■■■■■■■■■■■■
            self._post_report_hook(report_data)
            
            return stats
            
        except KeyboardInterrupt:
            self._logger.warning("Migración interrumpida por usuario")
            self._db_connector.rollback()
            raise
        except SystemExit:
            self._logger.warning("Migración terminada por sistema")
            self._db_connector.rollback()
            raise
        except Exception as e:
            self._logger.error(f"Error crítico en pipeline: {e}")
            self._db_connector.rollback()
            raise
        finally:
            # ■■■■■■■■■■■■■ Paso 7: Limpieza de recursos ■■■■■■■■■■■■■
            self._cleanup_resources()
    
    def _load_config(self, config_path: str) -> Dict:
        """Carga configuración desde archivo YAML.

        Args:
            config_path: Ruta al archivo de configuración YAML.

        Returns:
            Diccionario con configuración de migración. Estructura esperada:
                {
                    'source': {'file': 'path/to/data.csv'},
                    'target': {'table': 'table_name'},
                    'validation': {'max_errors': 100},
                    'reporting': {'output_path': 'path/to/report.json'}
                }

        Raises:
            FileNotFoundError: Si el archivo de configuración no existe.
        """

        # ■■■■■■■■■■■■■ DECISIÓN: Delegar carga de config a utilidad externa ■■■■■■■■■■■■■
        # para mantener pipeline desacoplado de detalles de YAML

        import yaml
        
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _establish_connection(self) -> None:
        """Establece conexión a base de datos.

        DBConnector ya fue configurado por la capa de presentación (CLI)
        con las credenciales apropiadas. Esta función solo delega la conexión.

        Raises:
            psycopg2.OperationalError: Si falla la conexión a PostgreSQL.
        """

        # ■■■■■■■■■■■■■ La configuración se inyectó desde el CLI al instanciar DBConnector ■■■■■■■■■■■■■
        self._db_connector.connect()
    
    
    def _load_and_validate_csv(self) -> Dict:
        """Carga y valida CSV con inyección de componentes.

        Esta función coordina dos operaciones principales:
        1. Carga del CSV a una tabla temporal con validación
        2. Transferencia de datos válidos a la tabla destino

        Returns:
            Diccionario con estadísticas del proceso:
                - 'imported': Número de filas importadas exitosamente.
                - 'rejected': Número de filas rechazadas por validación.
        """
        source_config = self._config.get("source", {})
        target_config = self._config.get("target", {})
        validation_config = self._config.get("validation", {})
        
        csv_path = source_config.get("file")
        schema = self._config.get("schema", {})
        validators = self._config.get("validators", {})
        
        # ■■■■■■■■■■■■■ Hook pre-carga (extensibilidad) ■■■■■■■■■■■■■
        self._pre_load_hook(csv_path)
        
        # ■■■■■■■■■■■■■ Cargar CSV a tabla temporal ■■■■■■■■■■■■■
        temp_table = self._csv_loader.load_csv_to_temp_table(
            csv_path=csv_path,
            schema=schema,
            validators=validators,
            db_connector=self._db_connector,
            config=validation_config
        )
        
        # ■■■■■■■■■■■■■ Validar y transferir a tabla destino ■■■■■■■■■■■■■
        stats = self._csv_loader.validate_and_transfer(
            temp_table=temp_table,
            target_table=target_config.get("table"),
            schema=schema,
            db_connector=self._db_connector
        )
        
        # ■■■■■■■■■■■■■ Hook post-carga (extensibilidad) ■■■■■■■■■■■■■
        self._post_load_hook(stats)
        
        return stats
    
    def _finalize_transaction(self) -> None:
        """Finaliza transacción según estado del error handler.

        Commit solo si no se superó el umbral crítico de errores.
        Rollback automático en caso contrario.

        El umbral se lee de la configuración en 'validation.max_errors'.
        """
        max_errors = self._config.get("validation", {}).get("max_errors", 100)
        
        if self._error_handler.has_critical_errors(max_errors):
            self._logger.error("Umbral crítico de errores superado, iniciando rollback")
            self._db_connector.rollback()
        else:
            self._logger.info("Validación exitosa, iniciando commit")
            self._db_connector.commit()
    
    def _generate_report(self, stats: Dict) -> Dict:
        """Genera reporte con métricas y errores.

        El reporte se genera en dos formatos según configuración:
        - JSON: Exportado a archivo si 'reporting.output_path' está configurado
        - CLI: Mostrado en consola si 'reporting.cli_output' es True

        Args:
            stats: Estadísticas del proceso de migración con claves
                'imported' y 'rejected'.

        Returns:
            Diccionario con datos del reporte incluyendo métricas,
            errores y metadatos de configuración.
        """
        report_data = self._report_generator.generate_summary(
            imported=stats.get("imported", 0),
            rejected=stats.get("rejected", 0),
            errors=self._error_handler.errors,
            config=self._config
        )
        
        # ■■■■■■■■■■■■■ Exportar a JSON si está configurado ■■■■■■■■■■■■■
        output_path = self._config.get("reporting", {}).get("output_path")
        if output_path:
            self._report_generator.export_to_json(report_data, output_path)
        
        # ■■■■■■■■■■■■■ Mostrar en CLI si está configurado ■■■■■■■■■■■■■
        if self._config.get("reporting", {}).get("cli_output", True):
            self._report_generator.print_human_readable(report_data)
        
        return report_data
    
    def _cleanup_resources(self) -> None:
        """Limpia recursos y cierra conexiones.

        Se ejecuta siempre en el bloque finally para garantizar
        liberación de recursos incluso en fallos. Cierra la conexión
        a la base de datos si está activa.
        """
        try:
            if self._db_connector.is_connected:
                self._db_connector.close()
                self._logger.info("Conexión a base de datos cerrada")
        except Exception as e:
            self._logger.error(f"Error cerrando conexión: {e}")
    
    # ▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣  Hooks para extensibilidad (OCP) ▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣▢▣
    
    def _pre_connection_hook(self) -> None:
        """Hook ejecutado antes de establecer conexión.

        Sobrescribir en subclases para comportamiento personalizado,
        como validación de configuración o preparación de recursos.

        Example:
            >>> class CustomPipeline(MigrationPipeline):
            ...     def _pre_connection_hook(self) -> None:
            ...         self._logger.info("Validando configuración pre-conexión...")
        """
        pass
    
    def _pre_transaction_hook(self) -> None:
        """Hook ejecutado antes de iniciar transacción.

        Sobrescribir en subclases para comportamiento personalizado,
        como verificación de estado de la base de datos.
        """
        pass
    
    def _pre_load_hook(self, csv_path: str) -> None:
        """Hook ejecutado antes de cargar CSV.

        Sobrescribir en subclases para comportamiento personalizado,
        como validación del archivo CSV o preparación de esquemas.

        Args:
            csv_path: Ruta del archivo CSV a cargar.
        """
        pass
    
    def _post_load_hook(self, stats: Dict) -> None:
        """Hook ejecutado después de cargar CSV.

        Sobrescribir en subclases para comportamiento personalizado,
        como notificaciones o procesamiento adicional de estadísticas.

        Args:
            stats: Estadísticas del proceso de carga con claves
                'imported' y 'rejected'.
        """
        pass
    
    def _post_report_hook(self, report_data: Dict) -> None:
        """Hook ejecutado después de generar reporte.

        Sobrescribir en subclases para comportamiento personalizado,
        como envío de notificaciones o almacenamiento adicional.

        Args:
            report_data: Datos del reporte generado con métricas y errores.
        """
        pass