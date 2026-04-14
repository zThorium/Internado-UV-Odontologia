#!/usr/bin/env bash
set -euo pipefail

HOST=""
USER="ubuntu"
KEY_PATH=""
PORT="22"

usage() {
  cat <<'USAGE'
Uso:
  ./scripts/deploy/aws/bootstrap-ec2.sh --host <EC2_PUBLIC_IP_OR_DNS> --key <PATH_PEM> [--user ubuntu] [--port 22]

Que hace:
  1) Instala dependencias base en EC2 (docker, compose plugin, git, rsync)
  2) Habilita y levanta Docker
  3) Agrega tu usuario al grupo docker
  4) Crea /opt/internado-uv para despliegue
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

SSH_OPTS=(
  -i "$KEY_PATH"
  -p "$PORT"
  -o StrictHostKeyChecking=accept-new
)

echo "[bootstrap] Conectando a $USER@$HOST ..."

ssh "${SSH_OPTS[@]}" "$USER@$HOST" 'bash -s' <<'EOF'
set -euo pipefail

REMOTE_USER="$(id -un)"

echo "[bootstrap] Actualizando paquetes..."
sudo apt-get update -y

echo "[bootstrap] Instalando dependencias base..."
sudo apt-get install -y \
  ca-certificates \
  curl \
  git \
  gnupg \
  lsb-release \
  rsync \
  unzip

if ! command -v docker >/dev/null 2>&1; then
  echo "[bootstrap] Instalando docker.io..."
  sudo apt-get install -y docker.io
else
  echo "[bootstrap] Docker ya estaba instalado"
fi

if ! sudo docker compose version >/dev/null 2>&1; then
  echo "[bootstrap] Instalando docker compose plugin..."
  if ! sudo apt-get install -y docker-compose-plugin; then
    echo "[bootstrap] docker-compose-plugin no disponible, instalando docker-compose legacy"
    sudo apt-get install -y docker-compose
  fi
else
  echo "[bootstrap] Docker Compose plugin ya estaba instalado"
fi

echo "[bootstrap] Habilitando servicio docker..."
sudo systemctl enable docker
sudo systemctl restart docker

echo "[bootstrap] Agregando $REMOTE_USER al grupo docker..."
sudo usermod -aG docker "$REMOTE_USER" || true

echo "[bootstrap] Creando directorio de despliegue..."
sudo mkdir -p /opt/internado-uv
sudo chown -R "$REMOTE_USER":"$REMOTE_USER" /opt/internado-uv

echo "[bootstrap] Listo"
EOF

echo "[bootstrap] Completado. Cierra y vuelve a abrir tu sesion SSH para aplicar el grupo docker."