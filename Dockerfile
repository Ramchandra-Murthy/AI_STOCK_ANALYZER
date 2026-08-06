FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for optimized caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Install package in editable/development mode
RUN pip install -e .

EXPOSE 8501

CMD ["streamlit", "run", "interfaces/streamlit/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
