import os
import certifi
from pymongo import MongoClient

API_TOKEN = os.getenv("BOT_TOKEN", "8951859856:AAG5teDA8nM6_sY7y6b_prOkT9tDXaSh5Iw")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://mpcpawan:RswOqZ4uy3UQtM3Q@cluster0.edkvmpu.mongodb.net/")

# Admin ID Safe Parsing
admin_id_raw = os.getenv("ADMIN_ID", "5772540382")
ADMIN_ID = int(admin_id_raw) if admin_id_raw.isdigit() else 0

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PPT_TEMPLATE = os.path.join(BASE_DIR, "template.pptx")
DOCX_TEMPLATE = os.path.join(BASE_DIR, "template.docx")

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
db = client["rcc_quiz_db"]
tests_col = db["test_papers"]
