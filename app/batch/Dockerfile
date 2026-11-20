FROM python:3.13-slim

WORKDIR /app

COPY batch/requirements.txt batch/
RUN pip install --no-cache-dir -r batch/requirements.txt

COPY batch/main.py batch/
COPY config/articles.yaml config/

CMD ["python", "batch/main.py"]