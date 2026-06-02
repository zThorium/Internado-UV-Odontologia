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

## 6) Despliegue automatico con GitHub Actions

El repositorio incluye workflows en `.github/workflows/`:

| Workflow | Disparador | Funcion |
|----------|------------|---------|
| `ci.yml` | Pull request a `main` | `pytest` (backend) + `npm run build` (frontend) |
| `deploy.yml` | Push a `main` | CI + rsync/SSH a EC2 + `remote-deploy.sh` |

El build de imagenes Docker ocurre **en la EC2 (ARM64)**, no en el runner de GitHub, para compatibilidad con instancias `t4g.*`.

### Configuracion previa (una vez)

Sigue el checklist completo en [github-actions-setup.md](./github-actions-setup.md):

1. Verificar SSH, bootstrap y primer deploy manual (Fase 0)
2. Abrir puerto 22 a los CIDR de GitHub Actions en el Security Group (Fase 1)
3. Crear secrets: `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`, `ENV_PROD` (Fase 2)

### Flujo en cada push a `main`

```text
push main → CI (tests + build) → rsync a /opt/internado-uv/app → scp .env.prod → remote-deploy.sh
```

### Re-ejecutar

En GitHub: **Actions** → selecciona el workflow **Deploy to EC2** → **Re-run all jobs** en un run fallido, o haz un nuevo push a `main`.

## Notas

- El frontend usa variables `VITE_*` en tiempo de build.
- El backend toma el resto de variables desde `.env.prod`.
- Si usas dominio real, configurar DNS y TLS (Nginx/ALB/CloudFront) en una etapa posterior.
- La IP publica de la EC2 puede cambiar al reiniciar; conviene asignar una **Elastic IP** y actualizar el secret `SSH_HOST`.
