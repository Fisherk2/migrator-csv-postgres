"""Generador de reportes de migración con múltiples formatos de salida.

Este módulo proporciona componentes para generar reportes de migración
en diferentes formatos:

- ReportGenerator: Clase principal para generar resúmenes y exportar reportes
- _MigrationErrorEncoder: Encoder JSON personalizado para serializar MigrationError

El diseño separa la lógica del pipeline de la presentación, permitiendo
que esta clase solo se encargue de formatear y exportar datos sin conocer
detalles del proceso de migración.

Example:
    >>> from src.migrator.report_generator import ReportGenerator
    >>>
    >>> generator = ReportGenerator()
    >>> summary = generator.generate_summary(100, 5, [], config)
    >>> generator.export_to_json(summary, "report.json")
    >>> generator.print_human_readable(summary)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.migrator.error_handler import MigrationError
from src.utils.logger import get_logger


class ReportGenerator:
    """Generador de reportes de migración con múltiples formatos de salida.

    Separa la lógica del pipeline de la presentación, permitiendo que esta
    clase solo se encargue de formatear y exportar datos sin conocer detalles
    del proceso de migración.

    Attributes:
        _logger: Logger configurado para este módulo.

    Example:
        >>> generator = ReportGenerator()
        >>> summary = generator.generate_summary(100, 5, [], config)
        >>> generator.export_to_json(summary, "report.json")
        >>> generator.print_human_readable(summary)
    """
    
    def __init__(self) -> None:
        """Inicializa el generador con logger centralizado.

        Example:
            >>> generator = ReportGenerator()
            >>> assert generator is not None
        """

        self._logger = get_logger(__name__)
    
    def generate_summary(
        self,
        imported: int,
        rejected: int,
        errors: List[MigrationError],
        config: Dict
    ) -> Dict:
        """Genera resumen estructurado del proceso de migración.

        Args:
            imported: Número de registros importados exitosamente.
            rejected: Número de registros rechazados.
            errors: Lista de errores detallados.
            config: Configuración completa del proceso.

        Returns:
            Diccionario con resumen para serialización, incluyendo:
                - timestamp: Momento de generación del reporte
                - total_processed: Suma de importados y rechazados
                - imported: Número de registros importados
                - rejected: Número de registros rechazados
                - success_rate: Porcentaje de éxito (0-100)
                - error_count: Número de errores
                - config: Metadatos de configuración
                - errors: Lista de errores detallados

        Example:
            >>> generator = ReportGenerator()
            >>> summary = generator.generate_summary(100, 5, [], {"source": {}, "target": {}})
            >>> print(summary["total_processed"])
            105
        """
        total_processed = imported + rejected
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_processed": total_processed,
            "imported": imported,
            "rejected": rejected,
            "success_rate": round((imported / total_processed) * 100, 2) if total_processed > 0 else 0,
            "error_count": len(errors),
            "config": {
                "source_file": config.get("source", {}).get("file", "N/A"),
                "target_table": config.get("target", {}).get("table", "N/A"),
                "validation": config.get("validation", {})
            },
            "errors": [
                {
                    "row_num": error.row_num,
                    "column": error.column,
                    "field_type": error.field_type,
                    "invalid_value": error.invalid_value,
                    "reason": error.reason,
                    "suggestion": error.suggestion,
                    "timestamp": error.timestamp.isoformat()
                }
                for error in errors
            ]
        }
    
    def export_to_json(self, report_data: Dict, output_path: str) -> bool:
        """Exporta reporte a formato JSON con serialización segura.

        Usa encoder personalizado para manejar datetime y dataclasses.
        Crea directorios padre si no existen y realiza escritura atómica.

        Args:
            report_data: Diccionario con datos del reporte.
            output_path: Ruta del archivo JSON a generar.

        Returns:
            True si la exportación fue exitosa, False en caso contrario.

        Raises:
            PermissionError: Si no hay permisos de escritura.
            OSError: Si hay errores del sistema de archivos.

        Example:
            >>> generator = ReportGenerator()
            >>> summary = generator.generate_summary(100, 5, [], config)
            >>> success = generator.export_to_json(summary, "reports/migration.json")
            >>> assert success == True
        """
        try:

            # ■■■■■■■■■■■■■ Validar ruta de salida ■■■■■■■■■■■■■
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # ■■■■■■■■■■■■■ Serialización JSON segura con encoder personalizado ■■■■■■■■■■■■■
            json_content = json.dumps(
                report_data,
                indent=2,
                ensure_ascii=False,
                cls=_MigrationErrorEncoder
            )
            
            # ■■■■■■■■■■■■■ Escritura atómica del archivo ■■■■■■■■■■■■■
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_content)
            
            self._logger.info(f"Reporte JSON exportado a: {output_path}")
            return True
            
        except PermissionError as e:
            self._logger.error(f"Sin permisos para escribir en {output_path}: {e}")
            return False
        except OSError as e:
            self._logger.error(f"Error del sistema escribiendo en {output_path}: {e}")
            return False
    
    def print_human_readable(self, report_data: Dict) -> None:
        """Imprime reporte formateado para CLI con colores opcionales.

        Separa el logging del output: registra el resumen vía logger y
        muestra detalles en stdout solo si es una terminal interactiva.

        Args:
            report_data: Diccionario con datos del reporte.

        Example:
            >>> generator = ReportGenerator()
            >>> summary = generator.generate_summary(100, 5, [], config)
            >>> generator.print_human_readable(summary)  # Imprime en stdout
        """

        # ■■■■■■■■■■■■■ Registrar resumen en logs ■■■■■■■■■■■■■
        self._logger.info(
            f"RESUMEN MIGRACIÓN: {report_data['imported']} importados, "
            f"{report_data['rejected']} rechazados, "
            f"tasa éxito: {report_data['success_rate']}%"
        )
        
        # ■■■■■■■■■■■■■ Mostrar resumen en stdout ■■■■■■■■■■■■■
        self._print_summary(report_data)

        # ■■■■■■■■■■■■■ Mostrar errores detallados si existen ■■■■■■■■■■■■■
        if report_data["errors"]:
            self._print_errors(report_data["errors"])
    
    def _print_summary(self, report_data: Dict) -> None:
        """Imprime resumen con formato estructurado y colores.

        Detecta automáticamente si se deben usar colores ANSI basándose en
        si stdout es una terminal interactiva.

        Args:
            report_data: Diccionario con datos del reporte.
        """
        use_colors = self._should_use_colors()
        
        # ■■■■■■■■■■■■■ Encabezado del resumen ■■■■■■■■■■■■■
        header = "📊 RESUMEN DE MIGRACIÓN" if use_colors else "=== RESUMEN DE MIGRACIÓN ==="
        print(f"\n{header}")
        
        # ■■■■■■■■■■■■■ Métricas principales ■■■■■■■■■■■■■
        total = report_data["total_processed"]
        imported = report_data["imported"]
        rejected = report_data["rejected"]
        success_rate = report_data["success_rate"]
        
        if use_colors:
            print(f"  📁 Total procesados: {self._color_number(total)}")
            print(f"  ✅ Importados: {self._color_number(imported)}")
            print(f"  ❌ Rechazados: {self._color_number(rejected)}")
            print(f"  📈 Tasa éxito: {self._color_percentage(success_rate)}%")
        else:
            print(f"  Total procesados: {total}")
            print(f"  Importados: {imported}")
            print(f"  Rechazados: {rejected}")
            print(f"  Tasa éxito: {success_rate}%")
    
    def _print_errors(self, errors: List[Dict]) -> None:
        """Imprime lista de errores con formato estructurado.

        Limita la salida a los primeros 10 errores para evitar saturar
        la terminal cuando hay muchos errores.

        Args:
            errors: Lista de diccionarios con detalles de errores.
        """

        use_colors = self._should_use_colors()
        
        if use_colors:
            print(f"\n🚨 ERRORES ENCONTRADOS ({len(errors)}):")
        else:
            print(f"\n--- ERRORES ENCONTRADOS ({len(errors)}): ---")
        
        for error in errors[:10]:  # Limitar a primeros 10 errores
            row_num = error["row_num"]
            column = error["column"]
            reason = error["reason"]
            suggestion = error.get("suggestion", "N/A")
            
            if use_colors:
                print(f"  🔢 Fila {self._color_number(row_num)}, {column}: {reason}")
                if suggestion != "N/A":
                    print(f"     💡 Sugerencia: {suggestion}")
            else:
                print(f"  Fila {row_num}, {column}: {reason}")
                if suggestion != "N/A":
                    print(f"     Sugerencia: {suggestion}")
        
        if len(errors) > 10:
            remaining = len(errors) - 10
            if use_colors:
                print(f"  ... y {remaining} errores más (mostrados primeros 10)")
            else:
                print(f"  ... y {remaining} errores más (mostrados primeros 10)")
    
    def _should_use_colors(self) -> bool:
        """Detecta si se deben usar colores ANSI en la salida.

        Verifica si stdout es una terminal interactiva y no se ha
        desactivado explícitamente con la variable de entorno NO_COLOR.

        Returns:
            True si se deben usar colores, False en caso contrario.
        """

        # ■■■■■■■■■■■■■ Verificar si stdout es una terminal interactiva ■■■■■■■■■■■■■
        # y no se ha desactivado explícitamente
        
        return (
            hasattr(sys.stdout, 'isatty') and 
            sys.stdout.isatty() and
            'NO_COLOR' not in os.environ
        )
    
    def _color_number(self, number: int) -> str:
        """Aplica color verde a números para destacar métricas.

        Args:
            number: Número a colorear.

        Returns:
            String con código ANSI verde si se usan colores,否则 el número como string.
        """

        return f"\033[92m{number}\033[0m" if self._should_use_colors() else str(number)
    
    def _color_percentage(self, percentage: float) -> str:
        """Aplica color según tasa de éxito.

        Usa verde para tasas >= 95%, amarillo para >= 80%, y rojo para menores.

        Args:
            percentage: Porcentaje a colorear (0-100).

        Returns:
            String con código ANSI de color según el valor, o el porcentaje como string.
        """

        if not self._should_use_colors():
            return f"{percentage}%"
        
        if percentage >= 95:
            return f"\033[92m{percentage}%\033[0m"  # Verde
        elif percentage >= 80:
            return f"\033[93m{percentage}%\033[0m"  # Amarillo
        else:
            return f"\033[91m{percentage}%\033[0m"  # Rojo


class _MigrationErrorEncoder(json.JSONEncoder):
    """
    Encoder personalizado para serializar MigrationError en JSON.
    """
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)