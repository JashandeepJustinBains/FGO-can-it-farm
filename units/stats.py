from data import class_advantage_matrix, attribute_dict, class_indices

class Stats:
    def __init__(self, servant):
        self.servant = servant

    def decrement_cooldowns(self, effect):
        for skill in self.servant.cooldowns:
            if self.servant.cooldowns[skill] > 0:
                self.servant.cooldowns[skill] = max(self.servant.cooldowns[skill] - effect['svals']['Value'], 0)

    def get_base_atk(self):
        return ( self.servant.bonus_attack + self.get_atk_at_level(self.servant.get_lvl()) ) * self.get_class_base_multiplier()

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
            self.servant.np_gauge = 0
        else:
            self.servant.np_gauge += val

    def get_current_buffs(self):
        return [
            {'atk': self.get_atk_mod()},
            {'buster+': self.get_b_up()},
            {'arts+': self.get_a_up()},
            {'quick+': self.get_q_up()},
            {'buster card damage+': self.get_buster_card_damage_up()},
            {'arts card damage+': self.get_arts_card_damage_up()},
            {'quick card damage+': self.get_quick_card_damage_up()},
            {'power mods': self.get_power_mod()},
            {'np gain': self.servant.np_gain_mod},
            {'np damage': self.get_np_damage_mod()}
        ]

    def get_class_multiplier(self, defender_class):
        return class_advantage_matrix[class_indices[self.servant.class_name]][class_indices[defender_class]]

    def get_class_base_multiplier(self):
        return self.servant.class_base_multiplier

    def get_attribute_modifier(self, defender):
        return attribute_dict.get(self.servant.attribute).get(defender.attribute)

    def contains_trait(self, trait_id):
        return trait_id[0]['id'] in self.servant.traits

    def get_buster_card_damage_up(self):
        return getattr(self.servant, 'buster_card_damage_up', 0)

    def get_arts_card_damage_up(self):
        return getattr(self.servant, 'arts_card_damage_up', 0)

    def get_quick_card_damage_up(self):
        return getattr(self.servant, 'quick_card_damage_up', 0)
        
    def resolve_generic_effect(self, effect, target=None):
        """Interpret a normalized effect for runtime use."""
        func_type = effect.get('funcType', '').lower()
        parameters = effect.get('parameters', {})
        
        # Damage calculation effects
        if 'damage' in func_type:
            return self._resolve_damage_effect(effect, target)
        
        # Stat modification effects
        elif any(pattern in func_type for pattern in ['up', 'buff', 'boost']):
            return self._resolve_stat_effect(effect)
        
        # Trait manipulation effects
        elif 'trait' in func_type:
            return self._resolve_trait_effect(effect, target)
        
        # Counter effects
        elif 'counter' in func_type:
            return self._resolve_counter_effect(effect)
        
        # Default: return raw effect data
        return effect
    
    def _resolve_damage_effect(self, effect, target):
        """Resolve damage-related effect parameters."""
        parameters = effect.get('parameters', {})
        damage_info = {
            'type': 'damage',
            'base_multiplier': parameters.get('value', 0) / 1000 if parameters.get('value') else 0,
            'correction': parameters.get('correction', 0) / 1000 if parameters.get('correction') else 0,
            'target_traits': parameters.get('targetlist', []),
            'special_target': parameters.get('target', 0)
        }
        return damage_info
    
    def _resolve_stat_effect(self, effect):
        """Resolve stat modification effect parameters."""
        parameters = effect.get('parameters', {})
        stat_info = {
            'type': 'stat_modification',
            'value': parameters.get('value', 0),
            'duration': parameters.get('turn', 1),
            'target_type': effect.get('targetType', 'self')
        }
        return stat_info
    
    def _resolve_trait_effect(self, effect, target):
        """Resolve trait manipulation effect parameters."""
        parameters = effect.get('parameters', {})
        trait_info = {
            'type': 'trait_manipulation',
            'trait_ids': parameters.get('tvals', []),
            'operation': 'add' if 'add' in effect.get('funcType', '').lower() else 'remove',
            'duration': parameters.get('turn', -1)
        }
        return trait_info
    
    def _resolve_counter_effect(self, effect):
        """Resolve counter effect parameters."""
        parameters = effect.get('parameters', {})
        counter_info = {
            'type': 'counter',
            'counter_id': parameters.get('counter_id', effect.get('variant_id')),
            'increment': parameters.get('count', 1),
            'max_count': parameters.get('max_count', 99)
        }
        return counter_info
    
    def resolve_np_damage_components(self, target, np_level=5, oc_level=3):
        """Calculate NP damage with all bonuses."""
        # Get NP damage multiplier
        np_damage_multiplier = self.servant.nps.get_np_damage_multiplier(np_level, oc_level)
        
        # Get special damage parameters
        special_damage = self.servant.nps.get_np_special_damage(np_level, oc_level)
        
        damage_components = {
            'base_multiplier': np_damage_multiplier,
            'special_damage': special_damage,
            'servant_atk': self.get_base_atk(),
            'atk_mod': self.get_atk_mod(),
            'card_mod': self._get_card_mod(),
            'np_damage_mod': self.get_np_damage_mod(),
            'class_modifier': self.get_class_multiplier(target.class_name) if target else 1.0,
            'attribute_modifier': self.get_attribute_modifier(target) if target else 1.0
        }
        
        return damage_components
    
    def _get_card_mod(self):
        """Get card type modifier based on NP card type."""
        card_type = self.servant.card_type
        if card_type == 'buster':
            return self.get_b_up()
        elif card_type == 'arts':
            return self.get_a_up()
        elif card_type == 'quick':
            return self.get_q_up()
        return 0
