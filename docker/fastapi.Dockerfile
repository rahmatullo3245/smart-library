FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Hyper-V ichidagi paketlar va DNS uchun maxsus APT sozlamalari
RUN echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4 && \
    echo 'Acquire::Retries "10";' > /etc/apt/apt.conf.d/80retries && \
    echo 'Acquire::http::Timeout "30";' >> /etc/apt/apt.conf.d/80retries && \
    echo 'Acquire::http::Pipeline-Depth "0";' >> /etc/apt/apt.conf.d/80retries

# Rasmiy debian manbasiga qaytamiz
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-tgk \
    poppler-utils \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONPATH=/app/src
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]