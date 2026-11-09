"""
Pattern Builder para los reportes de comedor (INPROMAR).

Provee `BaseReportBuilder` (abstracto) y `ExcelReportBuilder` (concreto) para
construir reportes de comedor en varios formatos (excel por defecto; PDF/CSV
reservados para el futuro) y salidas (descarga por defecto; también
visualización en pantalla).

El handler (vista/admin) alimenta al builder mediante `add_dataset(rows,
layout)`, indicando el dataset a visualizar y su distribución en el archivo:
cada dataset puede mapearse a una hoja de Excel distinta (reporte por
empresa) o a secciones fusionadas (totalización de servicios por
procedencia).

Relación con otros archivos: es consumido por src/src/dining_room/views.py
(report_dining_today_excel) y por el modal de descarga de
templates/unfold/dining/management.html (admin de gestíon de comedor).
"""

from datetime import datetime
import math
import os
from typing import Dict, List, Optional

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import column_index_from_string, get_column_letter


class UnsupportedReportFormatException(Exception):
    """Formato de reporte solicitado no soportado aún por el builder."""

    def __init__(self, report_format: str = ""):
        """
        Inicializa la excepción indicando el formato no soportado.

        Parámetros:
            report_format (str): formato solicitado (ej: 'pdf').

        Retorna:
            None.
        """
        super().__init__(
            f"El formato de reporte '{report_format}' no está soportado "
            "por el builder de reportes de comedor"
        )


class ReportFormats:
    """Catálogo de formatos de salida soportados/reservados."""

    EXCEL = "excel"
    PDF = "pdf"
    CSV = "csv"

    SUPPORTED = (EXCEL,)
    RESERVED = (PDF, CSV)


class ReportOutputs:
    """Catálogo de tipos de salida del reporte (download por defecto)."""

    DOWNLOAD = "download"
    DISPLAY = "display"
    VALID = (DOWNLOAD, DISPLAY)


