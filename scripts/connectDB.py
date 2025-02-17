import os
from pymongo import MongoClient
from dotenv import load_dotenv
import sys

# Connect to MongoDB
# Load environment variables from .env file
load_dotenv()
# Get the username and password from environment variables
# Set the encoding to UTF-8
username = os.getenv('MONGO_USER')
password = os.getenv('MONGO_PASS')
route = os.getenv('MONGO_ROUTE')
# Connect to MongoDB
client = MongoClient(f"mongodb+srv://{username}:{password}@{route}/")
db = client['FGOCanItFarmDatabase']
# Set the encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')
