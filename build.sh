#!/usr/bin/env bash
set -o errexit
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-render.txt
python -m pip check
python manage.py check --deploy --fail-level ERROR
python manage.py collectstatic --noinput
python manage.py migrate
