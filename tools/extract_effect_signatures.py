#!/usr/bin/env python3
"""
FGO Effect Signature Extractor
=====================================

Usage:
    python tools/extract_effect_signatures.py

Environment Variables:
    None required - uses embedded connection string for read-only access

Required pip packages:
    pymongo

Description:
    This script connects to the FGO MongoDB read-replica and extracts unique effect signatures
    from skills, noble_phantasms, and related collections. It produces a local JSON file mapping
    each signature to suggested trigger classifications and canonical action hints.

    The script implements conservative heuristics to classify trigger types as:
    - "immediate": Effects that apply immediately when activated
    - "on-hit": Effects triggered when attacking/being attacked
    - "end-turn": Effects that trigger at the end of a turn
    - "counter": Effects with limited usage counts
    - "unknown": Ambiguous or unclassified effects

Next Steps for Integration:
    1. Review outputs/effect_signatures.json for accuracy of classifications
    2. Integrate signature mappings into the skill_manager.py trigger registry
    3. Use confidence scores to prioritize which signatures to implement first
    4. Extend heuristics based on additional game knowledge
    5. Create unit tests for new trigger classifications
"""

import logging
import json
import csv
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict
import pymongo
from pymongo import MongoClient

# Configuration Constants
MAX_DOCS_PER_COLLECTION = 5000  # Limit per-collection sampled docs
MAX_SAMPLES_PER_SIGNATURE = 20  # Max examples to store per signature
SOCKET_TIMEOUT_MS = 30000  # 30 second socket timeout

