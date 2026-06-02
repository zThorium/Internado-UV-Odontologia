# Roster — Piloto tesis 2026 (usuarios reales)

Cohorte: **Piloto Tesis 2026**  
URL prod: http://18.234.37.107

## Participantes registrados

| Email | Rol en sistema | Nombre | Código sesión (asignar) |
|-------|----------------|--------|-------------------------|
| felipe.vidal@uv.cl | `coordinator` | Felipe Vidal | P-coord-01 |
| marjorie.borgeat@uv.cl | `tutor` | Marjorie Borgeat | P-tutor-01 |
| karina.cordero@uv.cl | `tutor` | Karina Cordero | P-tutor-02 |

### Estudiantes asignados (cuentas demo para pruebas de tutor)

Las tutoras tienen estudiantes de la cohorte demo vinculados en **Piloto Tesis 2026** (solo para probar evaluación y asistencia):

| Tutora | Estudiantes asignados | Campo clínico |
|--------|----------------------|---------------|
| marjorie.borgeat@uv.cl | estudiante01@demo.internado-uv.cl, estudiante02@demo.internado-uv.cl | CESFAM Lorca / Hospital Base Valdivia |
| karina.cordero@uv.cl | estudiante03@demo.internado-uv.cl, estudiante04@demo.internado-uv.cl | CESFAM Villa Colín / CESFAM Paillaco |

Login estudiantes demo: contraseña `Demo2026!` (distinta del piloto UV).

Si el botón **Validar** aparece bloqueado, las bitácoras ya tienen validación del seed demo. Reset:

```bash
./scripts/deploy/aws/reset-pilot-validations-prod.sh \
  --host 18.234.37.107 \
  --key ~/Downloads/internado-uv.pem
```

## Pendiente

- Estudiantes **reales** @uv.cl para las sesiones formales de tesis (mínimo 4): agregar al CSV cuando los tengas.

## Contraseña inicial (entregar en persona)

Contraseña temporal compartida del piloto: **`PilotoTesis2026!`**

Cambiar tras la primera sesión si la facultad lo requiere. No publicar en la tesis.

## Alta en prod

```bash
cp docs/testing/data/pilot-users.uv-tesis.csv docs/testing/data/pilot-users.csv
# Editar CSV: agregar estudiantes y assignments si aplica

./scripts/deploy/aws/seed-pilot-tesis-prod.sh \
  --host 18.234.37.107 \
  --key ~/Downloads/internado-uv.pem \
  --csv docs/testing/data/pilot-users.uv-tesis.csv
```

O en el servidor:

```bash
docker-compose --env-file .env.prod -f docker-compose.prod.yml exec -T backend \
  python -m scripts.seed_pilot_tesis --csv /tmp/pilot-users.uv-tesis.csv
```

## Mapeo moderador (no commitear nombres reales en CSV de resultados)

Guardar en hoja privada:

| Código tesis | Email real |
|--------------|------------|
| P01 | (estudiante por definir) |
| P-coord-01 | felipe.vidal@uv.cl |
| P-tutor-01 | marjorie.borgeat@uv.cl |
| P-tutor-02 | karina.cordero@uv.cl |

Los resultados van a [`data/user-tests-real-2026.csv`](data/user-tests-real-2026.csv) solo con `P01`, `P02`, etc.
