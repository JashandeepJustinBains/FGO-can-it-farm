import argparse
import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from Driver import Driver
import logging

# Module logger (Driver.py will configure handlers)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variable
mongo_uri = os.getenv('MONGO_URI_READ')
if not mongo_uri:
    raise ValueError("No MONGO_URI_READ environment variable set")

# Connect to MongoDB
client = MongoClient(mongo_uri)
db = client['FGOCanItFarmDatabase']
globals()['db'] = db

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
    # If we completed iterating through commands without breaking early,
    # and all enemies are defeated, mark the driver run as successful so
    # callers/tests that check truthiness (driver == True) will pass.
    enemies = driver.game_manager.get_enemies()
    if not any(enemy.get_hp() > 0 for enemy in enemies):
        driver.run_succeeded = True
        logging.info("Commands executed successfully and all enemies defeated.")
    else:
        logging.warning("Commands executed but enemies remain alive.")

    # Persist a compact per-token trace for replay/visualization by web
    try:
        os.makedirs('outputs', exist_ok=True)
        trace_path = os.path.join('outputs', 'step_log.json')
        with open(trace_path, 'w', encoding='utf-8') as fh:
            json.dump(driver.all_tokens, fh, ensure_ascii=False)
        logging.info(f"Wrote step trace to {trace_path}")
    except Exception:
        logging.exception('Failed to write step trace')

    return driver  # Always return driver for logging and testing purposes