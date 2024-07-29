from data import class_advantage_matrix, attribute, class_indices, base_multipliers, traits_dict, character_list
import requests
from bidict import bidict
import pandas as pd
import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
import sys
import random

#TODO implement 1 quest fight with 1 specific team, early era 90+ with simple castoria team, then add in 1 quick team and 1 buster team just to see if proper refund and damage
#   create an algorithm that detemrines possible ways to fill up the bar i.e. servant skills, mystic code skills, swap teammember, clear first wave with arash/sojuro/hebetrot, increase over charge
#   create 3 different standards of character investment (apart from just NP levels) such as [90 10/10/10] [100 10/10/10] [120 10/10/10] [120 10/10/10 Class Score]
#    
class Simulator:
    def __init__(self):
        self.turn = 1

    def simulate_battle(self):       
        self.turn += 1

# holds the data for the current team
class Team:
    def createTeam():
        team_comp = []
        # add upto 6 team members

# holds thedata for the current quest
class Encounter:
    def load():
        # loads from a quest from mongodb collection 'quests' the enemy types on each wave
        return

# holds data for loading the unit after being retrieved from mongodb
class Servant:
    def __init__(self, data):
        self.collection_no = data.get('collectionNo')
        self.name = data.get('name')
        self.battle_name = data.get('battleName')
        self.class_id = data.get('classId')
        self.image_url = data.get("extraAssets", {}).get("faces", {}).get("ascension", {}).get("4")
        self.gender = data.get('gender')
        self.attribute = data.get('attribute')
        self.traits = [trait['id'] for trait in data.get('traits', [])]
        self.cards = data.get('cards', [])
        self.atk_growth = data.get('atkGrowth', [])
        self.skills = self.parse_skills(data.get('skills', []))
        self.class_passive = self.parse_class_passive(data.get('classPassive', []))
        self.rarity = data.get('rarity')

    def parse_skills(self, skills):
        parsed_skills = []
        for skill in skills:
            skill_info = {
                'name': skill['name'],
                'cooldown': skill['coolDown'][9] if len(skill['coolDown']) > 9 else None,
                'functions': [],
            }
            for func in skill['functions']:
                func_info = {
                    'funcType': func['funcType'],
                    'funcTargetType': func['funcTargetType'],
                    'svals': func['svals'][9] if 'svals' in func and len(func['svals']) > 9 else None,
                    'buffs': []
                }
                for buff in func.get('buffs', []):
                    buff_info = {
                        'name': buff['name'],
                        'svals': buff['svals'][9] if 'svals' in buff and len(buff['svals']) > 9 else None
                    }
                    func_info['buffs'].append(buff_info)
                skill_info['functions'].append(func_info)
            parsed_skills.append(skill_info)
        return parsed_skills

    def parse_class_passive(self, class_passive):
        parsed_passive = []
        for passive in class_passive:
            passive_info = {
                'name': passive['name'],
                'functions': []
            }
            for func in passive['functions']:
                func_info = {
                    'funcType': func['funcType'],
                    'buffs': []
                }
                for buff in func.get('buffs', []):
                    buff_info = {
                        'name': buff['name'],
                        'svals': buff['svals'][9] if 'svals' in buff and len(buff['svals']) > 9 else None
                    }
                    func_info['buffs'].append(buff_info)
                passive_info['functions'].append(func_info)
            parsed_passive.append(passive_info)
        return parsed_passive

    def get_atk_at_level(self, level):
        return self.atk_growth[level-1] if level <= 120 else None

    def __repr__(self):
        return f"Servant(name={self.name}, class_id={self.class_id}, attribute={self.attribute})"

    def get_class_multiplier(self, defender_class):       
        defender_index = class_indices[defender_class]
        return class_advantage_matrix[self.class_multiplier][defender_index]

    def get_class_base_multiplier(self):
        return self.class_base_multiplier

    def NP_damage(self, defender, card, position, busterChain, class_advantage, trait_advantage):
        firstCardBonus = 0.5 if card == "Buster" else 0
        cardDamageValue = {"Arts": 1, "Buster": 1.5, "Quick": 0.8}[card][position]
        busterChainMod = 0.2 if card == "Buster" and busterChain else 0
        randomModifier = random.uniform(0.9, 1.1)
        criticalModifier = 2 if isCrit else 1
        npDamageMultiplier = 1 if isNP else 1  # This should be replaced with the actual NP's damage multiplier
        superEffectiveModifier = 1  # This should be replaced with the actual NP's super effective modifier
        isSuperEffective = 0  # This should be replaced with 1 if the enemy qualifies (via trait or status), 0 otherwise

        # These should be replaced with the actual buff values
        cardMod = 0
        atkMod = 0
        defMod = 0
        specialDefMod = 0
        powerMod = 0
        selfDamageMod = 0
        critDamageMod = 0
        npDamageMod = 0
        dmgPlusAdd = 0
        selfDmgCutAdd = 0

        # Class and Trait Multipliers
        class_multiplier = class_advantage.get_class_multiplier(self.unit_type, defender.unit_type)
        trait_multiplier = trait_advantage.get_trait_multiplier(self.trait, defender.trait)

        damage = self.servantAtk * npDamageMultiplier * (firstCardBonus + (cardDamageValue * (1 + cardMod))) * self.classAtkBonus * class_multiplier * trait_multiplier * self.triangleModifier * self.attributeModifier * randomModifier * 0.23 * (1 + atkMod - defMod) * criticalModifier * (1 - specialDefMod) * (1 + powerMod + selfDamageMod + (critDamageMod * isCrit) + (npDamageMod * isNP)) * (1 + ((superEffectiveModifier - 1) * isSuperEffective)) + dmgPlusAdd + selfDmgCutAdd + (self.servantAtk * busterChainMod)
        
    def card_damage(self, defender, card, position, isCrit, isNP, busterChain, class_advantage, trait_advantage):
        firstCardBonus = 0.5 if card == "Buster" and position == 0 and not isNP else 0
        cardDamageValue = {"Arts": [1, 1.2, 1.4], "Buster": [1.5, 1.8, 2.1], "Quick": [0.8, 0.96, 1.12]}[card][position]
        busterChainMod = 0.2 if card == "Buster" and busterChain else 0
        randomModifier = random.uniform(0.9, 1.1)
        criticalModifier = 2 if isCrit else 1
        npDamageMultiplier = 1 if isNP else 1  # This should be replaced with the actual NP's damage multiplier
        superEffectiveModifier = 1  # This should be replaced with the actual NP's super effective modifier
        isSuperEffective = 0  # This should be replaced with 1 if the enemy qualifies (via trait or status), 0 otherwise

        # These should be replaced with the actual buff values
        cardMod = 0
        atkMod = 0
        defMod = 0
        specialDefMod = 0
        powerMod = 0
        selfDamageMod = 0
        critDamageMod = 0
        npDamageMod = 0
        dmgPlusAdd = 0
        selfDmgCutAdd = 0

        # Class and Trait Multipliers
        class_multiplier = class_advantage.get_class_multiplier(self.unit_type, defender.unit_type)
        trait_multiplier = trait_advantage.get_trait_multiplier(self.trait, defender.trait)

        damage = self.servantAtk * npDamageMultiplier * (firstCardBonus + (cardDamageValue * (1 + cardMod))) * self.classAtkBonus * class_multiplier * trait_multiplier * self.triangleModifier * self.attributeModifier * randomModifier * 0.23 * (1 + atkMod - defMod) * criticalModifier * (1 - specialDefMod) * (1 + powerMod + selfDamageMod + (critDamageMod * isCrit) + (npDamageMod * isNP)) * (1 + ((superEffectiveModifier - 1) * isSuperEffective)) + dmgPlusAdd + selfDmgCutAdd + (self.servantAtk * busterChainMod)
        return damage

    def calculate_np_gain(self, offensiveNPRate, firstCardBonus, cardNpValue, cardMod, enemyServerMod, npChargeRateMod, criticalModifier, overkillModifier):
        np_per_hit = (offensiveNPRate * (firstCardBonus + (cardNpValue * (1 + cardMod))) * enemyServerMod * (1 + npChargeRateMod) * criticalModifier) * overkillModifier
        return np_per_hit // 1  # Round down

    def gain_np(self, np_gain):
        self.np_charge = min(self.np_charge + np_gain, self.np_charge_max)

