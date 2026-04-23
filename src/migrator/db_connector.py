"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO:      DBConnector - Repository/Adapter PostgreSQL
AUTOR:       Fisherk2
FECHA:       2026-04-23
DESCRIPCIÓN: Aísla psycopg2 del dominio mediante patrón Repository.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Sequence

import psycopg2
import psycopg2.extras
from psycopg2 import sql
from psycopg2.extensions import connection

# ▏▎▍▌▋▊▉▉▉▉▉▉▉▉ Excepciones de dominio para aislamiento de psycopg2 ▉▉▉▉▉▉▉▉▉▊▋▌▍▎▏
class DatabaseError(Exception):
    """Base exception para errores de base de datos."""
    pass

class IntegrityError(DatabaseError):
    """Violación de constraints (FK, UNIQUE, CHECK)."""
    pass

class OperationalError(DatabaseError):
    """Errores operacionales (conexión, timeout, sintaxis)."""
    pass

class ConfigurationError(DatabaseError):
    """Errores de configuración de conexión."""
    pass

# ◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤ ⎡ DECISIÓN DE DISEÑO ⎦ ◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤
# Desactivar autocommit para control explícito de transacciones
# Esto permite que el pipeline controle exactamente cuándo se confirman los cambios


class DBConnector:
    """
    Repository/Adapter que aísla psycopg2 del dominio.
    
    Gestiona ciclo de vida de conexión, transacciones y operaciones de ingesta
    contra PostgreSQL, siguiendo el Principio de Inversión de Dependencias.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Inicializa el connector con configuración de conexión.
        
        Args:
            config: Diccionario con claves: host, dbname, user, password, port (opcional).
        Raises:
            ConfigurationError: Si faltan claves requeridas.
        """
        self._validate_config(config)
        self._config = config.copy()  # Evitar mutación externa
        self._connection: Optional[connection] = None
        self._logger = logging.getLogger(__name__)
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Valida configuración mínima requerida.
        :param config: Configuración de conexión a base de datos
        """

        required_keys = {"host", "dbname", "user", "password"}
        missing_keys = required_keys - set(config.keys())
        
        if missing_keys:
            raise ConfigurationError(
                f"Configuración incompleta. Faltan claves: {', '.join(missing_keys)}"
            )
    
    def connect(self) -> None:
        """
        Establece conexión a PostgreSQL.
        
        Raises:
            OperationalError: Si falla la conexión.
        """

        try:
            # ■■■■■■■■■■■■■ DECISIÓN DE DISEÑO: autocommit=False para control explícito ■■■■■■■■■■■■■
            self._connection = psycopg2.connect(
                host=self._config["host"],
                database=self._config["dbname"],
                user=self._config["user"],
                password=self._config["password"],
                port=self._config.get("port", 5432),
                autocommit=False
            )
            self._logger.info("Conexión establecida con PostgreSQL")
            
        except psycopg2.OperationalError as e:
            raise OperationalError(f"Error de conexión a PostgreSQL: {e}") from e
        except psycopg2.Error as e:
            raise OperationalError(f"Error inesperado al conectar: {e}") from e
    
    def close(self) -> None:
        """
        Cierra la conexión y limpia recursos.
        """

        if self._connection and not self._connection.closed:
            try:
                self._connection.close()
                self._logger.info("Conexión cerrada correctamente")
            except psycopg2.Error as e:
                self._logger.error(f"Error al cerrar conexión: {e}")
            finally:
                self._connection = None
    
    def begin(self) -> None:
        """
        Inicia una transacción explícita.
        """

        if not self._connection or self._connection.closed:
            raise OperationalError("No hay conexión activa para iniciar transacción")
        
        try:
            self._connection.autocommit = False
            self._logger.debug("Transacción iniciada")
        except psycopg2.Error as e:
            raise OperationalError(f"Error al iniciar transacción: {e}") from e
    
    def commit(self) -> None:
        """
        Confirma la transacción actual.
        """

        if not self._connection or self._connection.closed:
            raise OperationalError("No hay conexión activa para confirmar")
        
        try:
            self._connection.commit()
            self._logger.debug("Transacción confirmada")
        except psycopg2.Error as e:
            raise OperationalError(f"Error al confirmar transacción: {e}") from e
    
    def rollback(self) -> None:
        """
        Revierte la transacción actual.
        """

        if not self._connection or self._connection.closed:
            raise OperationalError("No hay conexión activa para revertir")
        
        try:
            self._connection.rollback()
            self._logger.debug("Transacción revertida")
        except psycopg2.Error as e:
            raise OperationalError(f"Error al revertir transacción: {e}") from e
    
    def execute_copy_from(self, csv_path: str, table_name: str) -> int:
        """Ejecuta COPY FROM para ingesta masiva de CSV.
        
        DECISIÓN DE DISEÑO: Usar copy_expert para máximo rendimiento
        en archivos grandes, evitando overhead de Python.
        
        Args:
            csv_path: Ruta al archivo CSV.
            table_name: Nombre de la tabla destino.
        Returns:
            Número de filas procesadas.
        Raises:
            OperationalError: Si falla el COPY.
            IntegrityError: Si hay violación de constraints.
        """

        if not self._connection or self._connection.closed:
            raise OperationalError("No hay conexión activa para COPY")
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csv_file:

                # ■■■■■■■■■■■■■ DECISIÓN DE DISEÑO: COPY con formato CSV para compatibilidad ■■■■■■■■■■■■■
                copy_sql = f"COPY {table_name} FROM STDIN WITH (FORMAT csv, HEADER true)"
                cursor = self._connection.cursor()
                
                cursor.copy_expert(copy_sql, csv_file)
                rows_copied = cursor.rowcount
                self._logger.info(f"COPY completado: {rows_copied} filas en {table_name}")
                
                return rows_copied
                
        except psycopg2.IntegrityError as e:
            raise IntegrityError(f"Violación de constraints en COPY: {e}") from e
        except psycopg2.OperationalError as e:
            raise OperationalError(f"Error operacional en COPY: {e}") from e
        except (OSError, IOError) as e:
            raise OperationalError(f"Error al leer archivo CSV: {e}") from e
        except psycopg2.Error as e:
            raise OperationalError(f"Error inesperado en COPY: {e}") from e
    
    def insert_batch(self, records: Sequence[Dict[str, Any]], table_name: str) -> int:
        """
        Inserta lote de registros usando execute_values.
        
        DECISIÓN DE DISEÑO: execute_values es más eficiente que executemany
        para lotes grandes, y maneja automáticamente la conversión de tipos.
        
        Args:
            records: Secuencia de diccionarios con datos a insertar.
            table_name: Nombre de la tabla destino.
        Returns:
            Número de filas insertadas.
        Raises:
            OperationalError: Si falla la inserción.
            IntegrityError: Si hay violación de constraints.
        """

        if not self._connection or self._connection.closed:
            raise OperationalError("No hay conexión activa para inserción")
        
        if not records:
            self._logger.warning("Lote vacío, no se realizan inserciones")
            return 0
        
        try:

            # ■■■■■■■■■■■■■ Extraer columnas del primer registro (asume estructura consistente) ■■■■■■■■■■■■■
            columns = list(records[0].keys())
            values = [tuple(record[col] for col in columns) for record in records]
            
            # ■■■■■■■■■■■■■ Construir query seguro usando sql.Composition ■■■■■■■■■■■■■
            query = sql.SQL("INSERT INTO {} ({}) VALUES %s").format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(map(sql.Identifier, columns))
            )
            
            cursor = self._connection.cursor()
            inserted = psycopg2.extras.execute_values(
                cursor,
                query,
                values,
                template=None,  # Usar template por defecto
                page_size=1000  # Tamaño de página para grandes lotes
            )
            
            self._logger.info(f"Batch insert completado: {len(records)} filas en {table_name}")
            return len(records)
            
        except psycopg2.IntegrityError as e:
            raise IntegrityError(f"Violación de constraints en batch insert: {e}") from e
        except psycopg2.OperationalError as e:
            raise OperationalError(f"Error operacional en batch insert: {e}") from e
        except (KeyError, ValueError) as e:
            raise OperationalError(f"Error en estructura de datos: {e}") from e
        except psycopg2.Error as e:
            raise OperationalError(f"Error inesperado en batch insert: {e}") from e
    
    def __enter__(self) -> "DBConnector":
        """
        Context manager entry point.
        """
        self.connect()
        self.begin()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit point con rollback automático.
        
        Args:
            exc_type: Tipo de excepción si ocurrió.
            exc_val: Valor de excepción si ocurrió.
            exc_tb: Traceback si ocurrió.
        """
        try:
            if exc_type is not None:

                # ■■■■■■■■■■■■■ Hubo excepción: hacer rollback ■■■■■■■■■■■■■
                self._logger.warning(f"Excepción detectada, haciendo rollback: {exc_val}")
                self.rollback()
            else:

                # ■■■■■■■■■■■■■ Esta bien: hacer commit ■■■■■■■■■■■■■
                self.commit()
        finally:

            # ■■■■■■■■■■■■■ Siempre cerrar conexión ■■■■■■■■■■■■■
            self.close()
    
    @property
    def is_connected(self) -> bool:
        """
        Verifica si hay conexión activa.
        """

        return (
            self._connection is not None 
            and not self._connection.closed
        )
    
    @property
    def connection_info(self) -> Dict[str, str]:
        """
        Retorna información de conexión sin credenciales.
        """

        return {
            "host": self._config["host"],
            "dbname": self._config["dbname"],
            "user": self._config["user"],
            "port": str(self._config.get("port", 5432))
        }


# ▁▂▃▄▅▆▇███████ Exportación pública ███████▇▆▅▄▃▂▁
__all__ = [
    "DBConnector",
    "DatabaseError",
    "IntegrityError", 
    "OperationalError",
    "ConfigurationError"
]