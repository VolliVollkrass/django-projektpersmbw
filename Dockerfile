FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Systembibliotheken für WeasyPrint (PDF-Erzeugung) + Fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    shared-mime-info \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Nicht als root laufen; media muss beschreibbar sein (PDF-Uploads)
RUN useradd --create-home appuser \
    && mkdir -p /app/media /app/staticfiles \
    && chown -R appuser:appuser /app/media /app/staticfiles
USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
