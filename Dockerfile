FROM python:3.13-slim

WORKDIR /app

# Copy project metadata first for better layer caching.
COPY pyproject.toml requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip install --no-cache-dir -e .

# Copy application source code.
COPY . .

EXPOSE 8501

# Container-level liveness check for the Streamlit HTTP endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4).read()" || exit 1

CMD ["streamlit", "run", "interfaces/streamlit/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
