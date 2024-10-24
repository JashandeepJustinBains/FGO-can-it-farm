import os
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
db = client['FGOCanItFarmDatabase']
# Set the encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')
