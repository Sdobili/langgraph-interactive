FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY harness ./harness
COPY lessons ./lessons
COPY web ./web
COPY README.md .

EXPOSE 8765

# Use system Python (no .venv); web.app falls back to sys.executable for grading.
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8765"]
