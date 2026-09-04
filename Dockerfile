FROM python:3.10-slim

# LibreOffice और fontconfig इंस्टॉल करें (PDF रूपांतरण और हिंदी/कस्टम फॉन्ट्स के लिए)
RUN apt-get update && apt-get install -y \
    libreoffice \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. आपके 'fonts' फोल्डर से सभी फॉन्ट्स (MS Word / PPT के लिए) को सिस्टम फॉन्ट डायरेक्टरी में कॉपी करें
COPY fonts/ /usr/share/fonts/truetype/custom_fonts/

# 2. Linux फॉन्ट कैश रीफ्रेश करें ताकि LibreOffice इन्हें तुरंत पहचान सके
RUN fc-cache -f -v

# 3. LibreOffice के लिए पर्यावरण चर (Environment Variable) सेट करें ताकि वह सिस्टम फॉन्ट्स का सही से उपयोग करे
ENV SAL_USE_VCLPLUGIN=gen

# Python requirements इंस्टॉल करें
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# बाकी सारा कोड और टेंप्लेट फाइलें कॉपी करें
COPY . .

# पोर्ट एक्सपोज़ करें
EXPOSE 8080

# बॉट चालू करें
CMD ["python", "main.py"]
