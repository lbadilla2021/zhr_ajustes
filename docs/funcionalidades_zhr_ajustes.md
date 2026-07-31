# Funcionalidades del modulo zhr_ajustes

Documento resumido de uso funcional y uso tecnico del modulo `zhr_ajustes`.

## Empleados

| Funcionalidad | Uso para el usuario | Uso en el sistema / variable |
|---|---|---|
| Nombre separado del trabajador | Permite registrar apellidos, nombres y nombre preferido de forma ordenada. | Usa `apellido_paterno`, `apellido_materno`, `nombres`, `nombre_preferido`; `_prepare_employee_vals()` y `_build_employee_name_from_values()` arman automaticamente `name`. |
| Validacion de RUT | Evita guardar empleados con RUT duplicado o digito verificador incorrecto. | Usa `identification_id` y `rut_dv`; `_check_employee_rut()`, `_find_employee_with_same_rut()`, `_calculate_rut_dv()` validan duplicidad y DV. |
| Ciudad normalizada | Permite seleccionar una ciudad desde mantenedor en vez de escribir texto libre. | Usa `city_id`; `_onchange_city_id()` y `_prepare_employee_vals()` sincronizan `private_city`. |
| Centro de costo | Permite asociar el trabajador a una cuenta analitica. | Usa `analytic_account_id` relacionado a `account.analytic.account`, filtrado por compania. |
| Familia de cargo | Permite ver la familia asociada al cargo del trabajador. | Usa `job_family_id` relacionado desde `job_id.job_family_id`. |
| Fechas laborales en ficha | Permite consultar Fecha Contrato, Fecha Termino y Fecha primer ingreso desde Informacion de trabajo. | Usa `fecha_contrato`, `fecha_finiquito`, `fecha_primer_ingreso`; se actualizan desde contratos mediante `_sync_contract_work_dates()`. |
| Fecha primer ingreso | Conserva la fecha historica del primer contrato real del trabajador. | Usa `fecha_primer_ingreso`; `_get_first_entry_contract_date()` excluye anexos y finiquitos para no modificar la fecha historica. |
| Prevision | Permite registrar AFP, sistema de salud y sistema horario. | Usa `afp_id`, `health_system_id`, `system_schedule`; `system_schedule` viene relacionado desde el calendario de trabajo. |
| Acreditaciones | Permite registrar acreditaciones con fecha, estado y adjunto. | Usa `hr.employee.accreditation` y `hr.accreditation.type`, ligados al empleado por `accreditation_ids`. |
| Recursos asignados | Permite registrar recursos entregados al trabajador con identificacion y fechas. | Usa `hr.employee.assigned.resource` y `hr.assigned.resource`, ligados por `assigned_resource_ids`. |
| Estado del trabajador | Permite ver si el trabajador esta Activo o Inactivo. | Usa `state` en `hr.employee`; `_compute_is_active_employee()` calcula `is_active_employee`. |
| Dar de baja | Permite inactivar un trabajador indicando motivo y fecha de salida. | `action_open_termination_wizard()` abre `hr.employee.termination.wizard`; al confirmar archiva el empleado, guarda `departure_reason_id`, `departure_date`, `fecha_finiquito` y pasa contratos a `cancel`. |
| Dar de alta | Permite reactivar un trabajador y crear un nuevo contrato base. | `action_open_reactivation_wizard()` abre `hr.employee.reactivation.wizard`; al confirmar activa el empleado, limpia `fecha_finiquito`, cancela contratos pendientes y duplica el ultimo contrato como nuevo contrato. |

## Contratos

