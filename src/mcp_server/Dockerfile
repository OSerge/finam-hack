FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN groupadd -r mcp && useradd -r -g mcp mcp

WORKDIR /app

COPY src/mcp_server/requirements.txt ./
COPY src/mcp_server/server.py ./
COPY src/mcp_server/__init__.py ./

COPY src/app/adapters/ ./app/adapters/

RUN mkdir -p app/adapters

RUN uv pip install --system --no-cache -r requirements.txt

RUN chown -R mcp:mcp /app

USER mcp

EXPOSE 8765

CMD ["python", "server.py"]
