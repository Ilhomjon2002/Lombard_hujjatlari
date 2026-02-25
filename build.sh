#!/bin/bash
apt-get update
apt-get install -y libreoffice libreoffice-writer fonts-dejavu
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