# MongoDB connection string (read-only access)
MONGO_URI = "mongodb+srv://githubcopilot_readonly_access:SIqxD69lCXmbH9qo@fgocombatsim.e9ih5.mongodb.net/?retryWrites=true&w=majority&appName=FGOCombatSim"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EffectSignatureExtractor:
    """Extracts and classifies effect signatures from FGO game data."""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.signatures = defaultdict(list)  # signature_hash -> list of samples
        self.extraction_log = []
        
    def connect_database(self) -> bool:
        """Connect to MongoDB with read-only access."""
        try:
            # Connect with socket timeout for safety
            self.client = MongoClient(
                MONGO_URI,
                socketTimeoutMS=SOCKET_TIMEOUT_MS,
                serverSelectionTimeoutMS=SOCKET_TIMEOUT_MS
            )
            
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client['FGOCanItFarmDatabase']
            logger.info("Successfully connected to MongoDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def get_relevant_collections(self) -> List[str]:
        """Identify collections that likely contain effect data."""
        try:
            all_collections = self.db.list_collection_names()
            logger.info(f"Found {len(all_collections)} total collections")
            
            # Look for collections containing skills, NPs, or effects
            relevant_keywords = ['skill', 'np', 'noble', 'phantasm', 'effect', 'servant']
            relevant_collections = []
            
            for collection_name in all_collections:
                lower_name = collection_name.lower()
                if any(keyword in lower_name for keyword in relevant_keywords):
                    relevant_collections.append(collection_name)
            
            # Always include standard collections if they exist
            standard_collections = ['skills', 'noble_phantasms', 'servants', 'effects', 'nps']
            for std_name in standard_collections:
                if std_name in all_collections and std_name not in relevant_collections:
                    relevant_collections.append(std_name)
            
            # If no relevant collections found, try common FGO API collection names
            if not relevant_collections:
                fallback_collections = ['servants', 'mysticcodes', 'craftessences']
                for fallback in fallback_collections:
                    if fallback in all_collections:
                        relevant_collections.append(fallback)
                        logger.warning(f"Using fallback collection: {fallback}")
            
            logger.info(f"Identified relevant collections: {relevant_collections}")
            return relevant_collections
            
        except Exception as e:
            logger.error(f"Failed to get collections: {e}")
            return []
    
    def extract_function_signature(self, func_data: Dict[str, Any], collection_name: str, doc_id: str) -> Dict[str, Any]:
        """Extract canonical signature from a function/effect document."""
        signature = {
            'funcType': func_data.get('funcType'),
            'funcTargetType': func_data.get('funcTargetType'),
            'has_svals': bool(func_data.get('svals')),
            'has_buffs': bool(func_data.get('buffs')),
            'has_functvals': bool(func_data.get('functvals')),
            'has_tvals': False,
            'has_fieldReq': bool(func_data.get('fieldReq')),
            'has_condTarget': bool(func_data.get('condTarget')),
            'triggered_func_position': func_data.get('TriggeredFuncPosition'),
        }
        
        # Analyze svals structure
        svals = func_data.get('svals', {})
        if svals:
            if isinstance(svals, list) and svals:
                svals = svals[0] if svals[0] else {}
            signature['svals_keys'] = sorted(svals.keys()) if isinstance(svals, dict) else []
            signature['has_count'] = 'Count' in svals if isinstance(svals, dict) else False
            signature['has_value'] = 'Value' in svals if isinstance(svals, dict) else False
            signature['has_value2'] = 'Value2' in svals if isinstance(svals, dict) else False
            signature['has_turn'] = 'Turn' in svals if isinstance(svals, dict) else False
        else:
            signature['svals_keys'] = []
            signature['has_count'] = False
            signature['has_value'] = False
            signature['has_value2'] = False
            signature['has_turn'] = False
        
        # Analyze buffs structure
        buffs = func_data.get('buffs', [])
        if buffs:
            # Get structure from first buff
            first_buff = buffs[0] if buffs else {}
            signature['buff_keys'] = sorted(first_buff.keys())
            signature['buff_name'] = first_buff.get('name')
            signature['buff_type'] = first_buff.get('type')
            
            # Check for tvals in buffs
            buff_tvals = first_buff.get('tvals', [])
            signature['has_tvals'] = bool(buff_tvals)
            if buff_tvals:
                # Extract tval IDs for card type detection
                tval_ids = [tval.get('id') for tval in buff_tvals if isinstance(tval, dict)]
                signature['tval_ids'] = sorted([tid for tid in tval_ids if tid is not None])
        else:
            signature['buff_keys'] = []
            signature['buff_name'] = None
            signature['buff_type'] = None
            signature['tval_ids'] = []
        
        return signature
    
    def create_signature_hash(self, signature: Dict[str, Any]) -> str:
        """Create a deterministic hash for the signature shape."""
        # Use only the structural elements for hashing
        hash_data = {
            'funcType': signature.get('funcType'),
            'funcTargetType': signature.get('funcTargetType'),
            'svals_keys': signature.get('svals_keys', []),
            'buff_keys': signature.get('buff_keys', []),
            'has_functvals': signature.get('has_functvals', False),
            'has_tvals': signature.get('has_tvals', False),
            'triggered_func_position': signature.get('triggered_func_position'),
        }
        
        # Create stable JSON string and hash it
        stable_json = json.dumps(hash_data, sort_keys=True)
        return hashlib.md5(stable_json.encode()).hexdigest()
    
    def classify_trigger_type(self, signature: Dict[str, Any], samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply conservative heuristics to classify trigger type and suggest actions."""
        
        func_type = signature.get('funcType', '').lower()
        has_count = signature.get('has_count', False)
        triggered_pos = signature.get('triggered_func_position')
        svals_keys = signature.get('svals_keys', [])
        buff_name = signature.get('buff_name', '').lower() if signature.get('buff_name') else ''
        tval_ids = signature.get('tval_ids', [])
        
        heuristic = {
            'trigger_type': 'unknown',
            'confidence': 0.25,
            'suggested_action': {'action': 'unknown', 'params': {}},
            'notes': 'No clear classification pattern detected'
        }
        
        # Priority-based classification (highest priority first)
        classified = False
        
        # Conservative heuristic 1: Count + TriggeredFuncPosition indicates on-hit
        if has_count and triggered_pos == 2 and not classified:
            heuristic.update({
                'trigger_type': 'on-hit',
                'confidence': 0.9,
                'suggested_action': {'action': 'on_hit_effect', 'params': {'count_field': 'svals.Count'}},
                'notes': 'Count > 0 with TriggeredFuncPosition = 2 indicates on-hit trigger'
            })
            classified = True
        
        # Conservative heuristic 2: TriggeredFuncPosition = 3 indicates end-turn
        elif triggered_pos == 3 and not classified:
            heuristic.update({
                'trigger_type': 'end-turn',
                'confidence': 0.8,
                'suggested_action': {'action': 'end_turn_effect', 'params': {}},
                'notes': 'TriggeredFuncPosition = 3 indicates end-turn trigger'
            })
            classified = True
        
        # Conservative heuristic 3: NP gain detection
        elif ('np' in func_type or 'np' in buff_name) and signature.get('has_value') and not classified:
            heuristic.update({
                'trigger_type': 'immediate',
                'confidence': 0.8,
                'suggested_action': {
                    'action': 'grant_np_pct',
                    'params': {'pct_field': 'svals.Value' if 'Value' in svals_keys else 'svals.Value2'}
                },
                'notes': 'NP-related function with numeric value suggests NP gain'
            })
            classified = True
        
        # Conservative heuristic 4: Buff application (lower priority than specific triggers)
        elif (func_type == 'addstate' or func_type == 'addstateshort') and not classified:
            # Check if it might be on-hit based on Count presence
            if has_count and not triggered_pos:
                heuristic.update({
                    'trigger_type': 'counter',
                    'confidence': 0.6,
                    'suggested_action': {'action': 'add_counter', 'params': {'count_field': 'svals.Count'}},
                    'notes': 'addState with Count but no trigger position suggests counter-based effect'
                })
            else:
                heuristic.update({
                    'trigger_type': 'immediate',
                    'confidence': 0.7,
                    'suggested_action': {'action': 'add_buff', 'params': {'buff_type': signature.get('buff_name')}},
                    'notes': 'addState function suggests immediate buff application'
                })
            classified = True
        
        # Add card type restrictions if present (supplements any classification)
        if tval_ids:
            card_restrictions = {}
            for tval_id in tval_ids:
                if tval_id == 4001:
                    card_restrictions['arts'] = True
                elif tval_id == 4002:
                    card_restrictions['buster'] = True
                elif tval_id == 4003:
                    card_restrictions['quick'] = True
            
            if card_restrictions:
                if 'params' not in heuristic['suggested_action']:
                    heuristic['suggested_action']['params'] = {}
                heuristic['suggested_action']['params']['card_restriction'] = card_restrictions
                heuristic['notes'] += f'; Card restrictions: {list(card_restrictions.keys())}'
        
        # Mark ambiguous cases
        ambiguous_fields = []
        if signature.get('has_count') and not triggered_pos and not classified:
            ambiguous_fields.append('Count without trigger position')
        if signature.get('buff_name') and signature.get('has_functvals'):
            ambiguous_fields.append('Both buff and functvals present')
        
        if ambiguous_fields:
            if not classified:
                heuristic['notes'] = f"Ambiguous: {'; '.join(ambiguous_fields)}"
            else:
                heuristic['notes'] += f"; Ambiguous: {'; '.join(ambiguous_fields)}"
            heuristic['confidence'] = min(heuristic['confidence'], 0.5)
        
        return heuristic
    
    def process_collection(self, collection_name: str) -> int:
        """Process a single collection and extract effect signatures."""
        try:
            collection = self.db[collection_name]
            
            # Get sample documents with streaming
            cursor = collection.find({}).limit(MAX_DOCS_PER_COLLECTION)
            doc_count = 0
            functions_found = 0
            
            logger.info(f"Processing collection: {collection_name}")
            
            for doc in cursor:
                doc_count += 1
                doc_id = str(doc.get('_id', doc_count))
                
                try:
                    # Look for functions in various locations
                    functions = []
                    
                    # Direct functions array
                    if 'functions' in doc and isinstance(doc['functions'], list):
                        functions.extend(doc['functions'])
                    
                    # Skills array with functions
                    if 'skills' in doc and isinstance(doc['skills'], list):
                        for skill in doc['skills']:
                            if isinstance(skill, dict) and 'functions' in skill and isinstance(skill['functions'], list):
                                functions.extend(skill['functions'])
                    
                    # Noble phantasms with functions
                    if 'noble_phantasms' in doc or 'nps' in doc:
                        nps = doc.get('noble_phantasms', doc.get('nps', []))
                        if isinstance(nps, list):
                            for np in nps:
                                if isinstance(np, dict) and 'functions' in np and isinstance(np['functions'], list):
                                    functions.extend(np['functions'])
                    
                    # NoblePhantasm field (alternative naming)
                    if 'noblePhantasms' in doc and isinstance(doc['noblePhantasms'], list):
                        for np in doc['noblePhantasms']:
                            if isinstance(np, dict) and 'functions' in np and isinstance(np['functions'], list):
                                functions.extend(np['functions'])
                    
                    # Process each function
                    for i, func in enumerate(functions):
                        if not isinstance(func, dict):
                            continue
                        
                        try:
                            signature = self.extract_function_signature(func, collection_name, doc_id)
                            signature_hash = self.create_signature_hash(signature)
                            
                            # Store sample with metadata
                            sample = {
                                'document_id': doc_id,
                                'collection_name': collection_name,
                                'function_index': i,
                                'raw_function': func,
                                'signature_shape': signature
                            }
                            
                            self.signatures[signature_hash].append(sample)
                            functions_found += 1
                            
                        except Exception as func_error:
                            logger.warning(f"Error processing function {i} in doc {doc_id}: {func_error}")
                            continue
                
                except Exception as doc_error:
                    logger.warning(f"Error processing document {doc_id} in {collection_name}: {doc_error}")
                    continue
            
            # Log the exact query used
            self.extraction_log.append({
                'collection': collection_name,
                'query': '{}',  # Empty query (find all)
                'limit': MAX_DOCS_PER_COLLECTION,
                'documents_processed': doc_count,
                'functions_extracted': functions_found,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Processed {doc_count} documents from {collection_name}, extracted {functions_found} functions")
            return doc_count
            
        except Exception as e:
            logger.error(f"Error processing collection {collection_name}: {e}")
            self.extraction_log.append({
                'collection': collection_name,
                'query': '{}',
                'limit': MAX_DOCS_PER_COLLECTION,
                'documents_processed': 0,
                'functions_extracted': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return 0
    
    def generate_output(self) -> Dict[str, Any]:
        """Generate the final output with classifications."""
        output = {}
        
        logger.info(f"Generating output for {len(self.signatures)} unique signatures")
        
        for signature_hash, samples in self.signatures.items():
            if not samples:
                continue
            
            # Limit samples per signature
            limited_samples = samples[:MAX_SAMPLES_PER_SIGNATURE]
            
            # Get collections this signature appears in
            collections = list(set(sample['collection_name'] for sample in samples))
            
            # Use first sample's signature for classification
            signature_shape = samples[0]['signature_shape']
            
            # Apply classification heuristics
            heuristic = self.classify_trigger_type(signature_shape, limited_samples)
            
            output[signature_hash] = {
                'signature_hash': signature_hash,
                'collections': sorted(collections),
                'signature_shape': signature_shape,
                'sample_count': len(samples),
                'samples': [sample['raw_function'] for sample in limited_samples],
                'heuristic': heuristic
            }
        
        return output
    
    def save_outputs(self, output_data: Dict[str, Any]):
        """Save results to JSON, CSV, and log files."""
        
        # Save JSON output
        json_path = 'outputs/effect_signatures.json'
        with open(json_path, 'w') as f:
            json.dump(output_data, f, indent=2, sort_keys=True)
        logger.info(f"Saved JSON output to {json_path}")
        
        # Save CSV output
        csv_path = 'outputs/effect_signatures.csv'
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'signature_hash', 'collections', 'sample_count',
                'trigger_type', 'confidence', 'suggested_action', 'notes'
            ])
            
            for signature_hash, data in output_data.items():
                heuristic = data['heuristic']
                writer.writerow([
                    signature_hash,
                    '; '.join(data['collections']),
                    data['sample_count'],
                    heuristic['trigger_type'],
                    heuristic['confidence'],
                    json.dumps(heuristic['suggested_action']),
                    heuristic['notes']
                ])
        
        logger.info(f"Saved CSV output to {csv_path}")
        
        # Save extraction log
        log_path = 'outputs/extraction_log.txt'
        with open(log_path, 'w') as f:
            f.write(f"FGO Effect Signature Extraction Log\n")
            f.write(f"Run timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Total unique signatures: {len(output_data)}\n\n")
            
            f.write("Collection Processing Summary:\n")
            total_docs = 0
            total_functions = 0
            for log_entry in self.extraction_log:
                docs = log_entry['documents_processed']
                funcs = log_entry.get('functions_extracted', 0)
                total_docs += docs
                total_functions += funcs
                
                if 'error' in log_entry:
                    f.write(f"  {log_entry['collection']}: ERROR - {log_entry['error']}\n")
                else:
                    f.write(f"  {log_entry['collection']}: {docs} documents, {funcs} functions\n")
            
            f.write(f"\nTotal documents scanned: {total_docs}\n")
            f.write(f"Total functions extracted: {total_functions}\n\n")
            
            f.write("Exact queries executed:\n")
            for log_entry in self.extraction_log:
                f.write(f"  Collection: {log_entry['collection']}\n")
                f.write(f"  Query: {log_entry['query']}\n")
                f.write(f"  Limit: {log_entry['limit']}\n")
                f.write(f"  Timestamp: {log_entry['timestamp']}\n")
                if 'error' in log_entry:
                    f.write(f"  Error: {log_entry['error']}\n")
                f.write("\n")
        
        logger.info(f"Saved extraction log to {log_path}")
    
    def run(self):
        """Main execution method."""
        logger.info("Starting FGO Effect Signature Extraction")
        
        # Connect to database
        if not self.connect_database():
            logger.error("Database connection failed. Exiting.")
            return
        
        try:
            # Get relevant collections
            collections = self.get_relevant_collections()
            if not collections:
                logger.error("No relevant collections found. Exiting.")
                return
            
            # Process each collection
            total_docs = 0
            for collection_name in collections:
                docs_processed = self.process_collection(collection_name)
                total_docs += docs_processed
            
            logger.info(f"Processed {total_docs} total documents from {len(collections)} collections")
            logger.info(f"Found {len(self.signatures)} unique effect signatures")
            
            # Generate and save output
            output_data = self.generate_output()
            self.save_outputs(output_data)
            
            # Print summary
            print(f"\nExtraction Complete!")
            print(f"Documents scanned: {total_docs}")
            print(f"Unique signatures found: {len(output_data)}")
            print(f"Collections processed: {len(collections)}")
            
            # Print top 10 signatures by sample count
            sorted_signatures = sorted(
                output_data.items(),
                key=lambda x: x[1]['sample_count'],
                reverse=True
            )
            
            print(f"\nTop 10 signatures by sample count:")
            for i, (sig_hash, data) in enumerate(sorted_signatures[:10], 1):
                print(f"  {i}. {sig_hash[:8]}... ({data['sample_count']} samples)")
            
        finally:
            if self.client:
                self.client.close()
                logger.info("Database connection closed")


def main():
    """Entry point for the script."""
    extractor = EffectSignatureExtractor()
    extractor.run()


if __name__ == '__main__':
    main()