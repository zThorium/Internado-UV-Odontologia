# Plataforma de Internado Odontología UV

Sistema web para gestionar el internado clínico de estudiantes de 6° año de Odontología de la Universidad de Valparaíso.

Permite a los **estudiantes** registrar su bitácora semanal y reportar incidentes de forma confidencial, a los **tutores clínicos** evaluar con escala Likert, y a los **coordinadores UV** tener visibilidad completa del proceso con alertas automáticas de bienestar y estadísticas por cohorte.

---

## 🏗️ Arquitectura

```
┌─────────────────┐
│   Navegador     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│          Frontend (React 18 + Vite 5)       │
│  Tailwind CSS v4 + React Router v6         │
│  Auth: Keycloak OIDC + JWT Legacy          │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         Backend (FastAPI + Python 3.14)     │
│  · Autenticación híbrida (Keycloak + JWT)  │
│  · SQLAlchemy async + Alembic              │
│  · API REST documentada con Swagger        │
└─┬───────┬───────┬────────┬─────────────────┘
  │       │       │        │
  ▼       ▼       ▼        ▼
┌────┐ ┌────┐ ┌─────┐ ┌──────┐
│ DB │ │IAM │ │Store│ │Cache │
│PG16│ │KClk│ │MinIO│ │Redis │
└────┘ └────┘ └─────┘ └──────┘
```

---

## 📁 Estructura del Proyecto

```
.
├── backend/              # API REST — FastAPI (Python)
│   ├── app/
│   │   ├── core/         # Configuración, seguridad, dependencias
│   │   │   ├── config.py           # Settings centralizadas (pydantic-settings)
│   │   │   ├── security.py         # JWT legacy + bcrypt
│   │   │   ├── keycloak_client.py  # Cliente OIDC (python-keycloak)
│   │   │   ├── deps.py             # Autenticación híbrida
│   │   │   └── limiter.py          # Rate limiting (slowapi)
│   │   ├── db/           # Sesión async de DB
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── routers/      # Endpoints FastAPI
│   │   │   └── auth.py   # OAuth2 endpoints (/callback, /refresh, /logout)
│   │   └── services/     # Lógica de negocio
│   ├── scripts/
│   │   ├── seed.py                 # Datos de prueba
│   │   └── migrate_to_keycloak.py  # Migración de usuarios a Keycloak
│   ├── tests/            # Pytest + Hypothesis
│   ├── alembic/          # Migraciones SQL
│   └── requirements.txt
│
├── frontend/             # Interfaz web — React + Vite
│   ├── src/
│   │   ├── context/
│   │   │   ├── AuthContext.jsx   # Autenticación (Keycloak + JWT)
│   │   │   └── ThemeContext.jsx  # Tema claro/oscuro
│   │   ├── components/
│   │   │   ├── AppShell.jsx      # Layout principal
│   │   │   ├── ProtectedRoute.jsx
│   │   │   └── ui/               # Componentes reutilizables (Alert, Badge, Modal…)
│   │   ├── pages/
│   │   │   ├── coordinator/      # Dashboards de coordinador
│   │   │   ├── student/          # Vistas de estudiante
│   │   │   └── tutor/            # Vistas de tutor
│   │   ├── services/api.js       # Cliente Axios centralizado
│   │   ├── keycloak.js           # Configuración Keycloak
│   │   └── main.jsx
│   ├── .env.example
│   └── package.json
│
├── docs/
│   └── keycloak-setup.md         # Guía paso a paso Keycloak
│
├── contexto/                     # Documentación de producto y requisitos
│   ├── product.md
│   └── Requisitos_Plataforma_Internado_UV.docx
│
├── docker-compose.yml            # Stack de desarrollo (PostgreSQL, Keycloak, Redis, MinIO)
├── docker-compose.prod.yml       # Stack de producción
├── dev.sh                        # Script que levanta todo el entorno en un comando
├── mvp_architecture.png          # Diagrama arquitectura MVP
└── system_architecture.png       # Diagrama arquitectura sistema completo
```

