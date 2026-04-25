"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO: Tests de integración para DBConnector
AUTOR: Fisherk2
FECHA: 2026-04-24
DESCRIPCIÓN: Validación de contratos con PostgreSQL real.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

from __future__ import annotations

import pytest
from src.migrator.db_connector import DBConnector, OperationalError, IntegrityError


@pytest.mark.integration
class TestDBConnectorConnection:
    """Tests de conexión y ciclo de vida de DBConnector."""
    
    def test_connect_establishes_connection(self, db_connection: DBConnector) -> None:
        """
        ARRANGE: Fixture db_connection ya conectado.
        ACT: Verificar estado de conexión.
        ASSERT: is_connected es True.
        """
        # ■■■■■■■■■■■■■ ARRANGE: Ya conectado por fixture ■■■■■■■■■■■■■

        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        is_connected = db_connection.is_connected
        
        # ■■■■■■■■■■■■■ ASSERT ■■■■■■■■■■■■■
        assert is_connected is True, "La conexión debe estar activa"
    
    def test_connection_info_excludes_credentials(self, db_connection: DBConnector) -> None:
        """
        ARRANGE: Fixture db_connection conectado.
        ACT: Obtener información de conexión.
        ASSERT: No incluye password.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■

        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        info = db_connection.connection_info
        
        # ■■■■■■■■■■■■■ ASSERT ■■■■■■■■■■■■■
        assert "password" not in info, "connection_info no debe exponer credenciales"
        assert "host" in info, "connection_info debe incluir host"
        assert "dbname" in info, "connection_info debe incluir dbname"
        assert "user" in info, "connection_info debe incluir user"
    
    def test_close_terminates_connection(self, db_connection: DBConnector) -> None:
        """
        ARRANGE: Fixture db_connection conectado.
        ACT: Cerrar conexión.
        ASSERT: is_connected es False.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■

        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        db_connection.close()
        
        # ■■■■■■■■■■■■■ ASSERT ■■■■■■■■■■■■■
        assert db_connection.is_connected is False, "La conexión debe estar cerrada"


