#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env.prod}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[env-check] No existe el archivo: $ENV_FILE"
  exit 1
fi

required_keys=(
  ENVIRONMENT
  SECRET_KEY
  POSTGRES_USER
  POSTGRES_PASSWORD
  POSTGRES_DB
  FRONTEND_URL
  BACKEND_URL
  VITE_API_URL
  VITE_KEYCLOAK_URL
  VITE_KEYCLOAK_REALM
  VITE_KEYCLOAK_CLIENT_ID
  KEYCLOAK_SERVER_URL
  KEYCLOAK_REALM
  KEYCLOAK_CLIENT_ID
  KEYCLOAK_CLIENT_SECRET
  KEYCLOAK_REDIRECT_URI
)

missing=()

get_value() {
  local key="$1"
  local raw
  raw="$(grep -E "^${key}=" "$ENV_FILE" | tail -n 1 || true)"
  raw="${raw#${key}=}"
  echo "$raw"
}

for key in "${required_keys[@]}"; do
  value="$(get_value "$key")"

  if [[ -z "$value" ]]; then
    missing+=("$key (vac\u00edo o no definido)")
    continue
  fi

  if [[ "$value" == *"CAMBIAR"* ]] || [[ "$value" == *"tu-dominio.com"* ]]; then
    missing+=("$key (a\u00fan con valor placeholder)")
  fi
done

recaptcha_enabled="$(get_value "RECAPTCHA_ENABLED")"
recaptcha_secret="$(get_value "RECAPTCHA_SECRET_KEY")"
recaptcha_enabled_lc="$(printf '%s' "$recaptcha_enabled" | tr '[:upper:]' '[:lower:]')"
if [[ "$recaptcha_enabled_lc" == "true" ]]; then
  if [[ -z "$recaptcha_secret" ]] || [[ "$recaptcha_secret" == *"CAMBIAR"* ]]; then
    missing+=("RECAPTCHA_SECRET_KEY (requerido cuando RECAPTCHA_ENABLED=true)")
  fi
fi

if (( ${#missing[@]} > 0 )); then
  echo "[env-check] Faltan variables o tienen placeholders en $ENV_FILE:"
  for item in "${missing[@]}"; do
    echo "  - $item"
  done
  exit 1
fi

echo "[env-check] OK: archivo de entorno validado ($ENV_FILE)"
