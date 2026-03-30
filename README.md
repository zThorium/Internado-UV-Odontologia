# Plataforma de Internado Odontología UV

Sistema web para gestionar el internado clínico de estudiantes de 6° año de Odontología de la Universidad Valparaíso de Chile.

Permite a los estudiantes registrar su bitácora semanal y reportar incidentes de forma confidencial, a los tutores clínicos externos evaluar con escala Likert, y a los coordinadores UV tener visibilidad completa del proceso con alertas automáticas de bienestar.

---

## 🏗️ Arquitectura

Este proyecto implementa una **arquitectura enterprise-grade** con las mejores prácticas de ingeniería de software, incluyendo:

- 🔐 **IAM con Keycloak** - Autenticación OAuth2/OIDC con MFA y SSO
- 📦 **Object Storage con MinIO** - Almacenamiento S3-compatible para archivos
- 📊 **Observabilidad** - Prometheus + Grafana + Sentry
- ⚙️ **Background Jobs** - Celery + Redis para tareas asíncronas
- 🔑 **Secrets Management** - HashiCorp Vault
- 🚀 **CI/CD** - GitHub Actions (planificado)

### Diagrama de Arquitectura

```
┌─────────────────┐
│   Navegador     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│          Frontend (React 19)                │
│  Tailwind CSS v4 + React Router v7         │
│  Auth: Keycloak OIDC + JWT Legacy          │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         Backend (FastAPI + Python 3.13)     │
│  · Autenticación híbrida (Keycloak + JWT)  │
│  · SQLAlchemy async + Alembic              │
│  · Background jobs con Celery              │
└─┬───────┬───────┬────────┬─────────┬────────┘
  │       │       │        │         │
  ▼       ▼       ▼        ▼         ▼
┌────┐ ┌────┐ ┌─────┐ ┌──────┐ ┌────────┐
│ DB │ │IAM │ │Store│ │Cache │ │Secrets │
│PG16│ │KClk│ │MinIO│ │Redis │ │ Vault  │
└────┘ └────┘ └─────┘ └──────┘ └────────┘
```

---

## 📁 Estructura del Proyecto

```
.
├── backend/              # API REST — FastAPI (Python)
│   ├── app/
│   │   ├── core/         # Configuración, seguridad, dependencias
│   │   │   ├── config.py       # Settings centralizadas
│   │   │   ├── security.py     # JWT legacy + bcrypt
│   │   │   ├── keycloak_client.py  # Cliente OIDC ⭐ NUEVO
│   │   │   ├── deps.py         # Autenticación híbrida ⭐ NUEVO
│   │   │   └── limiter.py      # Rate limiting
│   │   ├── db/           # Sesión async de DB
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── routers/      # Endpoints FastAPI
│   │   │   └── auth.py   # ⭐ + OAuth2 endpoints (/callback, /refresh)
│   │   └── services/     # Lógica de negocio
│   ├── scripts/
│   │   ├── seed.py       # Datos de prueba
│   │   └── migrate_to_keycloak.py  # ⭐ NUEVO - Migración de usuarios
│   ├── tests/            # Pytest + Hypothesis
│   ├── alembic/          # Migraciones SQL
│   └── requirements.txt  # ⭐ +10 dependencias nuevas
│
├── frontend/             # Interfaz web — React + Vite
│   ├── src/
│   │   ├── context/
│   │   │   └── AuthContext.jsx  # ⭐ Adaptado para Keycloak
│   │   ├── main.jsx      # ⭐ ReactKeycloakProvider integrado
│   │   ├── pages/        # Dashboards por rol
│   │   └── components/   # UI components
│   └── package.json      # ⭐ +2 dependencias (keycloak-js, @react-keycloak/web)
│
├── docs/                 # ⭐ NUEVO - Documentación arquitectura
│   └── keycloak-setup.md # Guía paso a paso Keycloak
│
├── docker-compose.yml    # ⭐ +3 servicios (Keycloak, Redis, MinIO)
├── dev.sh                # ⭐ Actualizado - Levanta todos los servicios
└── CONTEXT.md            # Documentación técnica completa
```

---

## 🚀 Stack Tecnológico

### Backend

