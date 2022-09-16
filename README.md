# Requirements

## System
* grep
* tail
* imapsync
* python

## App
* [Python](https://www.python.org/) >= 3.8.10
* Web server -> [Gunicorn](https://gunicorn.org/)/[Tornado](https://www.tornadoweb.org/en/stable/)/[Apache](https://www.apache.org/)/[Nginx](https://www.nginx.com/) to serve the built React App
* [Redis-server](https://redis.com/)
* [Imapsync](https://github.com/imapsync/imapsync)

### Other
* Database SQLite/MySQL (WIP/Not Implemented)

## Dev requirements

* NodeJS - LTS
* [Poetry](https://python-poetry.org/), make sure to use the new script at https://python-poetry.org/docs/master/#installing-with-the-official-installer
* `poetry install` in `pymap/src` for python dependencies
* `npm ci` in `pymap/src/client` for React dependencies

# Getting started

###See [requirements](#requirements) and [Dev requirements](#dev-requirements)

* Make sure the client is up to date
 - Navigate to `pymap/src/client` and run `npm run build`
 - This will build the app to `pymap/src/build`, either serve this with flask or one of the webservers mentioned above
* Serve the client with any of the servers mentioned in [requiremnts - Web server](#requirements)
* if you decide to serve the client without flask you will still need to start the API (**You should also set the environment variable of FLASK_HEADLESS="True" or FLASK_HEADLESS=1, this will not register the routes to serve the build react app**)
* Start the API
  - `poetry run task apiProd` -> This will start 4 gunicorn workers for the API
* Start the celery worker
  - `poetry run task worker`


# Dockers

### Pymap

#### This assumes you are on the project root directory

* Building pymap
  - `docker build -f .\dockers\ubuntu20.04\Dockerfile -t pymap .`
* Running pymap
  - ports are exposed with the following syntax HOST:GUEST
  - `docker run --name pymap -it -p 5000:5000 -p20:20 -p21:21 -p22:22 -p 3001:3000 -t pymap`
  - press 2 to automagically configure zsh



# DEV

#### TODO:
* Make a logo
* Implement start time, end time and status for each log/sync
* Add search functionality - to search for a domain in all tasks
* Add requeue functionality
* Add Database login and admin functionality 
* Add `RUN echo 'root:pymap' | chpasswd` ?



#### Notes

* [Configure poetry with VSCode](https://stackoverflow.com/a/64434542) 
 - `poetry config virtualenvs.in-project true`

### Bugs/Issues

- Celery on windows always pending ->
 * Issue on [github](https://github.com/celery/celery/issues/2146) / Thread on [SO](https://stackoverflow.com/a/27358974)
 * Command `celery -A server.tasks worker -E --loglevel debug --pool=solo`