class BaseReportBuilder:
    """
    Builder abstracto de reportes de comedor.

    Encadena configuraciones (formato, salida, header) y habilita add_dataset()
    para inyectar desde el handler el dataset con su distribución (layout).
    """

    def __init__(self):
        """
        Inicializa el builder con su configuración por defecto: formato excel,
        salida descarga y header habilitado.

        Parámetros:
            Ninguno.

        Retorna:
            None.
        """
        self._format = ReportFormats.EXCEL
        self._output = ReportOutputs.DOWNLOAD
        self._include_header = True
        self._datasets: List[Dict] = []

    # ------------------------------------------------------------------
    # Configuración encadenable
    # ------------------------------------------------------------------
    def with_format(self, report_format: str) -> "BaseReportBuilder":
        """
        Define el formato del reporte (excel por defecto; pdf/csv reservados).

        Parámetros:
            report_format (str): uno de ReportFormats.

        Retorna:
            BaseReportBuilder: self, para encadenar configuraciones.

        Lanza:
            UnsupportedReportFormatException: si el formato está reservado
            y aún no implementado.
        """
        if (
            report_format not in ReportFormats.SUPPORTED
            and report_format not in ReportFormats.RESERVED
        ):
            raise UnsupportedReportFormatException(report_format)

        if report_format not in ReportFormats.SUPPORTED:
            raise UnsupportedReportFormatException(report_format)

        self._format = report_format
        return self

    def with_output(self, output: str) -> "BaseReportBuilder":
        """
        Define el tipo de salida (descarga por defecto; también pantalla).

        Parámetros:
            output (str): ReportOutputs.DOWNLOAD o ReportOutputs.DISPLAY.

        Retorna:
            BaseReportBuilder: self, para encadenar configuraciones.
        """
        if output not in ReportOutputs.VALID:
            raise ValueError(
                f"Tipo de salida '{output}' no válido. Use "
                f"{ReportOutputs.DOWNLOAD} (descarga) o "
                f"{ReportOutputs.DISPLAY} (visualización en pantalla)"
            )

        self._output = output
        return self

    def enable_header(self, include_header: bool = True) -> "BaseReportBuilder":
        """
        Habilita o deshabilita el header (título 1) del reporte.

        Parámetros:
            include_header (bool): True para incluir el encabezado.

        Retorna:
            BaseReportBuilder: self, para encadenar configuraciones.
        """
        self._include_header = include_header
        return self

    def add_dataset(
        self,
        rows: List[Dict],
        layout: Dict,
    ) -> "BaseReportBuilder":
        """
        Agrega al builder el dataset indicado por el handler con su
        distribución.

        Parámetros:
            rows (list[dict]): filas de datos (dict por fila).
            layout (dict): distribución en el archivo:
                - sheet_title (str): nombre de la hoja de Excel.
                - start (str): celda inicial (ej: 'B7'); para filas se toma
                  el número y para columnas la letra correspondiente.
                - columns (list[str]): encabezados de columnas.
                - merge_key (str | None): campo por el cual las celdas de la
                  primera/las columnas iniciales se fusionan por sección.
                - section_field (str | None): campo de la fila que agrupa
                  las secciones.
                - totals (list[dict]): filas de totales finales por tipo de
                  servicio a las que se salta 2 líneas.
                - totals_title (str): título del bloque de totales.
                - merge_columns (int): cuántas columnas desde la celda
                  inicial se fusionan por sección (default 1).
                - merge_header_row (bool): fusiona toda la fila de
                  encabezados mostrando solo el primer texto (legacy).
                - row_merge (list[int, int]): fusión horizontal por fila de
                  datos (offsets de columnas relativos al inicio, ej: [2, 3]
                  para C:D).
                - column_widths (dict): ancho fijo por letra de columna
                  (prevalece sobre el auto-ajuste).
                - totals_skip (int): líneas en blanco antes del bloque de
                  totales (default 2).
                - totals_label_offset (int): offset de columnas desde el
                  inicio donde inicia la etiqueta de totales (default 0).
                - totals_value_label (str): encabezado de la columna de
                  valor (default 'Total').
                - totals_value_span (int): columnas que fusiona el encabezado
                  del valor (default 1).
                - same_sheet (bool): renderiza el dataset en la MISMA hoja
                  del dataset anterior (desgloses en una sola hoja; no
                  reescribe título ni header).
                - block_title (str): fila en negrita sobre el encabezado de
                  columnas para identificar el bloque.
        Retorna:
            BaseReportBuilder: self, para encadenar.
        """
        self._datasets.append({"rows": rows, "layout": layout})
        return self

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------
    def build(self) -> HttpResponse:
        """
        Construye el reporte según formato y salida configurados.

        Parámetros:
            Ninguno.

        Retorna:
            HttpResponse: archivo del reporte (descarga por defecto) o
            tabla HTML de vista previa (salida en pantalla).

        Lanza:
            NotImplementedError: el builder abstracto no renderiza.
        """
        if self._format == ReportFormats.EXCEL:
            return self._build_excel()
        raise NotImplementedError(
            f"El builder {self.__class__.__name__} no implementa el formato "
            f"{self._format}"
        )

    def _build_excel(self) -> HttpResponse:
        """Delegado a la implementación concreta de Excel."""
        raise NotImplementedError

    def _render_as_html(self) -> HttpResponse:
        """
        Vista previa en pantalla del dataset en formato tabla HTML.

        Parámetros:
            Ninguno.

        Retorna:
            HttpResponse: contenido HTML de la vista previa del reporte.
        """
        parts = ["<h1>Reportes INPROMAR comedor</h1>"]
        for item in self._datasets:
            layout = item["layout"]
            parts.append(f"<h2>{layout.get('sheet_title', '')}</h2>")
            parts.append("<table border='1'>")
            parts.append("<tr>")
            for column in layout.get("columns", []):
                parts.append(f"<th>{column}</th>")
            parts.append("</tr>")
            for row in item["rows"]:
                parts.append("<tr>")
                for key in layout.get("row_fields", layout.get("columns", [])):
                    parts.append(f"<td>{row.get(key, '')}</td>")
                parts.append("</tr>")
            parts.append("</table>")

            totals_rows = layout.get("totals") or []
            if totals_rows:
                parts.append(f"<h3>{layout.get('totals_title', 'Totales')}</h3>")
                parts.append("<table border='1'>")
                for totals in totals_rows:
                    parts.append("<tr>")
                    parts.append(f"<td>{totals}</td>")
                    parts.append("</tr>")
                parts.append("</table>")
        return HttpResponse("<hr>".join(parts))


