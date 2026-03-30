# Requisitos: Plataforma de Internado Odontología UV

## Requisito 1 — Autenticación y Control de Acceso

### Descripción
El sistema debe permitir el acceso diferenciado por rol mediante autenticación con usuario y contraseña, emitiendo un JWT que identifica el rol del usuario en cada request.

### Criterios de Aceptación

1. DADO que un usuario ingresa email y contraseña válidos, CUANDO hace POST /auth/login, ENTONCES recibe un JWT con su rol y un código 200.
2. DADO que un usuario ingresa credenciales incorrectas, CUANDO hace POST /auth/login, ENTONCES recibe 401 con mensaje genérico (sin revelar si el email existe).
3. DADO que un JWT expirado se usa en cualquier endpoint protegido, CUANDO el backend lo valida, ENTONCES retorna 401.
4. DADO que un usuario con rol "tutor" intenta acceder a /logbook o /incidents, CUANDO el backend evalúa el rol, ENTONCES retorna 403 (no 404).
5. DADO que un coordinador solicita recuperación de contraseña, CUANDO ingresa su email registrado, ENTONCES recibe un correo con enlace de reset válido por 1 hora.
6. DADO que el sistema tiene múltiples cohortes activas, CUANDO un usuario se autentica, ENTONCES el JWT incluye el rol pero no restringe la cohorte (la cohorte se filtra por asignación).

---

## Requisito 2 — Bitácora del Estudiante

### Descripción
Los estudiantes deben poder registrar una entrada semanal con los procedimientos clínicos realizados. Las entradas son completamente invisibles para los tutores.

### Criterios de Aceptación

1. DADO que un estudiante autenticado crea una entrada, CUANDO hace POST /logbook/entries con semana y procedimientos válidos, ENTONCES se crea la entrada con status="draft" y retorna 201.
2. DADO que un estudiante intenta crear una segunda entrada para la misma semana en la misma cohorte, CUANDO el backend valida, ENTONCES retorna 409 Conflict.
3. DADO que una entrada tiene status="draft", CUANDO el estudiante hace PUT /logbook/entries/{id}, ENTONCES puede actualizar procedimientos y retorna 200.
4. DADO que una entrada tiene status="reviewed", CUANDO el estudiante intenta editarla, ENTONCES retorna 409 Conflict.
5. DADO que un tutor autenticado intenta acceder a cualquier endpoint de /logbook, CUANDO el backend evalúa el rol, ENTONCES retorna 403.
6. DADO que un estudiante intenta ver la bitácora de otro estudiante, CUANDO el backend valida student_id vs token, ENTONCES retorna 403.
7. DADO que un coordinador accede a /logbook/students/{student_id}/entries, CUANDO el student_id existe, ENTONCES retorna la lista completa de entradas ordenadas por week_number ASC.
8. DADO que cada procedimiento se registra, CUANDO se guarda en DB, ENTONCES quantity >= 1 y name no es vacío.

---

## Requisito 3 — Reporte de Incidentes

### Descripción
Canal confidencial para que los estudiantes reporten situaciones de maltrato, acoso o discriminación. El tutor no tiene acceso bajo ninguna circunstancia.

### Criterios de Aceptación

1. DADO que un estudiante autenticado envía un reporte, CUANDO hace POST /incidents/ con tipo, descripción y fecha válidos, ENTONCES se crea el incidente con status="submitted" y retorna 201.
2. DADO que se crea un incidente, CUANDO el backend lo persiste, ENTONCES se envía notificación por email a todos los coordinadores activos.
3. DADO que el servicio de email falla al crear un incidente, CUANDO ocurre el error, ENTONCES el incidente se guarda igual y el fallo se registra en logs (no se retorna error al estudiante).
4. DADO que un tutor autenticado intenta acceder a cualquier endpoint de /incidents, CUANDO el backend evalúa el rol, ENTONCES retorna 403.
5. DADO que un estudiante consulta GET /incidents/my, CUANDO hace el request, ENTONCES solo ve sus propios incidentes con su estado actual.
6. DADO que un coordinador cambia el estado de un incidente, CUANDO hace PATCH /incidents/{id}/status con valor válido, ENTONCES el estado se actualiza y retorna 200.
7. DADO que el estado de un incidente cambia, CUANDO el estudiante consulta GET /incidents/my, ENTONCES ve el estado actualizado (submitted/under_review/resolved).

---

## Requisito 4 — Evaluación del Tutor

### Descripción
Los tutores clínicos externos deben poder evaluar a sus estudiantes asignados usando escala Likert en un flujo de máximo 3 pasos.

### Criterios de Aceptación

1. DADO que un tutor autenticado accede a GET /evaluations/my-students, CUANDO hace el request, ENTONCES ve solo los estudiantes activamente asignados a él.
2. DADO que un tutor intenta evaluar a un estudiante no asignado a él, CUANDO hace POST /evaluations/ con ese student_id, ENTONCES retorna 403.
3. DADO que un tutor envía una evaluación válida, CUANDO hace POST /evaluations/, ENTONCES se persisten todos los EvaluationItem con score in ["achieved", "in_progress", "not_achieved"] y retorna 201.
4. DADO que el formulario de evaluación tiene dimensiones Likert, CUANDO el tutor lo completa, ENTONCES el flujo completo (lista → formulario → confirmación) no supera 3 pantallas.
5. DADO que un estudiante consulta sus evaluaciones, CUANDO hace GET /evaluations/student/{id} con su propio id, ENTONCES ve sus evaluaciones pero no las de otros estudiantes.
6. DADO que un coordinador consulta evaluaciones de cualquier estudiante, CUANDO hace GET /evaluations/student/{id}, ENTONCES puede ver todas sin restricción.

---

## Requisito 5 — Dashboard del Coordinador

### Descripción
Los coordinadores UV deben tener visibilidad completa del sistema: bitácoras, evaluaciones, incidentes, estadísticas y gestión de asignaciones.

### Criterios de Aceptación

1. DADO que un coordinador accede a GET /dashboard/overview, CUANDO hace el request, ENTONCES recibe estadísticas agregadas: total estudiantes activos, entradas de bitácora pendientes de revisión, incidentes por estado.
2. DADO que un coordinador crea una asignación, CUANDO hace POST /dashboard/assignments con student_id, tutor_id, cohort_id y clinical_site válidos, ENTONCES se crea la asignación activa y retorna 201.
3. DADO que un coordinador desactiva una asignación, CUANDO hace PUT /dashboard/assignments/{id} con is_active=false, ENTONCES la asignación queda inactiva y el tutor ya no ve al estudiante.
4. DADO que un coordinador crea un tutor, CUANDO hace POST /dashboard/tutors con email y nombre, ENTONCES se crea el usuario con role="tutor" y se envía email de bienvenida con instrucciones de acceso.
5. DADO que el sistema tiene múltiples cohortes, CUANDO el coordinador filtra por cohort_id, ENTONCES todos los listados (bitácoras, evaluaciones, asignaciones) se filtran correctamente.
