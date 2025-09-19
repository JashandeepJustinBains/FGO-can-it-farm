from pymongo import MongoClient
import os
import logging

# Initialize MongoDB client from environment
mongo_uri = os.getenv('MONGO_URI')
if not mongo_uri:
    raise ValueError("No MONGO_URI environment variable set")

client = MongoClient(mongo_uri)
db = client['FGOCanItFarmDatabase']
servants_collection = db['servants']
quests_collection = db['quests']
mysticcode_collection = db['mysticcodes']

# Reduce pymongo logging noise
logging.getLogger('pymongo').setLevel(logging.WARNING)
