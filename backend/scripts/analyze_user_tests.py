from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = REPO_ROOT / "docs" / "testing" / "data" / "user-tests-simulated.csv"
REPORT_DIR = REPO_ROOT / "docs" / "testing" / "reports"
MARKDOWN_OUT = REPORT_DIR / "user-testing-summary.md"
HTML_OUT = REPORT_DIR / "user-testing-summary.html"


@dataclass
class UserResult:
    participant_id: str
    profile: str
    task_logbook: int
    task_attendance: int
    task_incident: int
    task_evaluation: int
    satisfaction: float
    comments: str


def _read_results(path: Path) -> list[UserResult]:
    rows: list[UserResult] = []
    with path.open("r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            rows.append(
                UserResult(
                    participant_id=row["participant_id"],
                    profile=row["profile"],
                    task_logbook=int(row["task_logbook"]),
                    task_attendance=int(row["task_attendance"]),
                    task_incident=int(row["task_incident"]),
                    task_evaluation=int(row["task_evaluation"]),
                    satisfaction=float(row["satisfaction"]),
                    comments=row.get("comments", ""),
                )
            )
    return rows


def _pct(success: int, total: int) -> float:
    return round((success / total * 100), 1) if total else 0.0


def _bar(percent: float) -> str:
    blocks = int(round(percent / 10))
    return "#" * blocks + "-" * (10 - blocks)


def _build_markdown(results: list[UserResult]) -> str:
    total = len(results)
    logbook_ok = sum(r.task_logbook for r in results)
    attendance_ok = sum(r.task_attendance for r in results)
    incident_ok = sum(r.task_incident for r in results)
    evaluation_ok = sum(r.task_evaluation for r in results)
    avg_satisfaction = round(sum(r.satisfaction for r in results) / total, 2) if total else 0.0

    task_rows = [
        ("Registrar bitacora", logbook_ok),
        ("Registrar asistencia", attendance_ok),
        ("Reportar incidente", incident_ok),
        ("Flujo de evaluacion", evaluation_ok),
    ]

    lines: list[str] = []
    lines.append("# Resumen de Pruebas con Usuarios Simulados")
    lines.append("")
    lines.append(f"Fecha: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")
    lines.append("## Metricas globales")
    lines.append("")
    lines.append(f"- Participantes: **{total}**")
    lines.append(f"- Satisfaccion promedio: **{avg_satisfaction} / 5**")
    lines.append("")
    lines.append("## Completitud por tarea")
    lines.append("")
    lines.append("| Tarea | Completadas | Total | Tasa (%) | Barra |")
    lines.append("|---|---:|---:|---:|---|")

    for label, success in task_rows:
        percent = _pct(success, total)
        lines.append(f"| {label} | {success} | {total} | {percent} | `{_bar(percent)}` |")

    lines.append("")
    lines.append("## Registro por participante")
    lines.append("")
    lines.append("| Participante | Perfil | Logbook | Attendance | Incident | Evaluation | Satisfaccion | Comentarios |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---|")

    for row in results:
        lines.append(
            "| "
            f"{row.participant_id} | {row.profile} | {row.task_logbook} | {row.task_attendance} | "
            f"{row.task_incident} | {row.task_evaluation} | {row.satisfaction} | {row.comments} |"
        )

    lines.append("")
    lines.append("## Discusion")
    lines.append("")
    lines.append("- Se observa alta completitud en bitacora e incidentes.")
    lines.append("- Los principales puntos de mejora se concentran en asistencia y evaluacion para algunos perfiles.")
    lines.append("- Recomendacion: agregar ayudas contextuales para usuarios nuevos.")

    return "\n".join(lines)


