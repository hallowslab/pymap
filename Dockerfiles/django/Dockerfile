FROM debian:bookworm as debian-builder

# Install system and perl dependencies
RUN apt-get update && \
    apt-get install -y git curl apt-file make time gcc lsb-release procps cpanminus \
    libauthen-ntlm-perl libcgi-pm-perl libcrypt-openssl-rsa-perl libdata-uniqid-perl libpar-packer-perl \
    libencode-imaputf7-perl libfile-copy-recursive-perl libfile-tail-perl libio-socket-inet6-perl \
    libio-socket-ssl-perl libio-tee-perl libhtml-parser-perl libjson-webtoken-perl libmail-imapclient-perl libtest-requires-perl \
    libparse-recdescent-perl libproc-processtable-perl libmodule-scandeps-perl libreadonly-perl libregexp-common-perl libtest-mock-guard-perl \
    libsys-meminfo-perl libterm-readkey-perl libtest-mockobject-perl libtest-pod-perl libunicode-string-perl liburi-perl libwww-perl \
    libtest-nowarnings-perl libtest-deep-perl libtest-warn-perl libnet-server-perl libpackage-stash-perl libpackage-stash-xs-perl

# Clean apt
RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Perl modules for imapsync
# See https://imapsync.lamiral.info/FAQ.d/FAQ.SSL_errors.txt
RUN cpanm Dist::CheckConflicts Module::Implementation IO::Socket::SSL

# Required for imapsync dependecy check
RUN apt-file update

# Clone and install imapsync
WORKDIR /opt/imapsync
RUN git clone https://github.com/imapsync/imapsync.git . && make install

FROM python:3.11

# Needed for fixing permissions of files created by Docker:
ARG UID=1000 \
    GID=1000 \
    DJANGO_ENV \
    DJANGO_SETTINGS_MODULE \
    CELERY_BROKER_URL \
    CELERY_RESULT_BACKEND \
    STATIC_ROOT \
    PYMAP_LOGDIR \
    PYMAP_ADMIN_USER \
    PYMAP_ADMIN_PASSWORD \
    SECRET_KEY \
    POSTGRES_DB \
    POSTGRES_USER \
    POSTGRES_PASSWORD \
    POSTGRES_HOST \
    POSTGRES_PORT \
    GROUPNAME \
    GID

# python:
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    # pip:
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_ROOT_USER_ACTION=ignore \
    # poetry:
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME='/opt/pypoetry' \
    POETRY_VIRTUALENVS_PREFER_ACTIVE_PYTHON=true \
    POETRY_INSTALLER_MAX_WORKERS=10 \
    # APP
    DJANGO_ENV=${DJANGO_ENV} \
    DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} \
    CELERY_BROKER_URL=${CELERY_BROKER_URL} \
    CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND} \
    STATIC_ROOT=${STATIC_ROOT}

# Helps track down issues in command execution
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

RUN apt-get update && apt-get install --no-install-recommends -y pipx \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

COPY --from=debian-builder /usr/bin/imapsync /usr/bin/imapsync

# Create user and group
RUN addgroup --gid $GID $GROUPNAME && \
    adduser --disabled-password --gecos '' --uid 1001 --gid $GID pymap

# Create the log directory and add permissions to user and group
RUN mkdir -p $PYMAP_LOGDIR
RUN chown -R pymap:$GROUPNAME $PYMAP_LOGDIR && chmod -R g+rw $PYMAP_LOGDIR

USER pymap
WORKDIR /home/pymap/app

# Poetry install
RUN pipx install poetry \
    # Add pipx executables to path
    && pipx ensurepath

# Set PATH to include pipx binary directory
# ensurepath does not refresh the environment during the build it seems
ENV PATH="/home/pymap/.local/bin:$PATH"
# Add poetry home to path
ENV PATH="$POETRY_HOME/bin:$PATH"

# Create .pg_service.conf
RUN cat > ~/.pg_service.conf <<EOF
[pymap]
host=$POSTGRES_HOST
user=$POSTGRES_USER
dbname=$POSTGRES_DB
port=$POSTGRES_PORT
EOF

# Create .pgpass file in the app directory so that it can be loaded by the app
RUN echo "$POSTGRES_HOST:$POSTGRES_PORT:$POSTGRES_DB:$POSTGRES_USER:$POSTGRES_PASSWORD" > ./.pgpass
RUN chmod 600 ./.pgpass

# Create .secret file for SECRET_KEY
RUN echo "$SECRET_KEY" > ./.secret
RUN chmod 600 ./.secret

# copy the app
COPY ./src ./

COPY Dockerfiles/django/init.sh ./init.sh

# Install dependecies trough poetry
RUN poetry install $(if [ "$DJANGO_ENV" = 'production' ]; then echo '--only main'; fi) \
    --no-interaction --no-ansi --sync

# Collect static assets
#RUN poetry run python manage.py collectstatic

ENTRYPOINT [ "/home/pymap/app/init.sh" ]
# For debbuging
#CMD ["tail", "-f", "/dev/null"]