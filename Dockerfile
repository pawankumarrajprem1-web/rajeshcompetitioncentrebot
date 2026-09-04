FROM python:3.10-slim

# Headless LibreOffice और X11 सपोर्टिंग लाइब्ररीज इंस्टॉल करें
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-script-provider-python \
    libx11-6 \
    libxext6 \
    libxrender1 \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# फॉन्ट्स कॉपी करें
COPY fonts/ /usr/share/fonts/truetype/custom_fonts/
RUN fc-cache -f -v

# Environment Variable
ENV SAL_USE_VCLPLUGIN=gen

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "main.py"]