def _build_html(results: list[UserResult]) -> str:
    total = len(results)
    logbook_ok = sum(r.task_logbook for r in results)
    attendance_ok = sum(r.task_attendance for r in results)
    incident_ok = sum(r.task_incident for r in results)
    evaluation_ok = sum(r.task_evaluation for r in results)
    avg_satisfaction = round(sum(r.satisfaction for r in results) / total, 2) if total else 0.0

    rows = []
    task_data = [
        ("Bitacora", logbook_ok),
        ("Asistencia", attendance_ok),
        ("Incidente", incident_ok),
        ("Evaluacion", evaluation_ok),
    ]

    for label, success in task_data:
        percent = _pct(success, total)
        rows.append(
            f"""
            <div class=\"metric\">
              <div class=\"line\"><strong>{label}</strong><span>{percent}%</span></div>
              <div class=\"bar-bg\"><div class=\"bar\" style=\"width:{percent}%\"></div></div>
            </div>
            """
        )

    participant_rows = []
    for r in results:
        participant_rows.append(
            f"<tr><td>{r.participant_id}</td><td>{r.profile}</td><td>{r.task_logbook}</td><td>{r.task_attendance}</td><td>{r.task_incident}</td><td>{r.task_evaluation}</td><td>{r.satisfaction}</td><td>{r.comments}</td></tr>"
        )

    return f"""
<!doctype html>
<html lang=\"es\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Resumen Pruebas con Usuarios</title>
  <style>
    body {{
      margin: 0;
      padding: 24px;
      font-family: "Source Sans 3", "Segoe UI", sans-serif;
      background: linear-gradient(130deg, #fefce8 0%, #ecfeff 100%);
      color: #1f2937;
    }}
    .wrap {{
      max-width: 980px;
      margin: 0 auto;
      background: #fff;
      border: 1px solid #e5e7eb;
      border-radius: 14px;
      box-shadow: 0 10px 28px rgba(0, 0, 0, 0.06);
      overflow: hidden;
    }}
    header {{
      padding: 20px;
      background: linear-gradient(120deg, #fef9c3 0%, #dbeafe 100%);
      border-bottom: 1px solid #e5e7eb;
    }}
    h1 {{ margin: 0; font-size: 1.4rem; }}
    .meta {{ color: #6b7280; margin-top: 6px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; padding: 16px 20px; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px; }}
    .k {{ color: #6b7280; font-size: 0.85rem; }}
    .v {{ font-size: 1.35rem; font-weight: 700; margin-top: 4px; }}
    .metrics {{ padding: 0 20px 16px; }}
    .metric {{ margin-bottom: 10px; }}
    .line {{ display: flex; justify-content: space-between; margin-bottom: 4px; }}
    .bar-bg {{ height: 10px; background: #f1f5f9; border-radius: 999px; overflow: hidden; }}
    .bar {{ height: 100%; background: #0ea5e9; }}
    table {{ width: calc(100% - 40px); margin: 0 20px 20px; border-collapse: collapse; }}
    th, td {{ border-top: 1px solid #e5e7eb; padding: 8px; text-align: left; font-size: 0.9rem; }}
    thead th {{ border-top: none; background: #f9fafb; color: #6b7280; font-size: 0.8rem; text-transform: uppercase; }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <header>
      <h1>Pruebas con Usuarios Simulados</h1>
      <div class=\"meta\">Generado: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
    </header>

    <section class=\"grid\">
      <article class=\"card\"><div class=\"k\">Participantes</div><div class=\"v\">{total}</div></article>
      <article class=\"card\"><div class=\"k\">Satisfaccion promedio</div><div class=\"v\">{avg_satisfaction}/5</div></article>
      <article class=\"card\"><div class=\"k\">Completitud bitacora</div><div class=\"v\">{_pct(logbook_ok, total)}%</div></article>
      <article class=\"card\"><div class=\"k\">Completitud asistencia</div><div class=\"v\">{_pct(attendance_ok, total)}%</div></article>
    </section>

    <section class=\"metrics\">
      {''.join(rows)}
    </section>

    <table>
      <thead>
        <tr>
          <th>ID</th><th>Perfil</th><th>Logbook</th><th>Attendance</th><th>Incident</th><th>Evaluation</th><th>Satisfaccion</th><th>Comentarios</th>
        </tr>
      </thead>
      <tbody>
        {''.join(participant_rows)}
      </tbody>
    </table>
  </div>
</body>
</html>
"""


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    results = _read_results(INPUT_CSV)
    markdown = _build_markdown(results)
    html = _build_html(results)

    MARKDOWN_OUT.write_text(markdown, encoding="utf-8")
    HTML_OUT.write_text(html, encoding="utf-8")

    print("Analisis de usuarios generado:")
    print(f"- {MARKDOWN_OUT}")
    print(f"- {HTML_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())