| Funcionalidad | Uso para el usuario | Uso en el sistema / variable |
|---|---|---|
| Referencia de contrato | Obliga a seleccionar una referencia controlada para nombrar contratos y anexos. | Usa `reference_id` hacia `hr.contract.reference`; `_prepare_reference_name()` y `_build_reference_name()` concatenan referencia + empleado. |
| Mantenedor de referencias | Permite administrar tipos como Contrato, Anexo IPC, Anexo Cargo, Finiquito, etc. | Modelo `hr.contract.reference` con `name`, `reference_type`, `sequence`, `active`. |
| Fecha Contrato | Registra la fecha documental del contrato original del trabajador. | Usa `fecha_contrato`; `_prepare_preserved_contract_date()` conserva la fecha para anexos/finiquitos y solo se edita en el primer contrato real. |
| Fecha inicio de vigencia | Indica desde cuando rige el contrato o anexo. | Usa `date_start`, renombrado visualmente a "Fecha inicio de vigencia"; `_prepare_contract_dates()` lo llena desde `fecha_contrato` cuando corresponde. |
| Fecha finalizacion vigencia | Indica hasta cuando rige el contrato o anexo. | Usa `date_end`, renombrado visualmente a "Fecha de finalizacion vigencia"; se limpia en contratos indefinidos. |
| Fecha Termino | Registra la fecha documental de termino o finiquito. | Usa `fecha_finiquito`; `_prepare_contract_dates()` sincroniza `date_end` cuando se informa esta fecha. |
| Motivo de salida en contrato | Permite conservar el motivo de salida historico incluso si luego se da de alta al trabajador. | Usa `departure_reason_id` en `hr.contract`, escrito desde el wizard de baja. |
| Estado Expirado | Permite separar historial contractual de los contratos vencidos por fecha. | Agrega estado `expired` a `state`; se usa para contratos reemplazados por duplicado o alta/baja. |
| Badge de estados | Permite identificar visualmente Nuevo, Vigente, Vencido, Expirado y Terminado. | La vista lista usa `widget="badge"`; `close` queda amarillo, `expired` y `cancel` quedan gris. |
| Salario obligatorio mayor a 0 | Evita guardar contratos sin remuneracion valida. | Usa constraint `_check_wage_positive()` sobre `wage`; `wage_positive_check` ayuda a la validacion visual de la vista. |
| Texto de salario en palabras | Permite usar el sueldo en texto dentro de reportes. | Usa `wage_text`, calculado en `_compute_wage_text()` con la moneda de la compania. |
| Pago diario | Permite seleccionar periodicidad diaria si aplica. | Agrega valor `daily` a `schedule_pay`; `_compute_schedule_pay_name()` traduce la etiqueta para reportes. |
| Tipo de obra | Permite registrar obra/faena en contratos por obra. | Usa `tipo_obra_id`, `duracion_obra` e `is_por_obra`; si el tipo de contrato contiene "obra", los campos se vuelven visibles/requeridos. |
| Lugar de trabajo | Permite registrar lugar de prestacion de servicios del contrato. | Usa `lugar_trabajo_id` y lineas `hr.employee.lugar.trabajo`; se usa en vistas/reportes. |
| Conceptos de pago | Permite agregar conceptos adicionales con valor en el contrato. | Usa `employee_payment_concept_ids`, modelo `hr.employee.payment.concept`, con `payment_concept_id` y `amount`. |
| Contrato indefinido | Bloquea fechas de termino cuando el tipo de contrato es Indefinido. | Usa `is_indefinite_contract`; `_onchange_contract_type_id_indefinite_dates()` limpia `date_end` y `fecha_finiquito`. |
| Sin vacios entre contratos reales | Evita que existan saltos o traslapes entre contratos reales del trabajador. | `_check_contract_date_continuity()` valida `date_start` y `date_end` solo en referencias que participan en continuidad. |
| Anexos sin continuidad contractual | Permite crear anexos que no generen error por vacios o traslapes. | `_participates_in_contract_continuity()` excluye referencias con `reference_type = 'annex'`. |
| Duplicar contrato con boton `+` | Permite crear un contrato/anexo desde el contrato actual con nueva fecha y referencia. | `action_open_duplicate_wizard()` abre `hr.contract.duplicate.wizard`; `action_duplicate_with_new_reference()` copia el contrato, deja el anterior `expired` y el nuevo `open`. |
| Anexo Renovacion | Permite extender la vigencia contractual manteniendo la Fecha Contrato original. | `_is_renewal_annex_reference()` detecta "Anexo Renovacion"; el origen queda `expired` y el nuevo anexo queda `open`. |
| Anexo Renovacion Indefinido | Permite renovar un contrato y dejarlo como indefinido. | `_is_indefinite_renewal_annex_reference()` detecta el tipo y `_get_indefinite_contract_type()` asigna `contract_type_id` Indefinido. |
| Sincronizacion contrato-empleado | Permite que la ficha del trabajador refleje el contrato vigente. | `_sync_employee_work_dates()` actualiza fechas laborales, cargo, departamento, horario y lugar de trabajo desde el contrato `open`. |
| Eliminacion de contratos | Mantiene limpias las fechas del empleado si se eliminan contratos. | `unlink()` llama `_sync_contract_work_dates(clear_without_open=True)` para recalcular o limpiar fechas laborales. |

## Impresiones y reportes

| Funcionalidad | Uso para el usuario | Uso en el sistema / variable |
|---|---|---|
| Imprimir Contrato | Genera PDF de contrato desde la ficha de contrato. | `action_print_contract()` selecciona reporte segun `struct_id`: operador, profesional o ejecutivo. |
| Contrato Operador | Imprime formato contractual para estructura operativa. | Reporte `action_report_contract_employee_operador` y template `contract_employee_template_operador`. |
| Contrato Profesional | Imprime formato contractual para estructura profesional. | Reporte `action_report_contract_employee_profesional` y template `contract_employee_template_profesional`. |
| Contrato Ejecutivo | Imprime formato contractual para estructura ejecutivo. | Reporte `action_report_contract_employee_ejecutivo` y template `contract_employee_template_ejecutivo`. |
| Anexo Planta | Imprime anexo de planta desde el contrato. | `action_print_anexo_planta()` llama `action_report_anexo_planta`. |
| Pacto HE | Imprime pacto de horas extraordinarias. | `action_print_pacto_he()` llama `action_report_pacto_he`. |
| Actualizacion / Renovacion | Permite elegir tipo de anexo y variables a mostrar. | `hr.contract.actualizacion.wizard` usa `report_type`, `show_sueldo_base`, `show_cargo_actual`, `show_jornada_trabajo`. |
| Impresion masiva | Permite seleccionar varios contratos y descargar un PDF unificado. | `hr.contract.mass.print.wizard` renderiza PDFs con `_render_qweb_pdf()` y los une con `_merge_pdfs()`. |
| Formato de papel | Mantiene margenes y formato A4 para documentos laborales. | `paperformat_contrato` define papel, margenes, orientacion y DPI. |
| Fechas en espanol | Muestra fechas formateadas para documentos. | `format_date_es()` y `format_today_es()` usan `babel` con locale `es`. |

