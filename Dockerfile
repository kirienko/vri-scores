FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt update && apt install -y \
    fonts-noto-cjk \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-rus \
    tesseract-ocr-jpn \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["python", "main.py"]
