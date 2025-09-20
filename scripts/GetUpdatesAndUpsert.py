import requests
import json
import os
import re
import time
try:
    from pymongo import MongoClient
except Exception as e:
    raise ImportError("pymongo is required to run this script. Install with: pip install pymongo") from e
from dotenv import load_dotenv
import logging
import hashlib
from copy import deepcopy
import argparse

# Configure logging: write to file and to console. LOG_LEVEL env can override.
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
try:
    numeric_level = getattr(logging, log_level)
except Exception:
    numeric_level = logging.INFO

formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

# File handler
file_handler = logging.FileHandler('script.log')
file_handler.setFormatter(formatter)
file_handler.setLevel(numeric_level)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(numeric_level)

root_logger = logging.getLogger()
root_logger.setLevel(numeric_level)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

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

# Reuse a single session for connection pooling
session = requests.Session()
session.headers.update({
    'Accept': 'application/json',
    'User-Agent': 'FGO-CanItFarm-Updater/1.0'
})

# Rate limiting: seconds between requests (can be fractional). Default 1s.
RATE_LIMIT_SECONDS = float(os.getenv('RATE_LIMIT_SECONDS', '1'))

def _compute_source_hash(obj):
    """Compute a stable hash for a JSON-serializable object.

    We canonicalize by dumping with sorted keys so equivalent objects map to the same hash.
    """
    try:
        canonical = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    except Exception:
        # Fallback: deep copy and let json handle it
        canonical = json.dumps(json.loads(json.dumps(obj)), sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def _normalize_query_types(query):
    # Try to coerce numeric string values to ints to avoid type-mismatch when querying
    newq = {}
    for k, v in query.items():
        if isinstance(v, str) and v.isdigit():
            try:
                newq[k] = int(v)
            except Exception:
                newq[k] = v
        else:
            newq[k] = v
    return newq


def compare_and_replace(collection, query, data):
    """Replace the document identified by `query` with `data` if changed.

    Behavior:
    - Compute a stable sourceHash for incoming data and store it in the document.
    - If an existing document has the same sourceHash, skip the write.
    - Use replace_one(..., upsert=True) so documents are truly replaced (not merged), keeping _id when matched.
    """
    try:
        # Work on a deep copy so we don't mutate the caller's data
        new_data = deepcopy(data)

        # Remove any _id from incoming data to avoid accidental conflicts on replace/upsert
        new_data.pop('_id', None)

        source_hash = _compute_source_hash(new_data)
        new_data['sourceHash'] = source_hash

        norm_query = _normalize_query_types(query)
        existing_entry = collection.find_one(norm_query)

        if existing_entry and existing_entry.get('sourceHash') == source_hash:
            logging.info(f"No update needed for query: {norm_query} (sourceHash match)")
            return

        # Use replace_one to truly replace the document; upsert will insert when not found
        collection.replace_one(norm_query, new_data, upsert=True)
        if existing_entry:
            logging.info(f"Replaced document for query: {norm_query}")
        else:
            logging.info(f"Inserted new document for query: {norm_query}")
    except Exception as e:
        logging.error(f"Error during replace/upsert: {e}")

def upsert_quest(data):
    quest_id = data.get('id')
    stages = data.get('stages', [])
    
    # Check if stages[0].enemies contains at least one item
    if quest_id and stages and 'enemies' in stages[0] and len(stages[0]['enemies']) > 0:
        # Normalize quest id to int where possible so queries match existing documents
        try:
            qid = int(quest_id)
        except Exception:
            qid = quest_id
        compare_and_replace(quests_collection, {'id': qid}, data)
    else:
        logging.error(f"Quest data missing 'id' field or stages[0].enemies is empty for quest ID: {quest_id}")

def upsert_servant(data):
    collection_no = data.get('collectionNo')
    if collection_no:
        # Ensure numeric collectionNo uses int type to match existing docs
        try:
            cno = int(collection_no)
        except Exception:
            cno = collection_no
        compare_and_replace(servants_collection, {'collectionNo': cno}, data)
    else:
        logging.error("Servant data missing 'collectionNo' field")

def download_and_upsert(url, upsert_function):
    # Configurable retry/backoff
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '4'))
    BACKOFF_BASE = float(os.getenv('BACKOFF_BASE', '1.0'))  # base seconds for exponential backoff
    MAX_BACKOFF = float(os.getenv('MAX_BACKOFF', '60'))

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=30)

            # Handle rate limiting explicitly
            if response.status_code == 429:
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    try:
                        sleep_seconds = float(retry_after)
                    except Exception:
                        sleep_seconds = BACKOFF_BASE * (2 ** attempt)
                else:
                    sleep_seconds = min(MAX_BACKOFF, BACKOFF_BASE * (2 ** attempt))

                # jitter: +/-20%
                jitter = sleep_seconds * 0.2 * (0.5 - os.urandom(1)[0] / 255.0)
                sleep_seconds = max(0.1, sleep_seconds + jitter)
                logging.warning(f"429 received for {url}, sleeping {sleep_seconds:.1f}s before retry")
                time.sleep(sleep_seconds)
                continue

            if response.status_code == 200:
                try:
                    data = response.json()
                    upsert_function(data)
                    return True
                except json.JSONDecodeError as e:
                    logging.error(f"JSONDecodeError: {e}")
                    logging.error(f"Response content: {response.content}")
                    return False

            # Other non-200 responses are treated as transient; log and retry with backoff
            logging.debug(f"Non-200 response {response.status_code} for {url}")

        except requests.RequestException as e:
            logging.warning(f"RequestException for {url}: {e}")

        # Exponential backoff with jitter before next attempt
        backoff = min(MAX_BACKOFF, BACKOFF_BASE * (2 ** attempt))
        # jitter +/- 30%
        jitter = backoff * 0.3 * (0.5 - os.urandom(1)[0] / 255.0)
        sleep_seconds = max(0.1, backoff + jitter)
        logging.debug(f"Sleeping {sleep_seconds:.1f}s before retrying {url} (attempt {attempt + 1}/{MAX_RETRIES})")
        time.sleep(sleep_seconds)

    logging.error(f"Exceeded max retries ({MAX_RETRIES}) for {url}")
    return False

