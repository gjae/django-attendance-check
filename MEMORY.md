# MEMORY.md — Resumen de iteraciones (django-attendance-check / INPROMAR)

## Iteración: empresa actual (is_current_center) primero en el reporte general (2026-11-11)

- **Orden de empresas con centro actual** (`views.py`, pedido del usuario): en
  el bloque de EMPRESAS del reporte general, la empresa marcada como centro
  actual (`WorkCenter.is_current_center=True`, default True) va PRIMERO; el
  resto alfabético. Cambio: `order_by("-is_current_center", "name", "id")`.
  El reporte por empresa (sheets de `company_checks_dataset`) sigue
  alfabético — el usuario solo pidió el general. Verificado con simulación:
  actuales primero (alfabético entre ellos), resto alfabético después.
- **Nota de despliegue** (evidencia en captura del usuario): su servidor
  seguía corriendo código VIEJO — beneficios alfabéticos (sin orden por
  horario) y "FÁBRICA DE HIELO EL CARMEN" sin fusionar con la empresa
  homónima. Hay que reiniciar/recargar el servidor Django para que el código
  nuevo (fusión + orden por horario + este cambio) tome efecto y regenerar
  el reporte.

## Iteración: beneficios del reporte general ordenados por horario de entrega (2026-11-11)

- **Orden por horario de entrega** (`views.py`, pedido del usuario): los
  beneficios del reporte general ya NO van alfabéticos; se ordenan por
  `start_time` del turno de comedor (ConfDiningRoom), del más temprano al más
  tardío; los sin horario conocido van al final, alfabéticos entre ellos
  (`orden_beneficios = sorted(service_schedule, key=(start_time or time.max,
  nombre))`). Refactor: el set `service_names` se reemplaza por el dict
  `service_schedule` (nombre → horario MÁS TEMPRANO visto, helper
  `registrar_beneficio()`) alimentado por las 3 fuentes (cargas, chequeos
  reales, catálogo activo). El horario NO se agrega al values del agrupado
  de cargas (dividiría los totales del mismo beneficio con horarios
  distintos): query aparte `values_list` no agregada sobre `all_loads`;
  `checks_flat` extiende con `conf_dining_room__start_time`. Ambos call-sites
  `sorted(service_names)` (secciones + totalización) usan `orden_beneficios`.
  Import ajustado a `from datetime import datetime, time` (el módulo `time`
  no se usaba en views.py). Docstring de `totalization_services_dataset`
  actualizado. Verificado con simulación: Desayuno 06:00 / Merienda 10:00 /
  Almuerzo 12:00 / Cena 18:00 / Extra(sin horario); repetición de horario
  más tardío para el mismo beneficio NO sobreescribe el más temprano; empate
  → alfabético.

## Iteración: fusión por nombre empresa/procedencia (2026-11-11)

- **Nuevo logo del reporte general** (`views.py` + `reportering.py`, pedido
  del usuario): `logo_reportes_excel.JPG` (1080x964, ya en
  `static/images/branding/`) reemplaza a `logo_inpromaro_lit.png` SOLO en el
  layout del reporte general. Builder: nueva llave `logo_height_px` (int) que
  reescala el logo PROPORCIONALMENTE al alto indicado (sin distorsión) y las
  celdas ancla (filas 1-2 y columna A) se adaptan al tamaño FINAL; sin la
  llave, tamaño natural (legacy por empresa intacto, 166x166 natural). El
  call-site pasa `layout.logo_height_px`. Verificado con builder test:
  visualización 186x166 (proporción 1.12 preservada), fila 1 = 62.25pt,
  col A ≈ 27.29 chars; el por empresa sigue insertando su logo a tamaño
  natural. NOTA openpyxl: al recargar, `img.width/height` viene del PNG
  embebido (tamaño natural); el tamaño de visualización real está en
  `img.anchor.ext` (EMU ÷ 9525).

- **Título del reporte general con salto de línea** (`reportering.py`, pedido
  del usuario): el header de hoja ahora usa `HEADER_ALIGN` (Alignment center/
  center con `wrap_text=True`) cuando `header_rows > 1` (el general usa 2
  filas); si el texto excede el ancho de la celda combinada (B1:X2 calculado
  por `_calculate_header_span`), Excel lo parte automáticamente en líneas y
  queda centrado. El legacy por empresa (`header_rows=1`) conserva
  `CENTER_ALIGN` sin wrap — formato original 1:1 intacto. Verificado con
  builder test: general wrap=True/centered; por empresa sin wrap.

