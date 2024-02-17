FROM python:3.11

# Needed for fixing permissions of files created by Docker:
ARG UID=1000 \
    GID=1000 \
    DJANGO_ENV \
    DJANGO_SETTINGS_MODULE \
    CELERY_BROKER_URL \
    CELERY_RESULT_BACKEND \
    STATIC_ROOT

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
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/opt/pypoetry' \
    POETRY_VIRTUALENVS_PREFER_ACTIVE_PYTHON=true \
    POETRY_INSTALLER_MAX_WORKERS=10


# Helps track down issues in command execution
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

WORKDIR /app

# Install imapsync dependencies
RUN apt-get update && \
    apt-get install -y apt-file pipx make time cpanminus libauthen-ntlm-perl libcgi-pm-perl libcrypt-openssl-rsa-perl \
    libdata-uniqid-perl libencode-imaputf7-perl libfile-copy-recursive-perl libfile-tail-perl libio-socket-inet6-perl \
    libio-socket-ssl-perl libio-tee-perl libhtml-parser-perl libjson-webtoken-perl libmail-imapclient-perl libparse-recdescent-perl \
    libproc-processtable-perl libmodule-scandeps-perl libreadonly-perl libregexp-common-perl libsys-meminfo-perl libterm-readkey-perl \
    libtest-mockobject-perl libtest-pod-perl libunicode-string-perl liburi-perl libwww-perl libtest-nowarnings-perl libtest-deep-perl \
    libtest-warn-perl libnet-server-perl libpar-packer-perl libtest-requires-perl libtest-mock-guard-perl

# Perl modules for imapsync
RUN cpanm Dist::CheckConflicts IO::Socket::SSL

# Required for imapsync dependecy check
RUN apt-file update

# Clone and install imapsync
RUN git clone https://github.com/imapsync/imapsync.git
RUN cd imapsync && make install

# Poetry install
RUN pipx install poetry
# Add pipx executables to path
RUN pipx ensurepath

# Set PATH to include pipx binary directory
# ensurepath does not refresh the environment during the build it seems
ENV PATH="/root/.local/bin:$PATH"

# copy the app
COPY ./src /app/

# Create the log directory
#RUN mkdir -p /var/log/pymap

# Install dependecies trough poetry
RUN poetry install --without=dev

CMD ["sh", "-c", "poetry run task server"]