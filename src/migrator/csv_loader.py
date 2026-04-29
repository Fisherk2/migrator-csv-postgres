"""Orquestador de carga CSV con validación delegada y COPY optimizado.

Este módulo implementa el pipeline completo de ingestión de datos CSV a PostgreSQL:
- Lectura de archivos CSV con configuración de codificación y delimitadores
- Validación fila-a-fila usando validadores inyectados (Strategy Pattern)
- Ingestión optimizada usando COPY FROM con buffer en memoria
- Validación de constraints en base de datos (unicidad, foreign keys)
- Transferencia atómica con rollback en caso de errores

El módulo sigue el Principio de Inversión de Dependencias recibiendo
DBConnector y validadores como dependencias inyectadas.

Example:
    >>> from src.migrator.csv_loader import CSVLoader
    >>> from src.migrator.db_connector import DBConnector
    >>>
    >>> loader = CSVLoader()
    >>> db = DBConnector(host="localhost", user="postgres", password="secret", database="mydb")
    >>> db.connect()
    >>>
    >>> schema = {"id": "INTEGER", "name": "VARCHAR(100)", "email": "TEXT"}
    >>> validators = {"email": lambda v: (bool(re.match(r"[^@]+@[^@]+", v)), "Email inválido", "ejemplo@dominio.com")}
    >>>
    >>> temp_table = loader.load_csv_to_temp_table(
    ...     csv_path="data/customers.csv",
    ...     schema=schema,
    ...     validators=validators,
    ...     db_connector=db
    ... )
    >>>
    >>> stats = loader.validate_and_transfer(temp_table, "customers", schema, db)
    >>> print(f"Importados: {stats['imported']}, Rechazados: {stats['rejected']}")
"""

from __future__ import annotations

import csv
import io
import logging
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.migrator.db_connector import DBConnector


