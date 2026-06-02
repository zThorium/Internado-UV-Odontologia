# Cuentas y roles disponibles

## Roles que existen en el sistema

- `coordinator`
- `tutor`
- `student`

No existe el rol `admin` en el modelo actual.

## Cuentas de prueba (desarrollo)

Al ejecutar el seed (`python -m scripts.seed`) se crean estas cuentas:

- Coordinador: `coord@internado-uv.cl` / `coord123`
- Tutor: `tutor@internado-uv.cl` / `tutor123`
- Estudiante: `estudiante@internado-uv.cl` / `estudiante123`

## Piloto tesis — usuarios reales (prod)

Cohorte **Piloto Tesis 2026**. Roster: [`docs/testing/pilot-users-roster.md`](docs/testing/pilot-users-roster.md).

| Email | Rol |
|-------|-----|
| felipe.vidal@uv.cl | Coordinador |
| marjorie.borgeat@uv.cl | Tutora clínica |
| karina.cordero@uv.cl | Tutora clínica |

Contraseña temporal del piloto: `PilotoTesis2026!` (entregar en persona; agregar estudiantes cuando los tengas).

CSV: [`docs/testing/data/pilot-users.uv-tesis.csv`](docs/testing/data/pilot-users.uv-tesis.csv)

Documentación: [`docs/testing/user-testing-protocol-real.md`](docs/testing/user-testing-protocol-real.md)

### Crear un usuario (cualquier rol)

```bash
cd backend
python -m scripts.create_user \
  --email nombre@uv.cl \
  --name "Nombre Apellido" \
  --role student \
  --password "ContraseñaTemporalSegura"
```

Sincroniza PostgreSQL + Keycloak.

### Cohort + assignments desde CSV

1. Editar [`docs/testing/data/pilot-users.uv-tesis.csv`](docs/testing/data/pilot-users.uv-tesis.csv) (estudiantes + assignments).
2. Ejecutar:

```bash
python -m scripts.seed_pilot_tesis --csv ../docs/testing/data/pilot-users.csv
```

En EC2:

```bash
./scripts/deploy/aws/seed-pilot-tesis-prod.sh \
  --host 18.234.37.107 \
  --key ~/Downloads/internado-uv.pem \
  --csv docs/testing/data/pilot-users.uv-tesis.csv
```

## Otras formas de crear cuentas

### Coordinador (legacy)

```bash
COORDINATOR_EMAIL="tu_correo@dominio.com" \
COORDINATOR_PASSWORD="TuPasswordSegura123" \
COORDINATOR_NAME="Nombre Apellido" \
python -m scripts.create_coordinator
```

### Seed desarrollo (3 cuentas base)

```bash
python -m scripts.seed
```
