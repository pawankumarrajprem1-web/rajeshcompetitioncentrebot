FROM python:3.10-slim

# System Dependencies & LibreOffice Installation
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    libreoffice-impress \
    libreoffice-writer \
    libreoffice-java-common \
    default-jre \
    xvfb \
    xauth \
    fonts-deva \
    fonts-noto-ui-core \
    fonts-noto-extra \
    fontconfig \
    libx11-6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Environment Setup for High Concurrency & Memory Savings
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Custom Fonts handling (Safe copy even if empty)
RUN mkdir -p /usr/share/fonts/truetype/custom_fonts/
COPY fonts/ /usr/share/fonts/truetype/custom_fonts/
RUN fc-cache -f -v

# Install Python Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy Application Files
COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
