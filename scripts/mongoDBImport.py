import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
import sys

# Set the encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

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

def import_servants(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            # Decode the filename using UTF-8
            servant_name = os.path.splitext(filename)[0].encode('utf-8').decode('utf-8')
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)

            # Check if servant already exists
            existing_servant = db['servants'].find_one({"name": servant_name})
            if existing_servant:
                print(f"Skipping duplicate servant: {servant_name.encode('utf-8').decode('utf-8')}")
            else:
                db['servants'].update_one({"name": servant_name}, {"$set": data}, upsert=True)
                print(f"Imported {servant_name.encode('utf-8').decode('utf-8')} into 'servants' collection.")



def import_quests(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            quest_name = os.path.splitext(filename)[0]
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
            db['quests'].insert_one(data)
            print(f"Imported {quest_name} into 'quests' collection.")

# import_servants('./ServantData')
import_quests('./Quests')
