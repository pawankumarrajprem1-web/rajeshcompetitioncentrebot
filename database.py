import html
from config import tests_col

def save_test_paper(doc_id: str, topic: str, raw_text: str, user_id: int = None):
    """पुराने और नए दोनों तरीकों से काम करेगा"""
    data = {
        "_id": doc_id,
        "topic": topic,
        "raw_text": raw_text
    }
    if user_id:
        data["user_id"] = user_id
    tests_col.insert_one(data)

def get_test_paper(doc_id: str):
    return tests_col.find_one({"_id": doc_id})

def get_recent_tests(limit: int = 5):
    """पुराना फ़ीचर - हालिया टेस्ट निकालना"""
    return list(tests_col.find().sort("_id", -1).limit(limit))

def get_user_tests_paginated(user_id: int, page: int = 1, page_size: int = 5):
    """नया फ़ीचर - केवल यूज़र के टेस्ट पेजिंग के साथ"""
    skip = (page - 1) * page_size
    query = {"user_id": user_id}
    total = tests_col.count_documents(query)
    records = list(tests_col.find(query).sort("_id", -1).skip(skip).limit(page_size))
    return records, total

def get_all_tests_paginated(page: int = 1, page_size: int = 5):
    """नया फ़ीचर - एडमिन के लिए सभी टेस्ट पेजिंग के साथ"""
    skip = (page - 1) * page_size
    total = tests_col.count_documents({})
    records = list(tests_col.find({}).sort("_id", -1).skip(skip).limit(page_size))
    return records, total

def delete_test_paper(doc_id: str):
    """नया फ़ीचर - टेस्ट डिलीट करना"""
    result = tests_col.delete_one({"_id": doc_id})
    return result.deleted_count > 0

def get_total_tests_count():
    return tests_col.count_documents({})
