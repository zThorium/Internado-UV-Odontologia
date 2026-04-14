#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

HOST=""
USER="ubuntu"
KEY_PATH=""
PORT="22"
REMOTE_DIR="/opt/internado-uv/app"
ENV_FILE="$REPO_ROOT/.env.prod"

usage() {
  cat <<'USAGE'
Uso:
  ./scripts/deploy/aws/deploy-via-ssh.sh \
    --host <EC2_PUBLIC_IP_OR_DNS> \
    --key <PATH_PEM> \
    [--user ubuntu] \
    [--port 22] \
    [--remote-dir /opt/internado-uv/app] \
    [--env-file /ruta/a/.env.prod]

Flujo:
  1) Valida .env.prod
  2) Sincroniza repo por rsync al servidor
  3) Copia .env.prod al servidor
  4) Ejecuta despliegue remoto con docker compose
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      HOST="$2"
      shift 2
      ;;
    --user)
      USER="$2"
      shift 2
      ;;
    --key)
      KEY_PATH="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --remote-dir)
      REMOTE_DIR="$2"
      shift 2
      ;;
    --env-file)
      ENV_FILE="$2"
      shift 2
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

if [[ -z "$HOST" || -z "$KEY_PATH" ]]; then
  usage
  exit 1
fi

if [[ ! -f "$KEY_PATH" ]]; then
  echo "No existe la llave privada: $KEY_PATH"
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "No existe el archivo de entorno: $ENV_FILE"
  exit 1
fi

command -v ssh >/dev/null 2>&1 || { echo "Falta comando ssh"; exit 1; }
command -v scp >/dev/null 2>&1 || { echo "Falta comando scp"; exit 1; }
command -v rsync >/dev/null 2>&1 || { echo "Falta comando rsync"; exit 1; }

SSH_OPTS=(
  -i "$KEY_PATH"
  -p "$PORT"
  -o StrictHostKeyChecking=accept-new
)

SCP_OPTS=(
  -i "$KEY_PATH"
  -P "$PORT"
  -o StrictHostKeyChecking=accept-new
)

echo "[deploy] Validando archivo de entorno..."
"$REPO_ROOT/scripts/deploy/aws/check-env-prod.sh" "$ENV_FILE"

echo "[deploy] Creando directorio remoto..."
ssh "${SSH_OPTS[@]}" "$USER@$HOST" "mkdir -p '$REMOTE_DIR'"

echo "[deploy] Sincronizando c\u00f3digo a $USER@$HOST:$REMOTE_DIR ..."
rsync -az --delete \
  --exclude='.git/' \
  --exclude='.venv/' \
  --exclude='backend/.venv/' \
  --exclude='frontend/node_modules/' \
  --exclude='frontend/dist/' \
  --exclude='backend/reports/' \
  --exclude='backend/.pytest_cache/' \
  --exclude='backend/.coverage' \
  --exclude='backend/coverage.xml' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  --exclude='.env' \
  --exclude='.env.prod' \
  -e "ssh -i $KEY_PATH -p $PORT -o StrictHostKeyChecking=accept-new" \
  "$REPO_ROOT/" "$USER@$HOST:$REMOTE_DIR/"

echo "[deploy] Copiando archivo de entorno a remoto..."
scp "${SCP_OPTS[@]}" "$ENV_FILE" "$USER@$HOST:$REMOTE_DIR/.env.prod"

echo "[deploy] Ejecutando despliegue remoto..."
ssh "${SSH_OPTS[@]}" "$USER@$HOST" "cd '$REMOTE_DIR' && chmod +x scripts/deploy/aws/check-env-prod.sh scripts/deploy/aws/remote-deploy.sh && ./scripts/deploy/aws/remote-deploy.sh --env-file .env.prod"

echo "[deploy] Despliegue finalizado"
