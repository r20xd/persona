FROM ghcr.io/astral-sh/uv:0.12.1@sha256:cf4eedcaa81655197f625739489effcbe71b61ceb1506f332c3facae5deceded AS uv
FROM python:3.13.14-slim-trixie@sha256:9662417aace5ae7b8e2609cce472b72a8958e134ba372808abe9cc1a0c0125e6 AS build
RUN apt-get update && apt-get upgrade -y \
    && mkdir -p /usr/share/doc/deanery \
    && date -u +%FT%TZ > /usr/share/doc/deanery/build-apt-updated-at.txt \
    && find /var/lib/apt/lists -type f -exec sha256sum {} + > /usr/share/doc/deanery/build-apt-index-sha256.txt \
    && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY apps ./apps
COPY config ./config
COPY static ./static
COPY manage.py ./
RUN DJANGO_SETTINGS_MODULE=config.settings.build .venv/bin/python manage.py collectstatic --noinput

FROM python:3.13.14-slim-trixie@sha256:9662417aace5ae7b8e2609cce472b72a8958e134ba372808abe9cc1a0c0125e6
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends libpq5=17.11-0+deb13u1 \
    && mkdir -p /usr/share/doc/deanery \
    && date -u +%FT%TZ > /usr/share/doc/deanery/apt-updated-at.txt \
    && find /var/lib/apt/lists -type f -exec sha256sum {} + > /usr/share/doc/deanery/apt-index-sha256.txt \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip uninstall -y pip \
    && rm -rf /usr/local/lib/python3.13/ensurepip/_bundled
RUN groupadd --gid 10001 deanery && useradd --uid 10001 --gid 10001 --no-create-home deanery
WORKDIR /app
ENV PATH=/app/.venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=config.settings.production PSYCOPG_IMPL=python
COPY --from=build /usr/share/doc/deanery /usr/share/doc/deanery
COPY --from=build /app/.venv ./.venv
COPY --from=build /app/apps ./apps
COPY --from=build /app/config ./config
COPY --from=build /app/static ./static
COPY --from=build /app/staticfiles ./staticfiles
COPY manage.py ./
COPY docs/third-party/libargon2-LICENSE.txt /usr/share/doc/deanery/libargon2-LICENSE.txt
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=7s --start-period=15s --retries=3 CMD ["python", "-c", "import os,http.client; c=http.client.HTTPConnection('127.0.0.1',8000,timeout=6); c.request('GET','/health/ready/',headers={'Host':os.environ['DJANGO_ALLOWED_HOSTS'].split(',')[0]}); assert c.getresponse().status==200"]
CMD ["gunicorn", "config.wsgi:application", "--bind=0.0.0.0:8000", "--workers=2", "--threads=4", "--timeout=30", "--graceful-timeout=25", "--keep-alive=5", "--limit-request-line=4094", "--limit-request-fields=50", "--limit-request-field_size=8190", "--access-logfile=/dev/null", "--error-logfile=-", "--log-level=critical"]

COPY docs/third-party/runtime-notices /usr/share/doc/deanery/third-party
