from .Quest import Quest
from units.Servant import Servant
from .MysticCode import MysticCode
import copy
import logging

# Configure logging
logging.basicConfig(filename='./outputs/output.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

class GameManager:
    def __init__(self, servant_ids, quest_id, mc_id, gm_copy=None):
        if gm_copy:
            self.__dict__ = copy.deepcopy(gm_copy.__dict__)
        else:
            self.servant_ids = servant_ids
            self.quest_id = quest_id
            self.mc_id = mc_id
            self.servants = [Servant(collectionNo=servant_id) for servant_id in servant_ids]
            self.mc = MysticCode(mc_id)
            self.fields = []
            self.quest = None  # Initialize the Quest instance
            self.wave = 1
            self.total_waves = 0
            self.enemies = []
            self.init_quest()
            if 413 in servant_ids:
                self.saoko = Servant(collectionNo=4132)

    def add_field(self, state):
        name = state.get('field_name', 'Unknown')
        turns = state.get('turns', 0)
        self.fields.append([name, turns])

    def reset(self):
        self.servants = [Servant(collectionNo=servant_id) for servant_id in self.servant_ids]
        self.fields = []

    def swap_servants(self, frontline_idx, backline_idx):
        self.servants[frontline_idx], self.servants[backline_idx] = self.servants[backline_idx], self.servants[frontline_idx]

    def transform_aoko(self, aoko_buffs, aoko_cooldowns):
        print("What? \nAoko is transforming!")
        servants_list = [servant.name for servant in self.servants]
        logging.info(f"servants are: {servants_list}")
        for i, servant in enumerate(self.servants):
            if servant.id == 413:
                self.saoko.buffs.buffs = copy.deepcopy(aoko_buffs)
                self.saoko.skills.cooldowns = copy.deepcopy(aoko_cooldowns)
                self.servants[i] = self.saoko
                self.servants[i].set_npgauge(-20)
                print(f"Contratulations! Your 'Aoko Aozaki' transformed into '{self.servants[i].name}' ")
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

    def copy(self):
        return GameManager(self.servant_ids, self.quest_id, gm_copy=self)
    
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
            
            # NP information
            np_info = self._format_servant_nps(servant)
            
            # Skills information (compact version)
            skills_info = self._format_servant_skills_compact(servant)
            
            # Transform information
            transform_info = self._format_servant_transforms(servant)
            
            # Combine all info
            full_line = f"  {slot_info} | {np_info} | {skills_info}"
            if transform_info:
                full_line += f" | {transform_info}"
                
            lines.append(full_line)
        
        return "\n".join(lines)
    
    def _format_servant_nps(self, servant):
        """Format servant NP information compactly."""
        if not servant.nps or not servant.nps.nps:
            return "NP: none"
        
        primary_np = servant.nps.nps[-1]  # Highest ID NP
        np_name = primary_np.get('name', 'Unknown')
        card_type = primary_np.get('card', 'unknown')
        
        if len(servant.nps.nps) > 1:
            return f"NP: {np_name} ({card_type}) (versions: {len(servant.nps.nps)})"
        else:
            return f"NP: {np_name} ({card_type})"
    
    def _format_servant_skills_compact(self, servant):
        """Format servant skills compactly."""
        if not servant.skills or not servant.skills.skills:
            return "Skills: none"
        
        skill_names = []
        for slot_num in sorted(servant.skills.skills.keys()):
            skill_variants = servant.skills.skills[slot_num]
            if skill_variants:
                primary_skill = skill_variants[-1]  # Latest version
                skill_name = primary_skill.get('name', 'Unknown')
                if len(skill_variants) > 1:
                    skill_names.append(f"{skill_name}(v{len(skill_variants)})")
                else:
                    skill_names.append(skill_name)
        
        return f"Skills: {' | '.join(skill_names)}"
    
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
                return f"transforms: {len(transforms)} available"
        
        return ""
