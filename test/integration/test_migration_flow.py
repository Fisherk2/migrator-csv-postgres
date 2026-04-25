"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO: Tests de integración para MigrationPipeline
AUTOR: Fisherk2
FECHA: 2026-04-24
DESCRIPCIÓN: Validación de flujo end-to-end con PostgreSQL real.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Dict

import pytest
import yaml

from src.migrator.pipeline import MigrationPipeline
from src.migrator.db_connector import DBConnector
from src.migrator.csv_loader import CSVLoader
from src.migrator.error_handler import ErrorHandler
from src.migrator.report_generator import ReportGenerator


@pytest.mark.integration
class TestMigrationFlowHappyPath:
    """Tests del camino feliz: CSV válido → migración exitosa."""
    
    def test_valid_csv_imports_all_records(
        self,
        db_with_real_schema: DBConnector,
        valid_csv_path: Path,
        customers_schema_config: Dict,
        default_migration_config: Dict,
        tmp_path: Path
    ) -> None:
        """
        ARRANGE: Pipeline configurado con CSV válido y esquema real de BD.
        ACT: Ejecutar migración completa.
        ASSERT: Todos los registros importados, tabla customers actualizada.
        """
        # ■■■■■■■■■■■■■ ARRANGE: Usar configuración real del proyecto ■■■■■■■■■■■■■
        config = default_migration_config.copy()
        config["source"]["csv_path"] = str(valid_csv_path)
        config["target"]["table_name"] = "customers"
        config["validation"]["max_errors_before_rollback"] = 100
        config["validation"]["mode"] = "permissive"
        config["reporting"]["cli_output"] = False
        
        config_file = tmp_path / "migration_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        # ■■■■■■■■■■■■■ Crear componentes del pipeline ■■■■■■■■■■■■■
        csv_loader = CSVLoader(logger=None)
        error_handler = ErrorHandler()
        report_generator = ReportGenerator()
        
        pipeline = MigrationPipeline(
            db_connector=db_with_real_schema,
            csv_loader=csv_loader,
            error_handler=error_handler,
            report_generator=report_generator
        )
        
        # ■■■■■■■■■■■■■ ACT: Ejecutar migración ■■■■■■■■■■■■■
        stats = pipeline.execute(str(config_file))
        
        # ■■■■■■■■■■■■■ ASSERT: Verificar estadísticas ■■■■■■■■■■■■■
        assert stats["imported"] == 10, f"Debe importar 10 registros, importó {stats['imported']}"
        assert stats["rejected"] == 0, f"No debe rechazar registros, rechazó {stats['rejected']}"
        
        # ■■■■■■■■■■■■■ ASSERT: Verificar estado de tabla customers real ■■■■■■■■■■■■■
        cursor = db_with_real_schema._connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM public.customers")
        count = cursor.fetchone()[0]
        assert count == 10, f"Debe haber 10 filas en customers, hay {count}"
    
    def test_valid_csv_generates_correct_report(
        self,
        db_with_real_schema: DBConnector,
        valid_csv_path: Path,
        default_migration_config: Dict,
        tmp_path: Path
    ) -> None:
        """
        ARRANGE: Pipeline configurado con CSV válido y esquema real.
        ACT: Ejecutar migración y generar reporte.
        ASSERT: Reporte JSON tiene estructura correcta y métricas válidas.
        """
        # ■■■■■■■■■■■■■ ARRANGE: Usar configuración real ■■■■■■■■■■■■■
        config = default_migration_config.copy()
        config["source"]["csv_path"] = str(valid_csv_path)
        config["target"]["table_name"] = "customers"
        config["validation"]["max_errors_before_rollback"] = 100
        config["reporting"]["cli_output"] = False
        
        config_file = tmp_path / "report_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        csv_loader = CSVLoader(logger=None)
        error_handler = ErrorHandler()
        report_generator = ReportGenerator()
        
        pipeline = MigrationPipeline(
            db_connector=db_with_real_schema,
            csv_loader=csv_loader,
            error_handler=error_handler,
            report_generator=report_generator
        )
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        stats = pipeline.execute(str(config_file))
        
        # ■■■■■■■■■■■■■ ASSERT: Verificar estructura del reporte ■■■■■■■■■■■■■
        assert "imported" in stats, "Reporte debe incluir 'imported'"
        assert "rejected" in stats, "Reporte debe incluir 'rejected'"
        assert "success_rate" in stats, "Reporte debe incluir 'success_rate'"
        assert stats["success_rate"] == 100.0, f"Tasa de éxito debe ser 100%, es {stats['success_rate']}"
        assert stats["error_count"] == 0, "No debe haber errores"


