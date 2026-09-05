FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --only-binary=:all: -r requirements.txt

COPY . .

RUN pip install --no-cache-dir -e .

RUN useradd --create-home --shell /bin/bash appuser
USER appuser

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