## Mantenedores

| Funcionalidad | Uso para el usuario | Uso en el sistema / variable |
|---|---|---|
| AFP | Mantiene listado de administradoras previsionales. | Modelo `hr.afp` con `name`, `code`, `active`; usado en `employee.afp_id`. |
| Sistema de salud | Mantiene Isapre/Fonasa. | Modelo `hr.health_system` con `name`, `type`, `active`; usado en `employee.health_system_id`. |
| Ciudad | Mantiene ciudades disponibles para empleados. | Modelo `hr.city`; tiene restriccion SQL `name_unique`. |
| Familia de cargos | Clasifica cargos por familia. | Modelo `hr.job.family`; `hr.job.job_family_id` relaciona el cargo con su familia. |
| Fecha de creacion de cargo | Permite registrar fecha asociada al cargo. | Campo `job_creation_date` en `hr.job`. |
| Tipo de obra | Mantiene nombres de obras/faenas. | Modelo `hr.tipo.obra`, usado por `contract.tipo_obra_id`. |
| Duracion de obra | Mantiene duraciones tipo para obras. | Modelo `hr.duracion.obra`. |
| Lugares de trabajo | Mantiene lugares disponibles para contratos. | Modelo `hr.lugar.trabajo`, usado por `lugar_trabajo_id` y `hr.employee.lugar.trabajo`. |
| Conceptos de pago | Mantiene conceptos remuneracionales adicionales. | Modelo `hr.payment.concept`, usado por `hr.employee.payment.concept`. |
| Recursos asignables | Mantiene recursos que pueden entregarse a empleados. | Modelo `hr.assigned.resource`, usado por `hr.employee.assigned.resource`. |
| Tipos de acreditacion | Mantiene catalogo de acreditaciones. | Modelo `hr.accreditation.type`, usado por `hr.employee.accreditation`. |
| Fecha de pago | Define dia de pago de remuneraciones. | Modelo `zhr.fecha.pago`; `_check_dia_pago()` exige valores entre 1 y 31. |
| Sistema horario | Permite registrar texto de sistema horario en calendarios. | Campo `system_schedule` en `resource.calendar`, relacionado al empleado. |

## Seguridad y perfiles

| Funcionalidad | Uso para el usuario | Uso en el sistema / variable |
|---|---|---|
| Perfil Barca empleados solo lectura | Permite consultar empleados sin editar informacion. | Grupo `group_zhr_employee_readonly` con permisos de lectura y reglas por compania. |
| Lectura de informacion privada | Permite al perfil consultar Informacion privada sin ser encargado de empleados. | `_setup_complete()` agrega `group_zhr_employee_readonly` a campos privados necesarios. |
| Bloqueo de contratos para solo lectura | Evita que el perfil de consulta acceda a contratos. | ACLs de `ir.model.access.csv` dejan `hr.contract` y `hr.contract.history` sin permisos para ese grupo. |
| Ocultar Curriculum | Evita que el perfil de consulta vea la pestana Curriculum. | `hide_resume_for_readonly` y vista `hr_employee_readonly_hide_resume_tab`. |
| Ocultar menus de tablas/contratos | Reduce accesos operativos del perfil de consulta. | Vistas y grupos restringen menus de contratos y mantenedores. |
| Regla multi-compania | Limita consulta a empleados de las companias permitidas. | Regla `rule_zhr_employee_readonly_employee` usa `company_ids`. |

## Utilidades tecnicas

| Funcionalidad | Uso para el usuario | Uso en el sistema / variable |
|---|---|---|
| Reporte de uso de campos | Permite descargar CSV con campos de empleados y cantidad de registros con valor. | `employee.field.usage.report.action_generate_report()` recorre `hr.employee._fields`, crea CSV y lo descarga como adjunto. |
| Limpieza de vistas obsoletas | Evita errores por vistas heredadas antiguas al actualizar. | `data/cleanup_stale_views.xml` elimina o corrige referencias antiguas segun datos del modulo. |
| Estilos de estados | Hace coherente el color visual de `Expirado` y `Terminado`. | `static/src/scss/hr_contract_status.scss` ajusta statusbar y validacion visual de salario. |