---

## 🚀 Stack Tecnológico

### Backend

| Categoría            | Tecnología                   | Versión  | Uso                          |
| -------------------- | ----------------------------- | -------- | ---------------------------- |
| **Runtime**          | Python                        | 3.14     | Lenguaje principal           |
| **Framework**        | FastAPI                       | latest   | API REST async               |
| **Database**         | PostgreSQL                    | 16       | Base de datos principal      |
| **ORM**              | SQLAlchemy                    | 2.x      | ORM async                    |
| **Migrations**       | Alembic                       | latest   | Migraciones SQL              |
| **Auth (Legacy)**    | python-jose + passlib[bcrypt] | latest   | JWT + passwords              |
| **Auth (Modern)**    | python-keycloak               | 4.2.2    | Cliente OIDC/OAuth2          |
| **IAM**              | Keycloak                      | 25.0     | Identity & Access Management |
| **Storage**          | MinIO                         | latest   | Object storage S3-compatible |
| **Cache/Queue**      | Redis                         | 7        | Cache + broker (futuro)      |
| **HTTP Client**      | httpx                         | <0.24.0  | Requerido por python-keycloak|
| **Rate Limiting**    | slowapi                       | latest   | Rate limiting                |
| **Email**            | fastapi-mail                  | latest   | Envío de correos             |
| **Testing**          | pytest + Hypothesis           | latest   | Tests unitarios + PBT        |

### Frontend

| Categoría       | Tecnología          | Versión   | Uso                     |
| --------------- | ------------------- | --------- | ----------------------- |
| **Runtime**     | Node.js             | 22 LTS    | JavaScript runtime      |
| **Framework**   | React               | 18.3      | UI framework            |
| **Bundler**     | Vite                | 5.4       | Build tool              |
| **Routing**     | React Router        | 6.26      | Navegación              |
| **Styling**     | Tailwind CSS        | 4.2       | Design system           |
| **HTTP Client** | Axios               | 1.7       | API calls               |
| **Auth**        | @react-keycloak/web | 3.4       | Integración con Keycloak|
| **Auth CLI**    | keycloak-js         | 25.0      | SDK Keycloak            |
| **Icons**       | lucide-react        | 1.0       | Iconos                  |
| **Charts**      | recharts            | 2.15      | Gráficos y estadísticas |
| **Tour**        | driver.js           | 1.4       | Onboarding guiado       |

---

## ⚡ Inicio Rápido

### Prerequisitos

- **Docker** y **Docker Compose** — para levantar PostgreSQL, Keycloak, Redis y MinIO
- **Python 3.13+**
- **Node.js 22+**

### 1. Clonar y configurar variables de entorno

```bash
# Copiar variables de entorno del frontend
cp frontend/.env.example frontend/.env
```

Edita `frontend/.env` si necesitas cambiar las URLs de los servicios.

### 2. Levantar todo el stack en un solo comando

```bash
./dev.sh
```

El script automáticamente:

1. Crea el virtualenv de Python e instala dependencias
2. Instala dependencias de Node.js
3. Levanta los servicios Docker (PostgreSQL, Keycloak, Redis, MinIO)
4. Ejecuta las migraciones de Alembic
5. Ejecuta el seed de datos si la base de datos está vacía
6. Levanta el backend FastAPI en `http://localhost:8000`
7. Levanta el frontend Vite en `http://localhost:5173`

> Presiona `Ctrl+C` para detener todo limpiamente.

### 3. Configurar Keycloak (solo primera vez)

Sigue la guía detallada: **[docs/keycloak-setup.md](docs/keycloak-setup.md)**

**Pasos resumidos:**

1. Acceder a `http://localhost:8080` (admin / admin123)
2. Crear realm `internado-uv`
3. Crear roles: `student`, `tutor`, `coordinator`
4. Crear clients: `internado-backend`, `internado-frontend`
5. Copiar el Client Secret a `backend/.env`

### 4. (Opcional) Migrar usuarios existentes a Keycloak

```bash
cd backend
python -m scripts.migrate_to_keycloak
```

