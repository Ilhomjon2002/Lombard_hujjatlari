FROM python:3.12-slim

# LibreOffice va kerakli paketlarni o'rnatish
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libreoffice-writer \
        libreoffice-common \
        fonts-liberation \
        fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# LibreOffice tekshirish
RUN which soffice && soffice --version

# Ishchi papka
WORKDIR /app

# Requirements o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Loyiha fayllarini nusxalash
COPY . .

# Static fayllarni yig'ish
RUN python manage.py collectstatic --noinput

# Port
EXPOSE 8000

# Migrate + Gunicorn ishga tushirish
CMD python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
