
class npManager:
    def __init__(self, skill_manager):
        self.sm = skill_manager
        self.tm = self.sm.tm
        self.gm = self.tm.gm

    def use_np(self, servant):
        if servant.stats.get_npgauge() >= 99:
            servant.stats.set_npgauge(0)  # Reset NP gauge after use
            functions = servant.nps.get_np_values(servant.stats.get_np_level(), servant.stats.get_oc_level())
            maintarget = None
            max_hp = 0

            # Identify the enemy with the highest HP
            for enemy in self.gm.enemies:
                if enemy.get_hp() > max_hp:
                    max_hp = enemy.get_hp()
                    maintarget = enemy

            # Apply effects and damage
            for i, func in enumerate(functions):

                if func['funcType'] == 'damageNp' or func['funcType'] == 'damageNpIndividual':
                    servant.process_buffs()
                    print(self.servants[0].get_current_buffs())
                    for enemy in self.gm.enemies:
                        self.apply_np_damage(servant, enemy)
                elif func['funcType'] == 'damageNpIndividualSum':
                    servant.process_buffs()
                    for enemy in self.gm.enemies:
                        self.apply_np_odd_damage(servant, enemy)
                else:
                    if func['funcTargetType'] == 'enemyAll':
                        for enemy in self.gm.enemies:
                            self.gm.skill_manager.apply_effect(func, servant)
                    if func['funcTargetType'] == 'enemy':
                        self.sm.apply_effect(func, maintarget)
                    else:
                        self.sm.apply_effect(func, servant)
        else:
            print(f"{servant.name} does not have enough NP gauge: {servant.get_npgauge()}")

    def apply_np_damage(self, servant, target):
        card_damage_value = None
        card_type = servant.get_cardtype()
        card_np_value = 1
        if card_type == 'buster':
            card_damage_value = 1.5
            card_mod = servant.get_b_up()
            enemy_res_mod = target.get_b_resdown()
        elif card_type == 'quick':
            card_damage_value = 0.8
            card_mod = servant.get_q_up()
            enemy_res_mod = target.get_q_resdown()
        elif card_type == 'arts':
            card_damage_value = 1
            card_np_value = 3
            card_mod = servant.get_a_up()
            enemy_res_mod = target.get_a_resdown()

        class_modifier = servant.get_class_multiplier(target.get_class())
        attribute_modifier = servant.get_attribute_modifier(target)
        atk_mod = servant.get_atk_mod()
        enemy_def_mod = target.get_def()
        power_mod = servant.get_power_mod(target)
        self_damage_mod = 0
        np_damage_mod = servant.get_np_damage_mod()
        np_damage_multiplier, np_correction_target, super_effective_modifier = servant.get_np_damage_values(np_level=servant.np_level, oc=servant.get_oc_level())
        is_super_effective = 1 if np_correction_target in target.traits else 0
        servant_atk = servant.get_atk_at_level()

        total_damage = (servant_atk * np_damage_multiplier * (card_damage_value * (1 + card_mod - enemy_res_mod)) *
                        class_modifier * attribute_modifier * 0.23 * (1 + atk_mod - enemy_def_mod) *
                        (1 + self_damage_mod + np_damage_mod + power_mod) * 
                        (1 + (((super_effective_modifier if super_effective_modifier else 0) - 1) * is_super_effective)))
        np_gain = servant.get_npgain() * servant.get_np_gain_mod()
        np_distribution = servant.get_npdist()
        
        damage_per_hit = [total_damage * value/100 for value in np_distribution]

        cumulative_damage = 0
        for i, hit in enumerate(np_distribution):
            hit_damage = damage_per_hit[i]
            cumulative_damage += hit_damage
            overkill_bonus = 1.5 if cumulative_damage > target.get_hp() else 1
            specific_enemy_modifier = target.np_per_hit_mult

            np_per_hit = (np_gain * card_np_value * (1 + card_mod) * specific_enemy_modifier * overkill_bonus)

            if card_type != 'buster':
                servant.set_npgauge(np_per_hit)

            target.set_hp(hit_damage)
            # print(f"{servant.name} deals {hit_damage} to {target.name} who has {target.get_hp()} hp left and gains {np_per_hit}% np")

            # if target.get_hp() <= 0:
                # print(f"{target.get_name()} has been defeated by hit {i+1}!")

        print(f"{servant.get_name()} attacks {target.get_name()} with Noble Phantasm for {'%.0f' % total_damage} total damage!")
  
    def apply_np_odd_damage(self, servant, target):
        card_damage_value = None
        card_type = servant.get_cardtype()
        card_np_value = 1
        if card_type == 'buster':
            card_damage_value = 1.5
            card_mod = servant.get_b_up()
            enemy_res_mod = target.get_b_resdown()
        elif card_type == 'quick':
            card_damage_value = 0.8
            card_mod = servant.get_q_up()
            enemy_res_mod = target.get_q_resdown()
        elif card_type == 'arts':
            card_damage_value = 1
            card_np_value = 3
            card_mod = servant.get_a_up()
            enemy_res_mod = target.get_a_resdown()

        class_modifier = servant.get_class_multiplier(target.get_class())
        attribute_modifier = servant.get_attribute_modifier(target)
        atk_mod = servant.get_atk_mod()
        enemy_def_mod = target.get_def()
        power_mod = servant.get_power_mod()
        self_damage_mod = 0
        np_damage_mod = servant.get_np_damage_mod()

        # servant applies their own super effective requires a different approach
        # check if the target is in tagetList for musashi
        # if Target1 == 0 that means count number of times ids in the TargetList are in servant.buffs[]
        # if Target1 == 1 that means count number of times ids in the TargetList are in target.buffs[]
        # correction = "Value2" + N * "Correction" to max of N="ParamAddMaxCount"

        # TODO test with allies who count buffs placed on them ,if this doesnt work jsut hard code it cuz lawwdd knows ereshkigal is gonna be ap ain itn the ass

        np_damage_multiplier, \
        np_damage_correction_init,\
        np_correction,\
        np_correction_id ,\
        np_correction_target = servant.get_np_damage_values(np_level=servant.np_level, oc=servant.get_oc_level())
        
        servant_atk = servant.get_atk_at_level() * servant.get_class_base_multiplier()
        is_super_effective = 1
        super_effective_modifier = 1
        if np_correction_target == 1:
            for id in np_correction_id:
                super_effective_modifier += np_correction * target.traits.count(id)
        else:
            for id in np_correction_id:
                cum = 0
                if servant.name == "Super Aoko":
                    for buff in servant.buffs:
                        if buff['buff'] == "Magic Bullet":
                            cum += 1
                    super_effective_modifier += cum * np_correction

        total_damage = (servant_atk * np_damage_multiplier * (card_damage_value * (1 + card_mod - enemy_res_mod)) *
                        class_modifier * attribute_modifier * 0.23 * (1 + atk_mod - enemy_def_mod) *
                        (1 + power_mod + self_damage_mod + np_damage_mod) *
                        (1 + ((super_effective_modifier - 1) * is_super_effective)))
        np_gain = servant.get_npgain() * servant.get_np_gain_mod()
        np_distribution = servant.get_npdist()
        damage_per_hit = [total_damage * value for value in np_distribution]

        cumulative_damage = 0
        for i, hit in enumerate(np_distribution):
            hit_damage = damage_per_hit[i]
            cumulative_damage += hit_damage
            overkill_bonus = 1.5 if cumulative_damage > target.get_hp() else 1
            specific_enemy_modifier = target.np_per_hit_mult  # Adjust based on enemy class and traits

            np_per_hit = (np_gain * card_np_value * (1 + card_mod) * specific_enemy_modifier * overkill_bonus)
            
            if card_type != 'buster':
                servant.set_npgauge(np_per_hit)
            
            target.set_hp(hit_damage)

        print(f"{servant.get_name()} attacks {target.get_name()} with Noble Phantasm for {'%.0f' % total_damage} total damage!")
  