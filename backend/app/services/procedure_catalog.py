from __future__ import annotations

from typing import Literal


CareLevel = Literal["primary", "secondary", "tertiary"]

COMMON_PROCEDURES = [
    "Examen y diagnóstico",
    "Promoción y educación en salud",
    "Prevención",
    "Urgencias odontológicas",
    "Otro",
]

PROCEDURES_BY_CARE_LEVEL: dict[CareLevel, list[str]] = {
    "primary": [
        *COMMON_PROCEDURES,
        "Operatoria básica",
        "Asistente clínica",
        "Observador clínico",
        "Exodoncia temporal",
        "Exodoncia permanente",
        "Signos vitales",
        "Atención de gestantes",
        "Atención de personas migrantes",
    ],
    "secondary": [
        *COMMON_PROCEDURES,
        "Cirugía menor",
        "Endodoncia",
        "Rehabilitación oral",
        "Periodoncia",
        "Odontopediatría",
        "Ortodoncia",
        "Interconsulta especialidad",
    ],
    "tertiary": [
        *COMMON_PROCEDURES,
        "Cirugía compleja",
        "Biopsia",
        "Manejo de urgencia hospitalaria",
        "Atención en pabellón",
        "Procedimiento multidisciplinario",
        "Interconsulta hospitalaria",
    ],
}


def normalize_care_level(value: str | None) -> CareLevel:
    if value in {"primary", "secondary", "tertiary"}:
        return value
    return "primary"


def get_procedure_catalog(care_level: str | None) -> list[str]:
    normalized_level = normalize_care_level(care_level)
    return PROCEDURES_BY_CARE_LEVEL[normalized_level]
