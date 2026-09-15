FROM python:3.10-slim

# Install LibreOffice, Xvfb, xauth and Fonts
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

# Copy custom fonts
COPY fonts/ /usr/share/fonts/truetype/custom_fonts/
RUN fc-cache -f -v

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
