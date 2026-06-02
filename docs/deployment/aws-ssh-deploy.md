# Despliegue en AWS EC2 por SSH

Esta guia usa los scripts del repositorio para desplegar por SSH de forma repetible.

## Scripts incluidos

- `scripts/deploy/aws/bootstrap-ec2.sh`
- `scripts/deploy/aws/check-env-prod.sh`
- `scripts/deploy/aws/deploy-via-ssh.sh`
- `scripts/deploy/aws/remote-deploy.sh`

## Prerrequisitos

1. Instancia EC2 Ubuntu (22.04/24.04) accesible por SSH.
2. Security Group con al menos:
   - `22/tcp` para SSH
   - `80/tcp` para frontend
   - `8000/tcp` si quieres exponer backend directo (opcional)
3. Llave privada `.pem` en tu maquina local.
4. En tu maquina local: `ssh`, `scp`, `rsync`.

## 1) Preparar archivo de entorno de produccion

En tu maquina local:

```bash
cd /ruta/al/proyecto
cp .env.prod.example .env.prod
```

Completa los valores reales en `.env.prod`.

Valida el archivo antes de desplegar:

```bash
./scripts/deploy/aws/check-env-prod.sh .env.prod
```

## 2) Bootstrap inicial de EC2 (solo la primera vez)

```bash
./scripts/deploy/aws/bootstrap-ec2.sh \
  --host <EC2_PUBLIC_IP_OR_DNS> \
  --user ubuntu \
  --key /ruta/tu-llave.pem
```

Al finalizar, reconecta tu sesion SSH para aplicar el grupo `docker`.

## 3) Desplegar por SSH

```bash
./scripts/deploy/aws/deploy-via-ssh.sh \
  --host <EC2_PUBLIC_IP_OR_DNS> \
  --user ubuntu \
  --key /ruta/tu-llave.pem \
  --env-file .env.prod
```

Este comando:

1. Valida `.env.prod`
2. Sincroniza el repo al servidor (`/opt/internado-uv/app` por defecto)
3. Copia `.env.prod` al servidor
4. Ejecuta build + up con `docker compose` en remoto
5. Verifica salud del backend y frontend

## 4) Comandos utiles en el servidor

```bash
cd /opt/internado-uv/app

# Estado de contenedores
docker compose --env-file .env.prod -f docker-compose.prod.yml ps

# Logs de backend
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f backend

# Logs de frontend
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f frontend

# Reiniciar stack
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

## 5) Re-despliegues

Para nuevos cambios de codigo, ejecuta nuevamente `deploy-via-ssh.sh`.

## Notas

- El frontend usa variables `VITE_*` en tiempo de build.
- El backend toma el resto de variables desde `.env.prod`.
- Si usas dominio real, configura DNS y TLS (Nginx/ALB/CloudFront) en una etapa posterior.
