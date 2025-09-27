import argparse
import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from Driver import Driver
import logging

# Configure logging
logging.basicConfig(filename='./outputs/traverse_api_input.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variable
mongo_uri = os.getenv('MONGO_URI_READ')
if not mongo_uri:
    raise ValueError("No MONGO_URI_READ environment variable set")

# Connect to MongoDB
client = MongoClient(mongo_uri)
db = client['FGOCanItFarmDatabase']

def traverse_api_input(servant_init_dicts, mc_id, quest_id, commands):
    servant_init_dicts = [s for s in servant_init_dicts if s.get("collectionNo")]
    driver = Driver(servant_init_dicts, quest_id, mc_id)
    driver.reset_state()

    for command in commands:
        result = driver.execute_token(command)
        if result is False:
            if command == '#':
                # Check if any enemies are still alive
                enemies = driver.game_manager.get_enemies()
                if any(enemy.get_hp() > 0 for enemy in enemies):
                    logging.error(f"End turn failed: Enemies are still alive. Command: {command}")
                    print("End turn failed: Enemies are still alive.")
                    break
                else:
                    logging.info(f"All waves have been completed. Command: {command}")
                    print("All waves have been completed.")
                    break
            else:
                logging.error(f"Failed to execute command: {command}")
                break
    logging.info("Commands executed successfully.")
    return driver  # Always return driver for logging and testing purposes