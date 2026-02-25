#!/usr/bin/env bash
set -o errexit

# LibreOffice o'rnatish (DOCX -> PDF konvertatsiya uchun)
apt-get update && apt-get install -y --no-install-recommends libreoffice-writer libreoffice-common fonts-liberation
rm -rf /var/lib/apt/lists/*

# LibreOffice yo'lini tekshirish
echo "=== LibreOffice yo'lini tekshirish ==="
which soffice || echo "soffice PATH da topilmadi"
which libreoffice || echo "libreoffice PATH da topilmadi"
ls -la /usr/bin/soffice 2>/dev/null || echo "/usr/bin/soffice topilmadi"
ls -la /usr/bin/libreoffice 2>/dev/null || echo "/usr/bin/libreoffice topilmadi"
ls -la /app/.apt/usr/bin/soffice 2>/dev/null || echo "/app/.apt/usr/bin/soffice topilmadi"
find / -name "soffice" -type f 2>/dev/null | head -5 || echo "soffice hech qayerda topilmadi"
echo "=== Tekshirish tugadi ==="

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate