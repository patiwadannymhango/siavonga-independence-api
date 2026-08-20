FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x docker-entrypoint.sh

# staticfiles/ and media/ are gitignored (build output / uploads, not
# source), so they don't exist in the image unless created here. Without
# this, docker-compose.prod.yml's named volumes mount over paths that
# don't pre-exist in the image, so Docker creates them root-owned instead
# of copying appuser-owned dirs from the image — collectstatic then fails
# with a permission error since the container runs as appuser.
RUN mkdir -p staticfiles media

RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
