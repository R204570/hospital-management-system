#!/usr/bin/env bash
# Render build script -- set the service's Build Command to: ./build.sh
#
# collectstatic is required because production runs with DEBUG = False, where
# Django no longer serves /static/ itself and WhiteNoise reads from STATIC_ROOT.
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
