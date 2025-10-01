import logging

# Module logger (Driver.py will configure handlers)
logger = logging.getLogger(__name__)

magic_bullet_buff = {'buff': 'Magic Bullet', 'functvals': [], 'value': 9999, 'tvals': [2885], 'turns': -1, 'source': 'system'}

class Buffs:
    def count_buffs_by_individuality(self, individuality_id):
        """Count buffs on this servant with a tval or vals id matching individuality_id (int)."""
        count = 0
        for buff in self.buffs:
            # Check tvals and vals for matching individuality
            tvals = buff.get('tvals', [])
            vals = buff.get('vals', [])
            # tvals/vals can be list of dicts or ints
            for v in tvals + vals:
                if isinstance(v, dict):
                    if v.get('id') == individuality_id:
                        count += 1
                elif v == individuality_id:
                    count += 1
        return count
    
    def __init__(self, servant=None, enemy=None):
        # Initialize basic buffs list and stateful effect tracking for all cases
        self.buffs = []
        self.stateful_effects = []
        self.counters = {}
        
        if servant:
            self.servant = servant
        if enemy:
            self.enemy = enemy

    def process_end_turn_skills(self):
        add_magic_bullets = False
        logger.debug(f"PROCESSING END TURN SKILLS")
        for i, buff in enumerate(self.buffs):
            # logging.info(f"step 2.{i}")
            if buff['buff'] == 'NP Gain Each Turn':
                # logging.info(f"step 3.{i} checking for NP GAIN PER TURN")
                self.servant.set_npgauge(buff['value'])
            if buff['buff'] == 'Delayed Effect (Death)':
                # logging.info(f"step 4.{i} checking for delayed effect of instant death")
                self.servant.kill = True
            if self.servant.name == 'Super Aoko':
                # logging.info(f"step 5.{i} checking if we are SUPER AOKO, IF true add 2 magic bullets")
                add_magic_bullets = True

        if add_magic_bullets == True:
            self.add_buff(magic_bullet_buff) # adds 4 per turn for some reason when both are added
            self.add_buff(magic_bullet_buff)

    def process_enemy_buffs(self):
        # Reset modifiers
        self.enemy.defense = 0
        self.enemy.b_resdown = 0
        self.enemy.a_resdown = 0
        self.enemy.q_resdown = 0
        self.enemy.roman = self.enemy.traits.count(2004)
        # Process buffs and update modifiers
        # print(f"{self.name} has the following effects applied: {self.buffs}")
        for buff in self.buffs:
            if buff['buff'] == 'DEF Down':
                self.enemy.defense -= buff['value'] / 1000
            elif buff['buff'] == 'Buster Card Resist Down':
                self.enemy.b_resdown -= buff['value'] / 1000
            elif buff['buff'] == 'Arts Card Resist Down':
                self.enemy.a_resdown -= buff['value'] / 1000
            elif buff['buff'] == 'Quick Card Resist Down':
                self.enemy.q_resdown -= buff['value'] / 1000
            elif buff['buff'] == 'Apply Trait (Rome)':
                self.enemy.traits.append(2004)
            # Add more buff processing as needed
        # print(buff)

    def process_servant_buffs(self):
        # Reset modifiers
        self.servant.atk_mod = self.servant.user_atk_mod
        self.servant.b_up = self.servant.user_b_up
        self.servant.a_up = self.servant.user_a_up
        self.servant.q_up = self.servant.user_q_up
        self.servant.power_mod = {}
        self.user_damage_mod= self.servant.user_damage_mod
        self.servant.np_damage_mod = self.servant.user_np_damage_mod
        self.servant.oc_level = 1
        self.servant.np_gain_mod = 1
        self.servant.buster_card_damage_up = self.servant.user_buster_damage_up
        self.servant.arts_card_damage_up = self.servant.user_arts_damage_up
        self.servant.quick_card_damage_up = self.servant.user_quick_damage_up

        # Store a flag for Boost NP Strength Up
        boost_np_strength_up_active = False

        # Initial pass to calculate np_damage_mod
        for buff in self.buffs:
            required_field = buff.get('script', {}).get('INDIVIDUALITIE', {}).get('id')
            if required_field is None:
                required_field = buff.get('originalScript', {}).get('INDIVIDUALITIE')
            if required_field is None or (required_field in self.servant.fields):
                if buff['buff'] == 'NP Strength Up' or buff['buff'] == 'upNpdamage':
                    self.servant.np_damage_mod += buff['value'] / 1000
                elif buff['buff'] == 'Boost NP Strength Up':
                    boost_np_strength_up_active = True

        # Apply the Boost NP Strength Up multiplier
        if boost_np_strength_up_active:
            self.servant.np_damage_mod *= 2

        #TODO buffs that have the same "value" number will overwrite each other
        #   as an example if you do 2 castoria skill 3's 1 turn after the first it will over writethe turn but not add a new one

        # Second pass for other buffs
        for buff in self.buffs:
            required_field = buff.get('script', {}).get('INDIVIDUALITIE', {}).get('id')
            if required_field is None:
                required_field = buff.get('originalScript', {}).get('INDIVIDUALITIE')
            if required_field is None or (required_field in self.servant.fields):
                if buff['buff'] == 'ATK Up':
                    self.servant.atk_mod += buff['value'] / 1000
                elif buff['buff'] == 'Buster Up':
                    self.servant.b_up += buff['value'] / 1000
                elif buff['buff'] == 'Arts Up':
                    self.servant.a_up += buff['value'] / 1000
                elif buff['buff'] == 'Quick Up':
                    self.servant.q_up += buff['value'] / 1000
                elif buff['buff'] == 'Buster Card Damage Up':
                    self.servant.buster_card_damage_up += buff['value'] / 1000
                elif buff['buff'] == 'Arts Card Damage Up':
                    self.servant.arts_card_damage_up += buff['value'] / 1000
                elif buff['buff'] == 'Quick Card Damage Up':
                    self.servant.quick_card_damage_up += buff['value'] / 1000
                elif buff['buff'] == 'Power Up':
                    # Power Up may target specific trait ids (tvals) or be a global power modifier.
                    tvals = buff.get('tvals', []) or []
                    if tvals:
                        for tval in tvals:
                            if tval not in self.servant.power_mod:
                                self.servant.power_mod[tval] = 0
                            self.servant.power_mod[tval] += buff.get('value', 0)
                    else:
                        # No tvals: store under a special global key to avoid type errors.
                        self.servant.power_mod.setdefault('global', 0)
                        self.servant.power_mod['global'] += buff.get('value', 0)
                elif buff['buff'] in ['NP Overcharge Level Up', 'Overcharge Lv. Up']:
                    self.servant.oc_level = min(self.servant.oc_level + buff['value'], 5)
                elif "STR Up" in buff["buff"] or "Strength Up" in buff["buff"]:
                    # Some buff entries (display-only or legacy) may not include 'tvals'.
                    # Use .get to default to an empty list to avoid KeyError.
                    for tval in buff.get('tvals', []):
                        if tval not in self.servant.power_mod:
                            self.servant.power_mod[tval] = 0
                        self.servant.power_mod[tval] += buff.get("value", 0)
                elif 'Triggers Each Turn' in buff['buff'] or 'Triggers Each Hit' in buff['buff']:
                    # Robust trigger: apply effect based on buff type, not just NP
                    # Try to infer effect from buff['buff'] name
                    name = buff['buff']
                    value = buff.get('value', 0) / 1000
                    if 'NP' in name and ('Increase' in name or 'Absorb' in name or 'Gain' in name):
                        self.servant.np_gauge += value
                    elif 'ATK Up' in name:
                        self.servant.atk_mod += value
                    elif 'NP Strength Up' in name or 'upNpdamage' in name:
                        self.servant.np_damage_mod += value
                    elif 'Star' in name and ('Gain' in name or 'Up' in name):
                        # If you have a star mechanic, increment it here
                        if hasattr(self.servant, 'star_count'):
                            self.servant.star_count += int(buff.get('value', 0) / 100)
                    # Add more trigger types as needed
                    else:
                        # Default: log and skip
                        logger.debug(f"[Buffs] Unhandled trigger effect: {name} value={value}")
                elif buff['buff'] == 'NP Gain Up':
                    self.servant.np_gain_mod += buff['value'] / 1000

    def parse_passive(self, passives_data):
        passives = []
        for passive in passives_data:
            parsed_passive = {
                'id': passive.get('id'),
                'name': passive.get('name'),
                'functions': self.parse_passive_functions(passive.get('functions', []))
            }
            passives.append(parsed_passive)
        return passives

    def parse_passive_functions(self, functions_data):
        functions = []
        for func in functions_data:
            svals = func.get('svals', {})
            # Handle both list and dict formats for svals
            if isinstance(svals, list):
                parsed_svals = svals[-1] if len(svals) > 0 else {}
            else:
                parsed_svals = svals
                
            parsed_function = {
                'funcType': func.get('funcType'),
                'funcTargetType': func.get('funcTargetType'),
                'functvals': func.get('functvals', []),
                'svals': parsed_svals,
                'buffs': func.get('buffs', [])
            }
            functions.append(parsed_function)
        return functions

    def add_buff(self, buff: dict):
        # Ensure Magic Bullet buffs always have tvals: [2885] for individuality counting
        if buff.get('buff') == 'Magic Bullet':
            # If tvals is missing or does not contain 2885, add it
            tvals = buff.get('tvals', [])
            if 2885 not in tvals:
                tvals = list(tvals) + [2885]
                buff['tvals'] = tvals
        # Defensive: ensure every buff has a 'source' key for debugging output.
        if 'source' not in buff or not buff.get('source'):
            if buff.get('is_passive'):
                buff['source'] = 'passive'
            elif buff.get('user_input') or buff.get('from_user'):
                buff['source'] = 'user'
            elif buff.get('from_skill') or buff.get('skill') or buff.get('skill_num'):
                # best-effort label when we know it came from a skill
                buff['source'] = 'skill'
            else:
                buff['source'] = 'unknown'

        self.buffs.append(buff)

    def remove_buff(self, buff: dict):
        for i, b in enumerate(self.buffs):
            if buff == b:
                self.buffs.pop(i)

    def decrement_buffs(self):
        for buff in self.buffs[:]:
            if buff['turns'] > 0:
                buff['turns'] -= 1
            if buff['turns'] == 0:
                self.buffs.remove(buff)

    def clear_buff(self, str):
        self.buffs = [i for i in self.buffs if i['buff'] != str]

    def grouped_str(self):
        from collections import defaultdict
        import math
        grouped = defaultdict(list)
        # Group buffs by name, but keep all instances
        for buff in self.buffs:
            name = buff.get('buff', 'Unknown')
            grouped[name].append(buff)
        lines = []
        for name, buffs in grouped.items():
            # Each buff instance on its own line, with value, turns, and source
            for buff in buffs:
                value = buff.get('value', 0)
                # If a user provided an explicit display value for permanent user-inputted buffs,
                # prefer that for debugging output so users see the numbers they entered.
                if buff.get('user_input') and buff.get('turns', -1) == -1 and 'display_value' in buff:
                    display_value = buff.get('display_value')
                    value_str = str(display_value)
                else:
                # FGO convention: value is percent if >1, else decimal
                    value_str = f"{value/1000:.3f}" if isinstance(value, (int, float)) and not math.isclose(value, 0) else str(value)
                turns = buff.get('turns', -1)
                # Try to get source: skill, passive, user, etc.
                source = buff.get('source', None)
                if not source:
                    # Try to infer from metadata
                    if buff.get('is_passive'):
                        source = 'passive'
                    elif buff.get('user_input', False):
                        source = 'user'
                    elif buff.get('from_skill', False):
                        source = 'skill'
                    else:
                        source = 'unknown'
                else:
                    # If a stored skill_turn is present, ensure the source string
                    # includes the turn (T#) for clarity. Many sources are like
                    # 'Aozaki Aoko S3' — if 'skill_turn' exists we append ' T#'.
                    st = buff.get('skill_turn', None)
                    if st is not None:
                        # only append if 'T' not already present
                        if 'T' not in str(source):
                            source = f"{source} T{st}"
                # Always show permanent buffs (turns=-1), even if value is 0
                # Always show user/passive buffs, even if value is 0
                show = True
                if value == 0 and turns != -1 and source not in ('user', 'passive'):
                    show = False
                if show:
                    lines.append(f"{name}: {{value={value_str}, turns={turns}, source={source}}}")
        return "\n".join(lines) if lines else "No active buffs"

    def __repr__(self):
        return self.grouped_str()
        
    def add_stateful_effect(self, effect_type, effect_id, owner, lifetime, params):
        """Add a stateful effect like a counter or per-turn trigger."""
        stateful_effect = {
            "type": effect_type,  # 'counter', 'per_turn', 'trait_add', etc.
            "id": effect_id,
            "owner": owner,  # 'self' or 'target'
            "lifetime": lifetime,  # turns or 'permanent' or 'per_trigger'
            "params": params,
            "stack_count": 1
        }
        
        self.stateful_effects.append(stateful_effect)
        
        # Special handling for counters
        if effect_type == 'counter':
            counter_id = params.get('counter_id', effect_id)
            if counter_id not in self.counters:
                self.counters[counter_id] = {
                    "count": params.get('initial_count', 0),
                    "max_count": params.get('max_count', 99),
                    "increment_per_trigger": params.get('increment', 1),
                    "consume_per_use": params.get('consume', 1)
                }
    
    def get_counters(self, owner=None):
        """Get current counter states, optionally filtered by owner."""
        if owner is None:
            return self.counters
        
        # Filter by owner if specified
        filtered_counters = {}
        for effect in self.stateful_effects:
            if effect['type'] == 'counter' and effect['owner'] == owner:
                counter_id = effect['params'].get('counter_id', effect['id'])
                if counter_id in self.counters:
                    filtered_counters[counter_id] = self.counters[counter_id]
        
        return filtered_counters
    
    def increment_counter(self, counter_id, amount=1):
        """Increment a counter by specified amount."""
        if counter_id in self.counters:
            counter = self.counters[counter_id]
            counter['count'] = min(
                counter['count'] + amount,
                counter['max_count']
            )
    
    def consume_counter(self, counter_id, amount=1):
        """Consume from a counter and return if successful."""
        if counter_id in self.counters:
            counter = self.counters[counter_id]
            if counter['count'] >= amount:
                counter['count'] -= amount
                return True
        return False
    
    def process_stateful_effects_end_turn(self):
        """Process stateful effects at end of turn."""
        for effect in self.stateful_effects[:]:  # Copy to avoid modification during iteration
            if effect['type'] == 'per_turn':
                self._apply_per_turn_effect(effect)
            
            # Decrement lifetime
            if isinstance(effect['lifetime'], int) and effect['lifetime'] > 0:
                effect['lifetime'] -= 1
                if effect['lifetime'] <= 0:
                    self.stateful_effects.remove(effect)
    
    def _apply_per_turn_effect(self, effect):
        """Apply a per-turn effect."""
        params = effect.get('params', {})
        effect_type = params.get('effect_type', 'unknown')
        
        if effect_type == 'np_gain':
            if hasattr(self, 'servant') and self.servant:
                self.servant.set_npgauge(params.get('value', 0))
        elif effect_type == 'damage':
            # Apply per-turn damage (not implemented in base game)
            pass
        elif effect_type == 'heal':
            # Apply per-turn healing (not implemented in base game)
            pass

