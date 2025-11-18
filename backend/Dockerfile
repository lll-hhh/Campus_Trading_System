FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt /tmp/
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app

CMD ["uvicorn", "apps.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
