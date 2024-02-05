FROM python:3.10-slim

# `DJANGO_ENV` arg is used to make prod / dev builds:
ARG DJANGO_ENV \
  # Needed for fixing permissions of files created by Docker:
  UID=1000 \
  GID=1000


ENV DJANGO_ENV=${DJANGO_ENV} \
  # python:
  PYTHONFAULTHANDLER=1 \
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
  POETRY_HOME='/usr/local'

# Helps track down issues in command execution
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

WORKDIR /app

# Install imapsync dependencies
RUN apt-get update && \
    apt-get install -y git curl tmux supervisor apt-file make gcc cpanminus libtest-mock-guard-perl \
    libjson-webtoken-perl libjson-perl libpar-packer-perl libwww-perl libio-socket-inet6-perl zlib1g-dev libssl-dev libpackage-stash-xs-perl \
    # Installing `poetry` package manager:
    # https://github.com/python-poetry/poetry
    && curl -sSL 'https://install.python-poetry.org' | python - \
    && poetry --version \
    # Cleaning cache:
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Required for imapsync dependecy check
RUN apt-file update

# Perl modules for imapsync
RUN cpanm Mail::IMAPClient Authen::NTLM CGI Crypt::OpenSSL::RSA Data::Uniqid \
    Digest::HMAC Digest::HMAC_MD5 Dist::CheckConflicts Encode::IMAPUTF7 File::Copy::Recursive \
    File::Tail IO::Socket::INET6 IO::Socket::SSL IO::Tee JSON JSON::WebToken::Crypt::RSA \
    LWP::UserAgent Module::ScanDeps Net::SSLeay Proc::ProcessTable Regexp::Common \
    Sys::MemInfo Term::ReadKey Test::Fatal Test::MockObject Test::Pod \
    Test::Requires Test::Deep Unicode::String Readonly Package::Stash


# Clone and install imapsync
RUN git clone https://github.com/imapsync/imapsync.git
RUN cd imapsync && make install

# supervisor config
COPY Dockerfiles/aio/supervisord.conf /etc/supervisord.conf

# Copy lock and project file for caching purposes
COPY ./src/poetry.lock /app/poetry.lock
COPY ./src/pyproject.toml /app/pyproject.toml


# Project initialization:
# RUN --mount=type=cache,target="$POETRY_CACHE_DIR" \
#   echo "$DJANGO_ENV" \
#   && poetry install \
#     $(if [ "$DJANGO_ENV" = 'production' ]; then echo '--only main'; fi) \
#     --no-interaction --no-ansi --sync
RUN echo "$DJANGO_ENV" && poetry install

# copy the app
COPY ./src /app/

# makemigrations and migrate (required for aio in first time setup)
RUN poetry run task prepare && poetry run task migrate

# Handle tasks with supervisor
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