- **Duplicidad visual** (evidencia `duplicidades.jpeg`): "FABRICA DE HIELO EL
  CARMEN" aparecía 2 veces (empresa en el bloque de chequeos + procedencia en
  el de cargas); los MONTOS no estaban duplicados (totales = INPROMAR una vez).
  Decisión del usuario: FUSIONAR POR NOMBRE — si una o más procedencias del
  detalle llevan el MISMO nombre normalizado (sin acentos/mayúsculas/espacios,
  helper `normalizar_nombre` con unicodedata NFKD + ascii) que una empresa, se
  muestra UNA sola sección (label = nombre de la empresa) con las cargas de
  esas procedencias + los chequeos ordinarios de la empresa; el resto de las
  procedencias conserva su sección propia (varias procedencias de una misma
  empresa NO homónimas siguen separadas). `ghosts_fusionados` evita render
  doble; el total general sigue calculándose independiente (sin doble conteo).
  Con filtro de procedencia específica la fusión solo aplica a la
  procedencia renderizada. Verificado con simulación: procedencia homónima
  absorbida, carga en la sección de la empresa, sin secciones duplicadas.

- **Selector de fecha fuera de la vista de Gestión** (`management.html`,
  pedido del usuario): el bloque "Reporte por día" (`id_date_selector`, que
  solo mutaba el estado Alpine `current_date` sin consumirlo en ninguna otra
  parte — los rangos se eligen en el modal) quedó retirado junto con su
  estado `current_date`. Limpieza asociada: los includes de
  `vanilla_calendar` CSS/JS eran restos muertos del date-picker anterior (el
  modal usa `<input type="date">` nativo) y se quitaron; `momentv1.js` se
  conserva porque inicializa singleDate/startDate/endDate. El kiosco
  (`index.html`) no se tocó.

- **Un SOLO bloque** en el reporte general (`views.py`, decisión del usuario):
  sin título de bloque (el encabezado de columnas arranca directo en B7) y
  las secciones identificadas solo por su nombre, en este orden:
  1) EMPRESAS — solo entregas por chequeo ordinario (todas las WorkCenter no
     eliminadas, 0 por defecto; "Sin empresa" defensivo);
  2) PROCEDENCIAS — solo sus cargas (todas las GhostEmployee no eliminadas, 0
     por defecto; "Sin procedencia registrada" si aplica).
  Placeholders "Sin empresas registradas"/"Sin procedencias registradas" solo
  si no existe nada en cada grupo. UNA totalización general al final (todas
  las cargas + todas las reales, universo completo con 0, offset 1), sin
  mezclar sumas entre fuentes. La función retorna un dataset único (el
  builder ya no necesita same_sheet para este reporte; la feature sigue
  disponible). Verificado con builder test: header B7, datos B8-B15 con
  merges verticales, totales fila 18 alineados C/D.

- **Separación de fuentes** (`views.py`, decisión del usuario; SUPERADA por la
  iteración anterior — hoy el reporte es UN bloque único empresas→procedencias,
  se conserva el registro del proceso): los cálculos de procedencias y empresas
  NO se mezclan. Cargas = solo procedencias; entregas por chequeo ordinario =
  solo empresas (atribución en Python: employer primero, si no person). La
  función retorna un dataset único; el total general se calcula independiente
  (todas las cargas + todas las reales) para que nunca haya doble conteo.

## Iteración: sección única de cargas + reales (2026-11-10)

> NOTA incidente: el reinicio del servidor corrompió `src/src/dining_room/views.py`
> (truncado ~offset 24k + 5932 bytes NUL). Se restauró desde HEAD (los commits del
> usuario `47f83a7`/`9e40c45` conservaban el builder y el desgloce) y se RE-APLICARON
> a mano el fix de permisos y esta iteración. Verificar con py_compile/import.

