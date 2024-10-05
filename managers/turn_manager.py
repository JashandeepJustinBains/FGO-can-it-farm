class TurnManager:
    def __init__(self, game_manager) -> None:
        self.gm = game_manager

    def end_turn(self):
        # End the turn and decrement buffs
        self.decrement_buffs()
        self.decrement_cooldowns()
        for servant in self.gm.servants[:3]:
            servant.buffs.process_end_turn_skills()
        for enemy in self.gm.enemies:
            if enemy.get_hp() > 0:
                print("FAILURE: Enemy still has HP remaining.")
                return "FAILURE"
        self.gm.wave += 1
        print(f"Wave {self.gm.wave} completed.")

    def decrement_buffs(self):
        # Decrement the timer for each buff and remove buffs with 0 time left
        for target in self.gm.enemies + self.gm.servants:
            target.buffs.decrement_buffs()

    def decrement_cooldowns(self):
        # Decrement the timer for each buff and remove buffs with 0 time left
        for target in self.gm.servants:
            target.skills.decrement_cooldowns(1)



