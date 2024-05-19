#!/usr/bin/env bash

# Wait for all systems to start
sleep 5
# Check for migrations
poetry run python manage.py migrate --check >> django_init.txt
exit_code="$?"
# If there are model changes without migrations, apply migrations
if [ $exit_code -eq 1 ]; then
    poetry run python manage.py migrate >> django_init.txt
fi

# Start the application
echo "Starting app..." >> django_init.txt
poetry run python -m gunicorn pymap.asgi:application -k uvicorn.workers.UvicornWorker
