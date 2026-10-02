FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

ARG APP_DIR=app_level_1
COPY ${APP_DIR}/app.py /app/app.py

ENV PORT=5000
EXPOSE 5000

CMD ["python", "app.py"]
