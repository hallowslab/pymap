# Requirements

## System
* grep
* tail
* imapsync

## App
* [Python](https://www.python.org/) >= 3.8.10
* [Poetry](https://python-poetry.org/), make sure to use the new script at https://python-poetry.org/docs/master/#installing-with-the-official-installer
* [Web-Server|Django deployment](https://docs.djangoproject.com/en/5.0/howto/deployment/)
* [Redis-server](https://redis.com/)
* [Imapsync](https://github.com/imapsync/imapsync)
* Database SQLite(current)/PostGreSQL(WIP)

# Initial setup
### See [requirements](#requirements)
**NOTE: poetry commands should be run in `pymap/src` folder**

- Clone the repo
- Install the python requirements
  * `poetry install` -> As indicated above this should be run in `pymap/src`
- Add user with admin rights (Ignore this step if you have imported a database)

# Getting started

* Start the celery worker
  - `poetry run task worker`


# Additional Info

* operator role is required for scheduling, archiving and cancelling tasks, and admin for  removal



# Advanced Usage

If you need to interact with the application for adding users or launch in debug mode, you will need to access the environment so that it recognizes the proper python interpreter and adittional packages, for this you can run the following command `poetry shell`


# DEV

# Dockers (not used atm)
### Pymap
#### This assumes you are on the project root directory

* Building pymap
  - `docker build -f .\dockers\ubuntu20.04\Dockerfile -t pymap .`
* Running pymap
  - ports are exposed with the following syntax HOST:GUEST
  - `docker run --name pymap -it -p 5000:5000 -p20:20 -p21:21 -p22:22 -p 3001:3000 -t pymap`
  - press 2 to automagically configure zsh

#### TODO:
* Make a logo
* Add queue/requeue functionality, queue should also support starting a task after another is marked as finished
* Add failsafe to pass --gmail or --office when it detects one of their hosts and the parameter missing
* There is a bug where sometimes the additional arguments on the client side do not get passed correctly to the API,
  probably something to do with React state, TODO: Ensure the arguments get loaded as soon as the APP is, or save the arguments
  in the database as a user property string 
* If running the CLI remove the pipe to /dev/null
* Configure logging for both Django and Celery (WIP)

#### Notes

* [Configure poetry with VSCode](https://stackoverflow.com/a/64434542) 
 - `poetry config virtualenvs.in-project true`

### Bugs/Issues

- Celery on windows always pending ->
 * Issue on [github](https://github.com/celery/celery/issues/2146) / Thread on [SO](https://stackoverflow.com/a/27358974)
 * Command `celery -A server.tasks worker -E --loglevel debug --pool=solo`
