import requests
import json
import os
import re
import time
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(filename='script.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Load environment variables from .env file
load_dotenv()

# Get the username and password from environment variables
username = os.getenv('MONGO_USER')
password = os.getenv('MONGO_PASS')

# Connect to MongoDB
host = 'localhost'
port = 27017
db_name = 'FGOCanItFarmDatabase'
client = MongoClient(f"mongodb://{username}:{password}@{host}:{port}/")
db = client[db_name]

def download_json(url, directory):
    response = requests.get(url)
    if response.status_code == 200:
        try:
            data = response.json()
            filename = None
            filepath = None
            if directory == './Quest':
                recommend_lv = data.get("recommendLv")
                consume = data.get("consume")
                if recommend_lv in ["90", "90+", "90++", "90★", "90★★"] and consume == 40:

                    name = f'{str(data["warLongName"])}-{str(data["recommendLv"])}'
                    # Invalid characters including escape sequences
                    invalid_chars = r'[\n\r\t\\&\'\"?<>{}%~/.]'

                    # Replace invalid characters with an empty string
                    filename = re.sub(invalid_chars, '', name).strip()
                    filepath = os.path.join(directory, f'{filename}.json')
                else:
                    logging.info(f"Skipped {url} due to filtering criteria.")
            elif directory == './ServantData':
                name = f'{str(data["collectionNo"])}-{str(data["name"])}'
                filename = "".join([c if c not in ["&",["\'"],"\"","?", "<", ">", "#","{", "}","%","~","/","\\","."] else "" for c in name])
                filepath = os.path.join(directory, f'{filename}.json')
            print(f"{filename} and {filepath}")
            if filename and filepath:
                # Ensure the directory exists
                os.makedirs(directory, exist_ok=True)
                
                if not os.path.exists(filepath):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f)
                    logging.info(f"Downloaded and saved {name}")
                else:
                    logging.info(f"Skipped {name} as it already exists")
                return True
        except json.JSONDecodeError as e:
            logging.error(f"JSONDecodeError: {e}")
            logging.error(f"Response content: {response.content}")
    else:
        logging.error(f"Failed to download data from {url}")
        return False

def import_servants(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
            collection_no = data.get("collectionNo")
            if collection_no:
                db['servants'].update_one(
                    {"collectionNo": collection_no},
                    {"$set": data},
                    upsert=True
                )
                logging.info(f"Upserted servant with collectionNo: {collection_no} into 'servants' collection.")
            else:
                logging.warning(f"collectionNo not found in file: {filename}")

def import_quests(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
            quest_name = os.path.splitext(filename)[0]
            db['quests'].update_one(
                {"name": quest_name},
                {"$set": data},
                upsert=True
            )
            logging.info(f"Upserted quest with name: {quest_name} into 'quests' collection.")

def retrieve_quests():
    base_url = 'https://api.atlasacademy.io/nice/JP/quest/{}/1?lang=en'
    quests = {
        # spiral testment lilith
        94097713,94097714, 94097715,
        # dubai sightseeing
        94099810,94099811,94099812,
        #dancing dragon castle
        94098808, 94098809, 94098810,
        # summer revival
        94096909,94096910,94096911,
        # witch on the holy night
        94095709, 94095710,94095711,
        # illusory waxing moon
        94091609,94091610,94091611,
        #kawanakajima
        94090207,94090208,94090209,

    }


    for quest_id in quests:  # Check suffixes 09 to 31
        url = base_url.format(quest_id)

        if download_json(url, './Quest'):
            logging.info(f"Successfully processed quest ID: {quest_id}")
        else:
            logging.error(f"Failed to process quest ID: {quest_id}")
            break
        time.sleep(1)  # Adding a delay of 1 second between requests



def retrieve_servants():
    servant_url = 'https://api.atlasacademy.io/nice/JP/servant/{}?lore=true&expand=true&lang=en'
    current_servant_id = 1
    last_known_servant_id = 426
    while current_servant_id < last_known_servant_id:
        url = servant_url.format(current_servant_id)
        download_json(url, './ServantData')
        current_servant_id += 1
        time.sleep(1)  # Adding a delay of 1 second between requests

def main():
    # retrieve_quests()
    import_quests('./Quest')

    # retrieve_servants()
    # import_servants('./ServantData')

if __name__ == '__main__':
    main()
