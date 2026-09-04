import os
import certifi
from pymongo import MongoClient

API_TOKEN = os.getenv("BOT_TOKEN", "")

MONGO_URI = os.getenv("MONGO_URI", "")

# टेंप्लेट फ़ाइलों के पाथ
BASE_DIR = os.path.dirname(__file__)
PPT_TEMPLATE = os.path.join(BASE_DIR, "template.pptx")
DOCX_TEMPLATE = os.path.join(BASE_DIR, "template.docx")

# MongoDB कनेक्शन
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
db = client["rcc_quiz_db"]
tests_col = db["test_papers"]
