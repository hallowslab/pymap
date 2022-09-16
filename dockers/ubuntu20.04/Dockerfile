# syntax=docker/dockerfile:experimental
FROM ubuntu:20.04

EXPOSE 3000 5000 8000 8080 22 20 21

ENV DEBIAN_FRONTEND=noninteractive

# System Dependencies #
RUN set -xe && apt update && apt install -y \
  git python-is-python3 python3 python3-pip \
  python3-venv redis-server procps wget make \
  cpanminus lsof lsb-release curl rcs tmux sudo bash \
  zsh vsftpd vim

# Oh-my-zsh
RUN sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"


# Perl Dependencies #
RUN set -xe && apt install -y libauthen-ntlm-perl libdist-checkconflicts-perl libcgi-pm-perl \
  libcrypt-openssl-rsa-perl libdata-uniqid-perl libencode-imaputf7-perl \
  libfile-copy-recursive-perl libfile-tail-perl libio-socket-ssl-perl \
  libio-socket-inet6-perl libio-tee-perl libhtml-parser-perl \
  libjson-webtoken-perl libmail-imapclient-perl libparse-recdescent-perl \
  libmodule-scandeps-perl libpar-packer-perl libreadonly-perl \
  libregexp-common-perl libsys-meminfo-perl libterm-readkey-perl \
  libtest-mockobject-perl libtest-pod-perl libunicode-string-perl \
  liburi-perl libwww-perl libtest-fatal-perl libtest-mock-guard-perl \
  libtest-requires-perl libtest-deep-perl && rm -rf /var/lib/apt/lists/*


# create directories : /var/share/empty
# in /etc/vsftpd.conf, add this line at the end of the file :
# secure_chroot_dir=/var/share/empty
# and it will be ok
RUN mkdir -p /var/share/empty


SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# Add a non root user, with sudo privileges
#RUN adduser --disabled-password --gecos '' pymap
RUN useradd -rm -d /home/pymap -s /bin/bash -g root -G sudo -u 1001 pymap
RUN echo 'pymap:pymap' | chpasswd
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
# Add user to ftp allowed list before switching accounts
RUN echo "pymap" | tee -a /etc/vsftpd.user_list
# Add vsftpd config file
COPY --chown=root:root ./configs/vsftpd.conf /etc/
USER pymap


# TODO: Can be moved to system dependencies
# Install node
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
RUN sudo apt install -y nodejs

# TODO: Enable caching
# Install poetry
ENV POETRY_HOME=/home/pymap/.poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
# Permanently export the path for bash
ENV PATH="$PATH:/home/pymap/.poetry/bin"


# Clone and build imapsync
WORKDIR /home/pymap/
RUN git clone https://github.com/imapsync/imapsync.git
WORKDIR /home/pymap/imapsync
RUN set -xe && mkdir W && sudo make install


# Pymap - project #
WORKDIR /home/pymap/pymap
COPY --chown=pymap:sudo ./src/ /home/pymap/pymap
# Add tmux startup script
COPY --chown=pymap:sudo ./configs/tmux.sh /home/pymap/pymap/
# Install python project dependencies
RUN poetry install

# Create log directories
RUN sudo mkdir -p /var/log/pymap
RUN sudo chown -R pymap:sudo /var/log/pymap
# Generate some random logs for testing purposes
RUN poetry run task genLogs


# Install node dependencies and build project
WORKDIR /home/pymap/pymap/client
# Caching NPM #
# remove default packages.json
RUN rm -rf package.json
# rename deps to package.json
RUN mv package-dependencies.json package.json
# Mount cache and install deps
RUN --mount=type=cache,target=/home/pymap/.npm,uid=1001 npm set cache /home/pymap/.npm && npm ci
# copy package.json to client
COPY ./src/client/package.json /home/pymap/pymap/client/package.json
# Build...
RUN npm run build

# Set workdir and environments
WORKDIR /home/pymap/pymap
ENV FLASK_ENV="development"


ENTRYPOINT [ "zsh" ]
