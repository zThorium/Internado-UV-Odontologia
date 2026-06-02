# Plan de Calidad de Pruebas

Este directorio centraliza la evidencia de calidad para evaluacion academica.

## Objetivos

- Ejecutar pruebas unitarias, integracion, sistema y aceptacion en forma repetible.
- Consolidar resultados en formatos legibles (Markdown, JUnit XML y HTML).
- Mantener trazabilidad entre funcionalidades, criterios de aceptacion y pruebas automatizadas.
- Incluir protocolo y analisis de pruebas con usuarios (simulados y reales — tesis).

## Estructura

- `acceptance-criteria.md`: matriz de criterios de aceptacion por funcionalidad.
- `user-testing-protocol.md`: guion base para pruebas con usuarios.
- `user-testing-protocol-real.md`: **guiones operativos para tesis (usuarios reales en prod)**.
- `consentimiento-informado-plantilla.md`: consentimiento para participantes.
- `pilot-sessions-checklist.md`: checklist sesiones piloto internas.
- `moderator-session-log-template.md`: registro por sesion del moderador.
- `post-pilot-cleanup.md`: limpieza post-estudio.
- `tesis-user-testing-metodologia-resultados.md`: borrador capitulo tesis.
- `user-testing-results-template.md`: formato para registrar resultados y discusion.
- `data/user-tests-simulated.csv`: dataset simulado.
- `data/user-tests-real-2026.csv`: **resultados reales pseudonimizados (tesis)**.
- `data/pilot-users.example.csv`: plantilla CSV para cohorte Piloto Tesis 2026.
- `reports/`: salidas consolidadas del analisis de usuarios.

## Ejecucion automatizada

Desde `backend/`:

```bash
python scripts/run_quality_suite.py
```

## Analisis de pruebas con usuarios

Simulados (default):

```bash
python scripts/analyze_user_tests.py
```

Reales (tesis):

```bash
python scripts/analyze_user_tests.py \
  --input ../docs/testing/data/user-tests-real-2026.csv \
  --title "Pruebas con usuarios reales — Tesis 2026"
```

Salidas:

- `docs/testing/reports/user-testing-summary.md` (simulados)
- `docs/testing/reports/user-testing-real-summary.md` (reales)
- Archivos `.html` equivalentes

## Alta de participantes piloto (prod)

```bash
python -m scripts.create_user --email x@uv.cl --name "..." --role student --password "..."
python -m scripts.seed_pilot_tesis --csv ../docs/testing/data/pilot-users.csv
```

Ver [`user-testing-protocol-real.md`](user-testing-protocol-real.md).
