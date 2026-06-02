from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = PROJECT_ROOT / "reports" / "testing"


@dataclass
class SuiteResult:
    name: str
    marker: str | None
    exit_code: int
    tests: int
    failures: int
    errors: int
    skipped: int
    passed: int
    time_seconds: float
    junit_path: Path
    html_path: Path


def _run_pytest(args: list[str]) -> int:
    cmd = [sys.executable, "-m", "pytest", *args]
    print(f"\n[run] {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return completed.returncode


def _parse_junit(junit_path: Path) -> tuple[int, int, int, int, float]:
    tree = ET.parse(junit_path)
    root = tree.getroot()

    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")

    tests = sum(int(s.attrib.get("tests", 0)) for s in suites)
    failures = sum(int(s.attrib.get("failures", 0)) for s in suites)
    errors = sum(int(s.attrib.get("errors", 0)) for s in suites)
    skipped = sum(int(s.attrib.get("skipped", 0)) for s in suites)
    time_seconds = sum(float(s.attrib.get("time", 0.0)) for s in suites)
    return tests, failures, errors, skipped, time_seconds


def _coverage_percent(coverage_xml: Path) -> float:
    root = ET.parse(coverage_xml).getroot()
    line_rate = float(root.attrib.get("line-rate", 0.0))
    return round(line_rate * 100, 2)


def _status_label(result: SuiteResult) -> str:
    return "PASS" if result.exit_code == 0 else "FAIL"


def _write_markdown_summary(
    suite_results: list[SuiteResult],
    all_result: SuiteResult,
    coverage_pct: float,
    output_path: Path,
) -> None:
    lines: list[str] = []
    lines.append("# Resumen Consolidado de Pruebas")
    lines.append("")
    lines.append(f"Fecha: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")
    lines.append("## Cobertura Global")
    lines.append("")
    lines.append(f"- Cobertura total de lineas: **{coverage_pct}%**")
    lines.append("- Reporte HTML: reports/testing/htmlcov/index.html")
    lines.append("")
    lines.append("## Resultado por Suite")
    lines.append("")
    lines.append("| Suite | Tests | Passed | Failed | Errors | Skipped | Tiempo(s) | Estado |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")

    for result in suite_results:
        lines.append(
            f"| {result.name} | {result.tests} | {result.passed} | {result.failures} | {result.errors} | {result.skipped} | {result.time_seconds:.2f} | {_status_label(result)} |"
        )

    lines.append(
        f"| all | {all_result.tests} | {all_result.passed} | {all_result.failures} | {all_result.errors} | {all_result.skipped} | {all_result.time_seconds:.2f} | {_status_label(all_result)} |"
    )
    lines.append("")
    lines.append("## Reportes Visuales")
    lines.append("")
    lines.append("- reports/testing/all/report.html")
    lines.append("- reports/testing/unit/report.html")
    lines.append("- reports/testing/integration/report.html")
    lines.append("- reports/testing/system/report.html")
    lines.append("- reports/testing/acceptance/report.html")
    lines.append("")
    lines.append("## Consola (Resumen)")
    lines.append("")
    lines.append(f"- Total ejecutadas: {all_result.tests}")
    lines.append(f"- Total aprobadas: {all_result.passed}")
    lines.append(f"- Total fallidas: {all_result.failures + all_result.errors}")
    lines.append(f"- Total omitidas: {all_result.skipped}")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def _write_html_dashboard(
    suite_results: list[SuiteResult],
    all_result: SuiteResult,
    coverage_pct: float,
    output_path: Path,
) -> None:
    max_tests = max([all_result.tests, *(r.tests for r in suite_results)]) or 1

    rows = []
    for result in [*suite_results, all_result]:
        pass_ratio = (result.passed / result.tests * 100) if result.tests else 0
        width = max(4, int((result.tests / max_tests) * 100))
        rows.append(
            f"""
            <tr>
              <td>{result.name}</td>
              <td>{result.tests}</td>
              <td>{result.passed}</td>
              <td>{result.failures}</td>
              <td>{result.errors}</td>
              <td>{result.skipped}</td>
              <td>{result.time_seconds:.2f}</td>
              <td><span class=\"status {'ok' if result.exit_code == 0 else 'bad'}\">{_status_label(result)}</span></td>
              <td>
                <div class=\"bar-wrap\" title=\"Pass rate: {pass_ratio:.1f}%\">
                  <div class=\"bar\" style=\"width:{width}%\"></div>
                </div>
              </td>
            </tr>
            """
        )

    html = f"""
<!doctype html>
<html lang=\"es\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Dashboard de Calidad de Pruebas</title>
  <style>
    :root {{
      --bg: #f7f4ef;
      --panel: #ffffff;
      --ink: #1f2937;
      --muted: #6b7280;
      --ok: #166534;
      --ok-bg: #dcfce7;
      --bad: #991b1b;
      --bad-bg: #fee2e2;
      --accent: #0f766e;
      --bar: #14b8a6;
      --border: #e5e7eb;
    }}
    body {{
      margin: 0;
      padding: 24px;
      font-family: "Source Sans 3", "Segoe UI", sans-serif;
      color: var(--ink);
      background: radial-gradient(circle at top right, #d1fae5 0%, var(--bg) 45%);
    }}
    .wrap {{
      max-width: 1100px;
      margin: 0 auto;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      box-shadow: 0 8px 28px rgba(0, 0, 0, 0.05);
      overflow: hidden;
    }}
    header {{
      padding: 20px 24px;
      border-bottom: 1px solid var(--border);
      background: linear-gradient(100deg, #ecfeff 0%, #f0fdf4 100%);
    }}
    h1 {{ margin: 0; font-size: 1.45rem; }}
    .meta {{ margin-top: 6px; color: var(--muted); font-size: 0.95rem; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      padding: 16px 24px;
    }}
    .card {{
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
      background: #fff;
    }}
    .k {{ color: var(--muted); font-size: 0.88rem; }}
    .v {{ font-size: 1.4rem; font-weight: 700; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-top: 1px solid var(--border); padding: 10px 12px; text-align: left; font-size: 0.95rem; }}
    thead th {{ background: #f9fafb; border-top: none; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }}
    .status {{ padding: 3px 8px; border-radius: 999px; font-weight: 600; font-size: 0.8rem; }}
    .status.ok {{ color: var(--ok); background: var(--ok-bg); }}
    .status.bad {{ color: var(--bad); background: var(--bad-bg); }}
    .bar-wrap {{ width: 100%; background: #ecfeff; height: 8px; border-radius: 999px; overflow: hidden; }}
    .bar {{ height: 100%; background: var(--bar); }}
    .links {{ padding: 16px 24px 24px; }}
    .links a {{ color: var(--accent); text-decoration: none; margin-right: 16px; }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <header>
      <h1>Dashboard Consolidado de Calidad</h1>
      <div class=\"meta\">Generado: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
    </header>

    <section class=\"grid\">
      <article class=\"card\"><div class=\"k\">Cobertura Global</div><div class=\"v\">{coverage_pct}%</div></article>
      <article class=\"card\"><div class=\"k\">Tests Ejecutados</div><div class=\"v\">{all_result.tests}</div></article>
      <article class=\"card\"><div class=\"k\">Tests Aprobados</div><div class=\"v\">{all_result.passed}</div></article>
      <article class=\"card\"><div class=\"k\">Tests Fallidos + Error</div><div class=\"v\">{all_result.failures + all_result.errors}</div></article>
    </section>

    <section>
      <table>
        <thead>
          <tr>
            <th>Suite</th>
            <th>Tests</th>
            <th>Pass</th>
            <th>Fail</th>
            <th>Error</th>
            <th>Skip</th>
            <th>Tiempo(s)</th>
            <th>Estado</th>
            <th>Volumen</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </section>

    <section class=\"links\">
      <a href=\"all/report.html\">Reporte all</a>
      <a href=\"unit/report.html\">Reporte unit</a>
      <a href=\"integration/report.html\">Reporte integration</a>
      <a href=\"system/report.html\">Reporte system</a>
      <a href=\"acceptance/report.html\">Reporte acceptance</a>
      <a href=\"htmlcov/index.html\">Coverage HTML</a>
    </section>
  </div>
</body>
</html>
"""

    output_path.write_text(html, encoding="utf-8")


def _suite_report_paths(name: str) -> tuple[Path, Path]:
    suite_dir = REPORT_ROOT / name
    suite_dir.mkdir(parents=True, exist_ok=True)
    return suite_dir / "junit.xml", suite_dir / "report.html"


def _run_suite(name: str, marker: str | None, include_coverage: bool = False) -> SuiteResult:
    junit_path, html_path = _suite_report_paths(name)
    args = ["tests", "-q", f"--junitxml={junit_path}", f"--html={html_path}", "--self-contained-html"]

    if marker:
        args.extend(["-m", marker])

    if include_coverage:
        coverage_xml = REPORT_ROOT / "coverage.xml"
        htmlcov_dir = REPORT_ROOT / "htmlcov"
        args.extend(
            [
                "--cov=app",
                f"--cov-report=xml:{coverage_xml}",
                f"--cov-report=html:{htmlcov_dir}",
                "--cov-report=term",
            ]
        )

    exit_code = _run_pytest(args)
    tests, failures, errors, skipped, time_seconds = _parse_junit(junit_path)
    passed = tests - failures - errors - skipped

    return SuiteResult(
        name=name,
        marker=marker,
        exit_code=exit_code,
        tests=tests,
        failures=failures,
        errors=errors,
        skipped=skipped,
        passed=passed,
        time_seconds=time_seconds,
        junit_path=junit_path,
        html_path=html_path,
    )


def main() -> int:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)

    suites = [
        ("unit", "unit"),
        ("integration", "integration"),
        ("system", "system"),
        ("acceptance", "acceptance"),
    ]

    suite_results = [_run_suite(name, marker) for name, marker in suites]
    all_result = _run_suite("all", None, include_coverage=True)

    coverage_xml = REPORT_ROOT / "coverage.xml"
    coverage_pct = _coverage_percent(coverage_xml)

    summary_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "coverage_percent": coverage_pct,
        "suites": [result.__dict__ for result in suite_results],
        "all": all_result.__dict__,
    }

    json_path = REPORT_ROOT / "summary.json"
    markdown_path = REPORT_ROOT / "TEST_REPORT_SUMMARY.md"
    html_path = REPORT_ROOT / "index.html"

    json_path.write_text(json.dumps(summary_payload, indent=2, default=str), encoding="utf-8")
    _write_markdown_summary(suite_results, all_result, coverage_pct, markdown_path)
    _write_html_dashboard(suite_results, all_result, coverage_pct, html_path)

    any_failure = any(r.exit_code != 0 for r in [*suite_results, all_result])
    print("\n[done] Reportes generados en:")
    print(f"- {REPORT_ROOT}")
    print(f"- {html_path}")

    return 1 if any_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())