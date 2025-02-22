import requests
import json
import os
import re
import time
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(filename='script.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# Load environment variables from .env file
load_dotenv()

# Adjust logging level for pymongo to suppress debug messages
logging.getLogger('pymongo').setLevel(logging.WARNING)

# MongoDB connection
mongo_uri = os.getenv('MONGO_URI')
if not mongo_uri:
    raise ValueError("No MONGO_URI environment variable set")

client = MongoClient(mongo_uri)
db = client['FGOCanItFarmDatabase']
servants_collection = db['servants']
quests_collection = db['quests']
mysticcode_collection = db['mysticcodes']

def compare_and_upsert(collection, query, data):
    try:
        existing_entry = collection.find_one(query)
        if existing_entry:
            if existing_entry != data:
                collection.update_one(query, {'$set': data}, upsert=True)
                logging.info(f"Updated entry with query: {query}")
            else:
                logging.info(f"No update needed for entry with query: {query}")
        else:
            collection.update_one(query, {'$set': data}, upsert=True)
            logging.info(f"Inserted new entry with query: {query}")
    except Exception as e:
        logging.error(f"Error during upsert: {e}")

def upsert_quest(data):
    quest_id = data.get('id')
    stages = data.get('stages', [])
    
    # Check if stages[0].enemies contains at least one item
    if quest_id and stages and 'enemies' in stages[0] and len(stages[0]['enemies']) > 0:
        compare_and_upsert(quests_collection, {'id': quest_id}, data)
    else:
        logging.error(f"Quest data missing 'id' field or stages[0].enemies is empty for quest ID: {quest_id}")

def upsert_servant(data):
    collection_no = data.get('collectionNo')
    if collection_no:
        compare_and_upsert(servants_collection, {'collectionNo': collection_no}, data)
    else:
        logging.error("Servant data missing 'collectionNo' field")

def download_and_upsert(url, upsert_function):
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                try:
                    data = response.json()
                    upsert_function(data)
                    return True
                except json.JSONDecodeError as e:
                    logging.error(f"JSONDecodeError: {e}")
                    logging.error(f"Response content: {response.content}")
                    return False
            else:
                logging.error(f"Failed to download data from {url}, status code: {response.status_code}")
        except requests.RequestException as e:
            logging.error(f"RequestException: {e}")
        time.sleep(2 ** attempt)  # Exponential backoff
    return False

def retrieve_servants():
    servant_url = 'https://api.atlasacademy.io/nice/JP/servant/{}?lore=true&expand=true&lang=en'
    current_servant_id = 1
    last_known_servant_id = 435
    while current_servant_id <= last_known_servant_id:
        url = servant_url.format(current_servant_id)
        if not download_and_upsert(url, upsert_servant):
            logging.error(f"Failed to process servant ID: {current_servant_id}")
        current_servant_id += 1
        time.sleep(1)  # Adding a delay of 1 second between requests

def get_quest_ids_from_api(war_id):
    url = f'https://api.atlasacademy.io/nice/JP/war/{war_id}?lang=en'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            quest_ids = []
            spots = data.get('spots', [])
            for spot in spots:
                quests = spot.get('quests', [])
                for quest in quests:
                    recommend_lv = quest.get('recommendLv', '')
                    consume = quest.get('consume', 0)
                    after_clear = quest.get('afterClear', '')
                    if recommend_lv in ['90', '90+', '90++', '90★', '90★★'] and consume == 40 and after_clear == 'repeatLast':
                        quest_ids.append(quest.get('id', 'UnknownID'))
            return quest_ids
        else:
            logging.error(f"Failed to download data from {url}, status code: {response.status_code}")
    except requests.RequestException as e:
        logging.error(f"RequestException: {e}")
    return []

def get_quest_details_and_upsert(quest_ids):
    for quest_id in quest_ids:
        url = f'https://api.atlasacademy.io/nice/JP/quest/{quest_id}/1?lang=en'
        if not download_and_upsert(url, upsert_quest):
            logging.error(f"Failed to process quest ID: {quest_id}")
        time.sleep(1)  # Adding a delay of 1 second between requests

def main():
    war_ids = [
        8382, 8383, 8384, 8385, 9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008, 9009, 9010, 9013, 9014, 9015, 9018, 9021, 9022, 9029, 9031, 9032, 9033, 9035, 9040, 9046, 9048, 9049, 9050, 9051, 9052, 9053, 9056, 9057, 9058, 9068, 9069, 9071, 9072, 9073, 9074, 9075, 9076, 9077, 9080, 9087, 9088, 9091, 9097, 9098, 9099, 9101, 9107, 9109, 9111, 9112, 9113, 9119, 9120, 9124, 9125, 9127, 9128, 9130, 9131, 9133, 9134, 9135, 9136, 9143, 9144, 9145, 9151, 9152, 9160, 9163, 9164, 9166, 9168, 9169, 9170, 9171, 9172, 9173, 9174, 9175, 9182, 9184, 9185, 9188, 9189, 9190, 9999, 11000, 12000, 13000, 14000
    ]

    all_quest_ids = []
    for war_id in war_ids:
        quest_ids = get_quest_ids_from_api(war_id)
        all_quest_ids.extend(quest_ids)

    get_quest_details_and_upsert(all_quest_ids)

    retrieve_servants()

if __name__ == "__main__":
    main()
