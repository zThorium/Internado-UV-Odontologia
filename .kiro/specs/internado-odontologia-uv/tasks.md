# Plan de Tareas: Plataforma de Internado Odontología UV

## Fase 0 — Infraestructura Base

- [x] 0.1 Inicializar repositorio con estructura monorepo (backend/ y frontend/)
- [x] 0.2 Configurar proyecto FastAPI con estructura de carpetas (routers/, models/, schemas/, services/, core/)
- [x] 0.3 Configurar proyecto React + Vite con estructura (pages/, components/, services/, hooks/)
- [x] 0.4 Configurar PostgreSQL local con Docker Compose para desarrollo
- [x] 0.5 Configurar Alembic para migraciones de base de datos
- [x] 0.6 Configurar variables de entorno (.env) para DB, JWT secret y email

## Fase 1 — Modelos de Base de Datos

- [x] 1.1 Crear modelo SQLAlchemy: User (id, email, hashed_password, full_name, role, is_active)
- [x] 1.2 Crear modelo SQLAlchemy: Cohort (id, name, year, semester, is_active)
- [x] 1.3 Crear modelo SQLAlchemy: Assignment (id, student_id, tutor_id, cohort_id, clinical_site, start_date, end_date, is_active)
- [x] 1.4 Crear modelos SQLAlchemy: LogbookEntry y LogbookProcedure con relación 1:N
- [x] 1.5 Crear modelo SQLAlchemy: Incident (id, student_id, incident_type, description, event_date, status)
- [x] 1.6 Crear modelos SQLAlchemy: Evaluation y EvaluationItem con relación 1:N
- [x] 1.7 Generar y aplicar migración inicial con todos los modelos
- [x] 1.8 Crear índices: logbook_entries(student_id, week_number), incidents(student_id), assignments(tutor_id, student_id, is_active)

## Fase 2 — Autenticación y Control de Acceso (Módulo 1)

_Dependencias: Fase 0, Fase 1 (modelo User)_

- [x] 2.1 Implementar utilidades de hashing: hash_password() y verify_password() con bcrypt
- [x] 2.2 Implementar create_access_token() y decode_access_token() con python-jose
- [x] 2.3 Implementar dependencia FastAPI get_current_user() que valida JWT
- [x] 2.4 Implementar dependencia require_role(*roles) que retorna 403 si el rol no está permitido
- [x] 2.5 Crear schemas Pydantic: LoginRequest, TokenResponse, UserInToken
- [x] 2.6 Implementar endpoint POST /auth/login
- [x] 2.7 Implementar endpoint POST /auth/forgot-password (genera token de reset, envía email)
- [x] 2.8 Implementar endpoint POST /auth/reset-password (valida token, actualiza contraseña)
- [x] 2.9 Crear script seed para usuarios iniciales (1 coordinador, 1 tutor, 1 estudiante de prueba)
- [x] 2.10 Escribir tests unitarios para verify_role() con todos los roles y combinaciones
- [x] 2.11 Escribir tests de propiedad (hypothesis): para cualquier token con role="tutor", endpoints de bitácora e incidentes retornan 403

## Fase 3 — Bitácora del Estudiante (Módulo 2)

_Dependencias: Fase 2_

- [x] 3.1 Crear schemas Pydantic: LogbookEntryCreate, LogbookEntryOut, LogbookProcedureCreate
- [x] 3.2 Implementar servicio create_logbook_entry() con validación de unicidad por semana
- [x] 3.3 Implementar servicio update_logbook_entry() con validación de status="draft"
- [x] 3.4 Implementar servicio get_logbook_entries() con control de acceso por rol
- [x] 3.5 Crear router /logbook con todos los endpoints (GET list, POST, GET by id, PUT, PATCH status)
- [x] 3.6 Aplicar require_role en router: student y coordinator permitidos; tutor bloqueado con 403
- [x] 3.7 Escribir tests de integración: flujo completo crear → editar → coordinador revisa → no editable
- [x] 3.8 Escribir test de propiedad: para cualquier student_id distinto al del token, retorna 403

## Fase 4 — Reporte de Incidentes (Módulo 3)

_Dependencias: Fase 2_

- [x] 4.1 Crear schemas Pydantic: IncidentCreate, IncidentOut, IncidentStatusUpdate
- [x] 4.2 Implementar servicio submit_incident() con persistencia y disparo de notificación
- [x] 4.3 Implementar NotificationService con envío de email via fastapi-mail (con manejo de fallo no bloqueante)
- [x] 4.4 Implementar servicio get_incidents() con filtro por rol (student: solo propios; coordinator: todos)
- [x] 4.5 Implementar servicio update_incident_status() para coordinador
- [x] 4.6 Crear router /incidents con todos los endpoints
- [x] 4.7 Aplicar require_role: tutor bloqueado con 403 en todos los endpoints del módulo
- [x] 4.8 Escribir tests de integración: crear incidente → verificar notificación enviada (mock email)
- [x] 4.9 Escribir test: fallo de email no impide creación del incidente

## Fase 5 — Evaluación del Tutor (Módulo 4)

