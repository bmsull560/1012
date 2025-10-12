# ValueVerse Development Container
# Multi-stage Dockerfile for full-stack development with Python 3.11 and Node.js 22

FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Configure apt and install packages
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
    # Essential build tools
    build-essential \
    ca-certificates \
    curl \
    wget \
    git \
    gnupg \
    lsb-release \
    software-properties-common \
    # Python build dependencies
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    # PostgreSQL client
    postgresql-client \
    # Redis client
    redis-tools \
    # Utilities
    vim \
    nano \
    less \
    jq \
    htop \
    sudo \
    openssh-client \
    iproute2 \
    procps \
    lsof \
    net-tools \
    psmisc \
    rsync \
    unzip \
    zip \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 22.x
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Install global Node.js packages
RUN npm install -g \
    typescript \
    ts-node \
    @types/node \
    pnpm \
    yarn \
    eslint \
    prettier

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Upgrade pip and install Python development tools
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir \
    # Formatters and linters
    black \
    isort \
    flake8 \
    pylint \
    mypy \
    ruff \
    # Testing
    pytest \
    pytest-cov \
    pytest-asyncio \
    pytest-mock \
    # Type stubs
    types-redis \
    types-requests \
    # Development tools
    ipython \
    ipdb \
    # Database tools
    alembic \
    psycopg2-binary \
    asyncpg \
    # FastAPI and dependencies
    fastapi \
    uvicorn[standard] \
    pydantic \
    pydantic-settings \
    python-multipart \
    # Redis
    redis \
    # AI/ML frameworks (base installations)
    openai \
    anthropic \
    langchain \
    langchain-community \
    langchain-openai \
    # Utilities
    python-dotenv \
    httpx \
    aiohttp \
    celery \
    sqlalchemy

# Install Docker CLI for Docker-in-Docker support
RUN curl -fsSL https://get.docker.com -o get-docker.sh \
    && sh get-docker.sh \
    && rm get-docker.sh

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Create workspace directory
RUN mkdir -p /workspace

# Set working directory
WORKDIR /workspace

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog

# Set up non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create user if not exists
RUN if ! id -u $USERNAME > /dev/null 2>&1; then \
    groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME; \
    fi

# Give user ownership of workspace
RUN chown -R $USERNAME:$USERNAME /workspace

# Set default shell to bash
ENV SHELL=/bin/bash

# Default command
CMD ["/bin/bash"]
