# MedDataCard — reproducible runtime
# Build:  docker build -t meddatacard .
# Run:    docker run -p 8501:8501 -e DASHSCOPE_API_KEY=sk-... meddatacard
FROM python:3.11-slim

WORKDIR /app

# System deps for any native packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project (datacards / schema / sources are part of the repo)
COPY . .

# NEVER bake a real key into the image; inject at runtime via -e
ENV STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
