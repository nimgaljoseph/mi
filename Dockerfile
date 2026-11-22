FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements-voice.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-voice.txt
COPY backend/app ./app
COPY frontend ./frontend
ENV MINI_HOME=/app
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","3000"]
