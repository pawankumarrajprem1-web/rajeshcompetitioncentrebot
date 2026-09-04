import html
from config import tests_col

def save_test_paper(doc_id: str, topic: str, raw_text: str):
    """नया टेस्ट पेपर डेटाबेस में सेव करता है"""
    tests_col.insert_one({
        "_id": doc_id,
        "topic": topic,
        "raw_text": raw_text
    })

def get_test_paper(doc_id: str):
    """ID के आधार पर टेस्ट पेपर निकालता है"""
    return tests_col.find_one({"_id": doc_id})

def get_recent_tests(limit: int = 5):
    """हाल ही में बनाए गए टेस्ट की लिस्ट निकालता है"""
    return list(tests_col.find().sort("_id", -1).limit(limit))

def get_total_tests_count():
    """कुल टेस्ट की संख्या बताता है"""
    return tests_col.count_documents({})
