# Borrador — Metodología y resultados (pruebas con usuarios reales)

Plantilla para el capítulo de tesis. Completar con datos reales tras las sesiones.

---

## 1. Metodología

### 1.1 Diseño del estudio

Se aplicó un diseño de **pruebas de usabilidad moderadas** sobre un prototipo funcional desplegado en entorno piloto (EC2, URL `http://18.234.37.107`). El enfoque fue mixto: métricas de completitud de tareas y escala de satisfacción (1–5), complementadas con observación y comentarios cualitativos.

### 1.2 Participantes

- **N total:** ___ (objetivo: 8–12)
- **Estudiantes 6° año:** ___
- **Tutores clínicos:** ___
- **Coordinadores UV:** ___

Reclutamiento apoyado por [profesora guía / coordinación de internado]. Criterios de inclusión: usuarios con rol activo en el internado o función equivalente en la facultad.

### 1.3 Instrumentos

| Instrumento | Descripción |
|-------------|-------------|
| Guion por rol | [`user-testing-protocol-real.md`](user-testing-protocol-real.md) |
| Completitud por tarea | Binaria (0/1) por tarea principal |
| Satisfacción | Escala Likert 1–5 post-sesión |
| Consentimiento informado | [`consentimiento-informado-plantilla.md`](consentimiento-informado-plantilla.md) |
| Registro CSV | [`data/user-tests-real-2026.csv`](data/user-tests-real-2026.csv) |

### 1.4 Procedimiento

1. Firma de consentimiento informado.
2. Sesión individual de 20–30 minutos (presencial o remota).
3. Tareas guiadas según rol; escenario ficticio para incidentes ([PRUEBA TESIS]).
4. Registro pseudonimizado (P01…Pn) en CSV.
5. Análisis con `python scripts/analyze_user_tests.py --input .../user-tests-real-2026.csv`.

### 1.5 Consideraciones éticas

- Participación voluntaria; posibilidad de retiro sin consecuencias.
- No se solicitaron relatos reales de maltrato o acoso; solo escenarios ficticios en el módulo de incidentes.
- Identificadores anónimos en informes; tabla nombre↔código almacenada fuera del repositorio.

---

## 2. Resultados

### 2.1 Métricas globales

_Completar tras generar el reporte en `docs/testing/reports/user-testing-real-summary.md`._

| Indicador | Valor | Umbral | Cumple |
|-----------|------:|--------|--------|
| Participantes | | — | — |
| Satisfacción promedio | / 5 | ≥ 4.0 | |
| Completitud bitácora | % | ≥ 80% | |
| Completitud asistencia | % | ≥ 80% | |
| Completitud incidente | % | ≥ 80% | |
| Completitud evaluación | % | ≥ 80% | |

### 2.2 Resultados por perfil

| Perfil | n | Satisfacción media | Tarea con menor completitud |
|--------|--:|-------------------:|----------------------------|
| Estudiante | | | |
| Tutor | | | |
| Coordinador | | | |

### 2.3 Hallazgos cualitativos

**Facilidades mencionadas:**

- 

**Dificultades / fricciones:**

- 

**Verbatim representativos (pseudonimizados):**

- P0_: "..."

---

## 3. Discusión

### 3.1 Relación con objetivos del sistema

Vincular hallazgos con los problemas que la plataforma aborda (visibilidad coordinador, estandarización evaluación tutor, canal confidencial estudiante) — ver [`contexto/product.md`](../../contexto/product.md).

### 3.2 Limitaciones

- Muestra pequeña no representativa de toda la facultad.
- Entorno piloto; no uso en producción masiva.
- Posible efecto de moderación ( sesión observada ).

### 3.3 Mejoras recomendadas

| Prioridad | Hallazgo | Acción sugerida |
|-----------|----------|-----------------|
| Alta | | |
| Media | | |

---

## 4. Anexos sugeridos

- Consentimiento informado (modelo)
- Guion de tareas por rol
- Tabla completa de participantes (pseudonimizada)
- Capturas de pantalla del reporte HTML generado
- [`user-testing-real-summary.html`](reports/user-testing-real-summary.html)

---

## Comando para regenerar resultados

```bash
cd backend
python scripts/analyze_user_tests.py \
  --input ../docs/testing/data/user-tests-real-2026.csv \
  --title "Pruebas con usuarios reales — Tesis 2026"
```
