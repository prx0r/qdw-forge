FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
RUN useradd -r -u 10001 qdw && chown -R qdw:qdw /app
USER qdw
ENV QDW_FORGE_DB=/data/forge.db
CMD ["uvicorn", "qdw_forge.api:app", "--host", "0.0.0.0", "--port", "8788"]
