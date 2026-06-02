import pytest

from app.services.procedure_catalog import (
    COMMON_PROCEDURES,
    get_procedure_catalog,
    normalize_care_level,
)


pytestmark = pytest.mark.unit


@pytest.mark.parametrize("value", ["primary", "secondary", "tertiary"])
def test_normalize_care_level_keeps_valid_values(value: str):
    assert normalize_care_level(value) == value


@pytest.mark.parametrize("value", [None, "", "unknown", "PRIMARY"])
def test_normalize_care_level_fallbacks_to_primary(value: str | None):
    assert normalize_care_level(value) == "primary"


def test_get_procedure_catalog_contains_common_and_specific_items():
    catalog = get_procedure_catalog("secondary")
    assert "Cirugía menor" in catalog
    assert "Promoción y educación en salud" in catalog
    assert all(item in catalog for item in COMMON_PROCEDURES)


def test_get_procedure_catalog_with_invalid_level_uses_primary_catalog():
    invalid_catalog = get_procedure_catalog("invalid")
    primary_catalog = get_procedure_catalog("primary")
    assert invalid_catalog == primary_catalog
