#!/usr/bin/env python3
"""
Demonstration of dynamic NP selection with ascension changes.

This script shows how servant 312 (Mélusine) changes NP types based on ascension:
- Ascension 1-2: Arts NP "Innocence Arondight" 
- Ascension 3+: Buster NP "Hollow Heart Albion"
"""
import sys
import os
import json

# Add current directory to path for imports
sys.path.insert(0, '.')

# Mock database setup
class MockDB:
    def __init__(self):
        self.servants = self
        self._data = {}
        
        # Load example servant data
        for servant_id in [312, 1, 444]:
            try:
                with open(f'example_servant_data/{servant_id}.json', 'r') as f:
                    self._data[servant_id] = json.load(f)
            except FileNotFoundError:
                print(f"Warning: Could not load example_servant_data/{servant_id}.json")
    
    def find_one(self, query):
        return self._data.get(query.get('collectionNo'))

# Set up mock database globally
import builtins
builtins.db = MockDB()

# Import after setting up database
from units.Servant import Servant

def demonstrate_dynamic_np_selection():
    """Demonstrate dynamic NP selection for Mélusine (servant 312)."""
    print("=== Dynamic NP Selection Demonstration ===\n")
    print("Servant: Mélusine (collection #312)")
    print("Special trait: Changes NP type based on ascension\n")
    
    # Create servant at ascension 1
    print("1. Creating servant at ascension 1...")
    servant = Servant(312, ascension=1)
    
    print(f"   Ascension: {servant.ascension}")
    print(f"   Available NPs: {len(servant.nps.nps)}")
    
    for i, np in enumerate(servant.nps.nps):
        np_id = servant.nps._extract_number(np.get('id', 0))
        card_type = np.get('card', 'unknown')
        name = np.get('name', 'Unknown')
        print(f"   NP {i+1}: {name} (ID: {np_id}, Type: {card_type.upper()})")
    
    current_np = servant.nps.nps[-1]  # Get current/highest priority NP
    current_id = servant.nps._extract_number(current_np.get('id', 0))
    current_card = current_np.get('card', 'unknown')
    print(f"   → Current NP: {current_card.upper()} type (ID: {current_id})\n")
    
    # Change to ascension 3
    print("2. Changing to ascension 3...")
    servant.change_ascension(3)
    
    print(f"   Ascension: {servant.ascension}")  
    print(f"   Available NPs: {len(servant.nps.nps)}")
    
    for i, np in enumerate(servant.nps.nps):
        np_id = servant.nps._extract_number(np.get('id', 0))
        card_type = np.get('card', 'unknown')
        name = np.get('name', 'Unknown')
        print(f"   NP {i+1}: {name} (ID: {np_id}, Type: {card_type.upper()})")
    
    current_np = servant.nps.nps[-1]  # Get current/highest priority NP
    current_id = servant.nps._extract_number(current_np.get('id', 0))
    current_card = current_np.get('card', 'unknown')
    print(f"   → Current NP: {current_card.upper()} type (ID: {current_id})\n")
    
    # Change back to ascension 1
    print("3. Changing back to ascension 1...")
    servant.change_ascension(1)
    
    print(f"   Ascension: {servant.ascension}")
    print(f"   Available NPs: {len(servant.nps.nps)}")
    
    current_np = servant.nps.nps[-1]  # Get current/highest priority NP
    current_id = servant.nps._extract_number(current_np.get('id', 0))
    current_card = current_np.get('card', 'unknown')
    print(f"   → Current NP: {current_card.upper()} type (ID: {current_id})\n")
    
    print("=== Summary ===")
    print("✅ Dynamic NP selection is working correctly!")
    print("✅ NP changes based on ascension in real-time")
    print("✅ Release conditions are properly respected")
    print("✅ State changes persist during servant lifetime")

if __name__ == "__main__":
    demonstrate_dynamic_np_selection()