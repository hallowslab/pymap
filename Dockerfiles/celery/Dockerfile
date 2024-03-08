FROM python:3.11

WORKDIR /app

# Poetry install
RUN apt-get update && apt-get install --no-recommends pipx \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Poetry install
RUN pipx install poetry \
    # Add pipx executables to path
    && pipx ensurepath

# Set PATH to include pipx binary directory
# ensurepath does not refresh the environment during the build it seems
ENV PATH="/root/.local/bin:$PATH"

# copy the app
COPY ./src /app/

# Install dependecies trough poetry
RUN poetry install --without=dev

CMD ["sh", "-c", "poetry shell && celery -A pymap.celery worker -l INFO"]
