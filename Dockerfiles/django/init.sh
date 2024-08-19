#!/usr/bin/env bash

# Wait for all systems to start
#sleep 5
# Check for migrations
poetry run python manage.py migrate --no-input --check >> django_init.txt
exit_code="$?"
# If there are model changes without migrations, apply migrations
if [ $exit_code -eq 1 ]; then
    poetry run python manage.py migrate --no-input >> django_init.txt
fi

# Run the initadmin command
echo "Running initadmin management command"
poetry run python manage.py initadmin >> django_init.txt

# Import fixtures, and other data
echo "Importing fixtures...."
poetry run python manage.py loaddata periodic.json
poetry run python manage.py loaddata purge_results.json

# Collect static assets 
poetry run python manage.py collectstatic --no-input

# Start the application
echo "Starting app..." >> django_init.txt
if [ "$DJANGO_ENV" == "production" ]; then
    echo "Starting production server"
    poetry run python -m gunicorn pymap.asgi:application -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker
else
    echo "Starting development server"
    poetry run python manage.py runserver 0.0.0.0:9000
fi