Migra todos los usuarios de PostgreSQL a Keycloak con contraseña temporal `changeme123`. Keycloak forzará el cambio en el primer login.

---

## 🔐 Autenticación Híbrida

El sistema soporta **dos modos de autenticación simultáneamente** para facilitar la migración gradual:

### Keycloak OIDC (recomendado)

1. Usuario hace click en "Iniciar Sesión"
2. Redirect a Keycloak (`http://localhost:8080`)
3. Usuario ingresa credenciales en Keycloak
4. Redirect de vuelta con `code`
5. Frontend intercambia `code` por `access_token` + `refresh_token`
6. Token se auto-refresca

### JWT Legacy (backward compatibility)

1. Usuario ingresa email/password en el formulario
2. POST a `/auth/login`
3. Backend retorna JWT firmado localmente
4. JWT se guarda en localStorage

---

## 🌐 URLs de la Aplicación

| Servicio           | URL                          | Descripción            |
| ------------------ | ----------------------------- | ---------------------- |
| **Frontend**       | http://localhost:5173         | Aplicación web         |
| **Backend API**    | http://localhost:8000         | API REST               |
| **API Docs**       | http://localhost:8000/docs    | Swagger UI interactivo |
| **Keycloak**       | http://localhost:8080         | Admin Console IAM      |
| **MinIO Console**  | http://localhost:9001         | Console de storage     |

---

## 🔑 Credenciales de Desarrollo

### Aplicación — Login Legacy (JWT)

| Rol          | Email                        | Contraseña    |
| ------------ | ---------------------------- | ------------- |
| Coordinador  | coord@internado-uv.cl        | coord123      |
| Tutor        | tutor@internado-uv.cl        | tutor123      |
| Estudiante   | estudiante@internado-uv.cl   | estudiante123 |

### Aplicación — Keycloak (después de migrar)

| Rol          | Email                        | Contraseña (temporal) |
| ------------ | ---------------------------- | --------------------- |
| Coordinador  | coord@internado-uv.cl        | changeme123           |
| Tutor        | tutor@internado-uv.cl        | changeme123           |
| Estudiante   | estudiante@internado-uv.cl   | changeme123           |

### Servicios Docker

| Servicio             | URL                    | Credenciales               |
| -------------------- | ---------------------- | -------------------------- |
| **Keycloak Admin**   | http://localhost:8080  | admin / admin123           |
| **MinIO Console**    | http://localhost:9001  | minioadmin / minioadmin123 |
| **PostgreSQL**       | localhost:5433         | user / password            |
| **Redis**            | localhost:6379         | (sin autenticación)        |

---

## 🌱 Variables de Entorno

### Frontend (`frontend/.env`)

| Variable                   | Descripción                      | Valor por defecto              |
| -------------------------- | --------------------------------- | ------------------------------ |
| `VITE_API_URL`             | URL del backend                   | `http://localhost:8000`        |
| `VITE_KEYCLOAK_URL`        | URL del servidor Keycloak         | `http://localhost:8080`        |
| `VITE_KEYCLOAK_REALM`      | Realm de Keycloak                 | `internado-uv`                 |
| `VITE_KEYCLOAK_CLIENT_ID`  | Client ID del frontend            | `internado-frontend`           |

---

## 🛠️ Comandos Útiles

### Backend

```bash
cd backend

# Instalar dependencias (manualmente, sin dev.sh)
pip install -r requirements.txt

# Crear nueva migración
alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones
alembic upgrade head

# Correr backend standalone
uvicorn app.main:app --reload

# Ejecutar suite de calidad completa
# (unit + integration + system + acceptance + all + cobertura + reportes visuales)
python scripts/run_quality_suite.py

# Ejecutar suites individuales por marcador
pytest -m unit
pytest -m integration
pytest -m system
pytest -m acceptance

# Analizar pruebas con usuarios simulados
python scripts/analyze_user_tests.py

# Abrir reportes principales
open reports/testing/index.html
open ../docs/testing/reports/user-testing-summary.html
```

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Modo desarrollo
npm run dev

