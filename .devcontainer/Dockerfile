# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.209.6/containers/python-3/.devcontainer/base.Dockerfile
ARG USERNAME=root
# [Choice] Python version (use -bullseye variants on local arm64/Apple Silicon)
ARG VARIANT="3.11-bullseye"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

ARG NODE_VERSION="18"
RUN if [ "${NODE_VERSION}" != "none" ]; then su $USERNAME -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

# Additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libsystemd-dev \
    libudev-dev \
    curl \
    gnupg \
    software-properties-common \
    unzip \
    wget \
    jq \
    shellcheck \
    sqlite3

RUN npm install -g yarn prettier 2>&1
