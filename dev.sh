#!/usr/bin/env bash
# dev.sh — Levanta el entorno de desarrollo completo
# Uso: ./dev.sh
# Para detener todo: Ctrl+C

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT_DIR/.venv"

# ─── Colores ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[dev]${NC} $1"; }
success() { echo -e "${GREEN}[dev]${NC} $1"; }
warn()    { echo -e "${YELLOW}[dev]${NC} $1"; }
error()   { echo -e "${RED}[dev]${NC} $1"; exit 1; }

# ─── Cleanup al salir ──────────────────────────────────────────────────────────
PIDS=()
cleanup() {
  echo ""
  info "Deteniendo servicios..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  info "Deteniendo servicios Docker (db, keycloak, redis, minio)..."
  docker compose stop db keycloak redis minio 2>/dev/null || true
  success "Todo detenido. ¡Hasta luego!"
}
trap cleanup EXIT INT TERM

# ─── 1. Verificar dependencias del sistema ─────────────────────────────────────
info "Verificando dependencias del sistema..."
command -v docker  >/dev/null 2>&1 || error "Docker no encontrado. Instálalo desde https://docker.com"
command -v node    >/dev/null 2>&1 || error "Node.js no encontrado. Instálalo desde https://nodejs.org"
command -v python3 >/dev/null 2>&1 || error "Python 3 no encontrado."

# ─── 2. Virtualenv Python ──────────────────────────────────────────────────────
if [ ! -d "$VENV" ]; then
  info "Creando entorno virtual Python..."
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

# ─── 3. Dependencias Python ────────────────────────────────────────────────────
info "Instalando dependencias Python..."
pip install -q -r "$ROOT_DIR/backend/requirements.txt"
success "Dependencias Python OK"

# ─── 4. Dependencias Node ──────────────────────────────────────────────────────
if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
  info "Instalando dependencias Node (npm install)..."
  npm install --prefix "$ROOT_DIR/frontend" --silent
  success "Dependencias Node OK"
else
  info "node_modules ya existe, omitiendo npm install"
fi

# ─── 5. Servicios Docker (Base de datos + Keycloak + Redis + MinIO) ──────────
info "Levantando servicios Docker..."
info "· PostgreSQL (base de datos)"
info "· Keycloak (autenticación IAM)"
info "· Redis (cache & queue)"
info "· MinIO (object storage)"
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d db keycloak redis minio

info "Esperando que PostgreSQL esté listo..."
for i in $(seq 1 40); do
  if docker compose -f "$ROOT_DIR/docker-compose.yml" exec -T db \
      psql -U user -d internado_uv -c "SELECT 1" >/dev/null 2>&1; then
    success "PostgreSQL listo"
    break
  fi
  if [ "$i" -eq 40 ]; then
    error "PostgreSQL no respondió después de 40 segundos"
  fi
  sleep 1
done

info "Esperando que Keycloak esté listo..."
for i in $(seq 1 90); do
  if curl -sf http://localhost:8080/realms/master/.well-known/openid-configuration >/dev/null 2>&1; then
    success "Keycloak listo en http://localhost:8080"
    break
  fi
  if [ "$i" -eq 90 ]; then
    warn "Keycloak no respondió. Puede necesitar más tiempo. Continuando..."
    break
  fi
  sleep 1
done

# ─── 5.5. Configurar Keycloak (realm, roles, clientes) ────────────────────────
info "Configurando Keycloak (realm, roles, clientes)..."
cd "$ROOT_DIR/backend"
if python -m scripts.setup_keycloak; then
  success "Keycloak configurado correctamente"
  
  # Actualizar el .env con el client secret correcto
  info "Actualizando archivo .env con client secret..."
  python -m scripts.get_and_setup_env >/dev/null 2>&1 || true
else
  warn "Hubo un problema configurando Keycloak. Revisa los logs arriba."
fi

success "Redis listo en localhost:6379"
success "MinIO listo en http://localhost:9000 (console: http://localhost:9001)"

# ─── 6. Migraciones ────────────────────────────────────────────────────────────
info "Ejecutando migraciones Alembic..."
cd "$ROOT_DIR/backend"
# Forzamos URL de desarrollo para evitar conflictos con PostgreSQL local en 5432.
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5433/internado_uv"
alembic upgrade head
success "Migraciones OK"

# ─── 7. Seed (solo si la tabla users está vacía) ───────────────────────────────
USER_COUNT=$(docker compose -f "$ROOT_DIR/docker-compose.yml" exec -T db \
  psql -U user -d internado_uv -tAc "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "0")

if [ "$USER_COUNT" -eq 0 ] 2>/dev/null; then
  info "Cargando datos de prueba (seed)..."
  python -m scripts.seed
  success "Seed OK — usuarios creados:"
  echo -e "  ${GREEN}Coordinador:${NC} coord@internado-uv.cl / coord123"
  echo -e "  ${GREEN}Tutor:${NC}       tutor@internado-uv.cl / tutor123"
  echo -e "  ${GREEN}Estudiante:${NC}  estudiante@internado-uv.cl / estudiante123"
else
  info "Base de datos ya tiene datos, omitiendo seed"
fi

# ─── 8. Levantar backend ───────────────────────────────────────────────────────
info "Iniciando backend FastAPI en http://localhost:8000 ..."
cd "$ROOT_DIR/backend"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
PIDS+=($BACKEND_PID)

# Esperar a que el backend responda
for i in $(seq 1 20); do
  if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    success "Backend listo"
    break
  fi
  sleep 1
done

# ─── 9. Levantar frontend ──────────────────────────────────────────────────────
info "Iniciando frontend Vite en http://localhost:5173 ..."
cd "$ROOT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
PIDS+=($FRONTEND_PID)

# ─── 10. Listo ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Entorno de desarrollo listo${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${YELLOW}Aplicación:${NC}"
echo -e "    Frontend:       ${CYAN}http://localhost:5173${NC}"
echo -e "    Backend:        ${CYAN}http://localhost:8000${NC}"
echo -e "    API Docs:       ${CYAN}http://localhost:8000/docs${NC}"
echo ""
echo -e "  ${YELLOW}Servicios:${NC}"
echo -e "    Keycloak Admin: ${CYAN}http://localhost:8080${NC}  (admin/admin123)"
echo -e "    MinIO Console:  ${CYAN}http://localhost:9001${NC}  (minioadmin/minioadmin123)"
echo -e "    PostgreSQL:     ${CYAN}localhost:5433${NC}  (user/password)"
echo -e "    Redis:          ${CYAN}localhost:6379${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  Presiona ${YELLOW}Ctrl+C${NC} para detener todo"
echo ""

# Mantener el script vivo esperando los procesos hijos
wait
