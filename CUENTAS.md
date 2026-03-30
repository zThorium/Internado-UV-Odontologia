# Cuentas y roles disponibles

## Roles que existen en el sistema

Actualmente el backend solo acepta estos roles:

- `coordinator`
- `tutor`
- `student`

No existe el rol `admin` en el modelo actual.

## Cuentas de prueba (desarrollo)

Al ejecutar el seed (`python -m scripts.seed`) se crean estas cuentas:

- Coordinador: `coord@internado-uv.cl` / `coord123`
- Tutor: `tutor@internado-uv.cl` / `tutor123`
- Estudiante: `estudiante@internado-uv.cl` / `estudiante123`

## Formas de crear cuentas

### 1) Crear cuentas demo (rápido)

Desde `backend/`:

```bash
python -m scripts.seed
```

Esto intenta crear las 3 cuentas de prueba (si no existen).

### 2) Crear coordinador personalizado (producción o local)

Desde `backend/`:

```bash
COORDINATOR_EMAIL="tu_correo@dominio.com" \
COORDINATOR_PASSWORD="TuPasswordSegura123" \
COORDINATOR_NAME="Nombre Apellido" \
python -m scripts.create_coordinator
```

### 3) Crear tutor o estudiante personalizados

No hay script dedicado para crear tutor/estudiante por variables de entorno.

Opciones actuales:

- Editar temporalmente `scripts/seed.py` y agregar usuarios en `SEED_USERS`.
- Crear un script similar a `create_coordinator.py` para `tutor` y `student`.

## Recomendación

Para trabajo diario, conviene agregar un script único tipo `create_user.py` que reciba:

- `--email`
- `--password`
- `--name`
- `--role` (`student|tutor|coordinator`)

Así puedes crear cualquier cuenta sin tocar código cada vez.
