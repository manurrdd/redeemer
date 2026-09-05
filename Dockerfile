FROM python:3.13-slim

RUN useradd --system --uid 10001 redeemer && install -d -o redeemer -g redeemer /data

WORKDIR /app
COPY redeemer ./redeemer

ENV REDEEMER_DB=/data/redeemer.db \
    REDEEMER_BACKUP_DIR=/data/backups \
    REDEEMER_HOST=0.0.0.0 \
    REDEEMER_PORT=8787 \
    REDEEMER_BEHIND_PROXY=1 \
    PYTHONUNBUFFERED=1

USER redeemer
EXPOSE 8787
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/healthz')"
CMD ["python", "-m", "redeemer", "serve"]
