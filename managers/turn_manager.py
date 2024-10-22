class TurnManager:
    def __init__(self, game_manager) -> None:
        self.gm = game_manager


    def end_turn(self):
        # Check if all enemies are defeated
        if all(enemy.get_hp() <= 0 for enemy in self.gm.enemies):
            # End the turn and decrement buffs if all enemies are defeated
            self.decrement_buffs()
            self.decrement_cooldowns()
            for servant in self.gm.servants[:3]:
                servant.buffs.process_end_turn_skills()
            print(f"Wave {self.gm.wave} completed.")
            
            # Check if it's the last wave
            if self.gm.wave >= self.gm.total_waves:  # Correcting the comparison
                print("All waves completed. Ending program.")
                exit(0)  # Ends the program
            else:
                self.gm.get_next_wave()
            return True
        else:
            # Return False if any enemy still has health
            print(self.gm.enemies)
            print("End turn failed: Enemies are still alive.")
            

    def decrement_buffs(self):
        # Iterate over the concatenated list of servants and enemies
        for target in self.gm.get_enemies() + self.gm.servants:
            if hasattr(target, 'buffs') and hasattr(target.buffs, 'decrement_buffs'):
                target.buffs.decrement_buffs()
            else:
                print(f"Object {target} does not have the required buffs attribute or decrement_buffs method")

    def decrement_cooldowns(self):
        # Decrement the timer for each buff and remove buffs with 0 time left
        for target in self.gm.servants:
            target.skills.decrement_cooldowns(1)
