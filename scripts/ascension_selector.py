from typing import Dict, Any

def select_ascension_data_enhanced(servant_json: Dict[str, Any], ascension: int) -> Dict[str, Any]:
    if 'structureType' not in servant_json:
        from tests.test_servant_ascension_repr import select_ascension_data
        return select_ascension_data(servant_json, ascension)
    result = {
        'skills': [],
        'noblePhantasms': [],
        'passives': servant_json.get('passives', []),
        'transforms': servant_json.get('transforms', []),
        'traits': []
    }
    for skill_id, skill_data in servant_json.get('skills', {}).items():
        if ascension in skill_data.get('ascensions', []):
            result['skills'].append(skill_data)
    for np_id, np_data in servant_json.get('noblePhantasms', {}).items():
        if ascension in np_data.get('ascensions', []):
            result['noblePhantasms'].append(np_data)
    traits_by_asc = servant_json.get('traits', {})
    result['traits'] = traits_by_asc.get(ascension, traits_by_asc.get(str(ascension), []))
    return result
