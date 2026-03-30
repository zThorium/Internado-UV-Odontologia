![1774329206973](image/CONTEXT/1774329206973.png)![1774329209440](image/CONTEXT/1774329209440.png)![1774329214889](image/CONTEXT/1774329214889.png)![1774329737594](image/CONTEXT/1774329737594.png)![1774329773094](image/CONTEXT/1774329773094.png)![1774329774883](image/CONTEXT/1774329774883.png)![1774365274900](image/CONTEXT/1774365274900.png)# Contexto del Proyecto — Internado Odontología UV

Documento de referencia para cualquier IA o desarrollador que tome este proyecto.
Última actualización: marzo 2026.

---

## 1. Qué es este proyecto

Plataforma web para gestionar el internado clínico de la carrera de Odontología de la Universidad Austral de Chile (UV). Es una tesis académica, por lo que el código debe ser comprensible y explicable, no solo funcional.

Tres tipos de usuario interactúan con el sistema:
- **Estudiante**: registra su bitácora semanal, asistencia e incidentes
- **Tutor**: evalúa a sus estudiantes asignados y revisa su asistencia
- **Coordinador**: supervisa todo — bitácoras, evaluaciones, incidentes, asistencia y bienestar

---

## 2. Stack tecnológico

### Backend
- **Python 3.13** + **FastAPI** (async)
- **SQLAlchemy 2** con `asyncpg` (PostgreSQL async)
- **Alembic** para migraciones
- **JWT** con `python-jose` + `bcrypt` para autenticación
- **Pydantic v2** para schemas
- **slowapi** para rate limiting
- **Hypothesis** + **pytest** para property-based testing
- Puerto: `8000`

### Frontend
- **React 19** + **Vite**
- **React Router v7** (rutas anidadas con `<Outlet>`)
- **Tailwind CSS v4** (con `@theme` para design tokens)
- **Axios** para llamadas HTTP (`frontend/src/services/api.js`)
- **driver.js** para el tour de bienvenida
- **lucide-react** para iconos
- Puerto: `5173`

### Base de datos
- **PostgreSQL 16** en Docker, puerto `5433` (no 5432, para evitar conflictos con instancias locales)
- Nombre de la base: `internado_uv`
- Usuario/contraseña: `user` / `password`

---

## 3. Cómo levantar el entorno

```bash
./dev.sh
```

Este script hace todo automáticamente:
1. Crea el virtualenv Python si no existe
2. Instala dependencias Python y Node
3. Levanta PostgreSQL en Docker (`docker compose up -d db`)
4. Ejecuta migraciones Alembic (`alembic upgrade head`)
5. Corre el seed si la tabla `users` está vacía
6. Levanta el backend con `uvicorn --reload`
7. Levanta el frontend con `npm run dev`

**Credenciales de desarrollo (seed):**
| Rol | Email | Contraseña |
|---|---|---|
| Coordinador | coord@internado-uv.cl | coord123 |
| Tutor | tutor@internado-uv.cl | tutor123 |
| Estudiante | estudiante@internado-uv.cl | estudiante123 |

---

## 4. Estructura de archivos

```
/
├── dev.sh                          # Script de arranque completo
├── docker-compose.yml              # Solo servicio "db" (PostgreSQL)
├── .env.prod.example               # Variables de entorno para producción
├── contexto/
│   ├── product.md                  # Descripción del producto
│   └── Requisitos_Plataforma_Internado_UV.docx
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, routers, CORS
│   │   ├── core/
│   │   │   ├── config.py           # Settings (pydantic-settings, lee .env)
│   │   │   ├── security.py         # bcrypt + JWT
│   │   │   ├── deps.py             # get_current_user, require_role()
│   │   │   └── limiter.py          # slowapi rate limiter
│   │   ├── db/session.py           # AsyncSessionLocal, Base, get_db
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   ├── schemas/                # Pydantic schemas (request/response)
│   │   ├── services/               # Lógica de negocio
│   │   └── routers/                # Endpoints FastAPI
│   ├── alembic/versions/           # Migraciones SQL
│   ├── scripts/seed.py             # Datos de prueba
│   ├── tests/                      # Tests de integración + PBT
│   └── .env                        # Variables locales (no commitear)
└── frontend/
    ├── src/
    │   ├── App.jsx                 # Router principal, todas las rutas
    │   ├── main.jsx                # Entry point React
    │   ├── index.css               # Design system completo (tokens + componentes)
    │   ├── context/AuthContext.jsx # Estado global de autenticación
    │   ├── services/api.js         # Instancia Axios con baseURL y token
    │   ├── components/
    │   │   ├── AppShell.jsx        # Layout con sidebar (usado por los 3 dashboards)
    │   │   ├── ProtectedRoute.jsx  # Guarda de rutas por rol
    │   │   └── ui/                 # Componentes reutilizables (Alert, Badge, Spinner, etc.)
    │   ├── hooks/useTour.js        # Hook del tour de bienvenida (driver.js)
    │   ├── pages/
    │   │   ├── LoginPage.jsx
    │   │   ├── StudentDashboard.jsx
    │   │   ├── TutorDashboard.jsx
    │   │   ├── CoordinatorDashboard.jsx
    │   │   ├── student/            # Páginas del estudiante
    │   │   ├── tutor/              # Páginas del tutor
    │   │   └── coordinator/        # Páginas del coordinador
    └── index.html
```