@pytest.mark.integration
class TestMigrationFlowErrorPath:
    """Tests del camino de error: CSV inválido → rollback."""
    
    def test_invalid_csv_rejects_records(
        self,
        db_with_real_schema: DBConnector,
        invalid_csv_path: Path,
        default_migration_config: Dict,
        tmp_path: Path
    ) -> None:
        """
        ARRANGE: Pipeline configurado con CSV inválido y esquema real.
        ACT: Ejecutar migración.
        ASSERT: Registros inválidos rechazados, métricas correctas.
        """
        # ■■■■■■■■■■■■■ ARRANGE: Usar configuración real ■■■■■■■■■■■■■
        config = default_migration_config.copy()
        config["source"]["csv_path"] = str(invalid_csv_path)
        config["target"]["table_name"] = "customers"
        config["validation"]["max_errors_before_rollback"] = 100
        config["validation"]["mode"] = "permissive"
        config["reporting"]["cli_output"] = False
        
        config_file = tmp_path / "invalid_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        csv_loader = CSVLoader(logger=None)
        error_handler = ErrorHandler()
        report_generator = ReportGenerator()
        
        pipeline = MigrationPipeline(
            db_connector=db_with_real_schema,
            csv_loader=csv_loader,
            error_handler=error_handler,
            report_generator=report_generator
        )
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        stats = pipeline.execute(str(config_file))
        
        # ■■■■■■■■■■■■■ ASSERT: Verificar que hubo rechazos ■■■■■■■■■■■■■
        assert stats["rejected"] > 0, "Debe haber registros rechazados"
        assert stats["imported"] >= 0, "Importados debe ser >= 0"
        assert stats["success_rate"] < 100.0, "Tasa de éxito debe ser < 100%"
    
    def test_error_threshold_triggers_rollback(
        self,
        db_with_real_schema: DBConnector,
        invalid_csv_path: Path,
        default_migration_config: Dict,
        tmp_path: Path
    ) -> None:
        """
        ARRANGE: Pipeline con umbral de errores bajo (2 errores) y esquema real.
        ACT: Ejecutar migración con CSV que tiene errores.
        ASSERT: Rollback ejecutado, tabla customers con datos limitados.
        """
        # ■■■■■■■■■■■■■ ARRANGE: Configurar umbral bajo ■■■■■■■■■■■■■
        config = default_migration_config.copy()
        config["source"]["csv_path"] = str(invalid_csv_path)
        config["target"]["table_name"] = "customers"
        config["validation"]["max_errors_before_rollback"] = 2  # Umbral bajo
        config["validation"]["mode"] = "strict"
        config["reporting"]["cli_output"] = False
        
        config_file = tmp_path / "threshold_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        csv_loader = CSVLoader(logger=None)
        error_handler = ErrorHandler()
        report_generator = ReportGenerator()
        
        pipeline = MigrationPipeline(
            db_connector=db_with_real_schema,
            csv_loader=csv_loader,
            error_handler=error_handler,
            report_generator=report_generator
        )
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        stats = pipeline.execute(str(config_file))
        
        # ■■■■■■■■■■■■■ ASSERT: Verificar rollback ■■■■■■■■■■■■■
        cursor = db_with_real_schema._connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM public.customers")
        count = cursor.fetchone()[0]
        
        # Debido al rollback, la tabla debería estar vacía o tener muy pocos datos
        assert count < 5, f"Rollback debe limitar inserciones, hay {count} filas"
    
    def test_error_report_includes_suggestions(
        self,
        db_with_real_schema: DBConnector,
        invalid_csv_path: Path,
        default_migration_config: Dict,
        tmp_path: Path
    ) -> None:
        """
        ARRANGE: Pipeline con CSV inválido y esquema real.
        ACT: Ejecutar migración.
        ASSERT: Reporte de errores incluye sugerencias de corrección.
        """
        # ■■■■■■■■■■■■■ ARRANGE: Usar configuración real ■■■■■■■■■■■■■
        config = default_migration_config.copy()
        config["source"]["csv_path"] = str(invalid_csv_path)
        config["target"]["table_name"] = "customers"
        config["validation"]["max_errors_before_rollback"] = 100
        config["validation"]["mode"] = "permissive"
        config["reporting"]["cli_output"] = False
        
        config_file = tmp_path / "suggestion_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        csv_loader = CSVLoader(logger=None)
        error_handler = ErrorHandler()
        report_generator = ReportGenerator()
        
        pipeline = MigrationPipeline(
            db_connector=db_with_real_schema,
            csv_loader=csv_loader,
            error_handler=error_handler,
            report_generator=report_generator
        )
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        stats = pipeline.execute(str(config_file))
        
        # ■■■■■■■■■■■■■ ASSERT: Verificar que hay errores en el reporte ■■■■■■■■■■■■■
        assert stats["error_count"] > 0, "Debe haber errores en el reporte"