1. **Reporte general: UNA sola sección "CARGAS DE PROCEDENCIAS"** (`views.py`);
   el bloque "DESGLOSE POR EMPRESA" quedó retirado:
   - TODAS las GhostEmployee no eliminadas aparecen (aunque no tengan cargas en el
     rango → TODOS los beneficios del universo con total 0; las secciones comparten
     el mismo juego de filas).
   - Entregas reales (DiningChecking por asistencia) se suman DENTRO de la sección:
     empresa con procedencia vinculada → se suman a sus filas por beneficio; empresa
     CON procedencia → sección con reales; empresa SIN → sección emulada con el
     MISMO formato (empresa sustituye la procedencia); trabajadores sin empresa →
     sección "Sin empresa". Cargas sin procedencia → "Sin procedencia registrada".
   - Multiples procedencias ligadas a la misma empresa: los reales se absorben una
     vez (pop de `reales_pendientes`) pero el TOTAL FINAL se calcula independiente
     (TODAS las cargas del rango + TODAS las reales), nunca hay doble conteo.
   - Con filtro de UNA procedencia: detalle = solo esa sección (+ reales de su
     empresa + completar 0 con el universo); el total final sigue siendo global.
   - Secciones emuladas completan 0; aserciones verificadas con builder test: 1
     hoja, B7 título, header fila 8, secciones 9-16 con merges verticales B9:B10,
     B11:B12, B13:B14, B15:B16, totales desde la fila 19 (2 de salto) con valores
     en columna C (label+1).
   - FIX prueba del usuario ("sin cargas en el rango seleccionado"): el universo
     de beneficios venía SOLO de cargas/reales del rango; con rango sin
     movimientos quedaba vacío y `seccion()` no agregaba ninguna fila aunque las
     procedencias existieran → placeholder. Ahora el universo SIEMPRE suma el
     catálogo `ConfDiningRoom` (is_removed=False, is_active__isnull=True), de
     modo que toda procedencia/empresa se lista con sus beneficios en 0.
   - FIX "empresas sin procedencia ocultas": las secciones emuladas solo se
     creaban para empresas CON entregas reales; ahora se listan TODAS las
     `WorkCenter` no eliminadas sin procedencia vinculada (queryset
     `is_removed=False`, mismo criterio del reporte por empresa), con sus
     beneficios en 0 si no registran movimiento; las que sí registran
     entran con sus reales (pop de `reales_pendientes`). La sección emulada
     usa `work_center.name` directo (ya no depende de nombres del values)
     y se limpió `empresa_nombres`.
   - FIX atribución de entregas reales (prueba del usuario: chequeo ordinario
     de carnet de un Person de la empresa TEST): el agrupado por rutas SQL
     con `isnull=True` marcaba como "Sin empresa" los chequeos con employer
     NULL aunque la person tuviera Department.work_center, y podía contar
     doble entre rutas. Ahora la atribución es en PYTHON (un chequeo → una
     empresa): employer primero y si no resuelve person (mismo criterio que
     `employer_object`/reporte por empresa); "Sin empresa" es solo bucket
     defensivo para cheques sin empresa en AMBOS lados. Verificado con
     simulación: Person de TEST → sección TEST con su beneficio.
   - FIX "totalización general por beneficios": el bloque de totales solo se
     renderizaba si el dict de totales tenía entradas (movimientos del rango);
     en rango sin movimiento no aparecía. Ahora `totals` se construye SIEMPRE
     desde el universo `service_names` (0 en los beneficios sin movimiento) y
     `totals_label_offset: 1` para alinear label bajo "Beneficio" y valor bajo
     "Total" (misma columna C/D que los datos). Verificado en builder test:
     título "Total por tipo de servicio" en C, "Total" en D, filas por
     beneficio con 0 incluidos.

2. **Permisos de reportes re-aplicados** (`views.py`): `REPORT_VIEW_PERMISSIONS`
   (view_diningroomproxymodel | view_conf_diningroom, any-of), helper
   `may_generate_dining_reports`, decorador `@permission_required` removido y guard
   DENTRO de `report_dining_today_excel` (raise PermissionDenied antes de
   parse_report_filters). `typing.Optional` importado. Kiosco sigue libre.

## Iteración: Reportes de comedor con builder (2026-11-04)

Último commit confirmado: `46328a7` feat(comedor) — reporte general en un
solo bloque y gestión sin selector de fecha (2026-11-11; sucesor de
`07bdbce`). Incluye las iteraciones
anteriores completas además de TODO el trabajo de reportes/UI de esta
memoria.

## Iteración: conteos duplicados + reporte general con chequeos reales (2026-11-07)

1. **Bug contador duplicado (fix)** (`views.py` — `company_checks_dataset`): el
   "Beneficio / Total/Día" del reporte por empresa contaba **2× cada entrega** porque
   `ConfDiningRoom` filtraba la relación multi-valor `checkings__…` en DOS llamadas
   `.filter()` separadas → Django crea un JOIN independiente por cada filtro y el mismo
   chequeo entra 2 veces en el `Count("checkings__id")`. El conteo ahora se arma DESDE
   `DiningChecking` (join único por lado employer/person, que son FK single-valued y no
   multiplican) agrupado por `conf_dining_room__check_name` con `values+annotate`.

2. **Reporte general: cargas + chequeos reales** (decisión del usuario): el bloque
   final "Total por tipo de servicio" de `totalization_services_dataset`, al generar
   con TODAS las procedencias (`procedencia='all'`) suma: **TODAS las cargas del rango**
   (ya sumadas por el bucle de secciones, con o sin empresa, erratas incluidas) **+
   entrega por chequeo del comedor** (DiningChecking del rango por beneficio, armada
   sin joins duplicados). **Corrección del 2026-11-07**: el primer intento sumaba las
   cargas ligadas a empresa POR SEPARADO (bloque `related_loads`) y el bucle de
   secciones ya las incluía → totalización duplicada (30 carga + 30 repetida + 1
   chequeo = 61 en el caso de prueba "30 entregas + 1 chequeo" que debía dar 31). El
   bloque `related_loads` se eliminó: las cargas cuentan UNA vez en el total del
   general, haya o no tengan empresa (la relación con empresa solo influye en el
   reporte POR EMPRESA). Con procedencia específica el bloque muestra solo sus cargas.

