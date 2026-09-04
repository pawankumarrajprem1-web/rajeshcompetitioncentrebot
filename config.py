import os
import certifi
from pymongo import MongoClient

API_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")

# Admin ID Safe Parsing
admin_id_raw = os.getenv("ADMIN_ID", "0")
ADMIN_ID = int(admin_id_raw) if admin_id_raw.isdigit() else 0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PPT_TEMPLATE = os.path.join(BASE_DIR, "template.pptx")
DOCX_TEMPLATE = os.path.join(BASE_DIR, "template.docx")

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
db = client["rcc_quiz_db"]
tests_col = db["test_papers"]
