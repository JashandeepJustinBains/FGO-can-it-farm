#!/usr/bin/env python3
"""Debug servant ID information."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from units.Servant import Servant

def debug_servant_ids():
    """Check servant ID values."""
    
    mash = Servant(1, ascension=1)
    print(f"Servant constructed:")
    print(f"  mash.id: {mash.id}")
    print(f"  mash.variant_svt_id: {mash.variant_svt_id}")
    print(f"  Top-level svtId in data: {mash.data.get('id')}")
    print(f"  Top-level svtId: {mash.data.get('svtId')}")
    
    print(f"\nAfter Ortenaus costume change:")
    mash.change_ascension(1, costume_svt_id=800101)
    print(f"  mash.id: {mash.id}")
    print(f"  mash.variant_svt_id: {mash.variant_svt_id}")

if __name__ == '__main__':
    debug_servant_ids()