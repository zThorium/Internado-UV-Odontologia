# Limpieza post-piloto — incidentes [PRUEBA TESIS]

Tras completar las sesiones de usabilidad, eliminar o cerrar datos de prueba para no mezclarlos con operación real.

## Incidentes ficticios

Identificar en el panel de coordinador incidentes con:

- Título que contiene `[PRUEBA TESIS]` o `[DEMO]`
- Descripción con *"ESCENARIO FICTICIO"*

**Acción recomendada:** marcar como **Resuelto** con nota interna *"Cierre piloto tesis"*.

## Opcional — SQL en servidor (solo si se requiere borrado)

Desde la EC2, con extremo cuidado:

```bash
cd /opt/internado-uv/app
docker-compose --env-file .env.prod -f docker-compose.prod.yml exec -T db \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
  "SELECT id, title, status FROM incidents WHERE title LIKE '%PRUEBA TESIS%';"
```

No ejecutar `DELETE` sin respaldo. Preferir cierre desde la UI.

## Cuentas piloto

- Cuentas `@demo.internado-uv.cl`: pueden permanecer para capacitación.
- Cuentas `@uv.cl` del piloto: desactivar (`is_active=false`) o rotar contraseñas según acuerdo con la facultad.

## Cohorte

La cohorte **Piloto Tesis 2026** puede archivarse (`is_active=false`) cuando finalice el estudio.

## Checklist

- [ ] Incidentes [PRUEBA TESIS] cerrados o eliminados
- [ ] Tabla moderador (nombre real ↔ P01) guardada fuera del repo
- [ ] CSV pseudonimizado respaldado para tesis
- [ ] Reporte generado con `analyze_user_tests.py --input user-tests-real-2026.csv`
