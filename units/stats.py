# Enhanced stats module with effect interpretation helpers
# Provides runtime interpretation for normalized effects from the enhanced parsers
# Supports damage calculation, buff resolution, and stateful effect queries

from data import class_advantage_matrix, attribute_dict, class_indices

class Stats:
    def __init__(self, servant):
        self.servant = servant

    def decrement_cooldowns(self, effect):
        for skill in self.servant.cooldowns:
            if self.servant.cooldowns[skill] > 0:
                self.servant.cooldowns[skill] = max(self.servant.cooldowns[skill] - effect['svals']['Value'], 0)

    def get_base_atk(self):
        # 1000atk from silver fous
        return ( self.CE_get_atk() + 1000 + self.get_atk_at_level() ) * self.servant.stats.get_class_base_multiplier()

    def get_atk_at_level(self, level=0):
        if level == 0:
            if self.servant.rarity == 1:
                level = 55
            if self.servant.rarity == 2:
                level = 60
            if self.servant.rarity == 3:
                level = 65
            if self.servant.rarity == 4:
                level = 80
            if self.servant.rarity == 5:
                level = 90
        atk = self.servant.atk_growth[level-1] if level <= 120 else None
        return atk

    def CE_get_atk(self):
        #TODO IMPLEMENT CE
        return 0

    def get_name(self):
        return self.servant.name

    def get_atk_mod(self):
        return self.servant.atk_mod

    def get_b_up(self):
        return self.servant.b_up

    def get_a_up(self):
        return self.servant.a_up

    def get_q_up(self):
        return self.servant.q_up

    def get_power_mod(self, target=None):
        if target:
            powermod = 0
            for key in self.servant.power_mod:
                if key in target.traits:
                    powermod += self.servant.power_mod[key]
            powermod /= 1000
            return powermod
        else:
            return self.servant.power_mod

    def get_np_damage_mod(self):
        return self.servant.np_damage_mod 

    def get_np_level(self):
        return self.servant.np_level

    def get_oc_level(self):
        return self.servant.oc_level

    def set_oc_level(self, oc):
        self.servant.oc_level = oc

    def get_npgain(self):
        return self.servant.nps.get_npgain(self.servant.card_type)

    def get_np_gain_mod(self):
        return self.servant.np_gain_mod

    def get_npdist(self):
        return self.servant.nps.get_npdist()

    def get_npgauge(self):
        return self.servant.np_gauge

    def set_npgauge(self, val=0):
        if val == 0:
            print(f"Setting NP gauge of {self.get_name()} to {val}%")
            self.servant.np_gauge = 0
        else:
            print(f"Increasing NP gauge of {self.get_name()} to {self.servant.np_gauge + val}%")
            self.servant.np_gauge += val

    def get_current_buffs(self):
        return [{'atk': self.get_atk_mod()},
                {'buster+': self.get_b_up()},
                {'arts+': self.get_a_up()},
                {'quick+': self.get_q_up()},
                {'power mods': self.get_power_mod()},
                {'np gain': self.servant.np_gain_mod},
                {'np damage': self.get_np_damage_mod()}]

    def get_class_multiplier(self, defender_class):
        return class_advantage_matrix[class_indices[self.servant.class_name]][class_indices[defender_class]]

    def get_class_base_multiplier(self):
        return self.servant.class_base_multiplier

    def get_attribute_modifier(self, defender):
        return attribute_dict.get(self.servant.attribute).get(defender.attribute)

    def contains_trait(self, trait_id):
        return trait_id[0]['id'] in self.servant.traits
    
    # Enhanced effect interpretation helpers
    def resolve_np_damage_components(self, target, np_level=None, oc_level=None):
        """Resolve NP damage components using enhanced effect parsing."""
        if np_level is None:
            np_level = self.get_np_level()
        if oc_level is None:
            oc_level = self.get_oc_level()
        
        # Get normalized NP effects
        np_effects = self.servant.nps.get_np_values(np_level, oc_level)
        
        damage_components = {
            'base_multiplier': 0.0,
            'special_damage': None,
            'trait_bonuses': [],
            'counter_bonuses': []
        }
        
        for effect in np_effects:
            func_type = effect.get('funcType', '')
            parameters = effect.get('parameters', {})
            
            # Handle different damage types
            if func_type in ['damageNp', 'damageNpPierce']:
                damage_components['base_multiplier'] = parameters.get('value', 0) / 1000.0
            
            elif func_type in ['damageNpIndividual', 'damageNpStateIndividualFix']:
                damage_components['special_damage'] = {
                    'type': 'individual',
                    'base_damage': parameters.get('value', 0) / 1000.0,
                    'correction': parameters.get('correction', 0) / 1000.0,
                    'target': parameters.get('target', 0)
                }
            
            elif func_type == 'damageNpIndividualSum':
                damage_components['special_damage'] = {
                    'type': 'individual_sum',
                    'base_damage': parameters.get('value', 0) / 1000.0,
                    'correction_damage': parameters.get('value2', 0) / 1000.0,
                    'correction': parameters.get('correction', 0) / 1000.0,
                    'target': parameters.get('target', 0),
                    'target_list': parameters.get('targetlist', [])
                }
            
            # Check for trait-based bonuses
            buffs = effect.get('buffs', [])
            for buff in buffs:
                buff_name = buff.get('name', '')
                if 'strength' in buff_name.lower() or 'str' in buff_name.lower():
                    tvals = buff.get('params', {}).get('tvals', [])
                    if any(trait in target.traits for trait in tvals):
                        damage_components['trait_bonuses'].append({
                            'buff_name': buff_name,
                            'value': buff.get('params', {}).get('value', 0) / 1000.0,
                            'traits': tvals
                        })
        
        # Check for counter-based bonuses
        counters = self.servant.buffs.get_counters('self')
        for counter_id, counter_data in counters.items():
            if counter_data['count'] > 0:
                damage_components['counter_bonuses'].append({
                    'counter_id': counter_id,
                    'count': counter_data['count'],
                    'bonus_per_count': counter_data.get('damage_bonus_per_count', 0)
                })
        
        return damage_components
    
    def get_effective_stat_buffs(self):
        """Get effective stat buffs from normalized effects."""
        stat_buffs = {
            'atk_up': 0.0,
            'buster_up': 0.0,
            'arts_up': 0.0,
            'quick_up': 0.0,
            'np_damage_up': 0.0,
            'trait_specific': {}
        }
        
        # Include existing buffs
        stat_buffs['atk_up'] += self.get_atk_mod()
        stat_buffs['buster_up'] += self.get_b_up()
        stat_buffs['arts_up'] += self.get_a_up()
        stat_buffs['quick_up'] += self.get_q_up()
        stat_buffs['np_damage_up'] += self.get_np_damage_mod()
        
        # Add trait-specific bonuses
        power_mods = self.get_power_mod()
        if isinstance(power_mods, dict):
            for trait_id, bonus in power_mods.items():
                stat_buffs['trait_specific'][trait_id] = bonus / 1000.0
        
        return stat_buffs
    
    def resolve_generic_effect(self, effect, target=None):
        """Generic runtime interpretation of normalized effects."""
        func_type = effect.get('funcType', '')
        parameters = effect.get('parameters', {})
        
        # Map common funcTypes to runtime semantics
        if func_type in ['atkUp', 'upAtk']:
            return {
                'type': 'stat_buff',
                'stat': 'attack',
                'value': parameters.get('value', 0) / 1000.0,
                'duration': parameters.get('turn', 3)
            }
        
        elif func_type in ['defUp', 'upDef']:
            return {
                'type': 'stat_buff',
                'stat': 'defense',
                'value': parameters.get('value', 0) / 1000.0,
                'duration': parameters.get('turn', 3)
            }
        
        elif func_type in ['busterUp', 'upBuster']:
            return {
                'type': 'card_buff',
                'card': 'buster',
                'value': parameters.get('value', 0) / 1000.0,
                'duration': parameters.get('turn', 3)
            }
        
        elif func_type in ['artsUp', 'upArts']:
            return {
                'type': 'card_buff',
                'card': 'arts',
                'value': parameters.get('value', 0) / 1000.0,
                'duration': parameters.get('turn', 3)
            }
        
        elif func_type in ['quickUp', 'upQuick']:
            return {
                'type': 'card_buff',
                'card': 'quick',
                'value': parameters.get('value', 0) / 1000.0,
                'duration': parameters.get('turn', 3)
            }
        
        elif func_type in ['npUp', 'upNpdamage']:
            return {
                'type': 'np_buff',
                'value': parameters.get('value', 0) / 1000.0,
                'duration': parameters.get('turn', 3)
            }
        
        elif 'trait' in func_type.lower() and 'add' in func_type.lower():
            return {
                'type': 'trait_add',
                'traits': parameters.get('functvals', []),
                'duration': parameters.get('turn', -1)  # -1 for permanent
            }
        
        elif 'counter' in func_type.lower():
            return {
                'type': 'counter',
                'counter_id': parameters.get('functvals', [None])[0],
                'increment': parameters.get('value', 1),
                'max_count': parameters.get('count', 10)
            }
        
        else:
            # Unknown funcType - return raw for best-effort handling
            return {
                'type': 'unknown',
                'funcType': func_type,
                'parameters': parameters,
                'raw': effect.get('raw', {})
            }
