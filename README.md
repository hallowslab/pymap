# Requirements

## System
* grep
* tail
* [Imapsync](https://github.com/imapsync/imapsync)
* [Docker-Engine](https://docs.docker.com/engine/) **Optional*
* python3.10+

## App
* [Python](https://www.python.org/) >= 3.8.10
* [Poetry](https://python-poetry.org/), make sure to use the new script at https://python-poetry.org/docs/master/#installing-with-the-official-installer
* [Web-Server|Django deployment](https://docs.djangoproject.com/en/5.0/howto/deployment/)
  * builtin support for Gunicorn with Uvicorn worker
* [Redis-server](https://redis.com/)
* Database SQLite(current)/PostGreSQL(WIP)

# Initial setup
### See [requirements](#requirements)
**NOTE: poetry commands should be run in `pymap/src` folder**

- Clone the repo
- Install the python requirements
  * `poetry install`
- On the first time setup it's necessary to create database structure and tables
  * `poetry run python manage.py migrate`
- Add user with admin rights (Ignore this step if you have imported a database)
  * `poetry run python manage.py createsuperuser --username ADMIN`

# Getting started



# Additional Info



# Advanced Usage

If you need to interact with the application for adding users or launch in debug mode, you will need to access the environment so that it recognizes the proper python interpreter and adittional packages, for this you can run the following command `poetry shell`

# Dockers (with docker or podman-compose)
### AIO

* The AIO(All In One) image runs all services in a single container, altought this is not ideal for scaling it might be easier to manage
* It's using supervisor to run multiple processes, the system processes like postgresql, nginx, and redis run under their own users and the app runs under the `pymap` user
* Nginx handles the traffic incoming to Gunicorn, which then uses the Uvicorn class worker to be able to process more requests(ASGI)


# DEV
#### TODO:
* Make a logo
* Add queue/requeue functionality, queue should also support starting a task after another is marked as finished
  * [django-celery-beat](https://github.com/celery/django-celery-beat)
* Add failsafe to pass --gmail or --office when it detects one of their hosts and the parameter missing
* If running the CLI remove the pipe to /dev/null
* Configure logging for both Django and Celery (WIP)


### Bugs/Issues

- Celery on windows always pending ->
 * Issue on [github](https://github.com/celery/celery/issues/2146) / Thread on [SO](https://stackoverflow.com/a/27358974)
 * Command `celery -A server.tasks worker -E --loglevel debug --pool=solo`
