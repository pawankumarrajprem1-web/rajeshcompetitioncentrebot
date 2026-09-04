FROM python:3.10-slim

# Render पर LibreOffice इंस्टॉल करें (PPT को PDF में कन्वर्ट करने के लिए)
RUN apt-get update && apt-get install -y \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements इंस्टॉल करें
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# बाकी सारा कोड कॉपी करें
COPY . .

# पोर्ट एक्सपोज़ करें
EXPOSE 8080

# बॉट चालू करें
CMD ["python", "main.py"]