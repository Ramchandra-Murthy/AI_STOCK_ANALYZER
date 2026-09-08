from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_and_docker_python_versions_match():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert 'requires-python = ">=3.13"' in pyproject
    assert "FROM python:3.13-slim" in dockerfile


def test_production_dockerfile_uses_same_python_major_minor():
    dockerfile = (ROOT / "Dockerfile.production").read_text(encoding="utf-8")
    assert "FROM python:3.13-slim" in dockerfile


def test_ci_uses_python_313():
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8-sig")
    assert 'python-version: "3.13"' in ci
