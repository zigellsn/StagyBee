FROM docker.io/python:3.14.0-slim
COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

RUN useradd --gid users --create-home pyuser

ENV HOME /home/pyuser
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV TMP /tmp
ENV PATH="$HOME/.venv/bin:$PATH"

WORKDIR $HOME