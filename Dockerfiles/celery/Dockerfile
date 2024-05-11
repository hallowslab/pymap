FROM debian:bookworm as debian-builder

# Install system and perl dependencies
RUN apt-get update && \
    apt-get install --no-install-recommends -y git curl apt-file make time gcc lsb-release procps cpanminus \
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

ARG DJANGO_ENV \
    DJANGO_SETTINGS_MODULE \
    CELERY_BROKER_URL \
    CELERY_RESULT_BACKEND \
    PYMAP_LOGDIR \
    SECRET_KEY \
    GROUPNAME \
    GID

ENV DJANGO_ENV=${DJANGO_ENV} \
    DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} \
    CELERY_BROKER_URL=${CELERY_BROKER_URL} \
    CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}

# Helps track down issues in command execution
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

# pipx install
RUN apt-get update && apt-get install --no-install-recommends -y pipx  \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*
    
COPY --from=debian-builder /usr/bin/imapsync /usr/bin/imapsync

# Create user and group
RUN addgroup --gid $GID $GROUPNAME && \
    adduser --disabled-password --gecos '' --uid 1001 --gid $GID celery

# Create the log directory
RUN mkdir -p $PYMAP_LOGDIR

RUN chown -R celery:$GROUPNAME $PYMAP_LOGDIR && chmod -R g+rw $PYMAP_LOGDIR


# Switch to user and app directory
USER celery

WORKDIR /home/celery/app

# Poetry install
RUN pipx install poetry \
    # Add pipx executables to path
    && pipx ensurepath


# Set PATH to include pipx binary directory
# ensurepath does not refresh the environment during the build it seems
ENV PATH="/home/celery/.local/bin:$PATH"

# Create .secret file for SECRET_KEY
RUN echo "$SECRET_KEY" > ./.secret
RUN chmod 600 ./.secret

# copy the project
COPY ./src/ ./

# Install dependecies trough poetry
RUN poetry install --without=dev

CMD ["sh", "-c", "sleep 10 && poetry run celery -A pymap.celery worker -l INFO"]
# For debbuging
#CMD ["tail", "-f", "/dev/null"]