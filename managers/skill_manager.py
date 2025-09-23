import logging

# Configure logging
logging.basicConfig(filename='./outputs/output.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Module-level trigger registry for future extensibility. We prefer
# data-driven detection of trigger semantics (on-hit, end-turn, counter)
# but keep a registry available if specific handlers are needed later.
trigger_registry = {}


def register_trigger(func_id, handler):
    trigger_registry[func_id] = handler


class SkillManager:
    def __init__(self, turn_manager):
        self.tm = turn_manager
        self.gm = self.tm.gm

        # Instance-bound mapping avoids referencing methods before they're defined
        self.effect_functions = {
            'addState': self.apply_add_state,
            'gainNp': self.apply_gain_np,
            'addStateShort': self.apply_add_state_short,
            'shortenSkill': self.apply_cooldown_reduction,
            'addFieldChangeToField': self.add_field_change,
            'transformServant': self.apply_transform,
            'gainMultiplyNp': self.apply_multiply_np,
            'forceInstantDeath': self.apply_self_kill,
            'instantDeath': self.apply_instant_death,
        }

    def _normalize_svals(self, effect):
        svals = effect.get('svals', {})
        if isinstance(svals, list):
            svals = svals[-1] if svals else {}
        return svals or {}

    def extract_state(self, effect):
        svals = self._normalize_svals(effect)

        if effect.get('funcType') == 'gainNp':
            state = {
                'type': 'gainNp',
                'functvals': effect.get('condTarget', []),
                'value': svals.get('Value', 0)
            }
            return state

        if effect.get('funcType') == 'addFieldChangeToField':
            state = {
                'type': 'fieldChange',
                'field_name': svals.get('FieldIndividuality', [None])[0],
                'turns': svals.get('Turn', 0),
            }
            return state

        # Generic buff parsing
        state = {
            'type': 'buff',
            'buff_name': 'Unknown',
            'functvals': effect.get('functvals', []),
            'tvals': [],
            'value': svals.get('Value', 0),
            'turns': svals.get('Turn', 0),
            'svals': svals,
            'count': svals.get('Count', None),
        }

        buffs = effect.get('buffs', [])
        if buffs:
            primary = buffs[0]
            state['buff_name'] = primary.get('name') or primary.get('type') or state['buff_name']
            state['tvals'] = primary.get('tvals', [])

        # Determine trigger_type heuristically from svals and tvals.
        # We avoid hardcoding function ids; instead we tag the buff with a
        # trigger role so callers can run the appropriate logic.
        state['trigger_type'] = self._determine_trigger_type(state)

        return state

    def _determine_trigger_type(self, state):
        svals = state.get('svals', {}) or {}
        tvals = state.get('tvals', []) or []
        name = (state.get('buff_name') or '').lower()

        # Magic-bullet style counters may have an explicit count or be named
        # as a stored counter; check this first before generic Count checks.
        if 'magic bullet' in name or 'bullet' in name or 'counter' in name:
            return 'counter'

        # If the buff contains a TriggeredFuncPosition or a Count it is often
        # a chained/triggered buff that fires later (commonly on-hit for NP
        # triggers). We'll interpret that as 'on-hit' unless other data
        # indicates end-of-turn behavior.
        if 'TriggeredFuncPosition' in svals or 'Count' in svals:
            return 'on-hit'

        # If a Turn is present but no TriggeredFuncPosition, this tends to be
        # an effect that lasts for N turns and may have an end-of-turn hook.
        if state.get('turns'):
            return 'end-turn'

        # Default to 'immediate' meaning the effect is applied at skill use time
        return 'immediate'

    def apply_effect(self, effect, servant, ally_target=None, source_functions=None):
        if not effect.get('funcType'):
            return

        effect_type = effect['funcType']
        target_type = effect.get('funcTargetType')
        condTarget = effect.get('condTarget', [])
        field_req = effect.get('fieldReq', {})

        if ally_target is None:
            ally_target = servant

        # Determine the targets based on target type. Ally-targeting effects
        # should only apply to the frontline (first 3 servants).
        frontline = self.gm.servants[:3]

        if target_type == 'self':
            targets = [servant] if servant is not None else []
        elif target_type == 'enemyAll':
            targets = self.gm.get_enemies()
        elif target_type == 'ptOther':
            if servant is None:
                targets = [ally for ally in frontline if ally != ally_target]
            else:
                targets = [ally for ally in frontline if ally != servant]
        elif target_type == 'ptAll':
            targets = frontline
        elif target_type == 'ptOne':
            targets = [ally_target] if ally_target is not None else []
        else:
            targets = []

        check_cond_target = lambda target: not condTarget or all(trait['id'] in [t for t in target.traits] for trait in condTarget)
        check_field_req = lambda: not field_req or any(field['id'] in [f[0] for f in self.gm.fields] for field in field_req)

        for target in targets:
            if check_cond_target(target) and check_field_req():
                if effect_type in self.effect_functions:
                    # call the bound method
                    try:
                        self.effect_functions[effect_type](effect=effect, target=target)
                    except TypeError:
                        # fallback signature for methods that expect (self, effect, target)
                        self.effect_functions[effect_type](self, effect=effect, target=target)

    def apply_add_state(self, effect=None, target=None):
        state = self.extract_state(effect)
        # include trigger_type metadata on the buff entry
        self.apply_buff(target, state)

    def apply_add_state_short(self, effect=None, target=None):
        state = self.extract_state(effect)
        self.apply_buff(target, state)

    def apply_passive_buffs(self, servant):
        for passive in servant.passives:
            for func in passive.get('functions', []):
                for buff in func.get('buffs', []):
                    state = {
                        'buff_name': buff.get('name', 'Unknown'),
                        'value': func.get('svals', {}).get('Value', 0),
                        'turns': -1,  # Infinite duration
                        'functvals': func.get('functvals', []),
                        'svals': func.get('svals', {}),
                        'count': func.get('svals', {}).get('Count')
                    }
                    state['trigger_type'] = self._determine_trigger_type(state)
                    self.apply_buff(servant, state)

    def apply_buff(self, target, state):
        buff = state.get('buff_name')
        value = state.get('value')
        functvals = state.get('functvals', [])
        tvals = [tval.get('id') for tval in state.get('tvals', [])] if state.get('tvals') else []
        turns = state.get('turns')
        logging.info(f"added buff {buff} to {getattr(target, 'name', '<unknown>')}")

        raw_svals = state.get('svals')
        count = state.get('count')
        buff_entry = {
            'buff': buff,
            'functvals': functvals,
            'value': value,
            'tvals': tvals,
            'turns': turns,
            'svals': raw_svals,
            'count': count,
            'trigger_type': state.get('trigger_type')
        }
        target.buffs.add_buff(buff_entry)

    def run_triggered_buff(self, buff, source_servant, target, card_type=None):
        """Interpret a stored buff's trigger semantics and execute it.

        We try to avoid hardcoding specific function ids. Instead we rely on the
        stored `trigger_type` and the svals/value fields to decide what to do.
        Returns True if a trigger action was executed (so callers may decrement
        a Count if needed).
        """
        trigger_type = buff.get('trigger_type') or (buff.get('svals') and ('TriggeredFuncPosition' in buff.get('svals')) and 'on-hit')
        svals = buff.get('svals', {}) or {}
        logging.info(f"run_triggered_buff check: buff={buff.get('buff')} trigger_type={trigger_type} card_type={card_type} svals={svals} tvals={buff.get('tvals')} count={buff.get('count')}")

        # Respect card-type restrictions if present
        if card_type and buff.get('tvals'):
            card_map = {'buster': 4002, 'arts': 4001, 'quick': 4003}
            required_id = card_map.get(card_type)
            if required_id and required_id not in buff.get('tvals'):
                return False

        # Generic on-hit behavior: many datasets encode a chained trigger that
        # grants NP or charges a counter. Detect common patterns and apply.
        if trigger_type == 'on-hit':
            # Common NP-grant patterns: svals.Value2 or buff['value'] holds a
            # small number representing percent (e.g., 10 -> 10%).
            val2 = svals.get('Value2')
            grant = None
            if isinstance(val2, (int, float)) and abs(val2) < 1000:
                grant = float(val2)
            elif isinstance(buff.get('value'), (int, float)) and abs(buff.get('value')) < 1000:
                grant = float(buff.get('value'))
            else:
                v = svals.get('Value')
                if isinstance(v, (int, float)) and abs(v) < 1000:
                    grant = float(v)

            if grant:
                # The codebase represents NP gauge as a percentage (0-100).
                # `grant` is already expressed in percent (e.g. 10 -> 10%),
                # so pass it through directly to set_npgauge which adds the
                # percentage value to the servant's np_gauge. Previously this
                # divided by 100 here which produced tiny fractional increases
                # and prevented NPs from charging as expected.
                logging.info(f"run_triggered_buff: granting NP {grant}% to {getattr(source_servant,'name',None)}")
                source_servant.set_npgauge(grant)
                return True

            # Counter-style on-hit: if no numeric grant but Count exists, we
            # treat this as a stack-consuming effect with no direct grant here.
            if isinstance(buff.get('count'), int) or ('Count' in svals):
                logging.info(f"run_triggered_buff: detected counter-style trigger for {buff.get('buff')}")
                # nothing to do here at generic level; caller may decrement
                return True

            return False

        # End-turn triggers should be handled by buff processing; not run here
        if trigger_type == 'end-turn':
            return False

        # Counter objects do not auto-trigger on hit
        if trigger_type == 'counter':
            return False

        # Immediate effects should not present here as triggers
        return False

    def skill_available(self, servant, skill_num):
        return servant.skills.skill_available(skill_num)

    def use_mystic_code_skill(self, skill_num, target=None):
        mystic_code = self.gm.mc
        if not hasattr(mystic_code, 'cooldowns'):
            mystic_code.cooldowns = {0: 0, 1: 0, 2: 0}
        if mystic_code.cooldowns[skill_num] == 0:
            skill = mystic_code.get_skill_by_num(skill_num)
            print(f"Using Mystic Code skill: {skill['name']}")
            for effect in skill['functions']:
                # Always use the last svals if it's a list
                svals = effect.get('svals', [])
                if isinstance(svals, list) and svals:
                    effect['svals'] = svals[-1]
                # Pass None as servant; apply_effect will handle targeting
                self.apply_effect(effect, None, target)
            mystic_code.cooldowns[skill_num] = skill['cooldown']
        else:
            print(f"Mystic Code skill {skill_num} is on cooldown: {mystic_code.cooldowns[skill_num]} turns remaining")

    def use_skill(self, servant, skill_num, target=None):
        logging.info(f"BEGINNING USE_SKILL OF {servant.name}' SKILL {servant.skills.get_skill_by_num(skill_num+1)}")
        skill_num += 1
        if self.skill_available(servant, skill_num):
            skill = servant.skills.get_skill_by_num(skill_num)
            servant.skills.set_skill_cooldown(skill_num)
            logging.info(f"Skill {skill_num} used. Cooldown remaining: {servant.skills.get_skill_cooldowns()[skill_num]} turns")
            logging.info(f"Applying {servant.name}'s {servant.skills.get_skill_by_num(skill_num)}")
            for effect in skill['functions']:
                self.apply_effect(effect, servant, target)

        else:
            print(f"{servant.name} skill {skill_num} is on cooldown: {servant.skills.cooldowns[skill_num]} turns remaining")
            return False

    # TODO check API call to see what indexing is necessary for swapping
    def swap_servants(self, frontline_idx, backline_idx):
        # Convert to 0-based indices
        frontline_index = frontline_idx - 1
        backline_index = backline_idx + 2

        # Check if indices are valid
        if frontline_index < 0 or frontline_index > 2 or backline_index < 3 or backline_index >= len(self.gm.servants):
            print(f"Invalid swap indices: frontline {frontline_idx}, backline {backline_idx}")
            return False

        # Print before swap for clarity
        print(f"Swapping frontline servant {frontline_idx}:{self.gm.servants[frontline_index].name} (ID {self.gm.servants[frontline_index].id}) "
            f"with backline servant {backline_idx}:{self.gm.servants[backline_index].name} (ID {self.gm.servants[backline_index].id})")

        self.gm.swap_servants(frontline_index, backline_index)
        return True

    def apply_gain_np(self, effect=None, target=None):
        # Prefer normalized parameters produced by NP parser
        params = effect.get('parameters', {}) or {}
        raw_val = None

        if 'value' in params:
            raw_val = params.get('value')
        else:
            # Try to extract from svals, handling NP-normalized structure
            svals = effect.get('svals', {}) or {}
            if isinstance(svals, dict):
                base = svals.get('base')
                if isinstance(base, list) and base:
                    last = base[-1]
                    if isinstance(last, dict) and 'Value' in last:
                        raw_val = last.get('Value')
                elif 'Value' in svals:
                    raw_val = svals.get('Value')
            elif isinstance(svals, list) and svals:
                last = svals[-1]
                if isinstance(last, dict) and 'Value' in last:
                    raw_val = last.get('Value')

        if not raw_val:
            return False

        # Normalize units: many dataset values encode percent as value/100 (e.g. 2000 -> 20%),
        # while some sources may already be expressed as percent (e.g. 20). Heuristically
        # convert large integers by dividing by 100.
        try:
            rv = float(raw_val)
        except Exception:
            return False

        if abs(rv) > 100:  # e.g. 2000 -> 20
            percent = rv / 100.0
        else:
            percent = rv

        logging.info(f"apply_gain_np: raw={raw_val} percent={percent} applied to {getattr(target,'name',None)}")
        target.set_npgauge(percent)

    def apply_cooldown_reduction(self, effect, target):
        target.skills.decrement_cooldowns(effect.get('svals', {}).get('Value'))

    def apply_transform(self, effect, target):
        # TODO how do we parse transform effects?
        return

    def add_field_change(self, effect, target):
        state = self.extract_state(effect)
        self.add_field(state)

    def apply_multiply_np(self, effect, target):
        # Multiply existing NP gauge by a factor. Parameter encoding varies;
        # common format uses permille (1000 -> 1.0). Read parameters or svals.
        params = effect.get('parameters', {}) or {}
        raw_val = params.get('value') if 'value' in params else None

        if raw_val is None:
            svals = effect.get('svals', {}) or {}
            if isinstance(svals, dict):
                base = svals.get('base')
                if isinstance(base, list) and base:
                    last = base[-1]
                    raw_val = last.get('Value') if isinstance(last, dict) else None
                else:
                    raw_val = svals.get('Value')
            elif isinstance(svals, list) and svals:
                last = svals[-1]
                raw_val = last.get('Value') if isinstance(last, dict) else None

        if raw_val is None:
            return False

        try:
            rv = float(raw_val)
        except Exception:
            return False

        # If value looks like permille (e.g. 1000 == 1.0), divide by 1000
        if abs(rv) > 10:
            multiplier = rv / 1000.0
        else:
            multiplier = rv

        old = getattr(target, 'np_gauge', None)
        if old is None:
            old = target.get_npgauge()
        new = old * multiplier
        logging.info(f"apply_multiply_np: multiplier={multiplier} old={old} new={new} for {getattr(target,'name',None)}")
        # Set absolute gauge
        target.np_gauge = new

    def apply_self_kill(self, effect, target):
        target.kill = True

    def apply_instant_death(self, effect, target):
        if effect.get('funcType') == "instantDeath":
            deathchance = effect.get('svals', {}).get('Rate', 0) / 1000
            for i, s in enumerate(self.gm.servants[:3]):
                if s.id == 297:
                    deathchance *= 1.2
                if s.id == 92:
                    deathchance *= 2
            deathrate = getattr(target, 'death_rate', 0) / 1000

            if deathchance * deathrate > 0.5:
                target.set_hp(target.get_hp())