| Categoría                | Tecnología          | Versión | Uso                      |
| ------------------------- | -------------------- | -------- | ------------------------ |
| **Runtime**         | Python               | 3.13     | Lenguaje principal       |
| **Framework**       | FastAPI              | latest   | API REST async           |
| **Database**        | PostgreSQL           | 16       | Base de datos principal  |
| **ORM**             | SQLAlchemy           | 2.x      | ORM async                |
| **Migrations**      | Alembic              | latest   | Migraciones SQL          |
| **Auth (Legacy)**   | python-jose + bcrypt | latest   | JWT + passwords          |
| **Auth (Modern)**   | Keycloak             | 25.0     | IAM OIDC/OAuth2 ⭐       |
| **Storage**         | MinIO                | latest   | S3-compatible ⭐         |
| **Cache/Queue**     | Redis                | 7        | Cache + Celery broker ⭐ |
| **Background Jobs** | Celery               | 5.4+     | Tasks asíncronas ⭐     |
| **Secrets**         | Vault                | 1.17+    | Secrets management ⭐    |
| **Monitoring**      | Prometheus           | latest   | Métricas ⭐             |
| **Error Tracking**  | Sentry               | SaaS     | Error tracking ⭐        |
| **Testing**         | pytest + Hypothesis  | latest   | Tests unitarios + PBT    |

### Frontend

| Categoría            | Tecnología         | Versión | Uso                     |
| --------------------- | ------------------- | -------- | ----------------------- |
| **Runtime**     | Node.js             | 22 LTS   | JavaScript runtime      |
| **Framework**   | React               | 19       | UI framework            |
| **Bundler**     | Vite                | 5        | Build tool              |
| **Routing**     | React Router        | 7        | Navegación             |
| **Styling**     | Tailwind CSS        | 4        | Design system           |
| **HTTP Client** | Axios               | latest   | API calls               |
| **Auth**        | @react-keycloak/web | latest   | Keycloak integration ⭐ |
| **Icons**       | lucide-react        | latest   | Iconos                  |
| **Charts**      | recharts            | latest   | Gráficos               |
| **Tour**        | driver.js           | latest   | Onboarding              |

---

## ⚡ Inicio Rápido

### Prerequisitos

- **Docker** (para PostgreSQL, Keycloak, Redis, MinIO)
- **Python 3.13+**
- **Node.js 22+**

### 1. Levantar todo el stack

```bash
./dev.sh
```

Esto levantará automáticamente:

