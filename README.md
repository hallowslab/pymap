# Requirements

## System
* grep
* tail
* [Python](https://www.python.org/) >= 3.10
* [Imapsync](https://github.com/imapsync/imapsync)
* PostgreSQL
* [Redis-server](https://redis.com/)
* [Docker Engine](https://docs.docker.com/engine/) **Optional*
* [Docker Compose](https://docs.docker.com/engine/) **Optional*
* [Podman](https://podman.io/) **Optional/docker alternative*
* [podman-compose](https://github.com/containers/podman-compose) **Optional/docker compose alternative*

## App
* [Python](https://www.python.org/) >= 3.10
* [Poetry](https://python-poetry.org/), make sure to use the new script at https://python-poetry.org/docs/master/#installing-with-the-official-installer or pipx
* [Web-Server|Django deployment](https://docs.djangoproject.com/en/5.0/howto/deployment/)
  * builtin support for Gunicorn using Uvicorn worker for ASGI with nginx as reverse proxy
* Database:
  * SQLite -> Should only be used for development it might be capable of handling a few users but since tasks run asynchronously we don't want to try to write to the database while it's locked in another thread, there are no failsafes for that at the moment.
  * PostGreSQL -> Recommended for performance and to avoid locking issues

# Getting started

## Barebones (more control and easier to interact with)
### See [requirements](#requirements)
**NOTE: poetry commands should be run in `pymap/src` folder**

This setup focus on running the app natively on a linux environment, the app should be run by a regular non root user to avoid exposing unecessary parts of the system
- Clone the project
`git clone https://github.com/hallowslab/Pymap.git`
- Export the required environment variables in your current shell or shell config file, more info in [Additional Info - Environment Variables](#environment-variables)
- Create a config file in `pymap/src/config.json`, You can copy it from the existing templates config*-template.json and modify the settings accordingly, more info in [Addtional Info - Config File](#config-file)
- Create the LOG_DIRECTORY that's defined in your config file or the environment variable and set the ownership to the user that runs the app
- Create the STATIC_ROOT if necessary and make sure nginx processes can read it, if you defined the static root to /var/html/static, then ensure the user has write access otherwise just define the variable to some other directory, copy the files over and verify permissions.
- Install the python requirements
  * `poetry install`
- On the first time setup it's necessary to create database structure and tables
  * `poetry run python manage.py migrate`
- Add user with admin rights (Ignore this step if you have imported a database)
  * `poetry run python manage.py createsuperuser --username ADMIN`

## Docker (Easier to deploy and scale)

*Altough not tested this should work with podman and podman-compose*

- Clone the project
`git clone https://github.com/hallowslab/Pymap.git`
- Create a .env file in the project's root directory where the file .env.template is located, you can duplicate it and modify accordingly
- Create a config file in `pymap/src/config.json`, You can copy it from the existing templates config*-template.json and modify the settings accordingly, more info in [Addtional Info - Config File](#config-file)
- From the project's root where the file docker-compose.yml is located, run the command `docker compose --env-file .env build pymap` to build the container and then `docker compose up pymap -d` to start it in the background, or in a single command `docker compose --env-file .env up pymap -d`

To remove containers/volumes and images:

* `docker rm -vf $(docker images -aq)` - Removes all containers and volumes
* `docker rmi -f $(docker images -aq)` - Removes all images (*Remove containers beforehand*)

# Additional Info

## Environment Variables:
The environment variable that can be defined will take precedence when loading the settings for the application, so if you defined LOGDIR in both config.json and .env file the one defined in .env will be used

* DJANGO_ENV=production # This defines if the app is running in production or development mode, development mode is unsafe to run in an environment exposed to the web
* DJANGO_SETTINGS_MODULE=pymap.settings # Defines the app settings modules to be used, should not be changed, the configs are set in the json file
* STATIC_ROOT=/var/www/static # The path to collect the static files from the app (javascript, css and html), needs to be writable by the app user
* CELERY_BROKER_URL=redis://localhost:6379/0 # The URL of the redis instance that will be used for the background tasks handling <b>*can be set in config/optional</b>
* CELERY_RESULT_BACKEND=redis://localhost:6379/0 # The URL that will save the temporary results of the task <b>*can be set in config/optional</b>
* PYMAP_LOGDIR=/var/log/pymap # Directory for the application's log files <b>*can be set in config/optional</b>

## Config File

There are 2 configuration files, for development config.dev.json, and for production config.json. You should always use the config.json unless you are developing or running the application in debug mode.

There are only 4 directives that you should be aware of (one being optional):
1. PYMAP_LOGDIR - Specifies the application log directory, can also be set in an environment variable like described previously
2. HOSTS - A list "[]" of lists [[...],[...]] in which the inner most elements are 2 strings (pieces of text), the first string is a regular expression of what **to match** and the second one is the piece of text to be appended to the matched string, they match the source and destination inputs on the application. So taking as example the strings in the config below "^(VPS|SV)$",".example.com" if a user inserts either VPS or SV in the source and/or destination, it considers it as VPS.example.com or SV.example.com
3. Databases - You should only change the service to the name defined in your [postgresql service file](https://www.postgresql.org/docs/9.1/libpq-pgservice.html) and the [passfile](https://www.postgresql.org/docs/current/libpq-pgpass.html) to the name of the one you create
4. SECRET_KEY - Missing from the default configuration file, it's best to be created on the app's directory (src/.secret) read more in [Additional Info - .secret file](#secret-file)

- You can also modify the "level": "DEBUG" defined inside the multiple levels of logging, "console" level changes what's printed to the terminal/command line, "file" level changes what's written on the log file defined in "filename": "/var/log/pymap/pymap.log", and root changes the whole application's log level
```
{
  "PYMAP_LOGDIR": "/var/log/pymap",
  "HOSTS": [
    ["^(VPS|SV)$",".example.com"]
  ],
  "DATABASES": {
    "default": {
      "ENGINE": "django.db.backends.postgresql",
      "OPTIONS": {
        "service": "pymap",
        "passfile": ".pgpass"
      }
    }
  },
  "LOGGING": {
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
      "custom_formatter": {
        "format": "%(asctime)s - %(name)s >>> %(levelname)s: %(message)s",
        "datefmt": "%d/%m/%Y %I:%M:%S %p"
      }
    },
    "handlers": {
      "console": {
        "class": "logging.StreamHandler",
        "level": "DEBUG",
        "formatter": "custom_formatter"
      },
      "file": {
        "class": "logging.FileHandler",
        "filename": "/var/log/pymap/pymap.log",
        "level": "DEBUG",
        "formatter": "custom_formatter"
      }
    },
    "root": {
      "handlers": ["console", "file"],
      "level": "DEBUG"
    }
  }
}
```

## .secret file

This file is only used to store the SECRET_KEY, the file should contain in a single line with no spaces a random generated piece of text around 50 characters long, I would reccomend using a password generator to create a complex enough secret. There are builtin tools to generate random cryptographically secure keys you can read more in [Advanced Usage - Generating Secrets](#generating-secrets)

# Advanced Usage

If you need to interact with the application for adding users or running the interactive shell, you will need to access the environment so that it recognizes the proper python interpreter and adittional packages, to access the environment you can run the command `poetry shell` in the application's main directory where you can also find a file with the name pyproject.toml (Poetry recognizes the applications environment trough this file)

## Generating Secrets



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
* Add failsafe to pass --gmail or --office when it detects one of their hosts and the parameter missing
* If running the CLI remove the pipe to /dev/null
* Configure logging for both Django and Celery (WIP)
* MEMOIZE and cache some common operations
* Add status to tasks page
* Add queue/requeue functionality, queue should also support starting a task after another is marked as finished
  * Encrypt celery task results (or just stop using them for now) *Required*


### Bugs/Issues

- Celery on windows always pending ->
 * Issue on [github](https://github.com/celery/celery/issues/2146) / Thread on [SO](https://stackoverflow.com/a/27358974)
 * Command `celery -A server.tasks worker -E --loglevel debug --pool=solo`
