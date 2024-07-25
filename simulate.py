import random

class Unit:
    def __init__(self, name, unit_type, trait, base_damage, bonuses=None, penalties=None, servantAtk=0, classAtkBonus=1, triangleModifier=1, attributeModifier=1):
        self.name = name
        self.unit_type = unit_type
        self.trait = trait
        self.base_damage = base_damage
        self.bonuses = bonuses if bonuses else {}
        self.penalties = penalties if penalties else {}
        self.servantAtk = servantAtk
        self.classAtkBonus = classAtkBonus
        self.triangleModifier = triangleModifier
        self.attributeModifier = attributeModifier

    def calculate_damage(self, defender, card, position, isCrit, isNP, busterChain):
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

        damage = self.servantAtk * npDamageMultiplier * (firstCardBonus + (cardDamageValue * (1 + cardMod))) * self.classAtkBonus * self.triangleModifier * self.attributeModifier * randomModifier * 0.23 * (1 + atkMod - defMod) * criticalModifier * (1 - specialDefMod) * (1 + powerMod + selfDamageMod + (critDamageMod * isCrit) + (npDamageMod * isNP)) * (1 + ((superEffectiveModifier - 1) * isSuperEffective)) + dmgPlusAdd + selfDmgCutAdd + (self.servantAtk * busterChainMod)
        return damage

class Simulator:
    def __init__(self):
        pass

    def simulate_battle(self, attackers, defenders):
        for attacker in attackers:
            for defender in defenders:
                # Simulate a battle with a Buster card in the first position, not a crit, not an NP, and not a Buster Chain
                damage = attacker.calculate_damage(defender, "Buster", 0, False, False, False)
                print(f"{attacker.name} deals {damage} damage to {defender.name}.")

# Create some units
saber = Unit("Saber", "saber", "earth", 100, bonuses={"lancer": 1.2}, penalties={"man": 0.9}, servantAtk=10000, classAtkBonus=1.1, triangleModifier=1.2, attributeModifier=0.9)
lancer = Unit("Lancer", "lancer", "man", 100, servantAtk=10000)

# Create a simulator
simulator = Simulator()

# Simulate a battle
simulator.simulate_battle([saber], [lancer])