def retrieve_servants():
    servant_url = 'https://api.atlasacademy.io/nice/JP/servant/{}?lore=true&expand=true&lang=en'
    current_servant_id = 1
    # Allow a simple hardcoded mode: if LAST_KNOWN_SERVANT_ID is set in env, just iterate to that id.
    last_known_env = os.getenv('LAST_KNOWN_SERVANT_ID')
    if last_known_env:
        try:
            last_known_servant_id = int(last_known_env)
        except Exception:
            last_known_servant_id = None
    else:
        last_known_servant_id = None

    # Hardcoded non-playable IDs that are known and rarely change. Keep this list short.
    HARDCODED_NON_PLAYABLE_IDS = [
        # Boss or NPC ids to skip (modify as needed). Added by user. 
        # TODO update as new units are identified
        240, 436, 83, 411, 149, 443, 333,
    ]

    # Allow overriding via env: comma-separated ids, e.g. "1001,1002,2003"
    env_skip = os.getenv('NON_PLAYABLE_IDS')
    if env_skip:
        try:
            env_list = [int(x.strip()) for x in env_skip.split(',') if x.strip()]
        except Exception:
            env_list = []
    else:
        env_list = []

    skip_ids = set(HARDCODED_NON_PLAYABLE_IDS) | set(env_list)

    # If last_known_servant_id is provided, use the simple loop (manual mode)
    if last_known_servant_id:
        while current_servant_id <= last_known_servant_id:
            if current_servant_id in skip_ids:
                logging.debug(f"Skipping hardcoded non-playable id {current_servant_id}")
                current_servant_id += 1
                continue

            url = servant_url.format(current_servant_id)
            if not download_and_upsert(url, upsert_servant):
                logging.error(f"Failed to process servant ID: {current_servant_id}")
            current_servant_id += 1
            time.sleep(RATE_LIMIT_SECONDS)  # Adding a configurable delay between requests
        return

    # Otherwise fall back to auto-discovery (conservative defaults)
    CONSECUTIVE_MISS_LIMIT = int(os.getenv('CONSECUTIVE_MISS_LIMIT', '5'))
    # TODO: Consider adding a MAX_CHECKED_ID_LIMIT to cap the number of checked IDs
    MAX_ID_LIMIT = int(os.getenv('MAX_ID_LIMIT', '500'))  # safety cap to avoid runaway loops

    consecutive_misses = 0
    max_checked_id = 0

    while consecutive_misses < CONSECUTIVE_MISS_LIMIT and current_servant_id <= MAX_ID_LIMIT:
        if current_servant_id in skip_ids:
            logging.debug(f"Skipping hardcoded non-playable id {current_servant_id}")
            current_servant_id += 1
            continue

        url = servant_url.format(current_servant_id)

        try:
            resp = session.get(url, timeout=30)
        except requests.RequestException as e:
            logging.error(f"RequestException while checking servant {current_servant_id}: {e}")
            # treat network issues as a miss and continue with backoff logic
            consecutive_misses += 1
            current_servant_id += 1
            time.sleep(RATE_LIMIT_SECONDS)
            continue

        if resp.status_code != 200:
            # Not a valid servant page
            logging.debug(f"Servant {current_servant_id} returned {resp.status_code}")
            consecutive_misses += 1
        else:
            try:
                data = resp.json()
            except Exception:
                logging.error(f"Invalid JSON for servant {current_servant_id}")
                consecutive_misses += 1
                current_servant_id += 1
                time.sleep(RATE_LIMIT_SECONDS)
                continue

            # Heuristic: treat entries without playable indicators as non-playable (bosses / NPCs)
            collection_no = data.get('collectionNo')
            # Some entries use 'mstSkill', others expose 'skills' or 'cards'; treat presence of any as playable
            has_mst_skill = bool(data.get('mstSkill'))
            has_skills = bool(data.get('skills'))
            has_cards = bool(data.get('cards'))

            if not collection_no or not (has_mst_skill or has_skills or has_cards):
                # This appears to be a non-playable or invalid servant (e.g., boss). Count as a miss.
                logging.debug(f"Servant {current_servant_id} not playable or missing collectionNo/playable fields (mstSkill/skills/cards)")
                consecutive_misses += 1
            else:
                # Valid playable servant found — process and reset consecutive misses
                consecutive_misses = 0
                max_checked_id = max(max_checked_id, current_servant_id)
                # Use the existing download_and_upsert pipeline so retries/backoff apply
                if not download_and_upsert(url, upsert_servant):
                    logging.error(f"Failed to process servant ID: {current_servant_id}")

        current_servant_id += 1
        time.sleep(RATE_LIMIT_SECONDS)

    logging.info(f"Finished servant discovery. Last checked id: {current_servant_id-1}, max playable id seen: {max_checked_id}")

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
                    if recommend_lv in ['90', '90+', '90++', '90★', '90★★', '90★★★', '100★★', '100★★★'] and consume == 40 and after_clear == 'repeatLast':
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
        time.sleep(RATE_LIMIT_SECONDS)  # Adding a configurable delay between requests

