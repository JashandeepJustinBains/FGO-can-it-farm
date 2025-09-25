import json
import sys
import os

# Mock database for testing
class MockDB:
    def __init__(self):
        self.servants = self
        with open('example_servant_data/312.json', 'r', encoding='utf-8') as f:
            self._data = {312: json.load(f)}
    
    def find_one(self, query):
        collection_no = query.get('collectionNo')
        return self._data.get(collection_no)

import builtins
builtins.db = MockDB()

from units.Servant import Servant, compute_variant_svt_id

# Create servant with debug
servant = Servant(312, ascension=1)

print(f'Servant 312 at ascension 1:')
print(f'  ascension: {servant.ascension}')
print(f'  variant_svt_id: {servant.variant_svt_id}')
print(f'  Number of NPs: {len(servant.nps.nps)}')

for i, np in enumerate(servant.nps.nps):
    id_val = servant.nps._extract_number(np.get('id', 0))
    print(f'  NP {i}: id={id_val}, card={np.get("card")}, name={np.get("name")}')

# Test variant computation manually
variant_id = compute_variant_svt_id(servant.data, 1)
print(f'\nDirect variant computation for ascension 1: {variant_id}')

variant_id_3 = compute_variant_svt_id(servant.data, 3)
print(f'Direct variant computation for ascension 3: {variant_id_3}')

# Check if there's any ascension data structure
print(f'\nData analysis:')
print(f'  Raw data keys: {list(servant.data.keys())}')
print(f'  Has npSvts: {"npSvts" in servant.data}')
print(f'  Has ascensions: {"ascensions" in servant.data}')

# Test change_ascension
print(f'\n=== ASCENSION CHANGE TEST ===')
print(f'Before change: ascension={servant.ascension}, NP card={servant.nps.nps[-1].get("card")}')
servant.change_ascension(3)
print(f'After change: ascension={servant.ascension}, NP card={servant.nps.nps[-1].get("card")}')

for i, np in enumerate(servant.nps.nps):
    id_val = servant.nps._extract_number(np.get('id', 0))
    print(f'  NP {i}: id={id_val}, card={np.get("card")}, name={np.get("name")}')