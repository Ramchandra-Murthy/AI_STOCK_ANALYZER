from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _function_names(path: str) -> list[str]:
    names = []
    for line in (ROOT / path).read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("def "):
            names.append(line.split("def ", 1)[1].split("(", 1)[0])
    return names


def test_technical_score_has_single_public_implementation():
    names = _function_names("services/technical_score_service.py")
    assert names.count("calculate_technical_score") == 1
    assert names.count("_valid_number") == 1


def test_restoration_boundary_exists():
    assert (ROOT / "services/eros_research_service.py").exists()
    assert (ROOT / "tests/test_eros_restoration_boundary.py").exists()
