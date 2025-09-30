import logging

# Configure logging
logging.basicConfig(filename='./outputs/output.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

class TurnManager:
    def __init__(self, game_manager, tm_copy=None) -> None:
        self.gm = game_manager
    
    def get_score(self):
        logging.info(f"calculating heuristic for wave: {self.gm.wave}")
        _score = 0
        for enemy in self.gm.get_enemies():
            _score += enemy.get_hp() / enemy.get_max_hp()

        # Add a penalty for not reaching or defeating subsequent waves
        if _score > 0:
            _score += self.gm.total_waves - self.gm.wave

        return _score


    def end_turn(self):
        logging.info(f"preparing to end turn")

        # Print buffs on all servants before ending the simulation
        if all(enemy.get_hp() <= 0 for enemy in self.gm.get_enemies()):
            print("=== Buffs on all servants before simulation ends ===")
            for servant in self.gm.servants:
                print("===============================================")
                print(servant)
                print(servant.buffs.grouped_str())
            print("===============================================")

            logging.info(f"checking if all enemies are dead")

            for servant in self.gm.servants[:3]:
                servant.buffs.process_end_turn_skills()

            # check for selfsac and reorganize party
            servants_list = [servant.name for servant in self.gm.servants]
            logging.info(f"BEFORE INSTANTDEATH servants are: {servants_list}")
            for i, servant in enumerate(self.gm.servants[:3]):  # Only check the frontline servants
                if servant.kill:
                    logging.info(f"killing servant {servant} who has flag kill={servant.kill}")

                    # Remove servant from front line and replace with backline servant
                    print(f"Servant {servant.name} has died.")
                    print(self.gm.servants[:3])
                    if len(self.gm.servants) > 3:
                        swap = self.gm.servants[3]
                        self.gm.servants[i] = swap
                        self.gm.servants.pop(3)
                        print(f"Servant {swap.name} has moved to the front line.")
                    else:
                        print("No backline servants available.")
                        return False        
                    # Reset the servant's kill status
                    servant.kill = False
            
            servants_list = [servant.name for servant in self.gm.servants]
            logging.info(f"AFTER INSTANTDEATH servants are: {servants_list}")

            # End the turn and decrement buffs if all enemies are defeated
            # End the turn. We will advance to the next wave (if any) and
            # perform buff/cooldown decrements on the wave-advance token so
            # decrements align with the '#' token (wave boundary).
            print(f"Wave {self.gm.wave} completed.")

            # If this was the final wave, perform a final decrement and finish.
            if self.gm.wave >= self.gm.total_waves:
                # Final wave completed: decrement timers once and end.
                self.decrement_buffs()
                self.decrement_cooldowns()
                print("All waves completed. Ending program.")
                return True
            else:
                # Advance to the next wave first (this is the '#' token),
                # then decrement buffs/cooldowns so the decrement is tied to
                # the wave advancement.
                self.gm.get_next_wave()
                self.decrement_buffs()
                self.decrement_cooldowns()
                return True
        else:
            # Return False if any enemy still has health
            print(self.gm.get_enemies())
            print("End turn failed: Enemies are still alive.")
            return False
            

    def decrement_buffs(self):
        # Iterate over the concatenated list of servants and enemies
        for target in self.gm.get_enemies() + self.gm.servants:
            if hasattr(target, 'buffs') and hasattr(target.buffs, 'decrement_buffs'):
                logging.info(f"Decrementing buff timers")
                logging.info(f"Servant:{target.name} has the following buffs:")
                for i in target.buffs.buffs:
                    logging.info(f"buff:{i.get('buff','')} has time limit of {i['turns']} turns")
                target.buffs.decrement_buffs()
                logging.info(f"After decrementing buffs ->")
                for i in target.buffs.buffs:
                    logging.info(f"buff:{i.get('buff', '')} has time limit of {i['turns']} turns")
            else:
                print(f"Object {target} does not have the required buffs attribute or decrement_buffs method")

    def decrement_cooldowns(self):
        # Decrement the timer for each buff and remove buffs with 0 time left
        for target in self.gm.servants[:3]:
            if target:
                target.skills.decrement_cooldowns(1)
