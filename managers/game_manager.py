from .Quest import Quest
from units.Servant import Servant
from .MysticCode import MysticCode
import copy
import logging

# Configure logging
logging.basicConfig(filename='./outputs/output.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

class GameManager:
    def __init__(self, servant_init_dicts, quest_id, mc_id, gm_copy=None):
        self.servant_init_dicts = servant_init_dicts  # List of dicts
        self.quest_id = quest_id
        self.mc_id = mc_id
        self.servants = [Servant(**params) for params in self.servant_init_dicts]
        self.mc = MysticCode(mc_id)
        self.fields = []
        self.quest = None  # Initialize the Quest instance
        self.wave = 1
        self.total_waves = 0
        self.enemies = []
        self.init_quest()
        if any(servant['collectionNo'] == 413 for servant in servant_init_dicts):
            # TODO if aoko is in the team init her super form with 
            #   Servant(**params) for params in self.servant_init_dicts for aoko's params only
            self.saoko = Servant(collectionNo=4132)

    def team_repr(self):
        repr_strings = []
        for idx, servant in enumerate(self.servants):
            repr_strings.append(f"Position {idx + 1}: {servant.name} {servant}")
        return "\n".join(repr_strings)

    def reset_servants(self):
        self.servants = [Servant(**params) for params in self.servant_init_dicts]

    def add_field(self, state):
        name = state.get('field_name', 'Unknown')
        turns = state.get('turns', 0)
        self.fields.append([name, turns])

    def reset(self):
        self.reset_servants()
        self.fields = []

    def swap_servants(self, frontline_idx, backline_idx):
        self.servants[frontline_idx], self.servants[backline_idx] = self.servants[backline_idx], self.servants[frontline_idx]

    def change_ascension(self, servant_idx, new_ascension):
        # TODO similar to aoko exchange character with different ascension and copy over buffs, cooldowns, np gauge
        return


    # updated
    def transform_aoko(self, aoko_buffs, aoko_cooldowns, aoko_np_gauge=None):
        print("What? \nAoko is transforming!")
        servants_list = [servant.name for servant in self.servants]
        logging.info(f"servants are: {servants_list}")
        for i, servant in enumerate(self.servants):
            if servant.id == 413:
                # Gather all relevant init parameters from the original Aoko
                init_kwargs = dict(
                    collectionNo=4132,  # transformed Aoko
                    ascension=getattr(servant, 'ascension', 4),
                    lvl=getattr(servant, 'lvl', 0),
                    np=getattr(servant, 'np_level', 1),
                    oc=getattr(servant, 'oc_level', 1),
                    atkUp=getattr(servant, 'user_atk_mod', 0),
                    busterUp=getattr(servant, 'user_b_up', 0),
                    artsUp=getattr(servant, 'user_a_up', 0),
                    quickUp=getattr(servant, 'user_q_up', 0),
                    damageUp=getattr(servant, 'user_damage_mod', 0),
                    npUp=getattr(servant, 'user_np_damage_mod', 0),
                    attack=getattr(servant, 'bonus_attack', 0),
                    append_5=True,  # preserve default
                    busterDamageUp=getattr(servant, 'user_buster_damage_up', 0),
                    quickDamageUp=getattr(servant, 'user_quick_damage_up', 0),
                    artsDamageUp=getattr(servant, 'user_arts_damage_up', 0)
                )
                # Create a fresh transformed Aoko instance with copied parameters
                transformed = Servant(**init_kwargs)
                # Deepcopy buffs into a flat list and preserve permanent buffs (turns == -1).
                import copy as _copy
                all_buffs = []
                if isinstance(aoko_buffs, dict):
                    # flatten dict-of-lists into a single list and deepcopy all dict buffs
                    for buff_list in aoko_buffs.values():
                        for buff in (buff_list or []):
                            if isinstance(buff, dict):
                                all_buffs.append(_copy.deepcopy(buff))
                else:
                    # aoko_buffs is a list (legacy): copy all dict entries
                    all_buffs = [_copy.deepcopy(buff) for buff in (aoko_buffs or []) if isinstance(buff, dict)]

                # Preserve owner references where present -> point to new transformed instance
                for buff in all_buffs:
                    if 'owner' in buff:
                        buff['owner'] = transformed

                # Diagnostic: log how many incoming buffs are missing explicit source metadata
                try:
                    missing_source = [b for b in all_buffs if not b.get('source')]
                    logging.info(f"transform_aoko: incoming aoko_buffs total={len(all_buffs)} missing_source_count={len(missing_source)}")
                    # Log a short preview of missing entries
                    for b in missing_source[:20]:
                        logging.info(f"transform_aoko: missing_source_preview: buff={b.get('buff')} value={b.get('value')} turns={b.get('turns')} keys={list(b.keys())}")
                    # Also log counts by buff name and preview Arts Up entries explicitly
                    try:
                        from collections import Counter
                        name_counts = Counter([b.get('buff', '<unknown>') for b in all_buffs])
                        logging.info(f"transform_aoko: buff_name_counts={dict(name_counts)}")
                        arts_up_pre = [b for b in all_buffs if (b.get('buff') or '').lower() == 'arts up']
                        logging.info(f"transform_aoko: arts_up_incoming_count={len(arts_up_pre)}")
                        for b in arts_up_pre[:20]:
                            logging.info(f"transform_aoko: arts_up_preview incoming: value={b.get('value')} turns={b.get('turns')} source={b.get('source')} keys={list(b.keys())}")
                    except Exception as e:
                        logging.exception(f"transform_aoko nested diagnostics failed: {e}")
                except Exception as e:
                    logging.exception(f"transform_aoko diagnostic logging failed: {e}")

                # Assign flattened list to transformed.buffs.buffs (Buffs expects a list)
                transformed.buffs.buffs = all_buffs

                # Diagnostic: after assigning, log what the transformed instance contains for Arts Up
                try:
                    arts_up_after = [b for b in transformed.buffs.buffs if (b.get('buff') or '').lower() == 'arts up']
                    logging.info(f"transform_aoko: arts_up_after_count={len(arts_up_after)}")
                    for b in arts_up_after[:20]:
                        logging.info(f"transform_aoko: arts_up_preview after assign: value={b.get('value')} turns={b.get('turns')} source={b.get('source')} keys={list(b.keys())}")
                except Exception as e:
                    logging.exception(f"transform_aoko post-assign diagnostics failed: {e}")

                # Snapshot the pre-assign buff signatures so we can detect any loss after processing
                try:
                    def _sig(b):
                        return (str(b.get('buff')), float(b.get('value') or 0), int(b.get('turns') or -1), str(b.get('source') or ''), str(b.get('display_value') or ''))
                    pre_sigs = [_sig(b) for b in all_buffs]
                except Exception:
                    pre_sigs = []

                # Only process buffs for correct stacking (do NOT re-apply passives)
                if hasattr(transformed.buffs, 'process_servant_buffs'):
                    transformed.buffs.process_servant_buffs()

                # After processing, compare signatures and log any missing entries
                try:
                    post_sigs = []
                    for b in getattr(transformed.buffs, 'buffs', []):
                        try:
                            post_sigs.append(_sig(b))
                        except Exception:
                            post_sigs.append((str(b.get('buff')), float(b.get('value') or 0), int(b.get('turns') or -1), str(b.get('source') or ''), str(b.get('display_value') or '')))

                    missing_after = [s for s in pre_sigs if s not in post_sigs]
                    added_after = [s for s in post_sigs if s not in pre_sigs]
                    logging.info(f"transform_aoko: pre_count={len(pre_sigs)} post_count={len(post_sigs)} missing_after_count={len(missing_after)} added_after_count={len(added_after)}")
                    if missing_after:
                        for s in missing_after[:50]:
                            logging.info(f"transform_aoko: MISSING AFTER PROCESS: buff={s[0]} value={s[1]} turns={s[2]} source={s[3]} display={s[4]}")
                    if added_after:
                        for s in added_after[:50]:
                            logging.info(f"transform_aoko: ADDED AFTER PROCESS: buff={s[0]} value={s[1]} turns={s[2]} source={s[3]} display={s[4]}")
                except Exception as e:
                    logging.exception(f"transform_aoko post-process comparison failed: {e}")
                transformed.skills.cooldowns = copy.deepcopy(aoko_cooldowns)
                # NP gauge resets to 0 by default (FGO-accurate), but allow override if explicitly provided
                if aoko_np_gauge is not None:
                    transformed.np_gauge = aoko_np_gauge
                # Replace in the party
                self.servants[i] = transformed
                print(f"Contratulations! Your 'Aoko Aozaki' transformed into '{transformed.name}' ")
        servants_list = [servant.name for servant in self.servants]
        logging.info(f"servants are: {servants_list}")

    
    
    def init_quest(self):
        self.quest = Quest(self.quest_id)
        self.total_waves = self.quest.total_waves
        self.enemies = self.quest.get_wave(self.wave)  # Set the initial wave enemies

    def get_next_wave(self):
        try:
            self.wave += 1
            next_wave = self.quest.get_wave(self.wave)  # Fetch the next wave
            self.enemies = next_wave  # Update self.enemies with the new wave
            print(f"Advancing to wave {self.wave}")  # Debug statement
        except StopIteration:
            print("All waves completed. Ending program.")
            exit(0)  # Ends the program
        return 

    def get_enemies(self):
        return self.enemies
    
    def __getstate__(self):
        state = self.__dict__.copy()
        # Remove database connection if present
        if 'mc' in state and hasattr(state['mc'], '__dict__'):
            mc_state = state['mc'].__dict__.copy()
            if 'db' in mc_state:
                mc_state['db'] = None
            state['mc'].__dict__ = mc_state
        if 'quest' in state and hasattr(state['quest'], '__dict__'):
            quest_state = state['quest'].__dict__.copy()
            if 'db' in quest_state:
                quest_state['db'] = None
            state['quest'].__dict__ = quest_state
        return state

