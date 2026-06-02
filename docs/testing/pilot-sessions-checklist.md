# Checklist — Sesiones piloto internas (1–2 sesiones)

Ejecutar **antes** de reclutar a los 8–12 participantes formales. Ideal: profesora guía + investigador, un participante por rol.

## Pre-requisitos técnicos

- [ ] Stack prod responde: `http://18.234.37.107` y `/health`
- [ ] Cohorte **Piloto Tesis 2026** creada
- [ ] 3 cuentas piloto (1 estudiante, 1 tutor, 1 coordinador) con assignment de prueba
- [ ] Cuentas `@demo.internado-uv.cl` **no** usadas en estas sesiones
- [ ] Script `seed_pilot_tesis.py` o `create_user.py` probado en contenedor backend

## Por cada sesión piloto

| Ítem | Estudiante | Tutor | Coordinador |
|------|:----------:|:-----:|:-----------:|
| Consentimiento explicado (puede ser borrador) | ☐ | ☐ | ☐ |
| Login sin bloqueos | ☐ | ☐ | ☐ |
| Guion completable en ≤ 30 min | ☐ | ☐ | ☐ |
| Escenario [PRUEBA TESIS] funciona | ☐ | N/A | ☐ |
| Notas de fricción anotadas | ☐ | ☐ | ☐ |

## Ajustes post-piloto (documentar aquí)

| Fecha | Rol | Problema detectado | Cambio al guion / sistema |
|-------|-----|-------------------|---------------------------|
| | | | |

## Criterio para pasar a sesiones reales

- [ ] Las 3 cuentas piloto completan el guion sin errores críticos del sistema
- [ ] Tiempos dentro de 20–30 min por rol
- [ ] Consentimiento final revisado con profesora guía
- [ ] CSV `user-tests-real-2026.csv` probado con filas P-piloto

Cuando todo esté marcado, programar reclutamiento formal (ver [`user-testing-protocol-real.md`](user-testing-protocol-real.md)).