3. **Caso de prueba 123456** (chequeo + 1 carga): si la carga estaba ligada a la empresa
   del empleado, `Almuerzo = 2` es el diseño acordado (1 chequeo + 1 carga); si la carga
   NO estaba ligada, el 2 venía del bug del doble JOIN (corregido) → ahora 1. Hacer al
   usuario re-probar ambos casos.

4. Nota: los chequeos de empleados cuyo departamento NO tiene work_center no aparecen en
   ninguna hoja por empresa (filtro employer/person → department.work_center); hoy eso
   también los excluye de la totalización real del reporte general... vigilar con datos
   reales (posible necesario un bucket "Sin empresa" en el futuro).

## Iteración: permisos any-of para generar reportes de comedor (2026-11-10)

1. **Generación de reportes de gestión de comedor** (`views.py`): dejaba de funcionar
   para usuarios con solo "ver Gestión de comedor" (403 al descargar) porque exigía
   `dining_room.view_conf_diningroom`. Ahora:
   - Constante `REPORT_VIEW_PERMISSIONS` = (`dining_room.view_diningroomproxymodel`,
     `dining_room.view_conf_diningroom`); basta UNO de los dos (semántica any-of).
   - Helper `may_generate_dining_reports(user)` (any-of con `has_perm`).
   - `report_dining_today_excel` ya no usa el decorador `@permission_required`;
     el guard está DENTRO de la vista (`if not may_generate_dining_reports(request.user):
     raise PermissionDenied(...)` antes de `parse_report_filters`), siempre
     `@login_required`. Docstring actualizado. Import `permission_required` limpiado.
   - Kiosco (`index`, `/check/`, `todayChecks`) sigue sin requerir login.

## Iteración: filtro de beneficios activos + desgloce por empresa en el general (2026-11-09)

1. **Selector de beneficio del form de cargas** (`forms.py`): `service_type` es ahora un
   `ModelChoiceField` explícito con queryset `ConfDiningRoom.filter(is_removed=False,
   is_active__isnull=True)` ordenado por check_name → deja de listar beneficios
   eliminados/desactivados. Refactor: helper `unfold_select_widget()` con las clases
   tailwind/unfold compartidas (procedencia, empresa, tipo de servicio ya no duplican
   el string del widget).

2. **Desgloce por empresa de chequeos ordinarios en el reporte general**:
   - Builder (`reportering.py`): soporte para varios datasets en la MISMA hoja
     (`same_sheet=True` reutiliza la hoja anterior; no reescribe título ni header) y
     `block_title` (fila en negrita sobre el encabezado de columnas; el bloque corre
     una fila abajo). Docstring de `add_dataset` documentado.
   - `totalization_services_dataset` (`views.py`) retorna DOS datasets: bloque 1
     "CARGAS DE PROCEDENCIAS" (desde B7: título fila 7, encabezado fila 8, datos fila
     9+) y bloque 2 "SERVICIOS ENTREGADOS POR CHEQUEO ORDINARIO - DESGLOSE POR EMPRESA"
     2 filas después de la última carga (título en fila `10+len(cargas)`), con
     secciones por empresa (employer|person → department.work_center) x beneficio,
     armado desde DiningChecking sin joins duplicados. El total general por tipo de
     servicio (todas las cargas + chequeos reales, con 'all') quedó al FINAL del
     bloque 2. Departments sin empresa no aparecen en el desgloce pero sí cuentan en
     el total general. Con procedencia específica el desgloce sigue completo (los
     chequeos no pertenecen a una procedencia).
   - Verificado con test de builder: 1 hoja, títulos B7/B13, encabezados B8/B14,
     merges verticales por sección y total general debajo del desgloce.

## Iteración: Logo sin distorsión + relación Procedencia–Empresa (2026-11-07)

1. **Logo del reporte general** (`dining_room/reportering.py` —
   `ExcelReportBuilder._add_corporate_logo`): el logo YA NO se reescala a las celdas
   (antes era la causa de la distorsión: el PNG es **cuadrado 166×166px** y se forzaba a
   90×32). Ahora se inserta en su **tamaño natural** (aspect ratio intacto) y **las celdas
   que lo contienen se adaptan al logo**: filas 1..header_rows reparten su altura
   (px→pt ×0.75, min 15pt) y la columna ancla crece hasta `(w+5)/7` caracteres si
   estaba menor. Verificado: 166×166, filas 1-2 a 62.25pt, col A 24.43 chars,
   header B1:K2 intacto.

2. **FK opcional Procedencia→Empresa**:
   - `GhostEmployee.work_center` (`settings.WorkCenter`, `null=True`, `PROTECT`,
     `related_name="ghost_employees"`) — migración `0016_ghostemployee_work_center`
     (escrita a mano; Docker sin acceso en la sesión).
   - `GhostEmployeeForm` nuevo (`forms.py`): selector de Empresa **opcional** con clases
     tailwind/unfold (mismo patrón que los selects del comedor).
   - `GhostEmployeeModelAdmin` (`admin.py`): columna "Empresa" ("General" si null),
     filtro por empresa y form nuevo.

