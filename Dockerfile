FROM python:3.13-slim

WORKDIR /app

# Copy project metadata and the resolved dependency set first for layer caching.
COPY pyproject.toml requirements.lock ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir --root-user-action=ignore --only-binary=:all: -r requirements.lock \
    && python -m pip install --no-cache-dir --root-user-action=ignore --no-deps -e .

# The current Streamlit entry point is the only runtime source needed by this image.
# Keep legacy snapshots, tests and unrelated repository content out of the image.
COPY interfaces/streamlit ./interfaces/streamlit

# Run the application as an unprivileged user.
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app /home/appuser
USER appuser

EXPOSE 8501

# Container-level liveness check for the Streamlit HTTP endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4).read()" || exit 1

CMD ["streamlit", "run", "interfaces/streamlit/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