---

## 5. Modelo de datos

### `users`
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| email | String UNIQUE | índice |
| hashed_password | String | bcrypt |
| full_name | String | |
| role | Enum | `student`, `tutor`, `coordinator` |
| is_active | Boolean | default True |
| has_completed_onboarding | Boolean | controla si se muestra el tour |
| created_at | DateTime TZ | |

### `cohorts`
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| name | String | ej: "Internado 2026-1" |
| year | Integer | |
| semester | Integer | 1 o 2 |
| is_active | Boolean | |

### `assignments`
Vincula un estudiante con un tutor en una cohorte y campo clínico.
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| student_id | UUID FK → users | |
| tutor_id | UUID FK → users | |
| cohort_id | UUID FK → cohorts | |
| clinical_site | String | ej: "Hospital Base Valdivia" |
| start_date | Date | |
| end_date | Date | |
| is_active | Boolean | solo uno activo por estudiante |

### `logbook_entries`
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| student_id | UUID FK → users | |
| cohort_id | UUID FK → cohorts | |
| week_number | Integer | ≥ 1 |
| week_start_date | Date | lunes de la semana |
| status | Enum | `draft`, `submitted`, `reviewed` |
| wellbeing_status | Enum nullable | `good`, `regular`, `difficult` |
| created_at / updated_at | DateTime TZ | |

### `logbook_procedures`
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| entry_id | UUID FK → logbook_entries | |
| name | String | |
| description | String | default "" |
| quantity | Integer | ≥ 1 |

### `incidents`
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| student_id | UUID FK → users | |
| incident_type | Enum | `abuse`, `harassment`, `discrimination`, `other` |
| description | Text | |
| event_date | Date | |
| status | Enum | `submitted`, `under_review`, `resolved` |

### `evaluations` + `evaluation_items`
- `evaluations`: cabecera con tutor_id, student_id, assignment_id, period_label
- `evaluation_items`: dimensión evaluada con score (`achieved`, `in_progress`, `not_achieved`) y comentario opcional

### `attendance_records`
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| student_id | UUID FK → users | |
| date | Date | |
| status | Enum | `present`, `absent`, `justified` |
| observation | Text nullable | |

### `wellbeing_alerts`
Generadas automáticamente cuando el estudiante reporta bienestar negativo en la bitácora.
| Campo | Tipo | Notas |
|---|---|---|
| id | UUID PK | |
| student_id | UUID FK → users | |
| alert_level | Enum | `yellow`, `red` |
| triggered_at | DateTime TZ | |
| resolved | Boolean | coordinador puede resolver |
| resolved_at | DateTime TZ nullable | |

---

## 6. API — Endpoints

Todos los endpoints requieren `Authorization: Bearer <token>` excepto `/auth/login` y `/auth/forgot-password`.

### Auth (`/auth`)
| Método | Ruta | Roles | Descripción |
|---|---|---|---|
| POST | `/login` | público | Retorna JWT. Body: `{email, password}` |
| POST | `/forgot-password` | público | Envía email de reset |
| POST | `/reset-password` | público | Cambia contraseña con token |
| POST | `/complete-onboarding` | cualquiera | Marca tour como completado |

