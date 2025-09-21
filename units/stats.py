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