- ✅ PostgreSQL (puerto 5433)
- ✅ **Keycloak** (http://localhost:8080) ⭐
- ✅ **Redis** (puerto 6379) ⭐
- ✅ **MinIO** (http://localhost:9000) ⭐
- ✅ Backend FastAPI (http://localhost:8000)
- ✅ Frontend React (http://localhost:5173)

### 2. Configurar Keycloak (solo primera vez)

Sigue la guía detallada: **[docs/keycloak-setup.md](docs/keycloak-setup.md)**

**Pasos resumidos**:

1. Acceder a http://localhost:8080 (admin/admin123)
2. Crear realm `internado-uv`
3. Crear roles: `student`, `tutor`, `coordinator`
4. Crear clients: `internado-backend`, `internado-frontend`
5. Copiar Client Secret a `backend/.env`

### 3. Migrar usuarios a Keycloak

```bash
cd backend
python -m scripts.migrate_to_keycloak
```

Esto migrará todos los usuarios de PostgreSQL a Keycloak con contraseña temporal `changeme123`.

---

## 🔐 Credenciales de Desarrollo

### Aplicación (después de migrar a Keycloak)

| Rol         | Email                      | Contraseña (temporal) |
| ----------- | -------------------------- | ---------------------- |
| Coordinador | coord@internado-uv.cl      | changeme123            |
| Tutor       | tutor@internado-uv.cl      | changeme123            |
| Estudiante  | estudiante@internado-uv.cl | changeme123            |

⚠️ **Nota**: Keycloak forzará cambio de contraseña en el primer login.

### Login Legacy (JWT - backward compatibility)

| Rol         | Email                      | Contraseña   |
| ----------- | -------------------------- | ------------- |
| Coordinador | coord@internado-uv.cl      | coord123      |
| Tutor       | tutor@internado-uv.cl      | tutor123      |
| Estudiante  | estudiante@internado-uv.cl | estudiante123 |

### Servicios

| Servicio                 | URL                   | Credenciales               |
| ------------------------ | --------------------- | -------------------------- |
| **Keycloak Admin** | http://localhost:8080 | admin / admin123           |
| **MinIO Console**  | http://localhost:9001 | minioadmin / minioadmin123 |
| **PostgreSQL**     | localhost:5433        | user / password            |
| **Redis**          | localhost:6379        | (sin auth)                 |

---

## 📊 URLs de la Aplicación

| Servicio              | URL                        | Descripción           |
| --------------------- | -------------------------- | ---------------------- |
| **Frontend**    | http://localhost:5173      | Aplicación web        |
| **Backend API** | http://localhost:8000      | API REST               |
| **API Docs**    | http://localhost:8000/docs | Swagger UI interactivo |
| **Keycloak**    | http://localhost:8080      | Admin Console IAM      |
| **MinIO**       | http://localhost:9001      | Console de storage     |

---

## 🧪 Testing

```bash
# Backend
cd backend
pytest --cov=app --cov-report=html

# Ver coverage
open htmlcov/index.html
```

**Tests incluidos**:

- ✅ Tests unitarios de seguridad (JWT, bcrypt)
- ✅ Tests de integración (logbook, incidents, evaluations)
- ✅ Property-based testing con Hypothesis
- ✅ Tests de roles y permisos
- 🔲 Tests de Keycloak integration (TODO)

---

## 📖 Documentación

- **[CONTEXT.md](CONTEXT.md)** - Contexto completo del proyecto (600+ líneas)
- **[docs/keycloak-setup.md](docs/keycloak-setup.md)** - Guía de configuración Keycloak
- **[Plan de Arquitectura](.claude/plans/)** - Diseño arquitectónico completo

---

## 🔄 Autenticación Híbrida

El sistema soporta **dos modos de autenticación simultáneamente**:

### 1. Keycloak OIDC (Recomendado)

```javascript
// Frontend: Login con redirect a Keycloak
const { keycloak } = useKeycloak()
keycloak.login()
```

**Flujo**:

1. Usuario hace click en "Iniciar Sesión"
2. Redirect a Keycloak (http://localhost:8080)
3. Usuario ingresa credenciales
4. Keycloak redirige de vuelta con `code`
5. Frontend intercambia `code` por `access_token` + `refresh_token`
6. Token se auto-refresca cada 10 segundos

### 2. JWT Legacy (Backward Compatibility)

```javascript
// Frontend: Login tradicional
const { login } = useAuth()
await login('estudiante@internado-uv.cl', 'estudiante123')
```

**Flujo**:

1. Usuario ingresa email/password en formulario
2. POST a `/auth/login`
3. Backend retorna JWT firmado
4. JWT se guarda en localStorage

**¿Por qué híbrido?**

- ✅ Migración gradual sin romper la app
- ✅ Rollback instantáneo si Keycloak falla
- ✅ Zero downtime durante migración

---

## 🛠️ Comandos Útiles

### Backend

```bash
# Instalar dependencias
cd backend
pip install -r requirements.txt

# Crear migración
alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones
alembic upgrade head

# Correr tests
pytest

# Correr backend standalone
uvicorn app.main:app --reload
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
# Levantar solo servicios (sin backend/frontend)
docker compose up -d

# Ver logs de un servicio
docker logs -f internado_uv_keycloak

# Detener todo
docker compose down

# Resetear todo (⚠️ ELIMINA DATOS)
docker compose down -v
```

---

## 🚧 Roadmap

### ✅ FASE 1: IAM con Keycloak (COMPLETADA)

- [X] Setup Keycloak en Docker
- [X] Cliente Keycloak en backend
- [X] Autenticación híbrida (Keycloak + JWT)
- [X] Endpoints OAuth2 (/callback, /refresh, /logout)
- [X] Integración React con @react-keycloak/web
- [X] Script de migración de usuarios
- [X] Documentación completa

### 🔲 FASE 2: Storage + Observabilidad (2-3 semanas)

- [ ] Object Storage con MinIO (buckets, upload endpoints)
- [ ] Prometheus + Grafana (métricas + dashboards)
- [ ] Sentry integration (error tracking frontend + backend)
- [ ] Upload de imágenes en procedimientos

### 🔲 FASE 3: Background Jobs + Secrets (2 semanas)

- [ ] Celery workers para emails
- [ ] MailHog para desarrollo
- [ ] HashiCorp Vault para secrets
- [ ] Tareas programadas (backups, reportes)

### 🔲 FASE 4: Documentación Arquitectónica (1 semana)

- [ ] ADRs (Architecture Decision Records)
- [ ] Diagramas detallados (deployment, data flow)
- [ ] Security checklist
- [ ] Guías de deployment (cloud + on-premise)

---

## 🙏 Créditos

Proyecto de título para la carrera de Ingeniería de Software.

**Universidad**: Universidad de Valparaíso
**Facultad**: Odontología
**Año**: 2026

---

## 📄 Licencia

Este proyecto es de uso académico interno.
