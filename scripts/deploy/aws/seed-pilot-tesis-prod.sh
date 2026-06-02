#!/usr/bin/env bash
# Ejecuta seed_pilot_tesis en la EC2 de prod (requiere CSV con usuarios reales).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
HOST=""
KEY_PATH=""
CSV_PATH="${REPO_ROOT}/docs/testing/data/pilot-users.uv-tesis.csv"

usage() {
  cat <<'USAGE'
Uso:
  ./scripts/deploy/aws/seed-pilot-tesis-prod.sh --host IP --key pem [--csv pilot-users.csv]

Requiere docs/testing/data/pilot-users.csv (copiar desde pilot-users.example.csv).
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --key) KEY_PATH="$2"; shift 2 ;;
    --csv) CSV_PATH="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Arg desconocido: $1"; usage; exit 1 ;;
  esac
done

[[ -n "$HOST" && -n "$KEY_PATH" ]] || { usage; exit 1; }
[[ -f "$CSV_PATH" ]] || { echo "Falta CSV: $CSV_PATH (copia pilot-users.example.csv)"; exit 1; }

REMOTE_DIR="/opt/internado-uv/app"
SSH_OPTS=(-i "$KEY_PATH" -o StrictHostKeyChecking=accept-new)

echo "[seed-pilot] Sincronizando scripts..."
rsync -az \
  "$REPO_ROOT/backend/scripts/seed_utils.py" \
  "$REPO_ROOT/backend/scripts/create_user.py" \
  "$REPO_ROOT/backend/scripts/seed_pilot_tesis.py" \
  -e "ssh ${SSH_OPTS[*]}" \
  "ubuntu@$HOST:$REMOTE_DIR/backend/scripts/"

scp "${SSH_OPTS[@]}" "$CSV_PATH" "ubuntu@$HOST:$REMOTE_DIR/docs/testing/data/pilot-users.csv"

ssh "${SSH_OPTS[@]}" "ubuntu@$HOST" "bash -lc '
  cd $REMOTE_DIR
  BACKEND=\$(docker ps --format \"{{.Names}}\" | grep backend | head -1)
  for f in seed_utils.py create_user.py seed_pilot_tesis.py; do
    docker cp backend/scripts/\$f \$BACKEND:/app/scripts/\$f
  done
  mkdir -p docs/testing/data
  docker cp docs/testing/data/pilot-users.csv \$BACKEND:/tmp/pilot-users.csv
  if docker compose version >/dev/null 2>&1; then
    docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T backend \
      python -m scripts.seed_pilot_tesis --csv /tmp/pilot-users.csv
  else
    docker-compose --env-file .env.prod -f docker-compose.prod.yml exec -T backend \
      python -m scripts.seed_pilot_tesis --csv /tmp/pilot-users.csv
  fi
'"
