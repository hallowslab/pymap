# Requirements

## System
* grep
* tail
* [Python](https://www.python.org/) >= 3.10
* [Imapsync](https://github.com/imapsync/imapsync)
* PostgreSQL
* [Redis-server](https://redis.com/)
* [Docker-Engine](https://docs.docker.com/engine/) **Optional*

## App
* [Python](https://www.python.org/) >= 3.10
* [Poetry](https://python-poetry.org/), make sure to use the new script at https://python-poetry.org/docs/master/#installing-with-the-official-installer or pipx
* [Web-Server|Django deployment](https://docs.djangoproject.com/en/5.0/howto/deployment/)
  * builtin support for Gunicorn using Uvicorn worker for ASGI with nginx as reverse proxy
* Database:
  * SQLite -> Should only be used for development it might be capable of handling a few users but since tasks run asynchronously we don't want to try to write to the database while it's locked in another thread, there are no failsafes for that at the moment.
  * PostGreSQL -> Recommended for performance and to avoid locking issues

# Initial setup

## Barebones
### See [requirements](#requirements)
**NOTE: poetry commands should be run in `pymap/src` folder**

This setup focus on running the app natively on a linux environment, the app should be run by a regular non root user to avoid exposing unecessary parts of the system
- First export the following variables in your current shell or shell config file
  * DJANGO_ENV=production # This defines if the app is running in production or development mode, development mode is unsafe to run in an environment exposed to the web
  * DJANGO_SETTINGS_MODULE=pymap.settings # Defines the app settings modules to be used, should not be changed, the configs are set in the json file
  * CELERY_BROKER_URL=redis://localhost:6379/0 # The URL of the redis instance that will be used for the background tasks handling <b>*can be set in config</b>
  * CELERY_RESULT_BACKEND=redis://localhost:6379/0 # The URL that will save the temporary results of the task <b>*can be set in config</b>
  * STATIC_ROOT=/var/www/static # The path to collect the static files from the app (javascript, css and html), needs to be writable by the app user
- Create the LOG_DIRECTORY that's defined in your config file (additional information in [Addtional Info - Config File](#config-file)), set the ownership to the user that runs the app
- Create the STATIC_ROOT if necessary and make sure nginx processes can read it, if you defined the static root to /var/html/static, then ensure the user has write access otherwise just define the variable to some other directory, copy the files over and verify permissions.
- Clone the repo
- Install the python requirements
  * `poetry install`
- On the first time setup it's necessary to create database structure and tables
  * `poetry run python manage.py migrate`
- Add user with admin rights (Ignore this step if you have imported a database)
  * `poetry run python manage.py createsuperuser --username ADMIN`

# Getting started



# Additional Info

## Config File

# Advanced Usage

If you need to interact with the application for adding users or running in debug mode, you will need to access the environment so that it recognizes the proper python interpreter and adittional packages, for this you can run the following command `poetry shell`

# Dockers (docker or podman with compose)
### AIO

* The AIO(All In One) image runs all services in a single container, altought this is not ideal for scaling it might be easier to manage
* It's using supervisor to run multiple processes, the system processes like postgresql, nginx, and redis run under their own users and the app runs under the `pymap` user
* Nginx handles the traffic incoming to Gunicorn, which then uses the Uvicorn class worker to be able to process more requests(ASGI)

#### Notes

You can specify multiple files as cli params: docker compose --env-file .env --env-file dev.env build aio



# DEV
### Notes:
I can change the celery stored results with something like this:
https://docs.celeryq.dev/en/stable/userguide/tasks.html#hiding-sensitive-information-in-arguments
```
add.apply_async((2, 3), argsrepr='(<secret-x>, <secret-y>)')
```

however my arguments are just a whole string of the command, I could refactor the core.....

I could also open a PR to the celery repo with a solution for encrypting this data provided a new argument/variable
```
class TaskExtended(Task):
    """For the extend result."""

    __tablename__ = 'celery_taskmeta'
    __table_args__ = {'sqlite_autoincrement': True, 'extend_existing': True}

    name = sa.Column(sa.String(155), nullable=True)
    args = sa.Column(sa.LargeBinary, nullable=True)
    kwargs = sa.Column(sa.LargeBinary, nullable=True)
    worker = sa.Column(sa.String(155), nullable=True)
    retries = sa.Column(sa.Integer, nullable=True)
    queue = sa.Column(sa.String(155), nullable=True)

    def to_dict(self):
        task_dict = super().to_dict()
        task_dict.update({
            'name': self.name,
            'args': self.args,
            'kwargs': self.kwargs,
            'worker': self.worker,
            'retries': self.retries,
            'queue': self.queue,
        })
        return task_dict
```

#### Celery support
revoke: Revoking tasks
pool support: all, terminate only supported by prefork and eventlet

#### TODO:
* Make a logo
* Add queue/requeue functionality, queue should also support starting a task after another is marked as finished
* Add failsafe to pass --gmail or --office when it detects one of their hosts and the parameter missing
* If running the CLI remove the pipe to /dev/null
* Configure logging for both Django and Celery (WIP)
* MEMOIZE and cache some common operations
* Encrypt celery task results


### Bugs/Issues

- Celery on windows always pending ->
 * Issue on [github](https://github.com/celery/celery/issues/2146) / Thread on [SO](https://stackoverflow.com/a/27358974)
 * Command `celery -A server.tasks worker -E --loglevel debug --pool=solo`
