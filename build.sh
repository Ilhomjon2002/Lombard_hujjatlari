#!/usr/bin/env bash
set -o errexit

# LibreOffice o'rnatish (DOCX -> PDF konvertatsiya uchun)
apt-get update && apt-get install -y --no-install-recommends libreoffice-writer libreoffice-common fonts-liberation
rm -rf /var/lib/apt/lists/*

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate