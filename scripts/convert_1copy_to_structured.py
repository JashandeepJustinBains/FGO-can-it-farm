import json
import copy

# Paths
input_path = r"example_servant_data/1 copy.json"
output_path = r"servants/1_structured.json"
reference_path = r"servants/2_structured.json"

# Helper: interpolate atkGrowth
def interpolate_atk_growth(atk_dict):
    # atk_dict: {level: value, ...}
    levels = sorted(int(k) for k in atk_dict.keys())
    values = [atk_dict[str(lv)] for lv in levels]
    atk_growth = [None] * 120
    for i, lv in enumerate(levels):
        atk_growth[lv-1] = values[i]
    # Linear interpolate missing
    last_known = None
    for i in range(120):
        if atk_growth[i] is not None:
            last_known = i
        else:
            # Find next known
            next_known = None
            for j in range(i+1, 120):
                if atk_growth[j] is not None:
                    next_known = j
                    break
            if last_known is not None and next_known is not None:
                # Linear interpolation
                v1 = atk_growth[last_known]
                v2 = atk_growth[next_known]
                atk_growth[i] = int(v1 + (v2-v1)*(i-last_known)/(next_known-last_known))
            elif last_known is not None:
                atk_growth[i] = atk_growth[last_known]
            elif next_known is not None:
                atk_growth[i] = atk_growth[next_known]
            else:
                atk_growth[i] = 0
    return atk_growth

# Load files
with open(input_path, encoding="utf-8") as f:
    servant = json.load(f)
with open(reference_path, encoding="utf-8") as f:
    ref = json.load(f)

# --- ATK Growth ---
if "atkGrowthPoints" in servant:
    servant["atkGrowth"] = interpolate_atk_growth(servant["atkGrowthPoints"])
    servant.pop("atkGrowthPoints")

# --- Skills and NPs ordering ---
# Use ref's skillPriorityMapping and npPriorityMapping to order
servant["skillsByPriority"] = copy.deepcopy(ref["skillsByPriority"])
servant["npsByPriority"] = copy.deepcopy(ref["npsByPriority"])
servant["skillPriorityMapping"] = copy.deepcopy(ref["skillPriorityMapping"])
servant["npPriorityMapping"] = copy.deepcopy(ref["npPriorityMapping"])

# --- Traits, passives, transforms ---
servant["traits"] = copy.deepcopy(ref["traits"])
servant["passives"] = copy.deepcopy(ref["passives"])
servant["transforms"] = copy.deepcopy(ref["transforms"])

# Save
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(servant, f, ensure_ascii=False, indent=2)
