from config import tests_col

async def save_test_paper(doc_id: str, topic: str, raw_text: str, user_id: int = None):
    """सुरक्षित और नॉन-ब्लॉकिंग इंसर्ट/अपडेट"""
    data = {
        "_id": doc_id,
        "topic": topic,
        "raw_text": raw_text
    }
    if user_id:
        data["user_id"] = user_id
        
    await tests_col.update_one({"_id": doc_id}, {"$set": data}, upsert=True)

async def get_test_paper(doc_id: str):
    """एक टेस्ट पेपर खोजना"""
    return await tests_col.find_one({"_id": doc_id})

async def get_recent_tests(limit: int = 5):
    """हालिया टेस्ट निकालना"""
    cursor = tests_col.find().sort("_id", -1).limit(limit)
    return await cursor.to_list(length=limit)

async def get_user_tests_paginated(user_id: int, page: int = 1, page_size: int = 5):
    """केवल यूज़र के टेस्ट पेजिंग के साथ"""
    skip = (page - 1) * page_size
    query = {"user_id": user_id}
    total = await tests_col.count_documents(query)
    cursor = tests_col.find(query).sort("_id", -1).skip(skip).limit(page_size)
    records = await cursor.to_list(length=page_size)
    return records, total

async def get_all_tests_paginated(page: int = 1, page_size: int = 5):
    """एडमिन के लिए सभी टेस्ट पेजिंग के साथ"""
    skip = (page - 1) * page_size
    total = await tests_col.count_documents({})
    cursor = tests_col.find({}).sort("_id", -1).skip(skip).limit(page_size)
    records = await cursor.to_list(length=page_size)
    return records, total

async def delete_test_paper(doc_id: str):
    """टेस्ट डिलीट करना"""
    result = await tests_col.delete_one({"_id": doc_id})
    return result.deleted_count > 0

async def get_total_tests_count():
    """कुल टेस्ट पेपर्स की संख्या"""
    return await tests_col.count_documents({})
