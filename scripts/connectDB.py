import os
from pymongo import MongoClient
from dotenv import load_dotenv
import sys

# Connect to MongoDB
# Load environment variables from .env file
load_dotenv()
# Get the username and password from environment variables
# Set the encoding to UTF-8

# MongoDB connection
mongo_uri = os.getenv('MONGO_URI_READ')
if not mongo_uri:
    raise ValueError("No MONGO_URI_READ environment variable set")

client = MongoClient(mongo_uri)
db = client['FGOCanItFarmDatabase']
servants_collection = db['servants']
quests_collection = db['quests']
mysticcode_collection = db['mysticcodes']

# Set the encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')
globals()['db'] = db