import os
import certifi
from concurrent.futures import ThreadPoolExecutor
from motor.motor_asyncio import AsyncIOMotorClient

# Environment Variables
API_TOKEN = os.getenv("BOT_TOKEN", "").strip()
MONGO_URI = os.getenv("MONGO_URI", "").strip()

# Admin ID Safe Parsing
admin_id_raw = os.getenv("ADMIN_ID", "").strip()
ADMIN_ID = int(admin_id_raw) if admin_id_raw.isdigit() else 0

# Base Directories & Templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PPT_TEMPLATE = os.path.join(BASE_DIR, "template.pptx")
DOCX_TEMPLATE = os.path.join(BASE_DIR, "template.docx")

# Thread Pool Executor for CPU-intensive tasks (PDF / PPT / DOCX conversions)
# Prevents blocking the asyncio event loop under heavy load
MAX_WORKERS = min(32, (os.cpu_count() or 1) + 4)
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# Async MongoDB Client Configuration with Connection Pooling
client = AsyncIOMotorClient(
    MONGO_URI,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=5000,
    maxPoolSize=200,          # High traffic load handling
    minPoolSize=10,           # Keep warm connections ready
    maxIdleTimeMS=45000,
    waitQueueTimeoutMS=10000
)

db = client["rcc_quiz_db"]
tests_col = db["test_papers"]