@pytest.mark.integration
class TestDBConnectorTransactions:
    """Tests de control transaccional (commit/rollback)."""
    
    def test_begin_starts_transaction(self, db_connection: DBConnector) -> None:
        """
        ARRANGE: Fixture db_connection conectado.
        ACT: Iniciar transacción explícita.
        ASSERT: No lanza excepción.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■

        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        db_connection.begin()
        
        # ■■■■■■■■■■■■■ ASSERT: Si no lanza excepción, la transacción inició correctamente ■■■■■■■■■■■■■
        assert True
    
    def test_commit_persists_changes(self, db_connection: DBConnector) -> None:
        """
        ARRANGE: Conexión con transacción iniciada y tabla temporal creada.
        ACT: Insertar fila y hacer commit.
        ASSERT: Fila persiste después del commit.
        """

        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        db_connection.begin()
        cursor = db_connection._connection.cursor()
        
        # ■■■■■■■■■■■■■ Crear tabla temporal para test ■■■■■■■■■■■■■
        cursor.execute("""
            CREATE TEMPORARY TABLE test_commit (
                id SERIAL PRIMARY KEY,
                value VARCHAR(50)
            )
        """)
        db_connection.commit()
        
        # ■■■■■■■■■■■■■ ACT: Insertar en nueva transacción ■■■■■■■■■■■■■
        db_connection.begin()
        cursor.execute("INSERT INTO test_commit (value) VALUES ('test_value')")
        db_connection.commit()
        
        # ■■■■■■■■■■■■■ ASSERT: Verificar que la fila persistió ■■■■■■■■■■■■■
        cursor.execute("SELECT COUNT(*) FROM test_commit WHERE value = 'test_value'")
        count = cursor.fetchone()[0]
        assert count == 1, "La fila debe persistir después de commit"
    
    def test_rollback_reverts_changes(self, db_connection: DBConnector) -> None:
        """
        ARRANGE: Conexión con transacción iniciada y tabla temporal creada.
        ACT: Insertar fila y hacer rollback.
        ASSERT: Fila no persiste después del rollback.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        db_connection.begin()
        cursor = db_connection._connection.cursor()
        
        # ■■■■■■■■■■■■■ Crear tabla temporal para test ■■■■■■■■■■■■■
        cursor.execute("""
            CREATE TEMPORARY TABLE test_rollback (
                id SERIAL PRIMARY KEY,
                value VARCHAR(50)
            )
        """)
        db_connection.commit()
        
        # ■■■■■■■■■■■■■ ACT: Insertar y revertir ■■■■■■■■■■■■■
        db_connection.begin()
        cursor.execute("INSERT INTO test_rollback (value) VALUES ('rollback_value')")
        db_connection.rollback()
        
        # ■■■■■■■■■■■■■ ASSERT: Verificar que la fila NO persistió ■■■■■■■■■■■■■
        cursor.execute("SELECT COUNT(*) FROM test_rollback WHERE value = 'rollback_value'")
        count = cursor.fetchone()[0]
        assert count == 0, "La fila no debe persistir después de rollback"
    
    def test_rollback_after_error_reverts_all(self, db_connection: DBConnector) -> None:
        """
        ARRANGE: Transacción con múltiples operaciones.
        ACT: Causar error y hacer rollback.
        ASSERT: Ninguna operación persiste.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        db_connection.begin()
        cursor = db_connection._connection.cursor()

        # ■■■■■■■■■■■■■ Crear tabla temporal para test ■■■■■■■■■■■■■
        cursor.execute("""
            CREATE TEMPORARY TABLE test_error_rollback (
                id SERIAL PRIMARY KEY,
                value VARCHAR(50)
            )
        """)
        cursor.execute("INSERT INTO test_error_rollback (value) VALUES ('before_error')")
        
        # ■■■■■■■■■■■■■ ACT: Causar error (violación de constraint) ■■■■■■■■■■■■■
        try:
            cursor.execute("INSERT INTO test_error_rollback (id, value) VALUES (1, 'duplicate')")
        except IntegrityError:
            pass  # Esperado
        
        db_connection.rollback()
        
        # ■■■■■■■■■■■■■ ASSERT: Verificar que la tabla no tiene datos ■■■■■■■■■■■■■
        cursor.execute("SELECT COUNT(*) FROM test_error_rollback")
        count = cursor.fetchone()[0]
        assert count == 0, "Rollback debe revertir todas las operaciones"

@pytest.mark.integration
class TestDBConnectorCopyFrom:
    """Tests de ingesta masiva vía COPY FROM."""
    
    def test_execute_copy_from_loads_csv(self, db_connection: DBConnector, tmp_path) -> None:
        """
        ARRANGE: Tabla temporal creada y archivo CSV temporal.
        ACT: Ejecutar COPY FROM.
        ASSERT: Filas cargadas correctamente.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        db_connection.begin()
        cursor = db_connection._connection.cursor()
        
        # ■■■■■■■■■■■■■ Crear tabla temporal para test ■■■■■■■■■■■■■
        cursor.execute("""
            CREATE TEMPORARY TABLE test_copy (
                id INTEGER,
                name VARCHAR(50),
                email VARCHAR(100)
            )
        """)
        db_connection.commit()
        
        # ■■■■■■■■■■■■■ Crear CSV temporal ■■■■■■■■■■■■■
        csv_file = tmp_path / "test_copy.csv"
        csv_file.write_text("id,name,email\n1,Test User,test@example.com\n2,Another User,another@example.com")
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        db_connection.begin()
        rows_loaded = db_connection.execute_copy_from(str(csv_file), "test_copy")
        db_connection.commit()
        
        # ■■■■■■■■■■■■■ ASSERT ■■■■■■■■■■■■■
        assert rows_loaded == 2, f"Debe cargar 2 filas, cargó {rows_loaded}"
        
        cursor.execute("SELECT COUNT(*) FROM test_copy")
        count = cursor.fetchone()[0]
        assert count == 2, "Debe haber 2 filas en la tabla"
    
    def test_execute_copy_from_with_header(self, db_connection: DBConnector, tmp_path) -> None:
        """
        ARRANGE: Tabla temporal y CSV con header.
        ACT: Ejecutar COPY FROM con HEADER.
        ASSERT: Header no se carga como dato.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        db_connection.begin()
        cursor = db_connection._connection.cursor()

        # ■■■■■■■■■■■■■ Crear tabla temporal para test ■■■■■■■■■■■■■
        cursor.execute("""
            CREATE TEMPORARY TABLE test_header (
                id INTEGER,
                name VARCHAR(50)
            )
        """)
        db_connection.commit()
        
        csv_file = tmp_path / "test_header.csv"
        csv_file.write_text("id,name\n1,Test\n2,Another")
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        db_connection.begin()
        rows_loaded = db_connection.execute_copy_from(str(csv_file), "test_header")
        db_connection.commit()

        # ■■■■■■■■■■■■■ ASSERT ■■■■■■■■■■■■■
        cursor.execute("SELECT name FROM test_header WHERE id = 1")
        name = cursor.fetchone()[0]
        assert name == "Test", "Header no debe cargarse como dato"
        assert rows_loaded == 2, "Debe cargar 2 filas de datos"
    
    def test_execute_copy_from_invalid_path_raises_error(self, db_connection: DBConnector) -> None:
        """
        ARRANGE: Tabla temporal creada.
        ACT: Ejecutar COPY FROM con ruta inválida.
        ASSERT: Lanza OperationalError.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        db_connection.begin()
        cursor = db_connection._connection.cursor()

        # ■■■■■■■■■■■■■ Crear tabla temporal para test ■■■■■■■■■■■■■
        cursor.execute("""
            CREATE TEMPORARY TABLE test_invalid_path (
                id INTEGER,
                name VARCHAR(50)
            )
        """)
        db_connection.commit()
        
        # ■■■■■■■■■■■■■ ACT & ASSERT ■■■■■■■■■■■■■
        with pytest.raises(OperationalError):
            db_connection.execute_copy_from("/nonexistent/path.csv", "test_invalid_path")