3. **Totalización por empresa con procedencias** (`views.py` —
   `company_checks_dataset`): el bloque "Beneficio / Total/Día" de cada hoja de
   empresa ahora es **por empresa y discriminado por tipo de beneficio**:
   chequeos de esa empresa (employer/person → department.work_center) +
   **Sum de GhostServiceLoad de procedencias con `work_center == esa empresa`**
   (erratas suman). Registros fantasma NUNCA generan filas de chequeo (solo
   totales, req. del usuario); procedencias **sin empresa** no se atribuyen a
   ninguna hoja por empresa → solo aparecen en el reporte general (totalización).

4. **Fix latente**: `Dict` (typing) se usaba en views.py sin importar → NameError
   al generar reportes; agregado `from typing import Dict`.

Nomenclatura vigente (ver AGENTS.md): "reporte general de cocina" = reportes de
dining_room de Ghost* (la opción del modal visible como "Reporte general", internamente
`report_type=totalizacion`).

1. **Patrón Builder** (`src/src/dining_room/reportering.py`, archivo nuevo):
   - `BaseReportBuilder`: encadena `with_format()` ('excel' por defecto, PDF/CSV reservados →
     `UnsupportedReportFormatException`), `with_output()` ('download' por defecto /
     'display' = vista previa HTML), `enable_header(True/False)` y
     `add_dataset(rows, layout)` (método para inyectar el dataset + su distribución desde el
     handler).
   - `ExcelReportBuilder`: renderiza cada dataset en su propia hoja de Excel; layout soporta
     `sheet_title`, `start` (celda inicial, ej: 'B7'), `columns`, `row_fields`,
     `section_field` + `merge_key` (fusiona verticalmente la 1.a columna por sección,
     ej: Procedencia) y `totals` + `totals_title` (bloque final saltando 2 líneas).