### Bitácora (`/logbook`)
| Método | Ruta | Roles | Descripción |
|---|---|---|---|
| GET | `/my-context` | student | Retorna cohort_id, week_number, week_start_date, clinical_site del assignment activo |
| GET | `/entries` | student, coordinator | Lista entradas del usuario autenticado |
| POST | `/entries` | student | Crea entrada. `cohort_id` es opcional (se resuelve desde assignment activo) |
| GET | `/entries/{id}` | student, coordinator | Detalle de una entrada |
| PUT | `/entries/{id}` | student | Edita entrada (solo si status=draft) |
| PATCH | `/entries/{id}/status` | coordinator | Cambia status a `reviewed` |
| GET | `/students/{id}/entries` | coordinator | Entradas de un estudiante específico |
| GET | `/wellbeing/history` | student | Historial de bienestar (últimas 8 semanas) |
| GET | `/wellbeing/coordinator-summary` | coordinator | Conteo verde/amarillo/rojo |
| GET | `/wellbeing/students` | coordinator | Lista estudiantes con nivel de alerta |
| GET | `/wellbeing/students/{id}/history` | coordinator | Historial de un estudiante |
| POST | `/wellbeing/alerts/{id}/resolve` | coordinator | Resuelve una alerta |

### Incidentes (`/incidents`)
| Método | Ruta | Roles | Descripción |
|---|---|---|---|
| GET | `` | student, coordinator | Lista incidentes (student: solo los propios) |
| POST | `` | student | Crea incidente |
| GET | `/{id}` | student, coordinator | Detalle |
| PATCH | `/{id}/status` | coordinator | Cambia status |

### Evaluaciones (`/evaluations`)
| Método | Ruta | Roles | Descripción |
|---|---|---|---|
| GET | `/my-students` | tutor | Lista estudiantes asignados al tutor |
| POST | `` | tutor | Crea evaluación con items |
| GET | `/students/{id}` | student, tutor, coordinator | Evaluaciones de un estudiante |

### Asistencia (`/attendance`)
| Método | Ruta | Roles | Descripción |
|---|---|---|---|
| POST | `` | student | Registra asistencia propia |
| PATCH | `/{id}` | student | Edita registro propio |
| GET | `/me` | student | Historial propio |
| GET | `/students/{id}` | coordinator, tutor | Historial de un estudiante |
| GET | `/students/{id}/stats` | coordinator, tutor | Estadísticas de asistencia |

### Dashboard (`/dashboard`)
Endpoints de resumen para el coordinador (conteos globales).

---

## 7. Autenticación y autorización

El JWT contiene `sub` (user UUID como string) y `role`. Se decodifica en `deps.py`.

`require_role(*roles)` es una factory de dependencias FastAPI:
```python
# Uso en router:
current_user: UserInToken = Depends(require_role("student", "coordinator"))
```

**Reglas de privacidad críticas:**
- Tutores NO pueden acceder a `/logbook/*` ni `/incidents/*` → 403
- Estudiantes solo ven sus propios datos → 403 si intentan ver datos de otro
- Coordinadores ven todo

---

## 8. Lógica de negocio importante

### Resolución automática de cohort_id
Cuando un estudiante crea una entrada de bitácora, **no necesita enviar `cohort_id`**. El backend lo resuelve automáticamente desde el `Assignment` activo del estudiante (`is_active=True`). Si no hay assignment activo, retorna 422.

El endpoint `GET /logbook/my-context` también calcula automáticamente:
- `week_number`: semanas transcurridas desde `assignment.start_date`
- `week_start_date`: lunes de la semana actual

### Alertas de bienestar
Después de cada entrada de bitácora, `evaluate_and_create_alert()` analiza las últimas semanas:
- **Alerta amarilla**: 2 semanas consecutivas con `difficult` o `regular`
- **Alerta roja**: 3+ semanas con `difficult`
- Solo se crea una alerta si no hay una activa (no resuelta) del mismo nivel

### Unicidad de entradas de bitácora
No puede existir más de una entrada para `(student_id, week_number, cohort_id)`. Si ya existe → 409.

---

## 9. Sistema de diseño (frontend)

**Reglas absolutas — nunca violar:**
- Fuentes: solo `Fraunces` (display/títulos) + `Plus Jakarta Sans` (cuerpo). NUNCA Inter, Roboto ni Arial.
- Fondo global: `#f7f3ee` (crema cálida), NO blanco puro
- NO gradientes morados ni azules eléctricos
- NO el patrón genérico sidebar gris + contenido blanco + tarjetas con box-shadow pesado

