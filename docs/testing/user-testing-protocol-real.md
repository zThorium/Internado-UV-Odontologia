# Protocolo de pruebas con usuarios reales — Tesis

Complementa [`user-testing-protocol.md`](user-testing-protocol.md) con guiones operativos para sesiones en producción (`http://18.234.37.107`).

**Roster actual del piloto:** [`pilot-users-roster.md`](pilot-users-roster.md)

## Antes de cada sesión

1. Consentimiento firmado ([`consentimiento-informado-plantilla.md`](consentimiento-informado-plantilla.md)).
2. Cuenta piloto creada (cohorte **Piloto Tesis 2026**).
3. Credenciales en sobre cerrado o pantalla compartida controlada por el moderador.
4. Navegador actualizado (Chrome / Firefox / Edge).
5. Cronómetro y hoja de registro del moderador ([`moderator-session-log-template.md`](moderator-session-log-template.md)).

## Escenario ficticio de incidentes (obligatorio)

Entregar al participante **solo si su rol incluye incidentes** (estudiante):

> *"Por favor registra un incidente de **capacitación [PRUEBA TESIS]**. Usa tipo **Otro**, urgencia **Baja**, fecha de hoy, y copia exactamente este texto en la descripción:*
>
> *'ESCENARIO FICTICIO DE PRUEBA DE USABILIDAD. No describe un hecho real. Solo validación del sistema para tesis.'*
>
> *Título sugerido: [PRUEBA TESIS] Incidente ficticio."*

**No** pedir relatos reales. Tras el estudio, marcar como resueltos o limpiar (ver [`post-pilot-cleanup.md`](post-pilot-cleanup.md)).

---

## Guion — Estudiante (20–25 min)

| # | Tarea | Instrucción al participante | Éxito (0/1) |
|---|-------|----------------------------|-------------|
| 1 | Login | Inicia sesión con tu cuenta piloto | Accede al panel estudiante |
| 2 | Asistencia | Registra tu asistencia de hoy como **Presente** | Registro guardado sin ayuda del moderador |
| 3 | Bitácora | Crea la bitácora de la semana actual con **2 procedimientos** del catálogo | Entrada creada y visible en historial |
| 4 | Incidente | Sigue el escenario ficticio [PRUEBA TESIS] | Incidente enviado con texto estandarizado |
| 5 | Consulta | Abre tu bitácora y el incidente recién creado | Encuentra ambos registros |
| 6 | Satisfacción | Escala 1–5 + 2 preguntas abiertas (ver abajo) | — |

**Preguntas abiertas:**

1. ¿Qué fue lo más fácil de usar?
2. ¿Qué cambiarías o qué te confundió?

**Prueba de privacidad (verbal):** *"¿Crees que tu tutor puede leer tu bitácora o tus incidentes?"* — Anotar respuesta (refuerzo esperado: no debería).

---

## Guion — Tutor (20–25 min)

| # | Tarea | Instrucción | Éxito (0/1) |
|---|-------|-------------|-------------|
| 1 | Login | Inicia sesión | Panel tutor visible |
| 2 | Estudiantes | Abre la lista de estudiantes asignados | Ve al menos un estudiante del piloto |
| 3 | Evaluación | Completa una evaluación Likert para un estudiante | Evaluación guardada (≤ 3 pantallas) |
| 4 | Validación bitácora | Abrir **Ver detalle**, revisar procedimientos y bienestar, luego **Confirmar validación** | Validación registrada tras revisar detalle |
| 5 | Asistencia | Revisa asistencia de un estudiante asignado | Ve registros o estado |
| 6 | Privacidad | *"¿Dónde verías los incidentes confidenciales del estudiante?"* | No encuentra acceso (comportamiento esperado) |
| 7 | Satisfacción | Escala 1–5 + comentarios | — |

**Preguntas abiertas:**

1. ¿El flujo de evaluación fue simple?
2. ¿Algo te bloqueó o faltó información en pantalla?

---

## Guion — Coordinador (25–30 min)

| # | Tarea | Instrucción | Éxito (0/1) |
|---|-------|-------------|-------------|
| 1 | Login | Inicia sesión | Dashboard coordinador |
| 2 | Overview | Revisa resumen / semáforos de estudiantes del **Piloto Tesis 2026** | Identifica al menos un estudiante |
| 3 | Alertas | Abre detalle de alertas de un estudiante | Ve listado de alertas |
| 4 | Bitácoras | Consulta bitácora de un estudiante del piloto | Entrada visible |
| 5 | Evaluaciones | Revisa evaluaciones de tutores | Al menos una evaluación listada |
| 6 | Incidentes | Abre panel de incidentes (incl. [PRUEBA TESIS] si existe) | Lista accesible |
| 7 | Asignaciones | Verifica o crea assignment estudiante–tutor en cohorte piloto | Assignment coherente |
| 8 | Satisfacción | Escala 1–5 + comentarios | — |

**Preguntas abiertas:**

1. ¿El dashboard te da la visibilidad que necesitas?
2. ¿Qué información extra agregarías?

---

## Registro post-sesión

Tras cada sesión, completar una fila en [`data/user-tests-real-2026.csv`](data/user-tests-real-2026.csv):

```csv
P01,student,1,1,1,0,4,"Comentario breve pseudonimizado"
```

Campos `task_*`: `1` = completada sin ayuda sustancial, `0` = no completada o completada solo con ayuda del moderador.

Generar reporte:

```bash
cd backend
python scripts/analyze_user_tests.py \
  --input ../docs/testing/data/user-tests-real-2026.csv \
  --title "Pruebas con usuarios reales — Tesis 2026"
```

---

## Criterios de éxito académico

- Completitud por tarea **≥ 80%**
- Satisfacción promedio **≥ 4.0 / 5**
- Hallazgos cualitativos documentados con acciones de mejora

---

## Distribución de participantes

| Perfil | Mínimo | Ideal |
|--------|--------|-------|
| Estudiante | 4 | 5–6 |
| Tutor | 2 | 3–4 |
| Coordinador | 2 | 2 |

Total mínimo: **8** | Ideal: **12**

---

## Referencias

- [`consentimiento-informado-plantilla.md`](consentimiento-informado-plantilla.md)
- [`moderator-session-log-template.md`](moderator-session-log-template.md)
- [`pilot-sessions-checklist.md`](pilot-sessions-checklist.md)
- [`tesis-user-testing-metodologia-resultados.md`](tesis-user-testing-metodologia-resultados.md)
