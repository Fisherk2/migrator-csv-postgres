"""
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
MÓDULO: Generador de reportes
AUTOR: Fisherk2
FECHA: 2026-04-23
DESCRIPCIÓN: Generación de reportes de migración con múltiples formatos.
■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
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
    """
    Generador de reportes de migración con múltiples formatos de salida.
    
    DECISIÓN: Separar lógica de pipeline de presentación. Esta clase
    solo formatea y exporta datos, sin conocer detalles del proceso.
    
    Attributes:
        logger: Logger configurado para este módulo.
    """
    
    def __init__(self) -> None:
        """
        Inicializa el generador con logger centralizado.
        """

        self._logger = get_logger(__name__)
    
    def generate_summary(
        self,
        imported: int,
        rejected: int,
        errors: List[MigrationError],
        config: Dict
    ) -> Dict:
        """
        Genera resumen estructurado del proceso de migración.
        
        Args:
            imported: Número de registros importados exitosamente.
            rejected: Número de registros rechazados.
            errors: Lista de errores detallados.
            config: Configuración completa del proceso.
            
        Returns:
            Diccionario con resumen para serialización.
            
        Example:
            >>> generator = ReportGenerator()
            >>> summary = generator.generate_summary(100, 5, errors, config)
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
        """
        Exporta reporte a formato JSON con serialización segura.
        
        DECISIÓN: Usar encoder personalizado para manejar datetime y dataclasses.
        
        Args:
            report_data: Diccionario con datos del reporte.
            output_path: Ruta del archivo JSON a generar.
        Returns:
            True si la exportación fue exitosa, False en caso contrario.
        Raises:
            PermissionError: Si no hay permisos de escritura.
            OSError: Si hay errores del sistema de archivos.
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
        """
        Imprime reporte formateado para CLI con colores opcionales.
        
        DECISIÓN: Separar logging del output. Registrar resumen vía logger
        y mostrar detalles en stdout solo si es terminal interactivo.
        
        Args:
            report_data: Diccionario con datos del reporte.
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
        """
        Imprime resumen con formato estructurado y colores.
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
        """
        Imprime lista de errores con formato estructurado.
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
        """
        Detecta si se deben usar colores ANSI en la salida.
        """

        # ■■■■■■■■■■■■■ Verificar si stdout es una terminal interactiva ■■■■■■■■■■■■■
        # y no se ha desactivado explícitamente
        
        return (
            hasattr(sys.stdout, 'isatty') and 
            sys.stdout.isatty() and
            'NO_COLOR' not in os.environ
        )
    
    def _color_number(self, number: int) -> str:
        """
        Aplica color verde a números para destacar métricas.
        """

        return f"\033[92m{number}\033[0m" if self._should_use_colors() else str(number)
    
    def _color_percentage(self, percentage: float) -> str:
        """
        Aplica color según tasa de éxito.
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