**Paleta:**
- Azul UV (acción primaria): `--color-uv-600: #1e4d8c`
- Tierra cálida (acento): `--color-earth-500: #a0622e`
- Ink (texto): `--color-ink-900: #0f1f2e`
- Fondo: `--color-bg-base: #f7f3ee`, superficie: `--color-bg-surface: #fdfaf6`
- Sidebar: `--color-bg-sidebar: #1a3a6b`

**Clases CSS disponibles (definidas en `index.css`):**
- `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-warm`, `.btn-ghost`, `.btn-danger`
- `.btn-xs`, `.btn-sm`, `.btn-lg`, `.btn-xl`
- `.card`, `.card-accent`, `.card-warm`, `.card-stat`
- `.badge`, `.badge-blue`, `.badge-green`, `.badge-yellow`, `.badge-red`, `.badge-earth`
- `.input`, `.input-warm`
- `.field`, `.label`
- `.table` (con `th`, `td` estilizados)
- `.nav-link`, `.nav-link.active`
- `.alert`, `.alert-error`, `.alert-success`, `.alert-warn`
- `.section-header`, `.section-title`, `.section-subtitle`
- `.empty-state`, `.empty-state-icon`, `.empty-state-title`, `.empty-state-desc`
- `.progress-track`, `.progress-fill`
- `.radio-card`, `.radio-card.selected-green/yellow/red`
- `.page-enter`, `.fade-in`, `.slide-up`, `.stagger` (animaciones)
- `.uv-tour-popover` (estilos del tour driver.js)

**Principio de diseño:** cada pantalla debe tener UN elemento visual memorable y distintivo. El módulo de incidentes tiene diseño especialmente cálido y contenido.

---

## 10. Estructura de rutas (frontend)

```
/login
/forgot-password

/student/*                    (ProtectedRoute: role=student)
  /student/logbook            LogbookPage — lista de entradas
  /student/logbook/new        LogbookNewPage — formulario en 2 pasos
  /student/logbook/:id        LogbookEditPage — editar entrada draft
  /student/incidents          IncidentsPage
  /student/attendance         AttendancePage

/tutor/*                      (ProtectedRoute: role=tutor)
  /tutor                      StudentsListPage
  /tutor/evaluate/:assignment_id  EvaluationFormPage
  /tutor/confirmation         ConfirmationPage
  /tutor/attendance/:student_id   TutorAttendancePage

/coordinator/*                (ProtectedRoute: role=coordinator)
  /coordinator/overview       OverviewPage
  /coordinator/logbooks       LogbooksPage
  /coordinator/evaluations    EvaluationsPage
  /coordinator/incidents      CoordinatorIncidentsPage
  /coordinator/assignments    AssignmentsPage
  /coordinator/tutors         TutorsPage
  /coordinator/attendance     CoordinatorAttendancePage
  /coordinator/wellbeing      WellbeingPage
```

Los dashboards (`StudentDashboard`, `TutorDashboard`, `CoordinatorDashboard`) usan `AppShell` con `<Outlet>` para renderizar las páginas anidadas.

---

## 11. Contexto de autenticación (frontend)

`AuthContext` expone:
- `user`: `{ id, role }` decodificado del JWT
- `token`: string JWT
- `login(email, password)`: llama a `POST /auth/login`, guarda token en localStorage, retorna el rol
- `logout()`: limpia localStorage y estado
- `showTour`: boolean — si debe mostrarse el tour de bienvenida
- `completeTour()`: llama a `POST /auth/complete-onboarding` y oculta el tour
- `triggerTour()`: activa el tour manualmente (botón en sidebar)

El token se persiste en `localStorage` con clave `auth_token`. Al inicializar, se decodifica y valida la expiración.

---

## 12. Tour de bienvenida

Implementado con `driver.js`. El hook `useTour` en `frontend/src/hooks/useTour.js` define los pasos según el rol del usuario. `AppShell` lo activa cuando `showTour=true`.

Los elementos del tour se identifican con atributos `data-tour` en los `NavLink` del sidebar, mapeados en `TOUR_KEY_MAP` dentro de `AppShell.jsx`.

