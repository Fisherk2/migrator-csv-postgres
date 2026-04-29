"""Repository/Adapter que aísla psycopg2 del dominio.

Este módulo implementa el patrón Repository para abstraer la complejidad
de psycopg2 y proporcionar una interfaz limpia para operaciones de base
de datos PostgreSQL. Gestiona el ciclo de vida de conexiones, transacciones
y operaciones de ingesta siguiendo el Principio de Inversión de Dependencias.

El módulo define excepciones de dominio para aislar errores específicos de
psycopg2 y facilitar el manejo de errores en capas superiores.

Example:
    >>> from src.migrator.db_connector import DBConnector
    >>>
    >>> config = {
    ...     "host": "localhost",
    ...     "dbname": "mydb",
    ...     "user": "postgres",
    ...     "password": "secret",
    ...     "port": 5432
    ... }
    >>> db = DBConnector(config)
    >>> db.connect()
    >>> db.begin_transaction()
    >>> # ... operaciones ...
    >>> db.commit()
    >>> db.close()
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
    """Repository/Adapter que aísla psycopg2 del dominio.

    Gestiona ciclo de vida de conexión, transacciones y operaciones de ingesta
    contra PostgreSQL, siguiendo el Principio de Inversión de Dependencias.

    Autocommit está desactivado para permitir control explícito de transacciones
    desde el pipeline de migración.

    Attributes:
        _config: Configuración de conexión (host, dbname, user, password, port).
        _connection: Conexión psycopg2 activa o None.
        _logger: Logger configurado para este módulo.

    Example:
        >>> config = {"host": "localhost", "dbname": "mydb", "user": "postgres", "password": "secret"}
        >>> db = DBConnector(config)
        >>> db.connect()
        >>> db.begin_transaction()
        >>> db.execute("SELECT 1")
        >>> db.commit()
        >>> db.close()
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Inicializa el connector con configuración de conexión.

        Args:
            config: Diccionario con claves requeridas: host, dbname, user, password.
                Clave opcional: port (default: 5432).

        Raises:
            ConfigurationError: Si faltan claves requeridas (host, dbname, user, password).

        Example:
            >>> config = {"host": "localhost", "dbname": "mydb", "user": "postgres", "password": "secret"}
            >>> db = DBConnector(config)
        """
        self._validate_config(config)
        self._config = config.copy()  # Evitar mutación externa
        self._connection: Optional[connection] = None
        self._logger = logging.getLogger(__name__)
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Valida configuración mínima requerida.

        Args:
            config: Configuración de conexión a base de datos.

        Raises:
            ConfigurationError: Si faltan claves requeridas.
        """

        required_keys = {"host", "dbname", "user", "password"}
        missing_keys = required_keys - set(config.keys())

        if missing_keys:
            raise ConfigurationError(
                f"Configuración incompleta. Faltan claves: {', '.join(missing_keys)}"
            )

    @property
    def connection(self) -> connection:
        """Propiedad pública para acceder a la conexión psycopg2.

        Exponer la conexión permite pruebas de integración que necesitan
        acceso directo al cursor y control de transacciones.

        Returns:
            Conexión psycopg2 activa.

        Raises:
            OperationalError: Si no hay conexión activa.

        Example:
            >>> db.connect()
            >>> cursor = db.connection.cursor()
            >>> cursor.execute("SELECT 1")
        """
        if self._connection is None:
            raise OperationalError("No hay conexión activa. Llame a connect() primero.")
        return self._connection
    
    def connect(self) -> None:
        """Establece conexión a PostgreSQL.

        Autocommit está desactivado para permitir control explícito de
        transacciones desde el pipeline de migración.

        Raises:
            OperationalError: Si falla la conexión a PostgreSQL.

        Example:
            >>> db.connect()
            >>> assert db.is_connected
        """

        try:
            # ■■■■■■■■■■■■■ DECISIÓN DE DISEÑO: autocommit=False para control explícito ■■■■■■■■■■■■■
            self._connection = psycopg2.connect(
                host=self._config["host"],
                database=self._config["dbname"],
                user=self._config["user"],
                password=self._config["password"],
                port=self._config.get("port", 5432)
            )
            self._connection.autocommit = False
            self._logger.info("Conexión establecida con PostgreSQL")

        except psycopg2.OperationalError as e:
            raise OperationalError(f"Error de conexión a PostgreSQL: {e}") from e
        except psycopg2.Error as e:
            raise OperationalError(f"Error inesperado al conectar: {e}") from e
    
    def close(self) -> None:
        """Cierra la conexión y limpia recursos.

        Es seguro llamar este método incluso si la conexión ya está cerrada.
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
        """Inicia una transacción explícita.

        Establece autocommit=False para permitir control manual de commit/rollback.

        Raises:
            OperationalError: Si no hay conexión activa.

        Example:
            >>> db.connect()
            >>> db.begin()
            >>> # ... operaciones ...
            >>> db.commit()
        """

        if not self._connection or self._connection.closed:
            raise OperationalError("No hay conexión activa para iniciar transacción")
        
        try:
            self._connection.autocommit = False
            self._logger.debug("Transacción iniciada")
        except psycopg2.Error as e:
            raise OperationalError(f"Error al iniciar transacción: {e}") from e
    
    def commit(self) -> None:
        """Confirma la transacción actual.

        Raises:
            OperationalError: Si no hay conexión activa.

        Example:
            >>> db.begin()
            >>> # ... operaciones ...
            >>> db.commit()
        """

        if not self._connection or self._connection.closed:
            raise OperationalError("No hay conexión activa para confirmar")
        
        try:
            self._connection.commit()
            self._logger.debug("Transacción confirmada")
        except psycopg2.Error as e:
            raise OperationalError(f"Error al confirmar transacción: {e}") from e
    
    def rollback(self) -> None:
        """Revierte la transacción actual.

        Raises:
            OperationalError: Si no hay conexión activa.

        Example:
            >>> db.begin()
            >>> # ... operaciones ...
            >>> db.rollback()
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

        Usa copy_expert para máximo rendimiento en archivos grandes, evitando
        overhead de Python. El formato CSV con HEADER true asume que el archivo
        tiene encabezados que coinciden con los nombres de columnas.

        Args:
            csv_path: Ruta al archivo CSV.
            table_name: Nombre de la tabla destino.

        Returns:
            Número de filas procesadas.

        Raises:
            OperationalError: Si falla el COPY.
            IntegrityError: Si hay violación de constraints.

        Example:
            >>> db.connect()
            >>> db.begin()
            >>> count = db.execute_copy_from("data.csv", "customers")
            >>> db.commit()
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
        """Inserta lote de registros usando execute_values.

        execute_values es más eficiente que executemany para lotes grandes
        y maneja automáticamente la conversión de tipos. Usa sql.Composition
        para prevenir SQL injection en nombres de tabla y columnas.

        Args:
            records: Secuencia de diccionarios con datos a insertar.
            table_name: Nombre de la tabla destino.

        Returns:
            Número de filas insertadas.

        Raises:
            OperationalError: Si falla la inserción.
            IntegrityError: Si hay violación de constraints.

        Example:
            >>> records = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
            >>> db.insert_batch(records, "users")
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
        """Context manager entry point.

        Establece conexión e inicia transacción automáticamente.

        Returns:
            Instancia de DBConnector para uso en bloque with.

        Example:
            >>> with DBConnector(config) as db:
            ...     db.execute("SELECT 1")
            ...     # Commit automático al salir del bloque
        """
        self.connect()
        self.begin()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit point con rollback automático.

        Si ocurre una excepción, hace rollback. Si no, hace commit.
        Siempre cierra la conexión en el bloque finally.

        Args:
            exc_type: Tipo de excepción si ocurrió.
            exc_val: Valor de excepción si ocurrió.
            exc_tb: Traceback si ocurrió.

        Example:
            >>> with DBConnector(config) as db:
            ...     db.execute("SELECT 1")
            ... # Commit automático, rollback si hay excepción
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
        """Verifica si hay conexión activa.

        Returns:
            True si la conexión está activa y no cerrada, False en caso contrario.

        Example:
            >>> db.connect()
            >>> assert db.is_connected
            >>> db.close()
            >>> assert not db.is_connected
        """

        return (
            self._connection is not None 
            and not self._connection.closed
        )
    
    @property
    def connection_info(self) -> Dict[str, str]:
        """Retorna información de conexión sin credenciales.

        Útil para logging y debugging sin exponer información sensible.

        Returns:
            Diccionario con host, dbname, user y port.

        Example:
            >>> db.connect()
            >>> info = db.connection_info
            >>> assert "password" not in info
            >>> assert "host" in info
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