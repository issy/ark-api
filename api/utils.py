import config
from pymongo import MongoClient
from typing import List


client = MongoClient(config.MONGO_CONNECTION_STRING)
db = client[config.MONGO_DB]
coll = db.intel


def search(query: str) -> List[dict]:
    # Prepare query
    for i in (' ', '-', '_'):
        query = query.replace(i, '[\s-]?')
    return [sanitise(i) for i in coll.find({"title": {"$regex": f".*{query}.*", "$options": "i"}})]


def sanitise(result: dict) -> dict:
    del result['_id']
    return result
