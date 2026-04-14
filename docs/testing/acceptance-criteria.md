# Criterios de Aceptacion

## Matriz funcional

| ID | Funcionalidad principal | Criterio de aceptacion | Prueba automatizada |
|---|---|---|---|
| AC-01 | Bitacora semanal | Estudiante crea entrada y coordinador puede revisar; luego no se permite editar | `tests/test_acceptance_criteria.py::test_ac01_logbook_review_flow_blocks_edits_after_review` |
| AC-02 | Evaluacion docente | Tutor solo puede evaluar estudiantes asignados | `tests/test_acceptance_criteria.py::test_ac02_tutor_can_evaluate_only_assigned_students` |
| AC-03 | Asistencia diaria | No se permite duplicar asistencia para mismo estudiante y fecha | `tests/test_acceptance_criteria.py::test_ac03_attendance_prevents_duplicates_same_date` |
| AC-04 | Gestion de incidentes | Estudiante reporta incidente y coordinador cambia estado hasta resuelto | `tests/test_acceptance_criteria.py::test_ac04_incident_lifecycle_student_to_coordinator_resolution` |
| AC-05 | Alertas tempranas | Incidente activa alerta roja y coordinador puede resolverla | `tests/test_acceptance_criteria.py::test_ac05_alerts_show_red_after_incident_and_can_be_resolved` |
| AC-06 | Privacidad | Estudiante no puede ver bitacora de otro estudiante | `tests/test_acceptance_criteria.py::test_ac06_student_cannot_access_other_student_logbook_entry` |

## Regla de aprobacion

Un criterio se considera PASS cuando su prueba asociada termina en verde en el reporte de aceptacion:

- `backend/reports/testing/acceptance/report.html`
- `backend/reports/testing/acceptance/junit.xml`

Si alguna prueba falla, el criterio queda en FAIL hasta corregir codigo y re-ejecutar la suite.