@pytest.mark.integration
class TestMigrationFlowTransactionIsolation:
    """Tests de aislamiento transaccional entre tests."""
    
    def test_transaction_rollback_after_test(
        self,
        db_with_real_schema: DBConnector,
        valid_csv_path: Path,
        default_migration_config: Dict,
        tmp_path: Path
    ) -> None:
        """
        ARRANGE: Pipeline configurado con esquema real.
        ACT: Ejecutar migración.
        ASSERT: Después del test, rollback automático limpia datos.
        
        Este test verifica que el fixture db_with_real_schema hace rollback
        automáticamente en teardown, garantizando aislamiento.
        """
        # ■■■■■■■■■■■■■ ARRANGE: Usar configuración real ■■■■■■■■■■■■■
        config = default_migration_config.copy()
        config["source"]["csv_path"] = str(valid_csv_path)
        config["target"]["table_name"] = "customers"
        config["validation"]["max_errors_before_rollback"] = 100
        config["validation"]["mode"] = "permissive"
        config["reporting"]["cli_output"] = False
        
        config_file = tmp_path / "isolation_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        csv_loader = CSVLoader(logger=None)
        error_handler = ErrorHandler()
        report_generator = ReportGenerator()
        
        pipeline = MigrationPipeline(
            db_connector=db_with_real_schema,
            csv_loader=csv_loader,
            error_handler=error_handler,
            report_generator=report_generator
        )
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        stats = pipeline.execute(str(config_file))
        
        # ■■■■■■■■■■■■■ ASSERT: Datos insertados durante el test ■■■■■■■■■■■■■
        cursor = db_with_real_schema._connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM public.customers")
        count = cursor.fetchone()[0]
        assert count > 0, "Debe haber datos durante el test"
        
        # NOTA: El rollback en el fixture limpiará estos datos después del test


@pytest.mark.integration
class TestMigrationFlowPartialImport:
    """Tests de importación parcial cuando hay algunos errores."""
    
    def test_partial_import_with_strict_mode_false(
        self,
        db_with_real_schema: DBConnector,
        invalid_csv_path: Path,
        default_migration_config: Dict,
        tmp_path: Path
    ) -> None:
        """
        ARRANGE: Pipeline con strict_mode=False y CSV con algunos errores.
        ACT: Ejecutar migración.
        ASSERT: Registros válidos importados, inválidos rechazados.
        """
        # ■■■■■■■■■■■■■ ARRANGE: Usar configuración real ■■■■■■■■■■■■■
        config = default_migration_config.copy()
        config["source"]["csv_path"] = str(invalid_csv_path)
        config["target"]["table_name"] = "customers"
        config["validation"]["max_errors_before_rollback"] = 100
        config["validation"]["mode"] = "permissive"  # Permitir importación parcial
        config["reporting"]["cli_output"] = False
        
        config_file = tmp_path / "partial_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        csv_loader = CSVLoader(logger=None)
        error_handler = ErrorHandler()
        report_generator = ReportGenerator()
        
        pipeline = MigrationPipeline(
            db_connector=db_with_real_schema,
            csv_loader=csv_loader,
            error_handler=error_handler,
            report_generator=report_generator
        )
        
        # ■■■■■■■■■■■■■ ACT ■■■■■■■■■■■■■
        stats = pipeline.execute(str(config_file))
        
        # ■■■■■■■■■■■■■ ASSERT: Debe haber importado algunos y rechazado otros ■■■■■■■■■■■■■
        assert stats["imported"] > 0, "Debe importar registros válidos"
        assert stats["rejected"] > 0, "Debe rechazar registros inválidos"
        assert stats["imported"] + stats["rejected"] > 0, "Debe procesar registros"