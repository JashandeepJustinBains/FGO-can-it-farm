import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
import sys

# Connect to MongoDB
host = 'localhost'  # If MongoDB runs on the same machine
port = 27017  # Default MongoDB port
db_name = 'mongodb-container'  # Your database name
# Load environment variables from .env file
load_dotenv()
# Get the username and password from environment variables
# Set the encoding to UTF-8
username = os.getenv('MONGO_USER')
password = os.getenv('MONGO_PASS')
# Connect to MongoDB
client = MongoClient(f"mongodb://{username}:{password}@localhost:27017/")
db = client['yourDatabase']  # Replace 'yourDatabase' with your actual database name

# delete all from db
# db['servants'].drop()
# db['quests'].drop()

all_quests = db['quests'].count_documents({})
print(all_quests)
for quest in all_quests:
    if quest['recommendedLv'] == "90+" or "90++":
        print(quest['recommendedLv'])

# count_servants = db['servants'].count_documents({})
# print(count_servants)
# all_servants = db['servants'].find()

# Process the retrieved data as needed
# for servant in all_servants:
    # print(servant['name'])