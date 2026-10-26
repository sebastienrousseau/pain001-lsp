# syntax=docker/dockerfile:1.6
# Multi-stage build for a minimal pain001-lsp image.
#
# The container runs the pygls language server over stdio so an LSP
# client can launch it directly with ``docker run -i --rm pain001-lsp``.

FROM python:3.12-slim@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704 AS builder

WORKDIR /build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Empty by default: the image installs the pain001 release pinned in
# requirements/runtime.txt. The GHCR pipeline sets it to a core branch
# name (main, feat/*, fix/*) to build against an unreleased core branch
# before that release reaches PyPI. The git client is needed only for
# that override; it stays in this build stage and never ships in the
# final image.
ARG PAIN001_REF=""
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# pyproject.toml carries ``readme = "README.md"``, so README.md must be
# present at build-time to resolve the package metadata.
COPY requirements/runtime.txt ./requirements/runtime.txt
COPY pyproject.toml README.md ./
COPY pain001_lsp ./pain001_lsp

# Every dependency comes hash-pinned from requirements/runtime.txt. The
# package (and the optional core branch) are built as wheels and
# installed with --no-deps, so nothing resolves an unpinned version.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --require-hashes -r requirements/runtime.txt \
    && if [ -n "$PAIN001_REF" ]; then \
         git clone --quiet --depth 1 --branch "$PAIN001_REF" \
           https://github.com/sebastienrousseau/pain001 /build/pain001-core \
         && /opt/venv/bin/pip wheel --no-deps -w /build/wheels /build/pain001-core; \
       fi \
    && /opt/venv/bin/pip wheel --no-deps -w /build/wheels . \
    && /opt/venv/bin/pip install --no-deps --force-reinstall /build/wheels/*.whl \
    && /opt/venv/bin/pip check


FROM python:3.12-slim@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704

LABEL org.opencontainers.image.title="pain001-lsp" \
      org.opencontainers.image.description="Language Server Protocol server for the pain001 ISO 20022 library." \
      org.opencontainers.image.source="https://github.com/sebastienrousseau/pain001-lsp" \
      org.opencontainers.image.licenses="Apache-2.0 OR MIT"

# Non-root user (LSP clients launch the container with stdio; no extra
# privileges needed).
RUN groupadd --system lsp && useradd --system --gid lsp --home /home/lsp lsp \
    && mkdir -p /home/lsp \
    && chown -R lsp:lsp /home/lsp

COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER lsp
WORKDIR /home/lsp

# A non-zero exit here means an import / dependency mismatch; the LSP
# client will see it before the first request.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import pain001_lsp.server" || exit 1

ENTRYPOINT ["pain001-lsp"]
