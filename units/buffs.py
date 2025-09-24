import logging

# Configure logging
logging.basicConfig(filename='./outputs/output.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

magic_bullet_buff = {'buff': 'Magic Bullet', 'functvals': [], 'value': 9999, 'tvals': [], 'turns': -1}

class Buffs:
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
        logging.info(f"PROCESSING END TURN SKILLS")
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
                elif buff['buff'] == 'Power Up':
                    self.servant.power_mod += buff['value'] / 1000
                elif buff['buff'] in ['NP Overcharge Level Up', 'Overcharge Lv. Up']:
                    self.servant.oc_level = min(self.servant.oc_level + buff['value'], 5)
                elif "STR Up" in buff["buff"] or "Strength Up" in buff["buff"]:
                    for tval in buff['tvals']:
                        if tval not in self.servant.power_mod:
                            self.servant.power_mod[tval] = 0
                        self.servant.power_mod[tval] += buff.get("value", 0)
                elif 'Triggers Each Turn (Increase NP)' in buff['buff'] or 'Triggers Each Turn (NP Absorb)' in buff['buff']: # TODO assumes all Triggers Each Turn buffs are for NP gain
                    self.servant.np_gauge += buff['value']
                elif buff['buff'] == 'NP Gain Up':
                    self.servant.np_gain_mod += buff['value'] / 1000
                elif buff['buff'] == 'Buster Card Damage Up':
                    self.servant.buster_card_damage_up += buff['value'] / 1000
                elif buff['buff'] == 'Arts Card Damage Up':
                    self.servant.arts_card_damage_up += buff['value'] / 1000
                elif buff['buff'] == 'Quick Card Damage Up':
                    self.servant.quick_card_damage_up += buff['value'] / 1000

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
        grouped = defaultdict(list)
        for buff in self.buffs:
            name = buff.get('buff', 'Unknown')
            value = buff.get('value', 0)
            turns = buff.get('turns', -1)
            grouped[name].append((value, turns))
        lines = []
        for name, vals in grouped.items():
            val_str = ', '.join([f"value={v/1000 if v else v}, turns={t}" for v, t in vals])
            lines.append(f"{name}: [{val_str}]")
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

