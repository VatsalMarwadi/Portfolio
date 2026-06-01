#!/usr/bin/env bash
# Render.com build script — run from the directory that contains manage.py
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput
