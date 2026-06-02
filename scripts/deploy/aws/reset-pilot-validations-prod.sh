#!/usr/bin/env bash
# Quita validaciones de tutor en bitácoras demo (estudiante01-04) en prod EC2.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
HOST=""
KEY_PATH=""
DRY_RUN=""

usage() {
  cat <<'USAGE'
Uso:
  ./scripts/deploy/aws/reset-pilot-validations-prod.sh --host IP --key pem [--dry-run]
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --key) KEY_PATH="$2"; shift 2 ;;
    --dry-run) DRY_RUN="--dry-run"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Arg desconocido: $1"; usage; exit 1 ;;
  esac
done

[[ -n "$HOST" && -n "$KEY_PATH" ]] || { usage; exit 1; }

REMOTE_DIR="/opt/internado-uv/app"
SSH_OPTS=(-i "$KEY_PATH" -o StrictHostKeyChecking=accept-new)

rsync -az \
  "$REPO_ROOT/backend/scripts/reset_pilot_logbook_validations.py" \
  -e "ssh ${SSH_OPTS[*]}" \
  "ubuntu@$HOST:$REMOTE_DIR/backend/scripts/"

ssh "${SSH_OPTS[@]}" "ubuntu@$HOST" "bash -lc '
  cd $REMOTE_DIR
  BACKEND=\$(docker ps --format \"{{.Names}}\" | grep backend | head -1)
  docker cp backend/scripts/reset_pilot_logbook_validations.py \$BACKEND:/app/scripts/reset_pilot_logbook_validations.py
  EXEC=\"docker-compose --env-file .env.prod -f docker-compose.prod.yml exec -T\"
  if docker compose version >/dev/null 2>&1; then
    EXEC=\"docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T\"
  fi
  \$EXEC -e ALLOW_RESET_VALIDATIONS=1 backend \
    python -m scripts.reset_pilot_logbook_validations $DRY_RUN
'"
