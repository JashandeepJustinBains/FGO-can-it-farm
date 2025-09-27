
import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Use the admin URI from your environment or config
MONGO_URI = os.environ.get("MONGO_URI_ADMIN")
DATABASE = "FGOCanItFarmDatabase"
COLLECTION = "servants"

if not MONGO_URI:
    raise RuntimeError("MONGO_URI_ADMIN environment variable not set!")

client = MongoClient(MONGO_URI)
db = client[DATABASE]
collection = db[COLLECTION]

servant_dir = "servants"
count = 0
uploaded_1 = False
for filename in os.listdir(servant_dir):
    if filename.endswith("_structured.json"):
        with open(os.path.join(servant_dir, filename), "r", encoding="utf-8") as f:
            data = json.load(f)
            collection.replace_one({"collectionNo": data["collectionNo"]}, data, upsert=True)
            count += 1
            if data.get("collectionNo") == 1:
                uploaded_1 = True

# If collectionNo 1 was not uploaded, try to upload it explicitly
if not uploaded_1:
    path_1 = os.path.join(servant_dir, "1_structured.json")
    if os.path.exists(path_1):
        with open(path_1, "r", encoding="utf-8") as f:
            data = json.load(f)
            collection.replace_one({"collectionNo": 1}, data, upsert=True)
            print("Explicitly uploaded collectionNo 1.")

print(f"Upload complete! {count} servants uploaded to the 'servants' collection in FGOCanItFarmDatabase.")
