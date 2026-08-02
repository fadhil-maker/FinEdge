#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing Dependencies..."
pip install -r requirements.txt

echo "Collecting Static Files..."
python manage.py collectstatic --noinput

echo "Running Database Migrations..."
python manage.py migrate
