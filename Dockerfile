FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
	libglib2.0-0 \
	libpango-1.0-0 \
	libpangoft2-1.0-0 \
	libcairo2 \
	libgdk-pixbuf-2.0-0 \
	libharfbuzz0b \
	shared-mime-info \
	&& rm -rf /var/lib/apt/lists/*
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app/