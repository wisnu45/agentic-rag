FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

ARG INSTALL_OCR=false
COPY requirements-ocr.txt .
RUN if [ "$INSTALL_OCR" = "true" ]; then \
      pip install --no-cache-dir -r requirements-ocr.txt; \
    fi

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
