.PHONY: install run-web run-cli clean test

install:
    python -m venv venv
    .\venv\Scripts\pip install --upgrade pip
    .\venv\Scripts\pip install -e .

run-web:
    .\venv\Scripts\streamlit run interfaces\streamlit\app.py

run-cli:
    .\venv\Scripts\python main.py --ticker AAPL

test:
    .\venv\Scripts\pytest tests/ -v

clean:
    if (Test-Path venv) { Remove-Item -Recurse -Force venv }
    Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem -Filter "*.egg-info" | Remove-Item -Recurse -Force
