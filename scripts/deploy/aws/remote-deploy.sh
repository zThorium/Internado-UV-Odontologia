#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

ENV_FILE=".env.prod"
COMPOSE_FILE="docker-compose.prod.yml"
PRUNE_IMAGES="false"

usage() {
  cat <<'USAGE'
Uso:
  ./scripts/deploy/aws/remote-deploy.sh [--env-file .env.prod] [--compose-file docker-compose.prod.yml] [--prune-images]

Ejecutar este script en el servidor remoto, dentro del repositorio sincronizado.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --compose-file)
      COMPOSE_FILE="$2"
      shift 2
      ;;
    --prune-images)
      PRUNE_IMAGES="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Argumento no reconocido: $1"
      usage
      exit 1
      ;;
  esac
done

cd "$REPO_ROOT"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[remote-deploy] Falta archivo de entorno: $ENV_FILE"
  exit 1
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "[remote-deploy] Falta archivo compose: $COMPOSE_FILE"
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "[remote-deploy] docker no est\u00e1 instalado"
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")
else
  echo "[remote-deploy] No se encontr\u00f3 docker compose"
  exit 1
fi

echo "[remote-deploy] Validando variables de entorno..."
./scripts/deploy/aws/check-env-prod.sh "$ENV_FILE"

echo "[remote-deploy] Construyendo im\u00e1genes (pull latest base)..."
"${COMPOSE_CMD[@]}" build --pull

echo "[remote-deploy] Levantando stack de producci\u00f3n..."
if ! "${COMPOSE_CMD[@]}" up -d --remove-orphans; then
  echo "[remote-deploy] 'up' fall\u00f3; aplicando fallback con ciclo down/up..."
  "${COMPOSE_CMD[@]}" down --remove-orphans
  "${COMPOSE_CMD[@]}" up -d --remove-orphans
fi

echo "[remote-deploy] Estado de contenedores:"
"${COMPOSE_CMD[@]}" ps

if command -v curl >/dev/null 2>&1; then
  echo "[remote-deploy] Esperando healthcheck de backend..."
  BACKEND_OK="false"
  for _ in $(seq 1 40); do
    if curl -fsS http://localhost:8000/health >/dev/null 2>&1; then
      BACKEND_OK="true"
      break
    fi
    sleep 2
  done

  if [[ "$BACKEND_OK" != "true" ]]; then
    echo "[remote-deploy] Backend no respondi\u00f3 en /health. Revisa logs:"
    "${COMPOSE_CMD[@]}" logs --tail=120 backend
    exit 1
  fi

  echo "[remote-deploy] Verificando frontend..."
  if ! curl -fsS http://localhost/ >/dev/null 2>&1; then
    echo "[remote-deploy] Frontend no respondi\u00f3 en puerto 80. Revisa logs:"
    "${COMPOSE_CMD[@]}" logs --tail=120 frontend
    exit 1
  fi
fi

if [[ "$PRUNE_IMAGES" == "true" ]]; then
  echo "[remote-deploy] Limpiando im\u00e1genes hu\u00e9rfanas..."
  docker image prune -f
fi

echo "[remote-deploy] Despliegue completado correctamente"
