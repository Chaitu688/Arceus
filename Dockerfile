FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends adb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY device_panel.py /app/device_panel.py
COPY DEVICE_PANEL.md /app/DEVICE_PANEL.md
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

RUN chmod +x /app/docker-entrypoint.sh

ENV PYTHONUNBUFFERED=1

EXPOSE 8090

ENTRYPOINT ["/app/docker-entrypoint.sh"]