class CSVLoader:
    """Orquestador de carga CSV con validación delegada y COPY optimizado.

    Coordina el pipeline completo: lectura → validación → buffering → ingestión.
    Sigue el Principio de Inversión de Dependencias recibiendo DBConnector
    y validadores como dependencias inyectadas.

    El flujo de carga es:
    1. Validar acceso al archivo CSV
    2. Generar nombre único para tabla temporal
    3. Crear tabla temporal con estructura del esquema
    4. Leer y validar CSV fila-a-fila
    5. Ingestar filas válidas usando COPY FROM
    6. Validar constraints en base de datos
    7. Transferir a tabla destino o rollback

    Attributes:
        _logger: Logger configurado para este módulo.

    Example:
        >>> loader = CSVLoader()
        >>> temp_table = loader.load_csv_to_temp_table(
        ...     csv_path="data.csv",
        ...     schema={"name": "TEXT", "email": "TEXT"},
        ...     validators={},
        ...     db_connector=db
        ... )
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Inicializa el loader con logger configurado.

        Args:
            logger: Logger opcional. Si no se proporciona, usa
                logging.getLogger(__name__).

        Example:
            >>> import logging
            >>> logger = logging.getLogger("custom")
            >>> loader = CSVLoader(logger=logger)
        """
        self._logger = logger or logging.getLogger(__name__)
    
    def load_csv_to_temp_table(
        self,
        csv_path: str,
        schema: Dict[str, Any],
        validators: Dict[str, Any],
        db_connector: DBConnector,
        config: Optional[Dict[str, Any]] = None
    ) -> str:

        """
        Carga CSV a tabla temporal con validación fila-a-fila.
        
        DECISIÓN: Usar buffer en memoria + COPY para máximo rendimiento
        evitando escritura en disco y aprovechando optimización de PostgreSQL.
        
        Args:
            csv_path: Ruta al archivo CSV a procesar.
            schema: Diccionario con definición de esquema de la tabla destino.
            validators: Diccionario con reglas de validación por campo.
            db_connector: Conector a base de datos ya inicializado.
            config: Configuración opcional de carga incluyendo:
                - source.encoding: Codificación del archivo (default: utf-8-sig)
                - source.delimiter: Separador CSV (default: coma)
                - validation.max_errors_before_rollback: Límite de errores para abortar
                - validation.strict_mode: Si rechaza carga completa ante errores
            
        Returns:
            Nombre de la tabla temporal creada.
            
        Raises:
            FileNotFoundError: Si el archivo CSV no existe en la ruta especificada.
            PermissionError: Si no hay permisos de lectura sobre el archivo.
            ValueError: Si faltan encabezados requeridos en el CSV.
            Exception: Si falla la creación de tabla temporal o la ingestión.
            
        Example:
            >>> loader = CSVLoader()
            >>> db = DBConnector(config)
            >>> schema = {"id": "INTEGER", "name": "VARCHAR(100)"}
            >>> validators = {"email": {"type": "email"}}
            >>> temp_table = loader.load_csv_to_temp_table(
            ...     csv_path="data/customers.csv",
            ...     schema=schema,
            ...     validators=validators,
            ...     db_connector=db,
            ...     config={"source": {"encoding": "utf-8-sig"}}
            ... )
            >>> print(f"Tabla temporal: {temp_table}")
        """

        # ■■■■■■■■■■■■■ Validación de archivo y configuración ■■■■■■■■■■■■■
        self._validate_file_access(csv_path)
        config = config or {}
        encoding = config.get("source", {}).get("encoding", "utf-8-sig")
        delimiter = config.get("source", {}).get("delimiter", ",")
        max_errors = config.get("validation", {}).get("max_errors_before_rollback", 100)
        strict_mode = config.get("validation", {}).get("strict_mode", False)

        # ■■■■■■■■■■■■■ Extraer solo columns del schema YAML si existe ■■■■■■■■■■■■■
        columns_schema = schema.get('columns', schema) if isinstance(schema, dict) else schema

        # ■■■■■■■■■■■■■ Generar nombre de tabla temporal único ■■■■■■■■■■■■■
        temp_table = self._generate_temp_table_name(csv_path)

        # ■■■■■■■■■■■■■ Crear tabla temporal con misma estructura que destino ■■■■■■■■■■■■■
        # Para evitar problemas de tipo durante la validación
        self._create_temp_table(temp_table, schema, db_connector)
        
        try:

            # ■■■■■■■■■■■■■ Fase 1: Lectura y validación ■■■■■■■■■■■■■
            valid_rows, errors = self._read_and_validate_csv(
                csv_path, columns_schema, validators, encoding, delimiter, max_errors
            )
            
            # ■■■■■■■■■■■■■ Fail-fast si excede umbral de errores ■■■■■■■■■■■■■
            if len(errors) >= max_errors:
                self._logger.error(f"Abortando carga: {len(errors)} errores >= umbral {max_errors}")
                self.rollback_temp_table(temp_table, db_connector)
                return temp_table
            
            # ■■■■■■■■■■■■■ Fase 2: Ingestión con COPY optimizado ■■■■■■■■■■■■■
            if valid_rows:
                self._copy_rows_to_temp_table(
                    valid_rows, temp_table, delimiter, db_connector
                )
            else:
                self._logger.warning("No hay filas válidas para cargar")
            
            return temp_table
                
        except Exception as e:
            self._logger.error(f"Error durante carga a tabla temporal: {e}")
            self.rollback_temp_table(temp_table, db_connector)
            raise
    
    def validate_and_transfer(
        self,
        temp_table: str,
        target_table: str,
        schema: Dict[str, Any],
        db_connector: DBConnector
    ) -> Dict[str, Any]:
        """
        Valida datos en tabla temporal y transfiere a destino.
        
        DECISIÓN: Realizar validación final en BD para detectar
        inconsistencias que no se capturan en validación por fila.
        
        Args:
            temp_table: Tabla temporal con datos ya validados y cargados.
            target_table: Tabla destino final donde se persistirán los datos.
            schema: Diccionario con definición de columnas y constraints:
                - sql_type: Tipo de dato SQL para cada columna
                - required: Si la columna permite valores NULL
                - unique: Si la columna debe ser única
                - foreign_key: Referencia a otra tabla (opcional)
            db_connector: Conector a base de datos con transacción activa.
            
        Returns:
            Diccionario con estadísticas completas del proceso:
                - imported: Número de filas transferidas exitosamente
                - rejected: Número de filas rechazadas por errores
                - errors: Lista detallada de errores encontrados
                
        Example:
            >>> loader = CSVLoader()
            >>> stats = loader.validate_and_transfer(
            ...     temp_table="temp_customers",
            ...     target_table="customers", 
            ...     schema=customer_schema,
            ...     db_connector=db
            ... )
            >>> print(f"Importados: {stats['imported']}, Rechazados: {stats['rejected']}")
        """
        stats = {"imported": 0, "rejected": 0, "errors": []}
        
        try:

            # ■■■■■■■■■■■■■ Validación de integridad referencial y constraints ■■■■■■■■■■■■■
            validation_errors = self._validate_temp_table_data(
                temp_table, target_table, schema, db_connector
            )
            
            if validation_errors:
                stats["rejected"] = len(validation_errors)
                stats["errors"] = validation_errors
                self._logger.warning(f"Se encontraron {len(validation_errors)} errores de validación")
                
                # ▲▲▲▲▲▲ Opción de transferencia parcial o total según modo estricto ▲▲▲▲▲▲
                if not schema.get("validation", {}).get("strict_mode", False):

                    # ▲▲▲▲▲▲ Transferir solo filas válidas ▲▲▲▲▲▲
                    valid_count = self._transfer_valid_rows(
                        temp_table, target_table, validation_errors, db_connector
                    )
                    stats["imported"] = valid_count
                else:

                    # ▲▲▲▲▲▲ Modo estricto: rechazar completamente ▲▲▲▲▲▲
                    self._logger.error("Modo estricto: rechazando carga completa")
                    return stats
            else:

                # ▲▲▲▲▲▲ Transferencia completa si no hay errores ▲▲▲▲▲▲
                stats["imported"] = self._transfer_all_rows(
                    temp_table, target_table, db_connector
                )
            
            return stats
            
        except Exception as e:
            self._logger.error(f"Error en validación y transferencia: {e}")
            stats["errors"].append(f"Error crítico: {e}")
            return stats
    
    def rollback_temp_table(self, temp_table: str, db_connector: DBConnector) -> bool:
        """
        Limpia tabla temporal en caso de error.
        
        DECISIÓN: Usar DROP TABLE IF EXISTS para garantizar limpieza
        incluso si la tabla quedó en estado inconsistente.
        
        Args:
            temp_table: Nombre de tabla temporal a limpiar.
            db_connector: Conector a base de datos.
        Returns:
            True si la limpieza fue exitosa, False si hubo error.
        """

        try:
            cursor = db_connector.connection.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
            db_connector.commit()
            self._logger.info(f"Tabla temporal {temp_table} eliminada correctamente")
            return True
            
        except Exception as e:
            self._logger.error(f"Error al limpiar tabla temporal {temp_table}: {e}")
            return False
    
    def _validate_file_access(self, csv_path: str) -> None:
        """Valida existencia y permisos del archivo CSV.

        Realiza validaciones de seguridad antes de intentar leer el archivo
        para proporcionar mensajes de error claros y tempranos.

        Args:
            csv_path: Ruta al archivo CSV a validar.

        Raises:
            FileNotFoundError: Si el archivo no existe en la ruta especificada.
            ValueError: Si la ruta existe pero no corresponde a un archivo.
            PermissionError: Si el usuario no tiene permisos de lectura.

        Example:
            >>> loader._validate_file_access("/path/to/data.csv")  # OK
            >>> loader._validate_file_access("/nonexistent.csv")  # Raises FileNotFoundError
        """
        path = Path(csv_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {csv_path}")
        
        if not path.is_file():
            raise ValueError(f"Ruta no es un archivo: {csv_path}")
        
        if not os.access(csv_path, os.R_OK):
            raise PermissionError(f"Sin permisos de lectura: {csv_path}")
    
    def _generate_temp_table_name(self, csv_path: str) -> str:
        """Genera nombre único para tabla temporal basado en el archivo CSV.

        Usa timestamp con microsegundos y sufijo aleatorio para evitar colisiones
        en migraciones concurrentes sin hardcodear nombres.

        Args:
            csv_path: Ruta al archivo CSV. El nombre del archivo (sin extensión)
                se usa como base para el nombre de la tabla.

        Returns:
            Nombre de tabla temporal único en formato:
            'temp_{csv_name}_{timestamp}_{random_suffix}'.

        Example:
            >>> name = loader._generate_temp_table_name("data/customers.csv")
            >>> assert name.startswith("temp_customers_")
        """
        import time
        import random
        from pathlib import Path

        csv_name = Path(csv_path).stem
        timestamp = int(time.time() * 1000000)  # Microsegundos para unicidad
        random_suffix = random.randint(1000, 9999)
        return f"temp_{csv_name}_{timestamp}_{random_suffix}"
    
    def _create_temp_table(
        self,
        temp_table: str,
        schema: Dict[str, Any],
        db_connector: DBConnector
    ) -> None:
        """Crea tabla temporal con estructura del esquema.

        Soporta dos formatos de schema:
        - Directo: {'col1': 'INTEGER', 'col2': 'TEXT'}
        - YAML: {'columns': {'col1': {'type': 'integer'}, 'col2': {'type': 'string'}}}

        Mapea tipos YAML a tipos SQL automáticamente y agrega id SERIAL
        PRIMARY KEY si no está definido en el esquema.

        Args:
            temp_table: Nombre de la tabla temporal a crear.
            schema: Diccionario con definición de columnas y tipos SQL.
                Puede tener estructura YAML (con 'columns') o directa.
            db_connector: Conector a base de datos para ejecutar CREATE.

        Raises:
            Exception: Si falla la creación de la tabla temporal.

        Example:
            >>> schema = {'name': 'TEXT', 'age': 'INTEGER'}
            >>> loader._create_temp_table('temp_users', schema, db)
        """

        # ■■■■■■■■■■■■■ Manejar estructura de schema YAML o directa ■■■■■■■■■■■■■
        # Si el schema tiene clave 'columns', usar solo esa sección
        if isinstance(schema, dict) and 'columns' in schema:
            columns_dict = schema['columns']
        else:
            columns_dict = schema

        # ■■■■■■■■■■■■■ Mapeo de tipos YAML a tipos SQL ■■■■■■■■■■■■■
        type_mapping = {
            'integer': 'INTEGER',
            'string': 'TEXT',
            'email': 'TEXT',
            'phone': 'TEXT',
            'datetime': 'TIMESTAMP',
            'date': 'DATE',
            'decimal': 'DECIMAL',
            'boolean': 'BOOLEAN'
        }

        # ■■■■■■■■■■■■■ Construcción dinámica de CREATE TABLE basada en schema ■■■■■■■■■■■■■
        columns_sql = []
        has_id = False
        for col_name, col_def in columns_dict.items():
            if col_name == 'id':
                has_id = True
            if isinstance(col_def, str):
                # ▲▲▲▲▲▲ Caso simple: col_def es directamente el tipo SQL ▲▲▲▲▲▲
                col_type = col_def
                nullable = "NULL"
            else:
                # ▲▲▲▲▲▲ Caso YAML: col_def es un diccionario con propiedades ▲▲▲▲▲▲
                yaml_type = col_def.get("type", "text")
                col_type = type_mapping.get(yaml_type, "TEXT")
                nullable = "" if col_def.get("required", False) else "NULL"
            columns_sql.append(f"{col_name} {col_type} {nullable}")

        # Agregar id SERIAL PRIMARY KEY solo si no existe en el schema
        if not has_id:
            columns_sql.insert(0, "id SERIAL PRIMARY KEY")

        create_sql = f"""
            CREATE TEMPORARY TABLE {temp_table} (
                {', '.join(columns_sql)}
            )
        """

        try:
            cursor = db_connector.connection.cursor()
            cursor.execute(create_sql)
            db_connector.commit()
            self._logger.info(f"Tabla temporal {temp_table} creada")

        except Exception as e:
            self._logger.error(f"Error creando tabla temporal {temp_table}: {e}")
            raise
    
    def _read_and_validate_csv(
        self,
        csv_path: str,
        schema: Dict[str, Any],
        validators: Dict[str, Callable],
        encoding: str,
        delimiter: str,
        max_errors: int
    ) -> tuple[List[Dict[str, Any]], List[str]]:
        """
        Lee CSV y valida filas usando validadores inyectados.
        
        DECISIÓN: Validación temprana para fail-fast antes de ingestión masiva.
        Esto evita procesar archivos completos con errores estructurales.
        
        Args:
            csv_path: Ruta al archivo CSV a procesar.
            schema: Diccionario con estructura esperada de columnas.
            validators: Diccionario de funciones validadoras por campo.
            encoding: Codificación del archivo (default: utf-8-sig para BOM).
            delimiter: Delimitador del CSV (default: coma).
            max_errors: Máximo número de errores antes de abortar procesamiento.
            
        Returns:
            Tupla con (filas_válidas, lista_errores):
            - filas_válidas: Lista de diccionarios listos para ingestión
            - lista_errores: Mensajes de error con número de fila y campo
            
        Raises:
            ValueError: Si los encabezados no coinciden con el esquema.
            FileNotFoundError: Si el archivo no existe.
            PermissionError: Si no hay permisos de lectura.
            
        Example:
            >>> valid_rows, errors = loader._read_and_validate_csv(
            ...     "data.csv", {"name": {}, "email": {}}, 
            ...     {"email": validate_email_format}, "utf-8-sig", ",", 10
            ... )
            >>> print(f"Válidas: {len(valid_rows)}, Errores: {len(errors)}")
        """

        valid_rows = []
        errors = []
        
        with open(csv_path, 'r', encoding=encoding) as csv_file:
            reader = csv.DictReader(csv_file, delimiter=delimiter)
            
            # ■■■■■■■■■■■■■ Validar encabezados contra esquema ■■■■■■■■■■■■■
            expected_headers = set(schema.keys())
            actual_headers = set(reader.fieldnames or [])
            
            missing_headers = expected_headers - actual_headers
            if missing_headers:
                raise ValueError(f"Encabezados faltantes: {missing_headers}")
            
            for row_num, row in enumerate(reader, 1):

                # ▲▲▲▲▲▲ Ignorar filas completamente vacías ▲▲▲▲▲▲
                if all(not value.strip() for value in row.values()):
                    continue
                
                # ▲▲▲▲▲▲ Validación delegada usando Strategy Pattern ▲▲▲▲▲▲
                row_errors = self._validate_row(
                    row, schema, validators, row_num
                )
                
                if row_errors:
                    errors.extend(row_errors)
                    if len(errors) >= max_errors:
                        break
                else:
                    valid_rows.append(row)
        
        self._logger.info(f"Validación completada: {len(valid_rows)} válidas, {len(errors)} errores")
        return valid_rows, errors
    
    def _validate_row(
        self,
        row: Dict[str, str],
        schema: Dict[str, Any],
        validators: Dict[str, Callable],
        row_num: int
    ) -> List[str]:
        """Valida una fila usando validadores inyectados.

        Aplica validación Strategy Pattern: si existe un validador para un campo,
        lo usa; otherwise, aplica validación básica de tipo según el esquema.

        Los validadores deben retornar una tupla (is_valid, error_msg, suggestion).

        Args:
            row: Diccionario con valores de la fila CSV como strings.
            schema: Definición de campos esperados con tipos y restricciones.
            validators: Diccionario de funciones validadoras por campo.
            row_num: Número de fila para reporte de errores.

        Returns:
            Lista de mensajes de error encontrados en la fila. Cada mensaje
            incluye el número de fila, nombre del campo y descripción del error.

        Example:
            >>> row = {'name': 'John', 'email': 'invalid'}
            >>> schema = {'name': {'type': 'string'}, 'email': {'type': 'email'}}
            >>> validators = {'email': lambda v: (bool('@' in v), 'Email inválido', 'user@domain.com')}
            >>> errors = loader._validate_row(row, schema, validators, 1)
            >>> assert 'Fila 1, campo' in errors[0]
        """
        row_errors = []

        for field_name, field_def in schema.items():
            value = row.get(field_name)

            # ■■■■■■■■■■■■■ Validación de tipo y formato delegada ■■■■■■■■■■■■■
            if field_name in validators:
                try:
                    is_valid, error_msg, suggestion = validators[field_name](value)

                    if not is_valid:
                        error_detail = f"Fila {row_num}, campo '{field_name}': {error_msg}"
                        if suggestion:
                            error_detail += f" (Sugerencia: {suggestion})"
                        row_errors.append(error_detail)

                except Exception as e:
                    row_errors.append(f"Fila {row_num}, campo '{field_name}': Error en validador: {e}")
            else:
                # ■■■■■■■■■■■■■ Validación de tipo básica según schema ■■■■■■■■■■■■■
                field_type = field_def if isinstance(field_def, str) else field_def.get("type", "string")
                if field_type == "integer":
                    if value is not None and value != "":
                        try:
                            int(value)
                        except (ValueError, TypeError):
                            row_errors.append(f"Fila {row_num}, campo '{field_name}': '{value}' no es un entero válido")

        return row_errors
    
    def _copy_rows_to_temp_table(
        self,
        rows: List[Dict[str, Any]],
        temp_table: str,
        delimiter: str,
        db_connector: DBConnector
    ) -> int:
        """Usa COPY FROM con buffer en memoria para máxima performance.

        Construye un CSV en memoria usando StringIO y usa copy_expert de
        psycopg2 para ingestión optimizada, evitando escritura en disco.

        Args:
            rows: Lista de diccionarios con datos a insertar.
            temp_table: Tabla temporal destino.
            delimiter: Delimitador CSV para el buffer.
            db_connector: Conector a base de datos.

        Returns:
            Número de filas copiadas exitosamente.

        Raises:
            Exception: Si falla la operación COPY.

        Example:
            >>> rows = [{'name': 'John', 'age': '30'}, {'name': 'Jane', 'age': '25'}]
            >>> count = loader._copy_rows_to_temp_table(rows, 'temp_users', ',', db)
            >>> assert count == 2
        """

        # ■■■■■■■■■■■■■ StringIO buffer para evitar escritura en disco ■■■■■■■■■■■■■
        # y aprovechar optimización nativa de PostgreSQL
        
        buffer = io.StringIO()
        
        # ■■■■■■■■■■■■■ Construir CSV en memoria (sin encabezado para tabla existente) ■■■■■■■■■■■■■
        writer = csv.writer(buffer, delimiter=delimiter)
        for row in rows:
            writer.writerow(row.values())
        
        # ■■■■■■■■■■■■■ Reset buffer position para lectura ■■■■■■■■■■■■■
        buffer.seek(0)
        
        try:
            cursor = db_connector.connection.cursor()
            copy_sql = f"COPY {temp_table} FROM STDIN WITH (FORMAT csv)"
            
            cursor.copy_expert(copy_sql, buffer)
            rows_copied = cursor.rowcount
            
            db_connector.commit()
            self._logger.info(f"COPY completado: {rows_copied} filas a {temp_table}")
            
            return rows_copied
            
        except Exception as e:
            self._logger.error(f"Error en COPY FROM: {e}")
            db_connector.rollback()
            raise
        finally:
            buffer.close()
    
    def _validate_temp_table_data(
        self,
        temp_table: str,
        target_table: str,
        schema: Dict[str, Any],
        db_connector: DBConnector
    ) -> List[str]:
        """Valida datos en tabla temporal contra constraints de BD.

        Realiza validaciones que no se pueden hacer en validación por fila:
        - Unicidad de campos marcados como unique
        - Integridad referencial de foreign keys

        Usa target_table como referencia por defecto para FKs implícitas,
        permitiendo validaciones flexibles sin hardcodear nombres de tablas.

        Args:
            temp_table: Tabla temporal con datos a validar.
            target_table: Tabla destino final (usada como referencia por defecto).
            schema: Definición de campos y constraints incluyendo:
                - unique: Si el campo debe ser único
                - foreign_key: Diccionario con {table, column} o usa target_table por defecto
            db_connector: Conector a base de datos.

        Returns:
            Lista de mensajes de error encontrados. Cada error describe
            el constraint violado y los valores involucrados.

        Example:
            >>> schema = {
            ...     "customer_id": {"foreign_key": {"table": "customers", "column": "id"}},
            ...     "email": {"unique": True},
            ...     "order_id": {"foreign_key": {}}  # Usa target_table por defecto
            ... }
            >>> errors = loader._validate_temp_table_data(
            ...     "temp_orders", "orders", schema, db
            ... )
            >>> if errors:
            ...     print(f"Errores de validación: {errors}")
        """
        errors = []
        
        try:
            cursor = db_connector.connection.cursor()
            
            # ■■■■■■■■■■■■■ Verificar duplicados de campos únicos ■■■■■■■■■■■■■
            unique_fields = [
                field for field, defn in schema.items() 
                if defn.get("unique", False)
            ]
            
            for field in unique_fields:
                dup_query = f"""
                    SELECT {field}, COUNT(*) as count 
                    FROM {temp_table} 
                    GROUP BY {field} 
                    HAVING COUNT(*) > 1
                """
                cursor.execute(dup_query)
                duplicates = cursor.fetchall()
                
                for dup in duplicates:
                    errors.append(f"Duplicado encontrado en {field}: {dup[0]} ({dup[1]} ocurrencias)")
            
            # ■■■■■■■■■■■■■ Verificar foreign keys (si aplica) ■■■■■■■■■■■■■
            fk_fields = [
                field for field, defn in schema.items() 
                if defn.get("foreign_key")
            ]
            
            for field in fk_fields:
                fk_info = schema[field]["foreign_key"]

                # ■■■■■■■■■■■■■ Usar target_table como referencia por defecto si no se especifica ■■■■■■■■■■■■■
                # Esto permite FKs implícitas hacia la tabla destino principal
                ref_table = fk_info.get("table", target_table)
                ref_column = fk_info.get("column", "id")
                
                # ■■■■■■■■■■■■■ Validación de seguridad para SQL injection ■■■■■■■■■■■■■
                if not ref_table.replace("_", "").replace("-", "").isalnum():
                    errors.append(f"Nombre de tabla de referencia inválido: {ref_table}")
                    continue
                if not ref_column.replace("_", "").replace("-", "").isalnum():
                    errors.append(f"Nombre de columna de referencia inválido: {ref_column}")
                    continue
                
                fk_query = f"""
                    SELECT t.{field} 
                    FROM {temp_table} t 
                    LEFT JOIN {ref_table} f ON t.{field} = f.{ref_column}
                    WHERE f.{ref_column} IS NULL
                """
                cursor.execute(fk_query)
                invalid_fks = cursor.fetchall()
                
                for fk in invalid_fks:
                    errors.append(f"Referencia inválida en {field}: {fk[0]} → {ref_table}.{ref_column}")
            
            return errors
            
        except Exception as e:
            self._logger.error(f"Error en validación de tabla temporal: {e}")
            return [f"Error crítico en validación: {e}"]
    
    def _transfer_valid_rows(
        self,
        temp_table: str,
        target_table: str,
        validation_errors: List[str],
        db_connector: DBConnector
    ) -> int:
        """Transfiere solo filas válidas excluyendo las con errores.

        Extrae los IDs de filas inválidas desde los mensajes de error y construye
        una consulta INSERT con WHERE NOT IN para transferir solo las filas válidas.

        Args:
            temp_table: Tabla temporal con datos filtrados.
            target_table: Tabla destino final.
            validation_errors: Lista de errores para identificar filas inválidas.
            db_connector: Conector a base de datos.

        Returns:
            Número de filas transferidas exitosamente.

        Raises:
            Exception: Si falla la transferencia.
        """

        # ■■■■■■■■■■■■■ Implementar transferencia condicional basada en errores ■■■■■■■■■■■■■
        # Filtrar filas inválidas usando información de validation_errors
        
        try:
            cursor = db_connector.connection.cursor()
            
            # ■■■■■■■■■■■■■ Extraer IDs de filas inválidas desde mensajes de error ■■■■■■■■■■■■■
            invalid_ids = self._extract_invalid_row_ids(validation_errors, temp_table, cursor)
            
            if invalid_ids:

                # ▲▲▲▲▲▲ Construir WHERE clause para excluir filas inválidas ▲▲▲▲▲▲
                id_list = ",".join(str(id_) for id_ in invalid_ids)
                transfer_sql = f"""
                    INSERT INTO {target_table} 
                    SELECT * FROM {temp_table}
                    WHERE id NOT IN ({id_list})
                """
                self._logger.info(f"Excluyendo {len(invalid_ids)} filas inválidas de la transferencia")
            else:

                # ▲▲▲▲▲▲ Si no hay errores específicos, transferir completo ▲▲▲▲▲▲
                transfer_sql = f"""
                    INSERT INTO {target_table} 
                    SELECT * FROM {temp_table}
                """
                self._logger.info("No se encontraron filas inválidas específicas, transfiriendo todo")
            
            cursor.execute(transfer_sql)
            transferred = cursor.rowcount
            
            db_connector.commit()
            self._logger.info(f"Transferidas {transferred} filas válidas a {target_table}")
            
            return transferred
            
        except Exception as e:
            self._logger.error(f"Error en transferencia parcial: {e}")
            db_connector.rollback()
            raise
    
    def _extract_invalid_row_ids(
        self,
        validation_errors: List[str],
        temp_table: str,
        cursor
    ) -> List[int]:
        """Extrae IDs de filas inválidas desde mensajes de error.

        Parsea errores de validación para identificar filas específicas que deben
        ser excluidas de la transferencia. Soporta errores de FK y duplicados.

        Args:
            validation_errors: Lista de mensajes de error de validación.
            temp_table: Tabla temporal para consultar IDs si es necesario.
            cursor: Cursor de base de datos para consultas adicionales.

        Returns:
            Lista de IDs de filas inválidas a excluir (sin duplicados).
        """
        invalid_ids = []
        
        for error in validation_errors:

            # ■■■■■■■■■■■■■ Parsear errores de FK: "Referencia inválida en customer_id: 999 → customers.id" ■■■■■■■■■■■■■
            if "Referencia inválida" in error:
                fk_match = re.search(rf"Referencia inválida en \w+: (\d+)", error)
                if fk_match:
                    invalid_ids.append(int(fk_match.group(1)))
            
            # ■■■■■■■■■■■■■ Parsear errores de duplicados: "Duplicado encontrado en email: test@test.com (2 ocurrencias)" ■■■■■■■■■■■■■
            elif "Duplicado encontrado" in error:
                dup_match = re.search(rf"Duplicado encontrado en \w+: ([^)]+) \(", error)
                if dup_match:
                    field_value = dup_match.group(1).strip()

                    # ▲▲▲▲▲▲ Extraer campo del error ▲▲▲▲▲▲
                    field_match = re.search(rf"Duplicado encontrado en (\w+):", error)
                    if field_match:
                        field_name = field_match.group(1)

                        # ▲▲▲▲▲▲ Consultar IDs de filas con valor duplicado ▲▲▲▲▲▲
                        try:

                            # ▲▲▲▲▲▲ Validación de seguridad para nombre de campo ▲▲▲▲▲▲
                            if not field_name.replace("_", "").isalnum():
                                continue
                                
                            dup_query = f"""
                                SELECT id FROM {temp_table} 
                                WHERE {field_name} = %s
                            """
                            cursor.execute(dup_query, (field_value,))
                            dup_ids = [row[0] for row in cursor.fetchall()]
                            invalid_ids.extend(dup_ids)
                        except Exception as e:
                            self._logger.warning(f"No se pudieron obtener IDs duplicados para {field_name}: {e}")

        # ■■■■■■■■■■■■■ Eliminar duplicados y retornar lista única ■■■■■■■■■■■■■
        return list(set(invalid_ids))
    
    def _transfer_all_rows(
        self,
        temp_table: str,
        target_table: str,
        db_connector: DBConnector
    ) -> int:
        """Transfiere todas las filas de temporal a destino.

        Se usa cuando no hay errores de validación, permitiendo una transferencia
        completa con un solo INSERT SELECT para máxima eficiencia.

        Args:
            temp_table: Tabla temporal con todos los datos.
            target_table: Tabla destino final.
            db_connector: Conector a base de datos.

        Returns:
            Número de filas transferidas exitosamente.

        Raises:
            Exception: Si falla la transferencia completa.
        """
        try:
            cursor = db_connector.connection.cursor()
            
            transfer_sql = f"""
                INSERT INTO {target_table} 
                SELECT * FROM {temp_table}
            """
            
            cursor.execute(transfer_sql)
            transferred = cursor.rowcount
            
            db_connector.commit()
            self._logger.info(f"Transferidas {transferred} filas a {target_table}")
            
            return transferred
            
        except Exception as e:
            self._logger.error(f"Error en transferencia completa: {e}")
            db_connector.rollback()
            raise


# ▁▂▃▄▅▆▇███████ Exportación pública ███████▇▆▅▄▃▂▁
__all__ = ["CSVLoader"]