# Plan de Calidad de Pruebas

Este directorio centraliza la evidencia de calidad para evaluacion academica.

## Objetivos

- Ejecutar pruebas unitarias, integracion, sistema y aceptacion en forma repetible.
- Consolidar resultados en formatos legibles (Markdown, JUnit XML y HTML).
- Mantener trazabilidad entre funcionalidades, criterios de aceptacion y pruebas automatizadas.
- Incluir protocolo y analisis de pruebas con usuarios simulados.

## Estructura

- `acceptance-criteria.md`: matriz de criterios de aceptacion por funcionalidad.
- `user-testing-protocol.md`: guion para aplicar pruebas con usuarios.
- `user-testing-results-template.md`: formato para registrar resultados y discusion.
- `data/user-tests-simulated.csv`: dataset base para pruebas con usuarios simulados.
- `reports/`: salidas consolidadas del analisis de usuarios.

## Ejecucion automatizada

Desde `backend/`:

```bash
python scripts/run_quality_suite.py
```

Artefactos generados:

- `backend/reports/testing/index.html`
- `backend/reports/testing/TEST_REPORT_SUMMARY.md`
- `backend/reports/testing/summary.json`
- `backend/reports/testing/htmlcov/index.html`
- `backend/reports/testing/<suite>/report.html`

## Analisis de pruebas con usuarios simulados

Desde `backend/`:

```bash
python scripts/analyze_user_tests.py
```

Salidas:

- `docs/testing/reports/user-testing-summary.md`
- `docs/testing/reports/user-testing-summary.html`