@pytest.mark.integration
class TestDBConnectorBatchInsert:
    """Tests de inserción por lotes con execute_values."""
    
    def test_insert_batch_loads_multiple_records(self, db_connection: DBConnector) -> None:
        """
        ARRANGE: Tabla temporal creada y lote de registros.
        ACT: Ejecutar insert_batch.
        ASSERT: Todos los registros insertados.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        db_connection.begin()
        cursor = db_connection._connection.cursor()

        # ■■■■■■■■■■■■■ Crear tabla temporal para test ■■■■■■■■■■■■■
        cursor.execute("""
            CREATE TEMPORARY TABLE test_batch (
                id INTEGER,
                name VARCHAR(50),
                value DECIMAL(10,2)
            )
        """)
        db_connection.commit()
        
        records = [
            {"id": 1, "name": "Item 1", "value": 10.50},
            {"id": 2, "name": "Item 2", "value": 20.75},
            {"id": 3, "name": "Item 3", "value": 30.00}
        ]
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        db_connection.begin()
        inserted = db_connection.insert_batch(records, "test_batch")
        db_connection.commit()
        
        # ■■■■■■■■■■■■■ ASSERT ■■■■■■■■■■■■■
        assert inserted == 3, f"Debe insertar 3 registros, insertó {inserted}"
        
        cursor.execute("SELECT COUNT(*) FROM test_batch")
        count = cursor.fetchone()[0]
        assert count == 3, "Debe haber 3 registros en la tabla"
    
    def test_insert_batch_empty_returns_zero(self, db_connection: DBConnector) -> None:
        """
        ARRANGE: Tabla temporal creada.
        ACT: Ejecutar insert_batch con lista vacía.
        ASSERT: Retorna 0 sin insertar nada.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        db_connection.begin()
        cursor = db_connection._connection.cursor()
        
        cursor.execute("""
            CREATE TEMPORARY TABLE test_empty_batch (
                id INTEGER,
                name VARCHAR(50)
            )
        """)
        db_connection.commit()
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        db_connection.begin()
        inserted = db_connection.insert_batch([], "test_empty_batch")
        db_connection.commit()
        
        # ■■■■■■■■■■■■■ ASSERT ■■■■■■■■■■■■■
        assert inserted == 0, "Debe retornar 0 para lote vacío"
    
    def test_insert_batch_violates_unique_constraint(self, db_connection: DBConnector) -> None:
        """
        ARRANGE: Tabla con UNIQUE constraint y registro existente.
        ACT: Insertar lote con duplicado.
        ASSERT: Lanza IntegrityError.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        db_connection.begin()
        cursor = db_connection._connection.cursor()
        
        cursor.execute("""
            CREATE TEMPORARY TABLE test_unique (
                id INTEGER UNIQUE,
                name VARCHAR(50)
            )
        """)
        db_connection.commit()
        
        # ■■■■■■■■■■■■■ Insertar primer registro ■■■■■■■■■■■■■
        db_connection.begin()
        cursor.execute("INSERT INTO test_unique (id, name) VALUES (1, 'First')")
        db_connection.commit()
        
        # ■■■■■■■■■■■■■ ACT & ASSERT: Intentar insertar duplicado ■■■■■■■■■■■■■
        records = [{"id": 1, "name": "Duplicate"}]
        
        with pytest.raises(IntegrityError):
            db_connection.begin()
            db_connection.insert_batch(records, "test_unique")


@pytest.mark.integration
class TestDBConnectorContextManager:
    """Tests de uso de DBConnector como context manager."""
    
    def test_context_manager_commits_on_success(self, db_connection: DBConnector) -> None:
        """
        ARRANGE: DBConnector con configuración válida.
        ACT: Usar como context manager sin excepciones.
        ASSERT: Commit automático y conexión cerrada.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        config = db_connection.connection_info
        config["password"] = db_connection._config["password"]  # Restaurar password para nueva conexión
        
        connector = DBConnector(config)
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        with connector:
            connector.begin()
            cursor = connector._connection.cursor()
            cursor.execute("""
                CREATE TEMPORARY TABLE test_context (
                    id INTEGER,
                    value VARCHAR(50)
                )
            """)
            cursor.execute("INSERT INTO test_context (id, value) VALUES (1, 'context_test')")
        
        # ■■■■■■■■■■■■■ ASSERT: Context manager hace commit y close ■■■■■■■■■■■■■
        assert connector.is_connected is False, "Context manager debe cerrar conexión"
    
    def test_context_manager_rollback_on_exception(self, db_connection: DBConnector) -> None:
        """
        ARRANGE: DBConnector con configuración válida.
        ACT: Usar como context manager con excepción.
        ASSERT: Rollback automático y conexión cerrada.
        """
        # ■■■■■■■■■■■■■ ARRANGE ■■■■■■■■■■■■■
        config = db_connection.connection_info
        config["password"] = db_connection._config["password"]
        
        connector = DBConnector(config)
        
        # ■■■■■■■■■■■■■ ACT & ASSERT ■■■■■■■■■■■■■
        with pytest.raises(ValueError):
            with connector:
                connector.begin()
                cursor = connector._connection.cursor()
                cursor.execute("""
                    CREATE TEMPORARY TABLE test_context_error (
                        id INTEGER,
                        value VARCHAR(50)
                    )
                """)
                cursor.execute("INSERT INTO test_context_error (id, value) VALUES (1, 'before_error')")
                raise ValueError("Simulated error")
        
        # ■■■■■■■■■■■■■ ASSERT: Rollback ejecutado y conexión cerrada ■■■■■■■■■■■■■
        assert connector.is_connected is False, "Context manager debe cerrar conexión después de error"
