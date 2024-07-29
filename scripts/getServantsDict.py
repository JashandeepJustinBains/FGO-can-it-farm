import pymongo
import json
import sys
from dotenv import load_dotenv
import os

# Set the encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Connect to MongoDB
host = 'localhost'  # If MongoDB runs on the same machine
port = 27017  # Default MongoDB port
db_name = 'mydb'  # Your database name
# Load environment variables from .env file
load_dotenv()
# Get the username and password from environment variables
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')

client = pymongo.MongoClient(host, port)
db = client[db_name]
servants_collection = db['servants']

# Iterate over the servants collection and print the collectionNo
collection_numbers = {}
for servant in servants_collection.find():
    collection_no = servant.get('collectionNo')
    if collection_no is not None:
        collection_numbers[collection_no] = servant.get('battleName')

for e in collection_numbers:
    print(f'{e}:\"{collection_numbers[e]}\",')
