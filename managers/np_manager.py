import logging

# Module logger (Driver.py will configure handlers)
logger = logging.getLogger(__name__)

# needed to increase consecutivly used NPs OC levels
# should be static 
np_oc_1_turn = {'funcType': 'addStateShort', 'funcTargetType': 'ptAll', 'functvals': [], 'fieldReq': [], 'condTarget': [], 'svals': {'Rate': 1000, 'Turn': 1, 'Count': 1, 'Value': 1}, 'buffs': [{'name': 'Overcharge Lv. Up', 'functvals': '', 'tvals': [], 'svals': None, 'value': 0, 'turns': 1}]}

class npManager:
    def __init__(self, skill_manager):
        self.sm = skill_manager
        self.tm = self.sm.tm
        self.gm = self.tm.gm

    def _consume_magic_bullets(self, servant, count=10):
        """Remove up to `count` Magic Bullet buffs (individuality 2885) from servant."""
        removed = 0
        new_buffs = []
        for buff in servant.buffs.buffs:
            if (
                buff.get('buff') == 'Magic Bullet'
                and 2885 in buff.get('tvals', [])
                and removed < count
            ):
                removed += 1
                continue  # skip (remove) this buff
            new_buffs.append(buff)
        servant.buffs.buffs = new_buffs
        logger.debug(f"[NPManager] Consumed {removed} Magic Bullets from {servant.name} after NP.")

    def use_np(self, servant):
        # Compact INFO: log NP usage; verbose/debug will include detailed internals
        logger.info(f"NP used: id={getattr(servant,'id',None)} name={getattr(servant,'name',None)} np_gauge={servant.stats.get_npgauge()}")
                

        if servant.stats.get_npgauge() >= 99:
            # Cap overcharge up to 2 extra (for a max of 3 total, as in FGO)
            oc_extra = min(2, max(0, int(servant.stats.get_npgauge() // 100) - 1))
            if oc_extra > 0:
                print(f"Servant {servant.name} has {servant.np_gauge} NP% and can apply OVERCHARGE UP 1 * {oc_extra} times (capped at 2 extra)")
                for i in range(oc_extra):
                    self.sm.apply_effect(np_oc_1_turn, servant, source_skill_num='NP')
                    servant.buffs.process_servant_buffs()

            functions = servant.nps.get_np_values(servant.stats.get_np_level(), servant.stats.get_oc_level())
            servant.stats.set_npgauge(0)  # Reset NP gauge after use
            
            # initialize maintarget to None and max_hp to 0
            # This is to ensure that the maintarget is set to the enemy with the highest HP next
            maintarget = None
            max_hp = 0

            # Identify the enemy with the highest HP
            for enemy in self.gm.get_enemies():
                if enemy.hp > max_hp:
                    max_hp = enemy.hp
                    maintarget = enemy
                    
            # Apply effects and damage
            for i, func in enumerate(functions):
                if func['funcType'] in ['damageNp', 'damageNpPierce']:
                    logger.debug(f"firing basic ST or AOE NP of servant {servant}")
                    # if non-SE NP check for AoE or ST    
                    if (func['funcTargetType'] == 'enemyAll'):
                        servant.buffs.process_servant_buffs()
                        for enemy in self.gm.get_enemies():
                            enemy.buffs.process_enemy_buffs()
                            self.apply_np_damage(servant, enemy)
                    
                    elif (func['funcTargetType'] == 'enemy'):
                        servant.buffs.process_servant_buffs()
                        for enemy in self.gm.get_enemies():
                            enemy.buffs.process_enemy_buffs()
                        self.apply_np_damage(servant, maintarget)

                elif func['funcType'] in ['damageNpIndividualSum', 'damageNpStateIndividualFix', 'damageNpIndividual']:
                    # SE NPs
                    logger.debug(f"firing SE NP of servant {servant}")
                    if (func['funcTargetType'] == 'enemyAll'):
                        servant.buffs.process_servant_buffs()
                        for enemy in self.gm.get_enemies():
                            enemy.buffs.process_enemy_buffs()
                            self.apply_np_odd_damage(servant, enemy)
 
                    elif (func['funcTargetType'] == 'enemy'):
                        servant.buffs.process_servant_buffs()
                        for enemy in self.gm.get_enemies():
                            enemy.buffs.process_enemy_buffs()
                        self.apply_np_odd_damage(servant, maintarget)
                
                else:
                    # non-damaging NP effects - pass source metadata so apply_buff can label the source
                    if func['funcTargetType'] == 'enemyAll':
                        self.sm.apply_effect(func, servant, source_skill_num='NP')
                    if func['funcTargetType'] == 'enemy':
                        self.sm.apply_effect(func, maintarget, source_skill_num='NP')
                    if func['funcTargetType'] == 'self':
                        self.sm.apply_effect(func, servant, source_skill_num='NP')
                    if func['funcTargetType'] == 'ptAll':
                        self.sm.apply_effect(func, servant, source_skill_num='NP')
            for s in self.gm.servants[0:2]:
                if s is not servant:
                    self.sm.apply_effect(np_oc_1_turn, s)
            # Special-case: Aoko transforms on NP use. Instrument and call transform.
            if servant.id == 413:
                logger.info(f"Aoko NP use detected: id={servant.id}, name={servant.name}, np_gauge={servant.stats.get_npgauge()}")
                try:
                    self.gm.transform_aoko(aoko_buffs=servant.buffs.buffs, aoko_cooldowns=servant.skills.cooldowns)
                    logger.info("transform_aoko called successfully")
                except Exception as e:
                    logger.exception(f"transform_aoko raised exception: {e}")
            # Remove up to 10 Magic Bullets after NP for Aoko/Super Aoko
            if getattr(servant, 'id', None) == 4132:
                self._consume_magic_bullets(servant, count=10)

            # If the NP had side-effects that mark the caster for death (self-sacrifice)
            # handle removal immediately so the effect is visible to the rest of the command flow.
            if getattr(servant, 'kill', False):
                logger.info(f"Servant {servant.name} flagged for kill after NP; removing from party")
                try:
                    idx = self.gm.servants.index(servant)
                except ValueError:
                    idx = -1

                if idx != -1:
                    # If frontline, swap in a backline servant when possible
                    if idx < 3 and len(self.gm.servants) > 3:
                        swap = self.gm.servants[3]
                        self.gm.servants[idx] = swap
                        self.gm.servants.pop(3)
                        logger.info(f"Replaced dead frontline servant with backline {swap.name}")
                    else:
                        # Otherwise just remove the servant from the list
                        removed = self.gm.servants.pop(idx)
                        logger.info(f"Removed servant {removed.name} from party")

                # Reset the flag
                servant.kill = False

            logger.debug("END NP LOG")
        else:
            print(f"{servant.name} does not have enough NP gauge: {servant.get_npgauge()}")

    def apply_np_damage(self, servant, target):
        # Card type and modifiers
        card_type = servant.nps.card
        card_damage_value = None
        card_damage_mod = 0.0
        enemy_res_mod = 0.0
        card_np_value = 1
        card_eff_mod = 0.0
        if card_type == 'buster':
            card_damage_value = 1.5
            card_damage_mod = servant.stats.get_buster_card_damage_up()
            enemy_res_mod = target.get_b_resdown()
            card_eff_mod = servant.stats.get_b_up()
        elif card_type == 'quick':
            card_damage_value = 0.8
            card_damage_mod = servant.stats.get_quick_card_damage_up()
            enemy_res_mod = target.get_q_resdown()
            card_eff_mod = servant.stats.get_q_up()
        elif card_type == 'arts':
            card_damage_value = 1
            card_np_value = 3
            card_damage_mod = servant.stats.get_arts_card_damage_up()
            enemy_res_mod = target.get_a_resdown()
            card_eff_mod = servant.stats.get_a_up()

        class_modifier = servant.stats.get_class_multiplier(target.get_class())
        attribute_modifier = servant.stats.get_attribute_modifier(target)
        atk_mod = servant.stats.get_atk_mod()
        enemy_def_mod = target.get_def()
        generic_pmod = servant.stats.get_damage_up_mod()
        power_mod = servant.stats.get_power_mod(target)
        np_damage_mod = servant.stats.get_np_damage_mod()

        np_damage_multiplier, np_damage_correction_init, np_correction, np_correction_id, np_correction_target = servant.nps.get_np_damage_values(np_level=servant.stats.get_np_level(), oc=servant.stats.get_oc_level())

        # For normal NPs, just use the base multiplier (no SE logic)
        se_multiplier = 1

        servant_atk = servant.stats.get_base_atk()
        # Verbose: print all buffs and modifiers for debugging
        logger.debug(f"Servant ATK: {servant_atk} | NP Damage Multiplier: {np_damage_multiplier} | Card Damage Value: {card_damage_value} | Card Damage Mod: {card_damage_mod} | Enemy Res Mod: {enemy_res_mod} | Class Modifier: {class_modifier} | Attribute Modifier: {attribute_modifier} | ATK Mod: {atk_mod} | Enemy Def Mod: {enemy_def_mod} | Power Mod: {power_mod} + generic pmod: {generic_pmod} | NP Damage Mod: {np_damage_mod} | SE Multiplier: {se_multiplier}")

        # FGO-accurate: Card Mod is multiplicative with card value, Card Damage Mod is additive
        total_damage = (servant_atk * np_damage_multiplier * se_multiplier * (card_damage_value * (1 + card_damage_mod + card_eff_mod - enemy_res_mod)) *
                        class_modifier * attribute_modifier * 0.23 * (1 + atk_mod - enemy_def_mod) *
                        (1 + np_damage_mod + generic_pmod + power_mod))

        # Record initial HP before damage
        initial_hp = getattr(target, 'initial_hp', None)
        if initial_hp is None:
            initial_hp = target.get_hp()
            setattr(target, 'initial_hp', initial_hp)

        servant.stats.set_npgauge(0)
        np_gain = servant.stats.get_npgain() * servant.stats.get_np_gain_mod()
        np_distribution = servant.stats.get_npdist()
        damage_per_hit = [total_damage * value/100 for value in np_distribution]

        cumulative_damage = 0
        for i, hit in enumerate(np_distribution):
            hit_damage = damage_per_hit[i]
            cumulative_damage += hit_damage
            overkill_bonus = 1.5 if cumulative_damage > target.get_hp() else 1
            specific_enemy_modifier = target.np_per_hit_mult

            np_per_hit = (np_gain * card_np_value * (1 + card_eff_mod) * specific_enemy_modifier * overkill_bonus)

            # Trigger handling: delegate to SkillManager.run_triggered_buff which
            # understands the preserved svals/count and a registry of trigger
            # handlers. This avoids hardcoding behaviors here and centralizes
            # trigger semantics in SkillManager.
            try:
                for buff in list(servant.buffs.buffs):
                    # let SkillManager decide if the buff should run for this card
                    ran = False
                    try:
                        ran = self.sm.run_triggered_buff(buff=buff, source_servant=servant, target=target, card_type=card_type, is_np=True)
                    except Exception:
                        ran = False
                    # If the triggered handler ran and the buff has a finite count,
                    # decrement and drop if depleted. Handlers may also handle this.
                    if ran:
                        # Only treat Count as a finite counter if it's a
                        # non-negative integer. Some svals use -1 as a sentinel
                        # meaning 'not a counter' and should be ignored here.
                        sval_count = (buff.get('svals') or {}).get('Count')
                        count = buff.get('count') if isinstance(buff.get('count'), int) else (sval_count if isinstance(sval_count, int) and sval_count >= 0 else None)
                        if isinstance(count, int):
                            new_count = count - 1
                            buff['count'] = new_count
                            if new_count <= 0:
                                try:
                                    servant.buffs.buffs.remove(buff)
                                except ValueError:
                                    pass
            except Exception:
                pass

            target.set_hp(hit_damage)
            logger.debug(f"{servant.name} deals {hit_damage} to {target.name} who has {target.get_hp()} hp left")
            servant.stats.set_npgauge(servant.stats.get_npgauge() + np_per_hit)
            if target.get_hp() <= 0:
                logger.info(f"{target.get_name()} has been defeated by hit {i+1}!")

        # Record damage summary
        dmg_record = {
            'servant': servant.name,
            'damage': total_damage,
            'initial_hp': initial_hp,
            'current_hp': target.get_hp(),
            'fraction_remaining': round(target.get_hp()/initial_hp, 4) if initial_hp else None
        }
        logger.info(f"Damage record: {dmg_record}")
        print(f"{servant.name} deals {total_damage} to {target.name} who has {target.get_hp()} hp left and gains {np_per_hit}% np | HP: {target.get_hp()}/{initial_hp} | Fraction Remaining: {dmg_record['fraction_remaining']}")

    def apply_np_odd_damage(self, servant, target):
        card_damage_value = None
        card_type = servant.nps.card
        card_np_value = 1
        
        if card_type == 'buster':
            card_damage_value = 1.5
            card_eff_mod = servant.stats.get_b_up()
            card_damage_mod = servant.stats.get_buster_card_damage_up()
            enemy_res_mod = target.get_b_resdown()
        elif card_type == 'quick':
            card_damage_value = 0.8
            card_eff_mod = servant.stats.get_q_up()
            card_damage_mod = servant.stats.get_quick_card_damage_up()
            enemy_res_mod = target.get_q_resdown()
        elif card_type == 'arts':
            card_damage_value = 1
            card_np_value = 3
            card_eff_mod = servant.stats.get_a_up()
            card_damage_mod = servant.stats.get_arts_card_damage_up()
            enemy_res_mod = target.get_a_resdown()
        
        class_modifier = servant.stats.get_class_multiplier(target.get_class())
        attribute_modifier = servant.stats.get_attribute_modifier(target)
        atk_mod = servant.stats.get_atk_mod()
        enemy_def_mod = target.get_def()
        generic_pmod = servant.stats.get_damage_up_mod()
        power_mod = servant.stats.get_power_mod(target)
        np_damage_mod = servant.stats.get_np_damage_mod()
        
        # Cumulative Damage Logic

        np_damage_multiplier, np_damage_correction_init, np_correction, np_correction_id, np_correction_target = servant.nps.get_np_damage_values(np_level=servant.stats.get_np_level(), oc=servant.stats.get_oc_level())
        servant_atk = servant.stats.get_base_atk()

        # Super Effective logic for SE NPs (damageNpIndividualSum, etc)
        se_multiplier = 1.0
        if np_correction is not None and np_correction_id is not None:
            individuality_ids = np_correction_id if isinstance(np_correction_id, list) else [np_correction_id]
            if np_correction_target == 0:
                # Count on self buffs (should check both buffs and traits)
                count = 0
                for indv in individuality_ids:
                    # Count buffs with tvals/vals matching individuality
                    c_buffs = servant.buffs.count_buffs_by_individuality(indv)
                    # Also count static traits if needed (legacy logic)
                    c_traits = 0
                    if hasattr(servant, 'traits'):
                        c_traits = servant.traits.count(indv)
                    logger.debug(f"[SE NP] Counting self buffs for individuality {indv}: buffs={c_buffs}, traits={c_traits}")
                    count += c_buffs + c_traits
                logger.debug(f"[SE NP] Total self buff+trait count for {individuality_ids}: {count}")
            elif np_correction_target == 1:
                # Count on enemy buffs/traits
                count = 0
                for indv in individuality_ids:
                    c_buffs = target.buffs.count_buffs_by_individuality(indv)
                    c_traits = 0
                    if hasattr(target, 'traits'):
                        c_traits = target.traits.count(indv)
                    logger.debug(f"[SE NP] Counting enemy buffs/traits for individuality {indv}: buffs={c_buffs}, traits={c_traits}")
                    count += c_buffs + c_traits
                logger.debug(f"[SE NP] Total enemy buff+trait count for {individuality_ids}: {count}")
            else:
                logger.warning(f"[SE NP] Unknown Target value for SE NP: {np_correction_target}")
                count = 0

            # Cap count if ParamAddMaxCount present
            param_add_max = None
            np_entry = servant.nps._get_np_entry()
            for func in np_entry.get('functions', []):
                if func.get('funcType') == 'damageNpIndividualSum':
                    svals = func.get('svals', [])
                    if svals:
                        svals0 = svals[servant.stats.get_np_level()-1] if servant.stats.get_np_level()-1 < len(svals) else svals[-1]
                        param_add_max = svals0.get('ParamAddMaxCount')
                        break
            if param_add_max is not None:
                count = min(count, param_add_max)
                logger.debug(f"[SE NP] Capped count to ParamAddMaxCount={param_add_max}")
            se_multiplier = max(np_damage_correction_init, 1 + np_correction * count)
            logger.debug(f"Super Effective NP: individuality_ids={individuality_ids}, count={count}, correction={np_correction}, base={np_damage_multiplier}, min={np_damage_correction_init}, se_multiplier={se_multiplier}, Target={np_correction_target}")
        else:
            se_multiplier = 1

        # Verbose: print all buffs and modifiers for debugging
        logger.debug(f"Servant ATK: {servant_atk} | NP Damage Multiplier: {np_damage_multiplier} | initial np correction amount: {np_damage_correction_init} | np correction: {np_correction} | what id is used for the correction {np_correction_id} | target or buff that effects np_correction amounts:{np_correction_target} | Card Damage Value: {card_damage_value} | Card Mod: {card_eff_mod} | Card Damage Mod: {card_damage_mod} | Enemy Res Mod: {enemy_res_mod} | Class Modifier: {class_modifier} | Attribute Modifier: {attribute_modifier} | ATK Mod: {atk_mod} | Enemy Def Mod: {enemy_def_mod} | Power Mod: {power_mod} + generic pmod {generic_pmod} | NP Damage Mod: {np_damage_mod} | SE Multiplier: {se_multiplier}")

        # FGO-accurate: Card Mod is multiplicative with card value, Card Damage Mod is additive
        total_damage = (servant_atk * np_damage_multiplier * se_multiplier * (card_damage_value * (1 + card_damage_mod + card_eff_mod - enemy_res_mod)) *
                        class_modifier * attribute_modifier * 0.23 * (1 + atk_mod - enemy_def_mod) *
                        (1 + np_damage_mod  + generic_pmod + power_mod))

        logger.info(f"Total Damage: {total_damage}")

        np_gain = servant.stats.get_npgain() * servant.stats.get_np_gain_mod()
        np_distribution = servant.stats.get_npdist()
        damage_per_hit = [total_damage * value/100 for value in np_distribution]

        cumulative_damage = 0
        for i, hit in enumerate(np_distribution):
            hit_damage = damage_per_hit[i]
            cumulative_damage += hit_damage
            overkill_bonus = 1.5 if cumulative_damage > target.get_hp() else 1
            specific_enemy_modifier = target.np_per_hit_mult

            np_per_hit = (np_gain * card_np_value * (1 + card_eff_mod) * specific_enemy_modifier * overkill_bonus)

            # Trigger handling: delegate to SkillManager.run_triggered_buff which
            # understands the preserved svals/count and a registry of trigger
            # handlers. This avoids hardcoding behaviors here and centralizes
            # trigger semantics in SkillManager.
            try:
                for buff in list(servant.buffs.buffs):
                    # let SkillManager decide if the buff should run for this card
                    ran = False
                    try:
                        ran = self.sm.run_triggered_buff(buff=buff, source_servant=servant, target=target, card_type=card_type)
                    except Exception:
                        ran = False
                    # If the triggered handler ran and the buff has a finite count,
                    # decrement and drop if depleted. Handlers may also handle this.
                    if ran:
                        count = buff.get('count') or (buff.get('svals') or {}).get('Count')
                        if isinstance(count, int):
                            new_count = count - 1
                            buff['count'] = new_count
                            if new_count <= 0:
                                try:
                                    servant.buffs.buffs.remove(buff)
                                except ValueError:
                                    pass
            except Exception:
                pass

            target.set_hp(hit_damage)
            logger.debug(f"{servant.name} deals {hit_damage} to {target.name} who has {target.get_hp()} hp left")
            servant.stats.set_npgauge(np_per_hit)

            if target.get_hp() <= 0:
                logger.info(f"{target.get_name()} has been defeated by hit {i+1}!")
        print(f"{servant.stats.get_name()} attacks {target.get_name()} with Noble Phantasm for {'%.0f' % total_damage} total damage! {target.get_name()} is left with {target.hp} hp")
        
