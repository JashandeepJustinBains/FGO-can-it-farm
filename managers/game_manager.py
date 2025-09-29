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
                # Deepcopy only non-permanent buffs (turns != -1), preserving new dict structure
                import copy as _copy
                if isinstance(aoko_buffs, dict):
                    transformed.buffs.buffs = {
                        buff_type: [_copy.deepcopy(buff) for buff in buff_list if isinstance(buff, dict) and buff.get('turns', 0) != -1]
                        for buff_type, buff_list in aoko_buffs.items()
                    }
                    # Fix owner reference if present
                    for buff_type, buff_list in transformed.buffs.buffs.items():
                        for buff in buff_list:
                            if 'owner' in buff:
                                buff['owner'] = transformed
                else:
                    # fallback: if aoko_buffs is a list (legacy), keep only non-permanent dicts
                    transformed.buffs.buffs = [_copy.deepcopy(buff) for buff in aoko_buffs if isinstance(buff, dict) and buff.get('turns', 0) != -1]
                    for buff in transformed.buffs.buffs:
                        if 'owner' in buff:
                            buff['owner'] = transformed
                # Only process buffs for correct stacking (do NOT re-apply passives)
                if hasattr(transformed.buffs, 'process_servant_buffs'):
                    transformed.buffs.process_servant_buffs()
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

