from .Quest import Quest
from units.Servant import Servant
from .MysticCode import MysticCode
import copy
import logging

# Configure logging
logging.basicConfig(filename='./outputs/output.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

class GameManager:
    def __init__(self, servant_init_dicts, quest_id, mc_id):
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

    # TODO part of the transformation refactoring mega todo
    def transform_aoko(self, aoko_buffs, aoko_cooldowns, aoko_np_gauge=None):
        print("What? \nAoko is transforming!")
        servants_list = [servant.name for servant in self.servants]
        logging.info(f"servants are: {servants_list}")
        for i, servant in enumerate(self.servants):
            if servant.id == 413:
                # Create a fresh transformed Aoko instance
                transformed = Servant(collectionNo=4132)
                # Copy buffs, cooldowns, and optionally NP gauge
                transformed.buffs.buffs = copy.deepcopy(aoko_buffs)
                transformed.skills.cooldowns = copy.deepcopy(aoko_cooldowns)
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

    def __repr__(self):
        return self.team_repr()

    def team_repr(self):
        """Generate human-readable team representation showing servant details."""
        if not self.servants:
            return "GameManager(no servants)"
        
        lines = ["Team composition:"]
        
        for i, servant in enumerate(self.servants):
            # Basic servant info
            slot_info = f"Slot {i + 1}: #{servant.id} {servant.name}"
            if hasattr(servant, 'ascension'):
                slot_info += f" (asc {servant.ascension})"

            lines.append(slot_info)

            # Chosen/active NP (first NP entry is treated as chosen/default)
            chosen_np = None
            try:
                if servant.nps and servant.nps.nps:
                    # If multiple NP versions exist, pick the one matching servant.oc_level if possible
                    for np_entry in servant.nps.nps:
                        # NP entries often have 'oc' or 'new_id' markers; fall back to first
                        chosen_np = servant.nps.nps[0]
                        break
            except Exception:
                chosen_np = None

            if chosen_np:
                np_name = chosen_np.get('name', 'Unknown')
                np_card = chosen_np.get('card', 'unknown')
                lines.append(f"  NP: {np_name} ({np_card})")
            else:
                lines.append(f"  NP: none")

            # Chosen skills: pick the chosen/default variant per slot with cooldowns
            skills_compact = []
            try:
                if servant.skills and servant.skills.skills:
                    for slot_num in sorted(servant.skills.skills.keys()):
                        chosen = servant.skills.get_skill_by_num(slot_num)
                        if chosen:
                            name = chosen.get('name', 'Unknown Skill')
                            cd = servant.skills.cooldowns.get(slot_num, 0)
                            skills_compact.append(f"S{slot_num}: {name} (cd={cd})")
            except Exception:
                pass

            if skills_compact:
                lines.append(f"  Skills: {', '.join(skills_compact)}")
            else:
                lines.append(f"  Skills: none")

            # Transform information
            transform_info = self._format_servant_transforms(servant)
            if transform_info:
                lines.append(f"  transforms: {transform_info}")
            else:
                lines.append(f"  transforms: none")
        
        return "\n".join(lines)

    def _format_servant_nps(self, servant):
        """Format servant NP information compactly."""
        if not servant.nps or not servant.nps.nps:
            return "NP: none"
        
        lines = ["NPs:"]
        for np in servant.nps.nps:
            np_name = np.get('name', 'Unknown')
            card_type = np.get('card', 'unknown')
            new_id = np.get('new_id', 1)
            lines.append(f"    ver new_id={new_id} | {np_name} ({card_type}) | OC-matrix: preserved")
        
        return "\n  ".join(lines)

    def _format_servant_skills_compact(self, servant):
        """Format servant skills compactly."""
        if not servant.skills or not servant.skills.skills:
            return "Skills: none"
        
        # Use the enhanced Skills repr but format more compactly for team view
        lines = ["Skills:"]
        for slot_num in sorted(servant.skills.skills.keys()):
            skill_variants = servant.skills.skills[slot_num]
            if not skill_variants:
                continue
                
            skill_lines = [f"    Skill {slot_num}:"]
            for i, variant in enumerate(skill_variants):
                context = "base" if i == 0 else f"ver {i + 1}"
                skill_name = variant.get('name', 'Unknown Skill')
                cooldown = variant.get('cooldown', 0)
                skill_lines.append(f"      {context} | {skill_name} | cooldown: {cooldown} | effects: raw preserved")
            
            lines.extend(skill_lines)
        
        return "\n  ".join(lines)

    def _format_servant_transforms(self, servant):
        """Format servant transform information."""
        # Check for Aoko transformation (413 -> 4132)
        if servant.id == 413:
            return "transforms->4132 on first NP use"
        elif servant.id == 4132:
            return "transformed from 413"
        
        # Check for other transform data if available
        if hasattr(servant, 'data') and servant.data:
            transforms = servant.data.get('transforms', [])
            if transforms:
                return f"{len(transforms)} available"
        
        return ""

