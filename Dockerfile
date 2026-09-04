FROM python:3.10-slim

# xvfb जोड़ें
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-script-provider-python \
    xvfb \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# फॉन्ट्स कॉपी करें
COPY fonts/ /usr/share/fonts/truetype/custom_fonts/
RUN fc-cache -f -v

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# xvfb-run के जरिए कमांड चलाएं
CMD ["xvfb-run", "--auto-servernum", "python", "main.py"]
