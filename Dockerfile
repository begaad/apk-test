FROM python:3.12-slim
WORKDIR /srv
COPY backend/requirements.txt /srv/requirements.txt
RUN pip install --no-cache-dir -r /srv/requirements.txt && mkdir -p /srv/apk && chmod 777 /srv/apk
COPY backend /srv/backend
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APK_PATH=/srv/apk/app.apk
USER 65534:65534
EXPOSE 8080
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