El tour se activa automáticamente en el primer login (`has_completed_onboarding=false`) y puede reactivarse desde el botón "Ver tour de bienvenida" en el sidebar.

---

## 13. Migraciones Alembic

Las migraciones están en `backend/alembic/versions/`:
- `0001_initial_schema.py` — tablas base: users, cohorts, assignments, logbook_entries, logbook_procedures, incidents, evaluations, evaluation_items
- `0002_attendance.py` — tabla attendance_records
- `0003_onboarding.py` — campo `has_completed_onboarding` en users
- `0004_wellbeing.py` — tabla wellbeing_alerts + campo `wellbeing_status` en logbook_entries (usa SQL puro con `IF NOT EXISTS` para ser idempotente)

Para crear una nueva migración:
```bash
cd backend
alembic revision --autogenerate -m "descripcion"
alembic upgrade head
```

---

## 14. Tests

Los tests están en `backend/tests/`:
- `test_security.py` — tests unitarios de JWT y bcrypt
- `test_require_role.py` — tests de la dependencia `require_role`
- `test_deps.py` — tests de `get_current_user`
- `test_logbook_integration.py` — tests de integración de bitácora
- `test_incidents_integration.py` — tests de integración de incidentes
- `test_evaluations_integration.py` — tests de integración de evaluaciones
- `test_pbt_logbook.py` — property-based tests de bitácora (Hypothesis)
- `test_pbt_role_privacy.py` — property-based tests de privacidad por rol

Para correr los tests:
```bash
cd backend
pytest --tb=short
```

Los tests de integración usan SQLite en memoria (`aiosqlite`) para no depender de PostgreSQL.

---

## 15. Variables de entorno

El backend lee `backend/.env`. Variables relevantes:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5433/internado_uv
SECRET_KEY=changeme
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:5173"]

# Email (para reset de contraseña)
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_SERVER=
```

El frontend usa `VITE_API_URL` (por defecto apunta a `http://localhost:8000`).

---

## 16. Decisiones de diseño importantes

**Por qué el estudiante no ingresa cohort_id manualmente:**
El `cohort_id` es un UUID técnico que el estudiante no conoce ni debería conocer. El backend lo resuelve automáticamente desde el `Assignment` activo. El endpoint `GET /logbook/my-context` también precalcula el número de semana y la fecha de inicio, para que el formulario sea lo más simple posible.

**Por qué el formulario de nueva entrada tiene 2 pasos:**
Paso 1 es la selección de bienestar (good/regular/difficult con emojis). Paso 2 son los procedimientos. Esto separa la dimensión emocional de la técnica, y permite mostrar un mensaje empático si el estudiante elige "difícil".

**Por qué las alertas de bienestar son automáticas:**
El coordinador no debería tener que revisar manualmente cada entrada. El sistema evalúa el patrón de bienestar y genera alertas amarillas/rojas automáticamente, que el coordinador puede resolver desde `WellbeingPage`.

**Por qué se usa SQL puro en la migración 0004:**
Alembic `--autogenerate` a veces tiene problemas con tipos Enum ya existentes en PostgreSQL. La migración usa `CREATE TYPE IF NOT EXISTS` y `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` para ser completamente idempotente.

---

## 17. Problemas conocidos y soluciones

**Vite sirve versión cacheada después de editar un archivo:**
Hacer hard reload en el browser: `Cmd+Shift+R` (macOS). Si persiste, reiniciar el servidor de Vite.

**Error "Objects are not valid as a React child" al mostrar errores de Pydantic:**
Los errores de validación de Pydantic v2 retornan un array de objetos `{type, loc, msg, input}`, no un string. El componente `AlertError` en `frontend/src/components/ui/Alert.jsx` normaliza esto. Si se muestra un error directamente sin pasar por `AlertError`, puede ocurrir este error. Siempre normalizar: `typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(d => d.msg).join(', ') : 'Error desconocido'`.

**Alembic no puede conectar a la base de datos:**
Verificar que Docker está corriendo y el contenedor `db` está activo. La URL debe usar puerto `5433`, no `5432`. Correr `docker compose up -d db` antes de `alembic upgrade head`.

**El seed falla si ya existen los datos:**
El seed es idempotente — verifica existencia antes de insertar. Si falla por otro motivo, revisar que las migraciones estén al día.
