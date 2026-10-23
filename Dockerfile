# Build the wheel with the hash-pinned poetry-core, then install it with
# --no-deps over the hash-pinned runtime tree, so the image resolves
# nothing unpinned (OpenSSF Scorecard Pinned-Dependencies). Dependabot
# keeps the base image digest current.
FROM python:3.12-slim@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704 AS builder

WORKDIR /src
COPY requirements/build.txt ./requirements/build.txt
RUN pip install --no-cache-dir --require-hashes -r requirements/build.txt
COPY pyproject.toml README.md ./
COPY acmt001/ ./acmt001/
RUN python -m build --wheel --no-isolation --outdir /dist

FROM python:3.12-slim@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704 AS base

LABEL maintainer="Sebastien Rousseau <sebastian.rousseau@gmail.com>"
LABEL description="Acmt001 ISO 20022 acmt Account Management XML Generation API"

WORKDIR /app

COPY requirements/runtime.txt ./requirements/runtime.txt
RUN pip install --no-cache-dir --require-hashes -r requirements/runtime.txt
COPY --from=builder /dist/ /tmp/dist/
RUN pip install --no-cache-dir --no-deps /tmp/dist/*.whl && rm -rf /tmp/dist

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

# Run the API server
CMD ["python", "-m", "uvicorn", "acmt001.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
