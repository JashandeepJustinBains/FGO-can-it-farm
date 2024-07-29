import pymongo
import json
import sys

# Set the encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Connect to MongoDB
host = 'localhost'  # If MongoDB runs on the same machine
port = 27017  # Default MongoDB port
db_name = 'mydb'  # Your database name

client = pymongo.MongoClient(host, port)
db = client[db_name]
servants_collection = db['servants']
quests_collection = db['quests']

# Initialize an empty dictionary to store traits
traits_dict = {}

# Function to extract traits from a list of traits
def extract_traits(traits_list):
    for trait in traits_list:
        trait_id = trait.get("id")
        trait_name = trait.get("name")
        if trait_id not in traits_dict:
            traits_dict[trait_id] = trait_name

# Check if the collections are accessible
print(f"Servants collection count: {servants_collection.count_documents({})}")
print(f"Quests collection count: {quests_collection.count_documents({})}")

# Iterate through each servant document in the collection
for servant in servants_collection.find():
    print(f"Processing servant: {servant.get('name', 'Unknown')}")
    extract_traits(servant.get("traits", []))

# Iterate through each quest document in the collection
for quest in quests_collection.find():
    for stage in quest.get("stages", []):
        for enemy in stage.get("enemies", []):
            print(f"Processing enemy: {enemy.get('name', 'Unknown')}")
            extract_traits(enemy.get("traits", []))

# Output the traits dictionary to a JSON file
with open("traits.json", "w") as file:
    json.dump(traits_dict, file, indent=4)

print("Traits have been successfully extracted and saved to traits.json")