def select_characters(db, character_ids):
    servants = []
    for character_id in character_ids:
        data = db.servants.find_one({'collectionNo': int(character_id)})  # Ensure character_id is an integer
        if data:
            servants.append(Servant(data))
    return servants

def display_character_stats(characters):
    data = []
    for c in characters:
        atk = (
            c.get_atk_at_level(60) if c.rarity == 1 else
            c.get_atk_at_level(65) if c.rarity == 2 else
            c.get_atk_at_level(70) if c.rarity == 3 else
            c.get_atk_at_level(80) if c.rarity == 4 else
            c.get_atk_at_level(90) if c.rarity == 5 else
            None  # Default value if none of the conditions are met
        )

        skills_summary = ", ".join([f"{skill['name']} (Cooldown: {skill['cooldown']})" for skill in c.skills])
        class_passive_summary = ", ".join([passive['name'] for passive in c.class_passive])
        data.append({
            'Name': c.name,
            'Gender': c.gender,
            'Attribute': c.attribute,
            'Cards': ", ".join(c.cards),
            'ATK': atk,
            'Skills': skills_summary,
            'Class Passive': class_passive_summary
        })
    
    df = pd.DataFrame(data)
    
    # Set display options to show all columns and rows
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_colwidth', None)
    
    print(df)

if __name__ == '__main__':
    # Connect to MongoDB
    host = 'localhost'  # If MongoDB runs on the same machine
    port = 27017  # Default MongoDB port
    db_name = 'mongodb-container'  # Your database name
    # Load environment variables from .env file
    load_dotenv()
    # Get the username and password from environment variables
    # Set the encoding to UTF-8
    username = os.getenv('MONGO_USER')
    password = os.getenv('MONGO_PASS')
    # Connect to MongoDB
    client = MongoClient(f"mongodb://{username}:{password}@localhost:27017/")
    db = client['yourDatabase']  # Replace 'yourDatabase' with your actual database name
    # Set the encoding to UTF-8
    sys.stdout.reconfigure(encoding='utf-8')

    # test with [Castoria, Castoria, Durga] against node "Quests\Flood Gate-9170.json"
    # character_ids = [284, 383, ]
    # team = select_characters(db, character_ids)
    # display_character_stats(team)
    # for c in team:
    #     for skill in c.skills:
    #         print(f"{skill}\n")
    numbers = []
    # for i in range(416,417,1):
    numbers.append(4132)
    team = select_characters(db, numbers)
    for c in team:
        # print(c.name)
        for skill in c.skills:
            print(f"{skill}\n")
