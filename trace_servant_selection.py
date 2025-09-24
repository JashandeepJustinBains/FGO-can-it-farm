#!/usr/bin/env python3
"""
Trace FGO servant skill/NP selection logic for specific servants and ascensions.
"""

import json
import sys
import os

# Add the repo path to sys.path to import modules
sys.path.append('/home/runner/work/FGO-can-it-farm/FGO-can-it-farm')

def _extract_number(value):
    """Extract number handling MongoDB format."""
    if isinstance(value, dict) and '$numberInt' in value:
        return int(value['$numberInt'])
    return int(value) if value is not None else 0

def load_servant_data(servant_id):
    """Load servant data from JSON file."""
    try:
        with open(f'/home/runner/work/FGO-can-it-farm/FGO-can-it-farm/example_servant_data/{servant_id}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Could not find servant data for ID {servant_id}")
        return None

def compute_variant_svt_id(servant_json, ascension, costume_svt_id=None):
    """
    Compute the selected variant svtId for the current ascension/costume.
    Mimics the logic from units/Servant.py
    """
    
    # Step 1: Check if user-supplied costume_svt_id is given
    if costume_svt_id is not None:
        return _extract_number(costume_svt_id)
    
    # Step 2: Heuristic for large ascension values (treat as variant IDs)
    try:
        asc_int = int(ascension)
        if asc_int >= 100000:
            # Check if this exists in costume data
            asc_add = servant_json.get('ascensionAdd', {}) or {}
            if isinstance(asc_add, dict):
                ind = asc_add.get('individuality', {}) or {}
                attr = asc_add.get('attribute', {}) or {}
                costume_keys = set()
                costume_keys.update((ind.get('costume') or {}).keys())
                costume_keys.update((attr.get('costume') or {}).keys())
                
                if str(ascension) in costume_keys:
                    return asc_int
    except Exception:
        pass
    
    # Step 3: Extract top-level svtId
    top_level_svt_id = _extract_number(servant_json.get('id', servant_json.get('svtId', 0)))
    
    # Step 4: Try npSvts.imageIndex mapping
    np_svts = servant_json.get('npSvts', [])
    if np_svts:
        # Build imageIndex → svtId mapping
        image_index_mapping = {}
        for np_entry in np_svts:
            image_index = _extract_number(np_entry.get('imageIndex', 0))
            svt_id = _extract_number(np_entry.get('svtId', top_level_svt_id))
            priority = _extract_number(np_entry.get('priority', 0))
            
            if image_index not in image_index_mapping:
                image_index_mapping[image_index] = {'svtId': svt_id, 'priority': priority}
            else:
                # Use highest priority, or highest svtId as tie-breaker
                current = image_index_mapping[image_index]
                if priority > current['priority'] or (priority == current['priority'] and svt_id > current['svtId']):
                    image_index_mapping[image_index] = {'svtId': svt_id, 'priority': priority}
        
        # Map ascension to imageIndex (typically 0-based ascension maps to 0-based imageIndex)
        try:
            ascension_image_index = int(ascension) - 1  # Convert 1-based to 0-based
            if ascension_image_index in image_index_mapping:
                return image_index_mapping[ascension_image_index]['svtId']
        except Exception:
            pass
    
    # Step 5: Try skillSvts releaseConditions
    skill_svts = servant_json.get('skillSvts', [])
    if skill_svts:
        for skill_entry in skill_svts:
            release_conditions = skill_entry.get('releaseConditions', [])
            for condition in release_conditions:
                if condition.get('condType') == 'equipWithTargetCostume':
                    cond_target_id = _extract_number(condition.get('condTargetId', 0))
                    # This maps costume/ascension to svtId
                    try:
                        if cond_target_id and (cond_target_id == int(ascension) or cond_target_id == int(ascension) + 10):
                            return _extract_number(skill_entry.get('svtId', top_level_svt_id))
                    except Exception:
                        pass
    
    # Step 6: Fallback to top-level svtId
    return top_level_svt_id

def select_ascension_data(servant_json, ascension):
    """
    Select ascension-specific data from servant JSON.
    Mimics the logic from units/Servant.py
    """
    result = {}
    
    # Check for explicit ascensions/forms array first
    ascensions_data = servant_json.get('ascensions', servant_json.get('forms', []))
    if ascensions_data:
        # Look for matching ascension
        selected_ascension = None
        for asc_data in ascensions_data:
            asc_index = _extract_number(asc_data.get('ascension', asc_data.get('ascensionIndex', asc_data.get('index', 0))))
            if asc_index == ascension:
                selected_ascension = asc_data
                break
        
        if selected_ascension:
            # Extract data from the ascension object
            result['skills'] = selected_ascension.get('skills', [])
            result['noblePhantasms'] = selected_ascension.get('noblePhantasms', [])
            result['passives'] = selected_ascension.get('passives', [])
            result['transforms'] = selected_ascension.get('transforms', [])
            return result
        else:
            # Requested ascension not found, use highest available
            if ascensions_data:
                highest_asc = max(ascensions_data, key=lambda x: _extract_number(x.get('ascension', x.get('ascensionIndex', x.get('index', 0)))))
                highest_level = _extract_number(highest_asc.get('ascension', highest_asc.get('ascensionIndex', highest_asc.get('index', 0))))
                result['skills'] = highest_asc.get('skills', [])
                result['noblePhantasms'] = highest_asc.get('noblePhantasms', [])
                result['passives'] = highest_asc.get('passives', [])
                result['transforms'] = highest_asc.get('transforms', [])
                return result
    
    # Check for list-of-lists format (per-ascension lists)
    skills_data = servant_json.get('skills', [])
    nps_data = servant_json.get('noblePhantasms', [])
    
    # Detect if skills/nps are list-of-lists
    is_skills_list_of_lists = (skills_data and 
                              isinstance(skills_data, list) and 
                              len(skills_data) > 0 and 
                              isinstance(skills_data[0], list))
    
    is_nps_list_of_lists = (nps_data and 
                           isinstance(nps_data, list) and 
                           len(nps_data) > 0 and 
                           isinstance(nps_data[0], list))
    
    if is_skills_list_of_lists or is_nps_list_of_lists:
        # Handle list-of-lists format
        if is_skills_list_of_lists:
            if ascension <= len(skills_data):
                result['skills'] = skills_data[ascension - 1]
            else:
                # Use highest available
                highest_idx = len(skills_data) - 1
                result['skills'] = skills_data[highest_idx]
        else:
            result['skills'] = skills_data
            
        if is_nps_list_of_lists:
            if ascension <= len(nps_data):
                result['noblePhantasms'] = nps_data[ascension - 1]
            else:
                # Use highest available
                highest_idx = len(nps_data) - 1
                result['noblePhantasms'] = nps_data[highest_idx]
        else:
            result['noblePhantasms'] = nps_data
            
        # For list-of-lists, other fields are typically ascension-independent
        result['passives'] = servant_json.get('passives', servant_json.get('classPassive', []))
        result['transforms'] = servant_json.get('transforms', [])
        return result
    
    # Legacy single-list format (ascension-independent)
    result['skills'] = skills_data
    result['noblePhantasms'] = nps_data
    result['passives'] = servant_json.get('passives', servant_json.get('classPassive', []))
    result['transforms'] = servant_json.get('transforms', [])
    
    return result

def trace_skill_selection(servant_json, variant_svt_id):
    """
    Trace skill selection logic using skillSvts data.
    Mimics the logic from units/skills.py
    """
    skills_data = servant_json.get('skills', [])
    skill_svts = servant_json.get('skillSvts', [])
    
    # Check if we have skillSvts format
    if skill_svts:
        # Use skillSvts format with variant-aware selection
        skills = {1: [], 2: [], 3: []}
        
        # Group skills by number
        skills_by_num = {}
        for skill in skill_svts:
            num = _extract_number(skill.get('num', 0))
            if num not in skills_by_num:
                skills_by_num[num] = []
            skills_by_num[num].append(skill)
        
        for skill_num in [1, 2, 3]:
            if skill_num not in skills_by_num:
                continue
                
            candidate_skills = skills_by_num[skill_num]
            
            # Step 1: Filter by variant_svt_id if possible
            variant_matches = [s for s in candidate_skills if _extract_number(s.get('svtId')) == variant_svt_id]
            
            # Step 2: If no variant matches, use all candidates
            if variant_matches:
                candidates = variant_matches
                source = "skillSvts"
            else:
                candidates = candidate_skills
                source = "skillSvts"
            
            # Step 3: Pick entry with highest id
            if candidates:
                selected_skill = max(candidates, key=lambda s: _extract_number(s.get('id', 0)))
                skills[skill_num] = {
                    'selected_id': _extract_number(selected_skill.get('id')),
                    'candidates': [_extract_number(s.get('id')) for s in candidate_skills],
                    'source': source,
                    'json_snippet': json.dumps(selected_skill, indent=2)[:200] + "..." if len(json.dumps(selected_skill)) > 200 else json.dumps(selected_skill, indent=2),
                    'reason': f"{'Variant match with' if variant_matches else 'No variant match, using'} highest ID ({_extract_number(selected_skill.get('id'))})"
                }
        
        return skills
    
    else:
        # Use legacy skills format
        skills = {1: [], 2: [], 3: []}
        for skill in skills_data:
            skill_num = _extract_number(skill.get('num', 1))
            skills[skill_num] = {
                'selected_id': _extract_number(skill.get('id')),
                'candidates': [_extract_number(skill.get('id'))],
                'source': 'skills',
                'json_snippet': json.dumps(skill, indent=2)[:200] + "..." if len(json.dumps(skill)) > 200 else json.dumps(skill, indent=2),
                'reason': 'Legacy format, single skill per slot'
            }
        return skills

def trace_np_selection(servant_json, variant_svt_id, ascension):
    """
    Trace NP selection logic using npSvts data.
    Mimics the logic from units/np.py
    """
    nps_data = servant_json.get('noblePhantasms', [])
    np_svts = servant_json.get('npSvts', [])
    
    # Check if we have npSvts format
    if np_svts:
        # Use npSvts format with variant-aware selection
        
        # Step 1: Try exact svtId match
        variant_matches = [np for np in np_svts if _extract_number(np.get('svtId')) == variant_svt_id]
        if variant_matches:
            selected_nps = variant_matches
            selection_reason = f"Exact svtId match ({variant_svt_id})"
            source = "npSvts"
        else:
            # Step 2: Try imageIndex mapping (ascension-based)
            # Ascension 1-4 typically maps to imageIndex 0-3
            try:
                expected_image_index = int(ascension) - 1
                image_matches = [np for np in np_svts if _extract_number(np.get('imageIndex')) == expected_image_index]
                if image_matches:
                    selected_nps = image_matches
                    selection_reason = f"ImageIndex mapping (ascension {ascension} → imageIndex {expected_image_index})"
                    source = "npSvts"
                else:
                    # Step 3: Use highest priority
                    if np_svts:
                        max_priority = max(_extract_number(np.get('priority', 0)) for np in np_svts)
                        priority_matches = [np for np in np_svts if _extract_number(np.get('priority', 0)) == max_priority]
                        if priority_matches:
                            selected_nps = priority_matches
                            selection_reason = f"Highest priority ({max_priority})"
                            source = "npSvts"
                        else:
                            # Step 4: Fallback to all
                            selected_nps = np_svts
                            selection_reason = "Fallback to all npSvts"
                            source = "npSvts"
                    else:
                        selected_nps = []
                        selection_reason = "No npSvts available"
                        source = "npSvts"
            except Exception:
                # Step 3: Use highest priority
                if np_svts:
                    max_priority = max(_extract_number(np.get('priority', 0)) for np in np_svts)
                    priority_matches = [np for np in np_svts if _extract_number(np.get('priority', 0)) == max_priority]
                    if priority_matches:
                        selected_nps = priority_matches
                        selection_reason = f"Highest priority ({max_priority})"
                        source = "npSvts"
                    else:
                        # Step 4: Fallback to all
                        selected_nps = np_svts
                        selection_reason = "Fallback to all npSvts"
                        source = "npSvts"
                else:
                    selected_nps = []
                    selection_reason = "No npSvts available"
                    source = "npSvts"
        
        # Sort NPs by their original ID to ensure the highest ID is last
        sorted_nps = sorted(selected_nps, key=lambda np: _extract_number(np.get('id', 0)))
        
        if sorted_nps:
            # Default to the highest ID NP (last after sorting)
            selected_np = sorted_nps[-1]
            return {
                'selected_id': _extract_number(selected_np.get('id')),
                'candidates': [_extract_number(np.get('id')) for np in np_svts],
                'source': source,
                'json_snippet': json.dumps(selected_np, indent=2)[:200] + "..." if len(json.dumps(selected_np)) > 200 else json.dumps(selected_np, indent=2),
                'reason': selection_reason
            }
        else:
            return {
                'selected_id': None,
                'candidates': [],
                'source': source,
                'json_snippet': "{}",
                'reason': "No NPs found"
            }
    
    else:
        # Use legacy noblePhantasms format
        if nps_data:
            # Sort by ID and take highest
            sorted_nps = sorted(nps_data, key=lambda np: _extract_number(np.get('id', 0)))
            selected_np = sorted_nps[-1]
            
            return {
                'selected_id': _extract_number(selected_np.get('id')),
                'candidates': [_extract_number(np.get('id')) for np in nps_data],
                'source': 'noblePhantasms',
                'json_snippet': json.dumps(selected_np, indent=2)[:200] + "..." if len(json.dumps(selected_np)) > 200 else json.dumps(selected_np, indent=2),
                'reason': 'Legacy format, highest ID NP'
            }
        else:
            return {
                'selected_id': None,
                'candidates': [],
                'source': 'noblePhantasms',
                'json_snippet': "{}",
                'reason': 'No NPs available'
            }

def trace_servant(servant_id, ascension_inputs):
    """
    Trace servant selection for multiple ascension inputs.
    """
    print(f"Tracing servant {servant_id}...")
    
    # Load servant data
    servant_json = load_servant_data(servant_id)
    if not servant_json:
        return None
    
    checks = []
    
    for ascension_input in ascension_inputs:
        print(f"  Testing ascension input: {ascension_input}")
        
        # Compute variant svt ID
        resolved_variant_svt_id = compute_variant_svt_id(servant_json, ascension_input)
        
        # Get ascension-specific data
        ascension_data = select_ascension_data(servant_json, ascension_input if not str(ascension_input).isdigit() or int(ascension_input) < 100000 else 1)
        
        # Trace skill selection
        skills_trace = trace_skill_selection(servant_json, resolved_variant_svt_id)
        
        # Trace NP selection  
        np_trace = trace_np_selection(servant_json, resolved_variant_svt_id, ascension_input if not str(ascension_input).isdigit() or int(ascension_input) < 100000 else 1)
        
        # Build selected_skills array
        selected_skills = []
        for num in [1, 2, 3]:
            if num in skills_trace and skills_trace[num]:
                skill_data = skills_trace[num]
                selected_skills.append({
                    "num": num,
                    "selected_id": skill_data['selected_id'],
                    "candidates": skill_data['candidates'],
                    "source": skill_data['source'],
                    "json_snippet": skill_data['json_snippet'],
                    "code_location": {
                        "file": "units/skills.py", 
                        "function": "_parse_skill_svts" if skill_data['source'] == 'skillSvts' else "_parse_legacy_skills",
                        "code_snippet": "selected_skill = max(candidates, key=lambda s: _extract_number(s.get('id', 0)))" if skill_data['source'] == 'skillSvts' else "parsed_skill = self._parse_single_skill(skill, use_max_level=True)"
                    },
                    "reason": skill_data['reason']
                })
        
        check = {
            "ascension_input": ascension_input,
            "resolved_variant_svt_id": resolved_variant_svt_id,
            "selected_skills": selected_skills,
            "selected_np": {
                "selected_id": np_trace['selected_id'],
                "candidates": np_trace['candidates'],
                "source": np_trace['source'],
                "json_snippet": np_trace['json_snippet'],
                "code_location": {
                    "file": "units/np.py",
                    "function": "_select_variant_nps" if np_trace['source'] == 'npSvts' else "parse_noble_phantasms",
                    "code_snippet": "variant_matches = [np for np in np_svts if _extract_number(np.get('svtId')) == variant_svt_id]" if np_trace['source'] == 'npSvts' else "sorted_nps = sorted(selected_nps, key=lambda np: _extract_number(np.get('id', 0)))"
                },
                "reason": np_trace['reason']
            },
            "trace": [
                {"file": "units/Servant.py", "function": "compute_variant_svt_id", "line_snippet": f"return {resolved_variant_svt_id}", "why_relevant": "Determines which variant/costume to use"},
                {"file": "units/Servant.py", "function": "select_ascension_data", "line_snippet": "ascension_data = select_ascension_data(self.data, ascension)", "why_relevant": "Selects ascension-specific skills/NPs"},
                {"file": "units/skills.py", "function": "parse_skills", "line_snippet": "skills = self._parse_skill_svts(skills_data)" if selected_skills and selected_skills[0]['source'] == 'skillSvts' else "skills = self._parse_legacy_skills(skills_data)", "why_relevant": "Entry point for skill selection"},
                {"file": "units/np.py", "function": "parse_noble_phantasms", "line_snippet": "selected_nps = self._select_variant_nps(nps_data)" if np_trace['source'] == 'npSvts' else "selected_nps = nps_data", "why_relevant": "Entry point for NP selection"}
            ]
        }
        
        checks.append(check)
    
    return {
        "servant_id": servant_id,
        "checks": checks,
        "notes": f"Analysis based on {servant_json.get('name', 'Unknown')} (ID: {servant_json.get('id', 'Unknown')}). Uses {'skillSvts/npSvts' if servant_json.get('skillSvts') or servant_json.get('npSvts') else 'legacy'} format."
    }

def main():
    # Test cases as specified in the problem
    servant_ids = [1, 312, 444]
    ascension_inputs = [0, 1, 2, 3, 4, 800190, 800200]
    
    results = []
    
    for servant_id in servant_ids:
        result = trace_servant(servant_id, ascension_inputs)
        if result:
            results.append(result)
    
    # Output as JSON
    print("\n" + "="*80)
    print("FINAL RESULTS:")
    print("="*80)
    print(json.dumps(results, indent=2))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    for result in results:
        servant_id = result['servant_id']
        servant_name = result['notes'].split('(ID:')[0].split('based on ')[1] if 'based on ' in result['notes'] else f"Servant {servant_id}"
        print(f"\n{servant_name}:")
        for check in result['checks']:
            ascension_input = check['ascension_input']
            variant_id = check['resolved_variant_svt_id']
            skill_ids = [s['selected_id'] for s in check['selected_skills']]
            np_id = check['selected_np']['selected_id']
            print(f"  Ascension {ascension_input} → Variant {variant_id} → Skills {skill_ids}, NP {np_id}")

if __name__ == '__main__':
    main()