def main(run_quests: bool = True, run_servants: bool = True):
    """Run quests and/or servants update phases.

    run_quests: if True, fetch and upsert quest data.
    run_servants: if True, fetch and upsert servant data.
    """
    logging.info(f"Starting main with run_quests={run_quests}, run_servants={run_servants}")

    war_ids = [
        400,401,402,403,404,405,8382, 8383, 8384, 8385, 
        9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008, 9009, 9010,
        9013, 9014, 9015, 9018, 9021, 9022, 9029, 9031, 9032, 9033, 9035,
        9040, 9046, 9048, 9049, 9050, 9051, 9052, 9053, 9056, 9057, 9058,
        9068, 9069, 9071, 9072, 9073, 9074, 9075, 9076, 9077, 9080, 9087, 9088, 9091,
        9097, 9098, 9099, 
        9101, 9107, 9109, 9111, 9112, 9113, 9119, 9120, 9124, 9125, 9127, 9128, 
        9130, 9131, 9133, 9134, 9135, 9136, 9143, 9144, 9145, 9151, 9152, 9160, 
        9163, 9164, 9166, 9168, 9169, 9170, 9171, 9172, 9173, 9174, 9175, 9182, 
        9184, 9185, 9188, 9189, 9190, 9999, 11000, 12000, 13000, 14000,
        # 2025 events?
        8386, 8387, 8388, 8389, 8390, 8391, 8392, 8393, 8394, 
        # unbeast uolga summer
        9193,
        # grand duels some are not in yet
        8395, 8396, 8397, 8398, 8399, 8400, 8401, 8402, 8403, 8404, 8405, 8406, 8407,
    ]

    all_quest_ids = []
    if run_quests:
        for war_id in war_ids:
            quest_ids = get_quest_ids_from_api(war_id)
            all_quest_ids.extend(quest_ids)

        logging.info(f"Found {len(all_quest_ids)} quest ids to process")
        get_quest_details_and_upsert(all_quest_ids)

    if run_servants:
        retrieve_servants()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download and upsert quest and servant data from Atlas Academy')
    parser.add_argument('-s', '--servants', action='store_true', help='Only run servant updates')
    parser.add_argument('-q', '--quests', action='store_true', help='Only run quest updates')
    args = parser.parse_args()

    # Determine mode: if neither flag provided, run both. If one provided, respect it.
    if args.servants and args.quests:
        run_quests = True
        run_servants = True
    elif args.servants:
        run_quests = False
        run_servants = True
    elif args.quests:
        run_quests = True
        run_servants = False
    else:
        run_quests = True
        run_servants = True

    try:
        main(run_quests=run_quests, run_servants=run_servants)
    except KeyboardInterrupt:
        logging.info("Interrupted by user (KeyboardInterrupt). Shutting down gracefully.")
    except Exception as e:
        logging.exception(f"Unhandled exception in main: {e}")
    finally:
        try:
            session.close()
        except Exception:
            pass
        try:
            client.close()
        except Exception:
            pass