_Dependencias: Fase 2, Fase 1 (Assignment)_

- [x] 5.1 Crear schemas Pydantic: EvaluationCreate, EvaluationOut, EvaluationItemCreate, StudentSummary
- [x] 5.2 Implementar servicio get_assigned_students() para tutor (solo asignaciones activas)
- [x] 5.3 Implementar servicio submit_evaluation() con validación de asignación activa
- [x] 5.4 Implementar servicio get_student_evaluations() con control de acceso (student: solo propias)
- [x] 5.5 Crear router /evaluations con todos los endpoints
- [x] 5.6 Escribir tests de integración: tutor evalúa estudiante asignado → éxito; no asignado → 403
- [x] 5.7 Escribir test de propiedad: para cualquier student_id no asignado al tutor, POST /evaluations retorna 403

## Fase 6 — Dashboard del Coordinador (Módulo 5)

_Dependencias: Fases 2, 3, 4, 5_

- [x] 6.1 Crear schemas Pydantic: DashboardStats, AssignmentCreate, AssignmentOut, TutorCreate, TutorOut
- [x] 6.2 Implementar servicio get_dashboard_overview() con estadísticas agregadas
- [x] 6.3 Implementar CRUD de asignaciones (crear, listar, actualizar is_active)
- [x] 6.4 Implementar CRUD de tutores (crear con envío de email de bienvenida, listar, editar)
- [x] 6.5 Crear router /dashboard con todos los endpoints, protegido con require_role("coordinator")
- [x] 6.6 Implementar filtrado por cohort_id en todos los listados del dashboard
- [x] 6.7 Implementar paginación (skip/limit) en endpoints de listado

## Fase 7 — Frontend: Autenticación

_Dependencias: Fase 2_

- [x] 7.1 Implementar página de Login con formulario email/contraseña
- [x] 7.2 Implementar AuthContext con almacenamiento de JWT y rol en memoria (no localStorage para seguridad)
- [x] 7.3 Implementar ProtectedRoute que redirige según rol al dashboard correspondiente
- [x] 7.4 Implementar página de Recuperación de Contraseña
- [x] 7.5 Implementar interceptor axios para adjuntar JWT y manejar 401 (redirect a login)

## Fase 8 — Frontend: Vista Estudiante

_Dependencias: Fase 7, Fases 3 y 4_

- [x] 8.1 Implementar página de Bitácora: lista de entradas semanales con estado
- [x] 8.2 Implementar formulario de nueva entrada de bitácora (semana + procedimientos dinámicos)
- [x] 8.3 Implementar formulario de edición de entrada (solo si status="draft")
- [x] 8.4 Implementar página de Reportes de Incidentes: lista con estado y formulario de nuevo reporte
- [x] 8.5 Deshabilitar botón de edición en UI cuando entry.status != "draft"

## Fase 9 — Frontend: Vista Tutor (máx. 3 pasos)

_Dependencias: Fase 7, Fase 5_

- [x] 9.1 Implementar Paso 1: lista de estudiantes asignados
- [x] 9.2 Implementar Paso 2: formulario de evaluación Likert por dimensiones + campo comentario
- [x] 9.3 Implementar Paso 3: pantalla de confirmación de evaluación enviada
- [x] 9.4 Verificar que el flujo completo no supera 3 pantallas/pasos

## Fase 10 — Frontend: Vista Coordinador

_Dependencias: Fase 7, Fases 3, 4, 5, 6_

- [x] 10.1 Implementar Dashboard overview con estadísticas (tarjetas resumen)
- [x] 10.2 Implementar vista de bitácoras de todos los estudiantes con filtro por cohorte
- [x] 10.3 Implementar vista de evaluaciones de tutores
- [x] 10.4 Implementar panel de incidentes con cambio de estado
- [x] 10.5 Implementar gestión de asignaciones (crear, listar, desactivar)
- [x] 10.6 Implementar gestión de tutores (crear, listar, editar)

## Fase 11 — Seguridad y Calidad

_Dependencias: Todas las fases anteriores_

- [x] 11.1 Configurar CORS en FastAPI para aceptar solo el origen del frontend en producción
- [x] 11.2 Implementar rate limiting en POST /auth/login (máx. 5 intentos por minuto por IP)
- [x] 11.3 Auditar todos los endpoints: verificar que ninguno expone datos de bitácora o incidentes a tutores
- [x] 11.4 Revisar que todos los mensajes de error de autenticación son genéricos (no revelan si email existe)
- [x] 11.5 Ejecutar suite completa de tests y verificar cobertura de propiedades críticas de privacidad

## Fase 12 — Despliegue

_Dependencias: Fase 11_

- [x] 12.1 Crear Dockerfile para backend FastAPI
- [x] 12.2 Crear Dockerfile para frontend React (build estático)
- [x] 12.3 Configurar docker-compose.yml de producción (backend + frontend + postgres)
- [x] 12.4 Configurar variables de entorno de producción en Railway o Render
- [x] 12.5 Ejecutar migración inicial en base de datos de producción
- [x] 12.6 Crear usuario coordinador inicial en producción