2. **Handler reescrito** (`report_dining_today_excel` en `dining_room/views.py`, misma URL
   `dining_room.today_report_xlsx`, permisos y `log_report` audit):
   - `parse_report_filters(query)`: normaliza `report_type` ('empresa'|'totalizacion'),
     `print_date` (compat) o `start_date`/`end_date`, `work_center` (id|'all') y
     `procedencia` (id|'all').
   - `company_checks_dataset(filters)`: reporte por empresa — **verificado (2026-11-05):
     cada WorkCenter sale en su propia hoja del Excel** (título de pestaña = nombre
     de la empresa; empresas sin chequeos del rango también obtienen hoja; nombres
     duplicados tras el recorte de 31 caracteres reciben sufijo «N»). Copia 1:1 de la
     versión original (commit c7cf574, validada con diff celda-a-celda: valores,
     fuentes, negritas y merges coinciden). Header en UNA fila A1:G1 con texto exacto
     "PERSONAL ASISTENTE AL {fecha} INPROMARCA" (rango: "DESDE ... HASTA ...
     INPROMARCA"), SIN logo; fila 3 fusionada A3:G3 con solo "Trabajador" (Arial 14);
     datos desde fila 4: A=N° (centrado), B=Cédula (centrado), C:D fusionado=Nombre,
     E=Departamento, F=Beneficio, G=Fecha y hora; anchos A=10/C=40/E=20/F=10/G=20
     (B y D quedan default); bloque de totales SIN negritas saltando 4 líneas con
     "Beneficio" en C y "Total/Día" fusionado D:E (conteo por beneficio global del
     rango, como el original). Se mantiene: rango de fechas + una hoja por WorkCenter
     (pestaña = nombre de la empresa, identidad solo en la pestaña). El reporte de
     empresa NO incluye datos de procedencias/totalización (eso vive solo en el
     reporte por totalización). Llaves del layout usadas: `header_rows=1`,
     `data_center_columns=2`, `merge_header_row`, `row_merge [2,3]`, `column_widths`,
     `totals_skip=4`, `totals_label_offset=2`, `totals_value_label`,
     `totals_value_span=2`, `totals_bold=False`.

   - `totalization_services_dataset(filters)`: reporte **"general"** (visible como
     "Reporte general" en el modal; valor interno `report_type=totalizacion`,
     título de hoja "REPORTE GENERAL DE SERVICIO ENTREGADO {rango}", auditado como
     "Reporte general de servicios de comedor"): secciones
     por Procedencia desde **B7** (columnas Procedencia / Beneficio / Total), celdas de
     procedencia fusionadas por cantidad de beneficios, y al final tras saltar 2 líneas el
     "Total por tipo de servicio" general. **Actualización (2026-11-04)**:
     `GhostServiceLoad.procedencia` (FK nullable a GhostEmployee, migración
     `0015_ghostserviceload_procedencia`) vincula cada carga con su
     procedencia: el reporte totaliza de verdad por procedencia (agrupando
     procedencia__name + service_type), las cargas históricas sin FK caen en la sección
      "Sin procedencia registrada" y el total general por servicio se calcula sobre los
     datos del filtro. La errata automática (is_errata) ahora evalúa por
     día+servicio+procedencia (model.save, register_load, admin save_model).
   - `ExcelReportBuilder._sanitize_sheet_title` (fix 500 en /dining_room/reports/): el
     nombre de hoja por empresa tenía "/" (fechas dd/mm) → Excel lo prohíbe. Sanitiza
     `[]:*?/\` y comillas → "-", recorta a 31 caracteres y agrega sufijo «N» para títulos
     duplicados.
   - Form/admin de cargas: selector de Procedencia (obligatorio, queryset filtrado por
     is_removed=False, widget con clases tailwind/unfold consistente con el resto del
     admin), columna "Procedencia" en el listado y filtro por procedencia; cargas previas
     a la FK muestran "S/A".
   - Selectores del modal de reportes (Procedencia y Empresa) usan las mismas clases
     tailwind/unfold + chevron SVG propio (appearance-none vía CSS `#reportModal select`).
3. **Modal de reportes** (`templates/unfold/dining/management.html`): el botón
   "Descargar reporte" de la Gestión de comedor (DiningRoomProxyModel) abre un modal Alpine
   para elegir tipo (Por empresa / Totalización), empresa o procedencia (con opción
   "todas"), y fecha específica o rango desde/hasta; genera la URL con querystring y
   descarga en pestaña nueva.
4. **Contexto del modal**: `ConfDiningRoomReportModelView.changelist_view` inyecta
   `work_centers`, `procedencias` y `today_iso`.

### Pendiente
- Commit de esta iteración; prueba del Excel en Docker (builder no ejecutado en runtime).
- Validar `makemigrations --check` no pendiente (no hubo cambios de modelos esta iteración).

### Ajustes de header del reporte de totalización (2026-11-04, misma iteración)
- `ExcelReportBuilder._render_on_sheet` ahora soporta `header_text` (layout) y calcula el
  ancho de la fusión con la **longitud del texto** (`_calculate_header_span`, ~9 caracteres
  por celda, mínimo la cantidad de columnas del dataset); fuente del header reducida a 11pt.
- `ExcelReportBuilder._add_corporate_logo` inserta el logo corporativo en A1 si el layout
  define `logo_path` (ruta absoluta resuelta con `staticfiles finders`,
  `images/branding/logo_inpromaro_lit.png`).
- El texto de header del totalización es:
  "REPORTE ENTREGA DE BENEFICIO ALIMENTARIO AL PERSONAL DESDE DD/MM/AAAA HASTA DD/MM/AAAA"
  (fechas del rango seleccionado) y la primera columna ya **no dice "Procedencia"**
  (header vacío; los nombres de procedencia siguen como secciones fusionadas en col. B).

### Ajustes finos (2026-11-04, misma iteración)
- `ExcelReportBuilder._fit_columns_to_content`: ajusta el ancho de cada columna según su
  contenido más largo (headers, valores, secciones); el ancho mínimo de la columna de
  procedencia queda relativo al nombre de procedencia más largo (+padding, mínimo 7).
- Modal de reportes (`management.html`) alineado con la modal de
  peladoydescabezado (`reports.html`): `<dialog>` nativo de **450px / max 95vw**
  centrado con `translate(-50%, -50%)`, `p-6 rounded-lg shadow-xl` con
  `backdrop:bg-black/50`, cierre por backdrop/X; el botón "Descargar reporte"
  abre con `$refs.reportModal.showModal()` y la descarga se dispara por
  submit del form (`@submit.prevent` + apertura en pestaña nueva).

## Iteración: Permisos, auditoría amigable y UI (2026-11-03b)

1. **AUDITLOG con nombres amigables**: el filtro "Resource Type" de
   django-auditlog mostraba el id técnico del content type
   (`content_type__model`, ej: "ghostserviceload"); `ContentType.name` ya no
   existe en Django 4.1+. Se re-registered `LogEntry` con
   `FriendlyLogEntryAdmin` en el nuevo archivo
   `reports/auditlog_admin.py` (importado desde `dining_room/admin.py`):
   columna "Resource" y filtro con `verbose_name` de cada modelo
   ("Procedencia", "Totalización de servicios"). La migración de datos 0015
   inicial se descartó (fallaba por el campo `name` eliminado).
2. **Input de fecha con estilo consistente**: el widget `date_day` de
   `GhostServiceLoadForm` usa las mismas clases tailwind/unfold que los
   selects del admin de clocking (bordes, shadow, dark mode).
3. **Eliminar totalización solo con permiso**: `GhostServiceLoadModelAdmin
   .has_delete_permission` exige `dining_room.delete_ghostserviceload`.
   La eliminación es auditable de fábrica en AUDITLOG (log de acción delete
   con actor vía `AuditlogMiddleware`).
4. **Acceso solo bajo permisos**:
   - `GhostEmployeeModelAdmin` y `GhostServiceLoadModelAdmin` validan
     explícitamente view/add/change (+ delete) por modelo.
   - `report_dining_today_excel` (`dining_room/views.py`) ahora exige
     `@login_required` +
     `@permission_required("dining_room.view_conf_diningroom",
     raise_exception=True)`.
   - El resto de admins del comedor usan los permisos automáticos de
     ModelAdmin; `ReportAdminView` ya se limitaba (`permissions_required`).
     Decisión del equipo: los endpoints de kiosco (`index`, `/check/`,
     `todayChecks`) quedan sin login porque las tablets/escáner no inician
     sesión.

## Iteración: UX del admin de comedor (2026-11-03)

Sobre la base de la iteración anterior (trabajadores fantasma del comedor):

1. **Responsable de carga automático**: `loaded_by` ya no se elige en el formulario
   (`GhostServiceLoadModelAdmin.save_model` asigna `request.user`). El selector desapareció del
   formulario (`GhostServiceLoadForm.Meta` excluye/existía `fields` limitado).
2. **Palabra "fantasma" removida de la UI**:
   - `GhostEmployee` ⇒ verbose_name "Procedencia / Procedencias".
   - `GhostServiceLoad` ⇒ verbose_name "Totalización de servicios" (ambos).
   - app `DiningRoomConfig.verbose_name` ⇒ "Comedor" (antes "Chequeos de comedor").
   - `__str__` de `GhostServiceLoad` ya no muestra "(errata)".
   Migración de metadatos: `dining_room/migrations/0014_rename_visible_metadata.py`.
3. **Fecha de carga DD/MM/AAAA + sin fechas futuras**:
   - `GhostServiceLoadForm` (`dining_room/forms.py`): `DateField(input_formats=["%d/%m/%Y", ...])`,
     widget texto con placeholder, y `clean_date_day()` que rechaza fechas posteriores a hoy.
     El cálculo de "hoy" maneja `USE_TZ=True` (timezone.localtime) y `USE_TZ=False`
     (naive, `timezone.now().date()`) — fix aplicado tras traceback
     "localtime() cannot be applied to a naive datetime" en entorno local.
   - Datepicker JS con el plugin ya presente en el proyecto **vanilla-calendar-pro**
     (`static/js/vanilla_calendar.js`), vía plantilla
     `templates/unfold/dining/ghost_serviceload_change_form.html` (`change_form_template` del
     admin), con `settings.format="dd/mm/yyyy"` y `range.max = hoy` (límite visual); la
     validación dura resta del lado del servidor. En la versión vendida del plugin el input
     serializado es `self.HTMLInputElement` (uso de `self.HTMLInput` lanzaba
     "can't access property 'value', self.HTMLInput is undefined"); por eso en
     `actions.changeToInput` se asigna sobre `self.HTMLInputElement`.
4. **Marca de tipo de carga oculta**: se retiró la insignia `errata_badge` del `list_display` y
   la mención "(errata...)" del success message. El flag `is_errata` sigue calculándose en
   backend (lógica inalterada en `save_model` / `GhostServiceLoad.save`).
5. **`is_removed` oculto** en el formulario de "Procedencias" (`GhostEmployeeModelAdmin.exclude`).
6. **AUDITLOG**: `GhostEmployee` y `GhostServiceLoad` registrados en django-auditlog
   (`auditlog.register` al final de `dining_room/models.py`, vía helper
   `register_auditlog()`); el actor se captura con el `AuditlogMiddleware` ya configurado en
   `config/settings/base.py`.
7. Menú: "Procedencias" y "Totalización de servicios" dentro de la app "Comedor"
   (labels provienen de los `Meta.verbose_name*` de cada modelo).

### Pendiente verificación (Docker no estaba disponible)
- Ejecutar `makemigrations --check` y `migrate` (0020 empleados sin cambios desde aquí; escaló
  a 0019 `employees` y `0013/0014 dining_room`).
- Confirmar comportamiento del plugin vanilla-calendar con la versión vendida en el proyecto.

---

## Iteración: Trabajadores fantasma del comedor (2026-11-02)

### Contexto / decisiones tomadas

Personal de comedor solicita crear registros de **"trabajadores fantasma"**: entradas que solo
sirven de shortcut para registrar la cantidad de servicios entregados, sin mantener un registro
personalizado ni afectar los cálculos de asistencia del personal fijo. Está dirigido a invitados
y personal de alta rotación.

Decisiones confirmadas con el equipo:

1. **`is_internal` (employees.Employee)**: `True` = personal fijo interno (default y válido para
   todos los registros existentes). `False` = comportamiento de trabajador fantasma.
2. **Empleados fantasma** son un **modelo aparte** (`GhostEmployee` en `dining_room`), solo
   requieren un nombre de procedencia. `employees.Employee` NO se usa para los registros
   fantasma (su `cedula` es única y obligatoria, incompatible).
3. **Registro del beneficio fantasma**: solo se registra el servicio en el modelo de control
   (`GhostServiceLoad`); **no** pasa por `DiningChecking` ni por la lógica de asistencia.
4. **Erratas**: cada carga posterior del mismo día + tipo de servicio es una **fila nueva** con
   `is_errata=True`; las erratas **SUMAN** al total del día, nunca sobreescriben.

### Cambios realizados (todo aditivo, no se modificó lógica existente salvo un guard punteado)

#### `src/src/employees/models.py`
- **`Employee.is_internal`** (BooleanField, default `True`): marca personal fijo vs fantasma.
- **`Employee.is_ghost`** (property, ~línea 88): retorna `not is_internal`.

#### `src/src/dining_room/models.py` (modelos nuevos)
- **`GhostEmployee`** (~línea 90): trabajador fantasma; solo `name` (nombre/procedencia) +
  `is_actived`. `TimeStampedModel + SoftDeletableModel`.
- **`GhostServiceLoad`** (~línea 210): control de servicios entregados a fantasmas por
  día (`date_day`) y tipo de servicio (`service_type` FK a `ConfDiningRoom`, cuyo `check_name`
  es el tipo de servicio configurable por la administración). Campos: `quantity` (¿cuántos
  servicios se entregaron?), `is_errata` (auto-calculado, `editable=False`), `note` (opcional,
  recomendada en erratas), `loaded_by` (FK User). La primera carga del día/servicio es
  original (`is_errata=False`); las siguientes son erratas que suman.
- **`GhostServiceLoadManager`** (~línea 126):
  - `register_load(service_type, quantity, loaded_by=None, date_day=None, note="")` — registra
    carga determinando errata automáticamente.
  - `totals_for_date(date_day=None)` — lista `{'service_type__check_name', 'total'}` del día.
  - `total_for(date_day=None, service_type=None)` — total plano del día (incluye erratas).
  - `erratas_for(date_day, service_type)` — cronología original + erratas.
  - `actives()` — queryset base (`is_removed=False`).
- `GhostServiceLoad.save()` recalcula `is_errata` en creación si no fue fijado.

#### `src/src/dining_room/admin.py` (admin de cocina)
- **`GhostEmployeeModelAdmin`** (registrado con `@admin.register(GhostEmployee)`): creación y
  gestión de trabajadores fantasma (solo nombre, activo/inactivo, búsqueda y filtro).
- **`GhostServiceLoadModelAdmin`** (registrado con `@admin.register(GhostServiceLoad)`):
  carga de servicios fantasma. Precarga hoy + usuario como responsable
  (`get_changeform_initial_data`); en `save_model` recalcula `is_errata` para cargas nuevas y
  muestra success message indicando si fue errata. Insignias "Carga original" (azul) /
  "Errata (suma)" (naranja). `date_hierarchy`, filtro por día y tipo de servicio.

#### `src/src/dining_room/managers.py` (único cambio sobre código existente)
- En `CheckDiningRoomManager.make_check_if_can`: guard aditivo `is_ghost_employee` — un
  `Employee` con `is_internal=False` no lanza `EmployerNotPresentException` aunque no haya
  marcado asistencia (recibe el beneficio igualmente y el chequeo queda registrado en
  `DiningChecking`, sin tocar el cálculo de asistencia del staff fijo). Los `GhostEmployee`
  no pasan por este path (no tienen cédula).

#### `src/src/dining_room/views.py`
- `report_dining_today_excel`: los totales de `GhostServiceLoad` del día se **suman** al
  `total_by_benefit` por beneficio (`combined_totals`) y se agrega una fila final de control
  "Servicios entregados a trabajadores fantasma" con el total del día. Sin tocar los cálculos
  de asistencia (`statistics_of` sigue siendo solo DailyChecks).

#### Migraciones (escritas a mano — Docker no disponible en el entorno de trabajo)
- `src/src/employees/migrations/0019_employee_is_internal.py`
- `src/src/dining_room/migrations/0013_ghostemployee_ghostserviceload.py`
  (depende de `0012_diningchecking_person_alter_diningchecking_employer`)

⚠️ **Pendiente verificar**: ejecutar `docker compose -f local.yml run --rm django python
manage.py makemigrations --check` (o `migrate`) al tener Docker disponible; las migraciones
fueron generadas manualmente y no se ejecutaron contra la base.

### Qué NO afecta
- Asistencia del personal fijo: los fantasmas no generan `DailyChecks`, no cuentan en
  `statistics_of`, y `Employee.is_internal` default `True` mantiene el comportamiento actual.
- `is_internal=False` sobre un `Employee`(existente) solo lo libera del requisito de
  asistencia en `make_check_if_can`.

### Puntos pendientes / ideas futuras
- Si se desea escanear tarjetas de fantasmas en el kiosco de comedor (view
  `check_dining_employer`), habría que extender el lookup hacia `GhostEmployee` (hoy solo
  cargan cantidades desde el admin de cocina).
- Posible reporte histórico de erratas (por responsable, con comparativa vs carga original).