# Build para producción
npm run build

# Preview del build
npm run preview
```

### Docker

```bash
# Levantar solo los servicios de infraestructura
docker compose up -d

# Ver logs de un servicio específico
docker logs -f internado_uv_keycloak

# Detener servicios
docker compose down

# Resetear todo (⚠️ elimina datos persistentes)
docker compose down -v
```

---

## 🧪 Testing y Calidad

### Ejecución recomendada (rubrica completa)

```bash
cd backend
python scripts/run_quality_suite.py
```

Este flujo ejecuta pruebas por categoría (`unit`, `integration`, `system`, `acceptance`) y una corrida global (`all`) con cobertura.

### Reportes generados automáticamente

- Dashboard consolidado: `backend/reports/testing/index.html`
- Resumen Markdown: `backend/reports/testing/TEST_REPORT_SUMMARY.md`
- Resumen JSON: `backend/reports/testing/summary.json`
- Cobertura HTML: `backend/reports/testing/htmlcov/index.html`
- Reportes por suite (HTML + JUnit): `backend/reports/testing/<suite>/`

### Pruebas con usuarios simulados

```bash
cd backend
python scripts/analyze_user_tests.py
```

Salidas:

- `docs/testing/reports/user-testing-summary.md`
- `docs/testing/reports/user-testing-summary.html`

### Cobertura funcional del plan de pruebas

- ✅ Unitarias
- ✅ Integración
- ✅ Sistema (E2E)
- ✅ Aceptación (AC-01 a AC-06)
- ✅ Property-based testing con Hypothesis
- ✅ Evidencia visual consolidada para evaluación académica

---

## 🗺️ Roadmap

### ✅ FASE 1 — IAM con Keycloak (completada)

- [x] Setup Keycloak en Docker
- [x] Cliente Keycloak en backend (`python-keycloak`)
- [x] Autenticación híbrida (Keycloak + JWT legacy)
- [x] Endpoints OAuth2 (`/callback`, `/refresh`, `/logout`)
- [x] Integración React con `@react-keycloak/web`
- [x] Script de migración de usuarios
- [x] Guía de configuración (`docs/keycloak-setup.md`)
- [x] Estadísticas de estudiantes (dashboard coordinador)
- [x] Vista de bienestar (dashboard coordinador)

### 🔲 FASE 2 — Storage + Observabilidad

- [ ] Object Storage con MinIO (buckets, upload endpoints)
- [ ] Upload de imágenes en procedimientos y logbook
- [ ] Prometheus + Grafana (métricas y dashboards)
- [ ] Sentry (error tracking frontend + backend)

### 🔲 FASE 3 — Background Jobs + Notificaciones

- [ ] Celery workers para envío de emails
- [ ] MailHog para desarrollo local
- [ ] Tareas programadas (backups, reportes automáticos)
- [ ] Notificaciones automáticas de alertas de bienestar

### 🔲 FASE 4 — Documentación Arquitectónica

- [ ] ADRs (Architecture Decision Records)
- [ ] Diagramas detallados (deployment, data flow)
- [ ] Security checklist
- [ ] Guías de deployment (cloud + on-premise)

---

## 📖 Documentación

- **[docs/keycloak-setup.md](docs/keycloak-setup.md)** — Guía completa de configuración Keycloak
- **[docs/testing/README.md](docs/testing/README.md)** — Plan de calidad, criterios de aceptación y pruebas con usuarios
- **[contexto/product.md](contexto/product.md)** — Documento de producto y visión
- **[mvp_architecture.png](mvp_architecture.png)** — Diagrama de arquitectura MVP
- **[system_architecture.png](system_architecture.png)** — Diagrama de arquitectura del sistema

---

## 🙏 Créditos

Proyecto de título para la carrera de Ingeniería de Software.

**Universidad**: Universidad de Valparaíso  
**Facultad**: Odontología  
**Año**: 2026  

---

## 📄 Licencia

Este proyecto es de uso académico interno.
