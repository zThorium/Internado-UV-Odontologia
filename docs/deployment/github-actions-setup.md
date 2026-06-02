# GitHub Actions — checklist de configuración

Guía para preparar la EC2 y GitHub antes del primer despliegue automático.

## Fase 0 — Verificación en tu máquina (obligatorio)

### 1. Conectividad SSH

```bash
ssh -i /ruta/tu-llave.pem ubuntu@18.234.37.107 "uname -m && docker --version"
```

Debe responder `aarch64` (instancia `t4g.*` = ARM64). Si falla, revisa Security Group y la clave `.pem`.

### 2. Bootstrap de la EC2 (solo la primera vez)

Si Docker no está instalado o no existe `/opt/internado-uv`:

```bash
./scripts/deploy/aws/bootstrap-ec2.sh \
  --host 18.234.37.107 \
  --user ubuntu \
  --key /ruta/tu-llave.pem
```

Cierra y vuelve a abrir la sesión SSH para aplicar el grupo `docker`.

### 3. Archivo `.env.prod`

```bash
cp .env.prod.example .env.prod
# Editar valores reales (sin placeholders CAMBIAR_* ni tu-dominio.com)
./scripts/deploy/aws/check-env-prod.sh .env.prod
```

### 4. Primer despliegue manual de prueba

Confirma que el stack levanta antes de activar GitHub Actions:

```bash
./scripts/deploy/aws/deploy-via-ssh.sh \
  --host 18.234.37.107 \
  --user ubuntu \
  --key /ruta/tu-llave.pem \
  --env-file .env.prod
```

---

## Fase 1 — Security Group (SSH para GitHub Actions)

Los runners de GitHub usan IPs dinámicas. Para deploy automático en cada push a `main`, el puerto **22/tcp** debe ser accesible desde los rangos oficiales de Actions.

1. Obtén los CIDR actuales:
   ```bash
   curl -s https://api.github.com/meta | jq -r '.actions[]'
   ```
2. En AWS → EC2 → Security Groups de la instancia, añade reglas **Inbound** `22/tcp` para esos rangos (o un subconjunto documentado por tu equipo).
3. Mantén también **80/tcp** (frontend) y, si aplica, **8000/tcp** (backend directo).

**No** abras SSH a `0.0.0.0/0` salvo entornos de prueba muy controlados.

> Si solo permites SSH desde tu IP personal, el workflow de deploy fallará con timeout. En ese caso usa despliegue manual con `deploy-via-ssh.sh` hasta abrir los rangos de Actions.

---

## Fase 2 — Secrets en GitHub

Repositorio → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret | Descripción |
|--------|-------------|
| `SSH_HOST` | IP o DNS de la EC2 (ej. `18.234.37.107`). Usa Elastic IP si la IP pública cambia al reiniciar. |
| `SSH_USER` | Usuario SSH (ej. `ubuntu`) |
| `SSH_PRIVATE_KEY` | Contenido completo del archivo `.pem` (incluye `-----BEGIN` / `-----END`) |
| `ENV_PROD` | Contenido completo de tu `.env.prod` validado con `check-env-prod.sh` |

Opcional: en **Environments** → `production`, activa *Required reviewers* para aprobar el primer deploy.

---

## Workflows del repositorio

| Archivo | Cuándo corre |
|---------|----------------|
| `.github/workflows/ci.yml` | Pull requests a `main`; también lo invoca el deploy |
| `.github/workflows/deploy.yml` | Cada push a `main` (tras pasar CI) |

Flujo en `main`: tests + build → rsync a `/opt/internado-uv/app` → `remote-deploy.sh` (build Docker **en la EC2**, ARM64).

---

## Re-ejecutar un deploy

1. **Actions** → **Deploy to EC2** → **Run workflow** (si habilitas `workflow_dispatch` en el futuro), o
2. Haz un nuevo push a `main`, o
3. **Re-run failed jobs** en un run anterior.

---

## Solución de problemas

| Síntoma | Causa probable |
|---------|----------------|
| `ssh: connect ... timed out` en deploy | SG sin rangos de GitHub Actions, IP de EC2 incorrecta, o instancia detenida |
| `Permission denied (publickey)` | `SSH_PRIVATE_KEY` mal copiado o usuario incorrecto |
| `env-check` falla en Actions | Secret `ENV_PROD` con placeholders o claves faltantes |
| Backend no pasa `/health` | Revisar logs: `docker compose ... logs backend` en la EC2 |
| Build Docker lento o OOM | `t4g.small` limitado; considerar instancia mayor |

Ver también: [aws-ssh-deploy.md](./aws-ssh-deploy.md).