class ExcelReportBuilder(BaseReportBuilder):
    """
    Builder concreto de reportes Excel de comedor.

    Renderiza cada dataset del handler en su propia hoja de Excel (secciones
    con celdas fusionadas por `merge_key`) y al final un bloque de totales
    saltando dos líneas (`salto de líneas` según el layout).
    """

    HEADER_FONT = Font(name="Calibri", size=11, bold=True)
    SUBTITLE_FONT = Font(name="Arial", size=14)
    COLUMN_HEADER_FONT = Font(name="Calibri", size=11, bold=True)
    TOTALS_FONT = Font(name="Calibri", size=11, bold=True)

    THIN = Side(style="thin")
    BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
    CENTER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=False)

    def __init__(self):
        """
        Inicializa el builder Excel reutilizando la configuración base del
        builder abstracto.

        Parámetros:
            Ninguno.

        Retorna:
            None.
        """
        super().__init__()
        self._workbook = Workbook()

    def _sanitize_sheet_title(self, title: str, fallback_index: int) -> str:
        """
        Normaliza y acorta el título de la hoja de Excel: Excel prohíbe los
        caracteres []:*?/\\ y el uso de comillas simples, y limita el título a
        31 caracteres.

        Parámetros:
            title (str): título propuesto del layout.
            fallback_index (int): índice del dataset para el título por
                defecto ('Hoja N') cuando el título sanitizado queda vacío.

        Retorna:
            str: título seguro para Excel.
        """
        invalid_chars = ["[", "]", ":", "*", "?", "/", "\\", "'", "`"]
        safe_title = title
        for char in invalid_chars:
            safe_title = safe_title.replace(char, "-")
        safe_title = safe_title.strip()

        if not safe_title:
            safe_title = f"Hoja {fallback_index + 1}"

        return safe_title[:31]

    def _build_excel(self) -> HttpResponse:
        """
        Genera el archivo Excel a partir de los datasets agregados (descarga
        por defecto o vista previa en pantalla).

        Parámetros:
            Ninguno.

        Retorna:
            HttpResponse: Excel descargable o HTML de vista previa según el
            tipo de salida configurado.
        """
        if self._output == ReportOutputs.DISPLAY:
            return self._render_as_html()

        workbook = self._workbook
        used_titles = set()
        current_sheet = None

        for index, item in enumerate(self._datasets):
            rows = item.get("rows") or []
            layout = item.get("layout") or {}
            if layout.get("same_sheet") and current_sheet is not None:
                # Dataset adicional del MAISMO sheet (desgloses de un
                # reporte en una sola hoja); no reescribe título ni header
                sheet = current_sheet
            else:
                sheet = workbook.active if index == 0 else workbook.create_sheet()
                title = self._sanitize_sheet_title(
                    str(layout.get("sheet_title") or f"Hoja {index + 1}"),
                    index,
                )
                if title in used_titles:
                    suffix = f" {index + 1}"
                    title = title[: 31 - len(suffix)].rstrip() + suffix
                used_titles.add(title)
                sheet.title = title
            current_sheet = sheet
            self._render_on_sheet(sheet, rows, layout)

        response = HttpResponse(
            content_type="application/ms-excel"
        )
        stamp = int(datetime.now().timestamp())
        response["Content-Disposition"] = (
            f"attachment; filename =Comedor_{stamp}.xlsx"
        )
        workbook.save(response)
        return response

    def _render_on_sheet(self, sheet, rows: List[Dict], layout: Dict) -> None:
        """
        Renderiza un dataset sobre su propia hoja de Excel aplicando el
        layout: header, columnas, secciones fusionadas y totales finales.

        Parámetros:
            sheet (Worksheet): hoja destino del dataset.
            rows (list[dict]): filas del dataset.
            layout (dict): distribución (ver BaseReportBuilder.add_dataset).

        Retorna:
            None.
        """
        sheet_title = layout.get("sheet_title")
        start = layout.get("start", "A1")
        start_col = column_index_from_string(start[0])
        start_row = int(start[1:]) if start[1:].isdigit() else 1

        # Título del bloque (ej: "CARGAS DE PROCEDENCIAS" / desgloses):
        # fila en negrita sobre el encabezado de columnas; los datos del
        # bloque corren una fila
        if layout.get("block_title"):
            block_cell = sheet.cell(row=start_row, column=start_col)
            block_cell.value = str(layout["block_title"])
            block_cell.font = self.TOTALS_FONT
            start_row += 1
        columns = layout.get("columns", [])
        row_fields = layout.get("row_fields", columns)
        merge_key = layout.get("merge_key")
        section_field = layout.get("section_field")
        merge_columns = int(layout.get("merge_columns", 1))

        rendered = sheet
        rendered.sheet_view.showGridLines = True

        # Header de la hoja: título + logo de identidad corporativa solo si
        # el layout define logo_path; el ancho a combinar del título se
        # calcula con la longitud del texto y la altura (filas) con
        # header_rows (2 default; el reporte original por empresa usa 1)
        if self._include_header and sheet_title:
            header_text = layout.get("header_text", sheet_title)
            header_span = self._calculate_header_span(header_text, len(columns))
            header_rows = max(int(layout.get("header_rows", 2)), 1)
            start_letter = get_column_letter(start_col)
            end_letter = get_column_letter(start_col + header_span - 1)
            rendered.merge_cells(f"{start_letter}1:{end_letter}{header_rows}")
            title_cell = rendered.cell(row=1, column=start_col)
            title_cell.value = header_text
            title_cell.font = self.HEADER_FONT
            title_cell.alignment = self.CENTER_ALIGN

            self._add_corporate_logo(
                rendered,
                layout.get("logo_path"),
                anchor="A1",
                anchor_rows=header_rows,
            )

        # Encabezados de columnas desde la celda inicial indicada
        for offset, column in enumerate(columns):
            header_cell = rendered.cell(row=start_row, column=start_col + offset)
            header_cell.value = column
            header_cell.font = self.COLUMN_HEADER_FONT
            header_cell.border = self.BORDER
            header_cell.alignment = self.CENTER_ALIGN

        # Header de fila único (legacy del reporte por empresa): toda la fila
        # de encabezados se fusiona mostrando solo el primer texto (ej:
        # "Trabajador" en A3:G3 con fuente Arial 14)
        if layout.get("merge_header_row") and len(row_fields) > 1:
            end_header_letter = get_column_letter(
                start_col + len(row_fields) - 1
            )
            rendered.merge_cells(
                f"{get_column_letter(start_col)}{start_row}:{end_header_letter}{start_row}"
            )
            top_header = rendered.cell(row=start_row, column=start_col)
            top_header.font = self.SUBTITLE_FONT

        # Secciones (con fusión de la columna de sección si corresponde)
        row_cursor = start_row + 1
        row_merge = layout.get("row_merge")
        data_center_columns = max(
            int(layout.get("data_center_columns", 0)), 0
        )
        sections = self._build_sections(rows, section_field)
        for section_label, section_rows in sections:
            first_row = row_cursor

            for row in section_rows:
                for offset, field in enumerate(row_fields):
                    data_cell = sheet.cell(
                        row=row_cursor, column=start_col + offset
                    )
                    data_cell.value = row.get(field, "")
                    data_cell.border = self.BORDER
                    # Alineación centrada inicial (legacy: N° y Cédula)
                    if offset < data_center_columns:
                        data_cell.alignment = self.CENTER_ALIGN
                row_cursor += 1

                # Fusión horizontal opcional por fila (ej: Trabajador C:D
                # del reporte original por empresa)
                if row_merge:
                    rendered.merge_cells(
                        start_row=row_cursor - 1,
                        start_column=start_col + row_merge[0],
                        end_row=row_cursor - 1,
                        end_column=start_col + row_merge[1],
                    )

            if merge_key is not None and len(section_rows) > 1:
                self._merge_section_column(
                    rendered,
                    start_col,
                    first_row,
                    first_row + len(section_rows) - 1,
                    section_label,
                    merge_columns,
                )
            elif merge_columns > 1:
                rendered.merge_cells(
                    start_row=first_row,
                    start_column=start_col,
                    end_row=first_row + len(section_rows) - 1,
                    end_column=start_col + merge_columns - 1,
                )

        # Bloque final de totales con salto configurable de líneas (2 por
        # defecto; el reporte legacy por empresa salta 4 líneas)
        if not layout.get("column_widths"):
            # Auto-ajuste de anchos solo en modo dinámico (totalización);
            # el modo legacy usa anchos fijos exactos del layout
            self._fit_columns_to_content(sheet, rows, layout, start_col)

        # Anchos de columna fijos del layout (legacy); prevalecen sobre el
        # auto-ajuste de _fit_columns_to_content
        for width_letter, width_value in (layout.get("column_widths") or {}).items():
            sheet.column_dimensions[width_letter].width = width_value

        totals_rows = layout.get("totals") or []
        totals_row_start = row_cursor + int(layout.get("totals_skip", 2))
        totals_label_col = start_col + int(layout.get("totals_label_offset", 0))
        totals_value_span = max(int(layout.get("totals_value_span", 1)), 1)
        if totals_rows:
            totals_bold = bool(layout.get("totals_bold", True))
            totals_title = layout.get("totals_title", "Totales")
            rendered.cell(
                row=totals_row_start, column=totals_label_col
            ).value = totals_title
            if totals_bold:
                rendered.cell(
                    row=totals_row_start, column=totals_label_col
                ).font = self.TOTALS_FONT

            value_header = rendered.cell(
                row=totals_row_start, column=totals_label_col + 1
            )
            value_header.value = str(layout.get("totals_value_label", "Total"))
            if totals_bold:
                value_header.font = self.TOTALS_FONT
            if totals_value_span > 1:
                # Header del valor fusionado horizontalmente (ej: "Total/Día"
                # en D:E del reporte legacy por empresa)
                rendered.merge_cells(
                    start_row=totals_row_start,
                    start_column=totals_label_col + 1,
                    end_row=totals_row_start,
                    end_column=totals_label_col + totals_value_span,
                )

            for offset, totals_row in enumerate(totals_rows, start=1):
                cursor = totals_row_start + offset
                label = totals_row.get("label", "")
                total = totals_row.get("total", 0)
                rendered.cell(
                    row=cursor, column=totals_label_col
                ).value = label
                rendered.cell(
                    row=cursor, column=totals_label_col + 1
                ).value = total
                if totals_bold or totals_row.get("bold"):
                    rendered.cell(
                        row=cursor, column=totals_label_col + 1
                    ).font = self.TOTALS_FONT
                rendered.cell(
                    row=cursor, column=totals_label_col
                ).border = self.BORDER
                rendered.cell(
                    row=cursor, column=totals_label_col + 1
                ).border = self.BORDER
                if totals_row.get("bold"):
                    rendered.cell(
                        row=cursor, column=totals_label_col
                    ).font = self.TOTALS_FONT

    def _calculate_header_span(self, header_text: str, columns_count: int) -> int:
        """
        Calcula el ancho (número de celdas) a combinar del header del
        reporte evaluando la longitud del texto y la cantidad de columnas del
        dataset; las columnas de datos son el mínimo a combinar.

        Parámetros:
            header_text (str): texto del header del reporte.
            columns_count (int): cantidad de columnas del dataset.

        Retorna:
            int: número de celdas a combinar (mínimo 1).
        """
        chars_per_cell = 9  # capacidad estimada por celda en ancho default
        span_from_text = math.ceil(max(len(header_text), 1) / chars_per_cell)
        return max(columns_count, span_from_text, 1)

    def _add_corporate_logo(
        self, sheet, logo_path: Optional[str], anchor: str = "A1",
        anchor_rows: int = 2,
    ) -> None:
        """
        Inserta el logo de identidad corporativa preservando su relación de
        aspecto (no se reescala para caber en las celdas): la dimensión del
        logo se mantiene en su tamaño natural y son las celdas que lo
        contienen las que se adaptan (alto de las filas del header y ancho
        de la columna ancla). Se omite la inserción cuando la ruta es
        None o el archivo no existe en disco.

        Parámetros:
            sheet (Worksheet): hoja del reporte.
            logo_path (str | None): ruta absoluta del logo en el sistema de
                archivos; None o ruta inexistente omiten la inserción.
            anchor (str): celda ancla del logo (esquina superior izquierda).
            anchor_rows (int): cantidad de filas del header que contienen
                al logo en vertical (se reparten su altura).

        Retorna:
            None.
        """
        if not logo_path or not os.path.exists(logo_path):
            return

        logo = ExcelImage(logo_path)
        # Tamaño natural del archivo (px); nunca se fuerza el aspect ratio
        natural_width = float(logo.width or 0)
        natural_height = float(logo.height or 0)
        sheet.add_image(logo, anchor)

        # Las celdas ancla se adaptan al logo en lugar del logo a las
        # celdas: altura de las filas del header y ancho de la columna
        anchor_row = int(anchor[1:]) if anchor[1:].isdigit() else 1
        if natural_height > 0:
            total_height_pt = natural_height * 0.75  # px → puntos (72/96)
            row_height_pt = max(total_height_pt / max(anchor_rows, 1), 15.0)
            for row_index in range(anchor_row, anchor_row + anchor_rows):
                if sheet.row_dimensions[row_index].height is None:
                    sheet.row_dimensions[row_index].height = row_height_pt

        if natural_width > 0:
            anchor_letter = get_column_letter(
                column_index_from_string(anchor[0])
            )
            width_chars = (natural_width + 5) / 7  # px → ancho aproximado
            if anchor_letter not in sheet.column_dimensions:
                sheet.column_dimensions[anchor_letter].width = width_chars
            else:
                current = sheet.column_dimensions[anchor_letter].width or 0
                if width_chars > current:
                    sheet.column_dimensions[anchor_letter].width = width_chars

    def _build_sections(
        self, rows: List[Dict], section_field: Optional[str]
    ):
        """
        Agrupa el dataset en secciones para el render.

        Parámetros:
            rows (list[dict]): filas del dataset.
            section_field (str | None): campo que agrupa las secciones.

        Retorna:
            list[tuple]: lista de (label, filas de la sección), conservando
            el orden original de aparición de las secciones en los rows.
        """
        if section_field is None:
            return [("", list(rows))]

        sections: List[tuple] = []
        by_label: Dict = {}
        for row in rows:
            label = row.get(section_field, "")
            if label not in by_label:
                by_label[label] = []
                sections.append((label, by_label[label]))
            by_label[label].append(row)
        return sections

    def _fit_columns_to_content(self, sheet, rows: List[Dict], layout: Dict, start_col: int) -> None:
        """
        Ajusta el ancho de cada columna según el contenido más largo
        renderizado en ella (encabezados, valores y secciones fusionadas);
        el ancho mínimo de la columna de secciones queda relativo al texto
        más largo de esa columna (ej: nombre de la procedencia).

        Parámetros:
            sheet (Worksheet): hoja del reporte ya renderizada.
            rows (list[dict]): filas del dataset.
            layout (dict): distribución del dataset (se usa columns y
                merge_key).
            start_col (int): columna donde inicia el dataset (1-based).

        Retorna:
            None.
        """
        columns = layout.get("columns", [])
        row_fields = layout.get("row_fields", columns)
        merge_key = layout.get("merge_key")

        longest = [0] * len(row_fields)
        for row in rows:
            for offset, field in enumerate(row_fields):
                value = "" if row.get(field) is None else str(row.get(field))
                longest[offset] = max(longest[offset], len(value))

        for offset, column in enumerate(columns):
            header_value = str(column or "")
            longest[offset] = max(longest[offset], len(header_value))

        padding = 4
        for offset, _length in enumerate(longest):
            column_letter = get_column_letter(start_col + offset)
            # Ancho mínimo relativo al contenido más largo de la columna
            # (incluye secciones fusionadas, ej: nombre de procedencia)
            width = longest[offset] + padding
            current = sheet.column_dimensions[column_letter].width or 0
            sheet.column_dimensions[column_letter].width = max(current, width, 7)

    def _merge_section_column(
        self,
        sheet,
        start_col: int,
        first_row: int,
        last_row: int,
        label: str,
        merge_columns: int,
    ) -> None:
        """
        Fusiona verticalmente las celdas de la sección (columna label) y escribe
        el valor de la sección en la celda superior de la fusión.

        Parámetros:
            sheet (Worksheet): hoja destino.
            start_col (int): columna inicial de la fusión (índice 1-based).
            first_row (int): primera fila de la sección.
            last_row (int): última fila de la sección.
            label (str): valor de la sección (ej: nombre de la procedencia).
            merge_columns (int): cuántas columnas horizontales fusionar
                además de la sección (para labels largos).

        Retorna:
            None.
        """
        start_letter = get_column_letter(start_col)
        end_column = start_col + max(merge_columns - 1, 0)
        end_letter = get_column_letter(end_column)
        sheet.merge_cells(
            f"{start_letter}{first_row}:{end_letter}{last_row}"
        )
        top_left = sheet.cell(row=first_row, column=start_col)
        top_left.value = label
        top_left.alignment = self.CENTER_ALIGN
        top_left.font = self.COLUMN_HEADER_FONT
