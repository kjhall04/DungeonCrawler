import json
import random as rand
import os

BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
ENEMIES = os.path.join(BASE_DIRECTORY, '..', 'data', 'enemies.json')
LOOT = os.path.join(BASE_DIRECTORY, '..', 'data', 'loot.json')
DESCRIPTIONS = os.path.join(BASE_DIRECTORY, '..', 'data', 'descriptions.json')

class Enemy():
    def __init__(self, name, health, max_health, defense, skills, dungeon, loot=None):
        
        self.name = name
        self.health = health
        self.max_health = max_health
        self.defense = defense
        self.skills = skills
        self.loot = loot if loot is not None else self.load_loot(dungeon)
        self.previous_description = None

    @classmethod
    def create_enemy(cls, enemy_name, dungeon, filename=ENEMIES):
        """Loads enemy data to create an enemy."""
        try:
            with open(filename, 'r') as file:
                enemy_data = json.load(file)
            
            floor_key = 'floor_' + str(dungeon.floor_level)
            if floor_key in enemy_data and enemy_name in enemy_data[floor_key]:
                data = enemy_data[floor_key][enemy_name]
                return cls(
                    enemy_name,
                    data['health'],
                    data['health'],
                    data['defense'],
                    data['skills'],
                    dungeon
                )
            else:
                print(f"Enemy '{enemy_name}' not found in data.")
                return None
        except FileNotFoundError:
            print('Enemy data file not found.')
            return None

    def load_loot(self, dungeon, filename=LOOT, default_min=0, default_max=2, gear_chance=0.25, max_gear=2, gold_range=(0, 10)):
        """
        Loads loot data and assigns random loot to the enemy.
        
        Parameters:
            dungeon (Dungeon): The current dungeon object.
            filename (str): Path to the loot table file.
            default_min (int): Min number of default drop item types.
            default_max (int): Max number of default drop item types.
            gear_chance (float): Chance (0.0 - 1.0) of dropping gear.
            max_gear (int): Max number of gear items that can drop.
            gold_range (tuple): Min and max amount of gold that can drop.
            
        Returns:
            dict: A dictionary of dropped items.
        """
        try:
            with open(filename, 'r') as file:
                loot_data = json.load(file)

            loot_drops = {}

            # Determine the loot level based on the dungeon floor
            level_key = f"level_{dungeon.floor_level}"

            # Random number of different default items
            num_items = rand.randint(default_min, default_max)
            selected_items = rand.sample(loot_data['items'][level_key], min(num_items, len(loot_data['items'][level_key])))

            for item in selected_items:
                if item == 'gold':
                    loot_drops[item['name']] = rand.randint(*gold_range)  # Random gold amount.
                else:
                    loot_drops[item['name']] = rand.randint(1, 3)  # Random amount for other items

            if rand.random() < gear_chance:
                num_gear = rand.randint(1, max_gear)
                gear_drops = rand.sample(loot_data["gear"][level_key], min(num_gear, len(loot_data['gear'][level_key])))
                
                for gear in gear_drops:
                    loot_drops[gear['name']] = gear
            
            return loot_drops

        except FileNotFoundError:
            print('Loot data file not found.')
            return None
        
    def attack_player(self, player):
        """
        Attacks the player using a random skill.
        
        Parameters:
            player (Player): The player object to attack.

        Returns:
            dict: Info about the attack for narration.
        """
        if not self.skills:
            return {
                'success': False,
                'message': f"{self.name} has no skills to attack with."
            }
        
        selected_skill = rand.choice(self.skills)

        if isinstance(selected_skill, dict):
            skill_name = selected_skill.get('name', 'Unknown Attack')
            base_damage = selected_skill.get('damage', 1)
        else:
            skill_name = selected_skill
            base_damage = rand.randint(1, 3)

        damage = base_damage + rand.randint(0, 2)

        damage_dealt = player.take_damage(damage)

        return {
            'success': True,
            'enemy': self.name,
            'skill_used': skill_name,
            'damage_attempted': damage,
            'damage_dealt': damage_dealt,
            'player_health': player.health
        }

    def take_damage(self, damage: int):
        """Reduces health based on incoming damage and defense."""
        damage_taken = max(damage - self.defense, 0)
        self.health -= damage_taken
        if self.health < 0:
            self.health = 0
            return True
        return damage_taken
    
    def load_description(self, player, filename=DESCRIPTIONS):
        """Loads and returns a non-repeating string based on the floor and enemy."""
        try:
            with open(filename, 'r') as file:
                description_data = json.load(file)

            floor_key = f"floor_{player.dungeon_level}"
            enemy_key = self.name

            if floor_key in description_data and enemy_key in description_data[floor_key]['enemies']:
                descriptions = description_data[floor_key]['enemies'][enemy_key]

                # Ensure description is not the same as previous one
                new_description = self.previous_description
                attempts = 0
                while new_description == self.previous_description and attempts < 10:
                    version = str(rand.randint(1, len(descriptions)))
                    new_description = descriptions[version]
                    attempts += 1

                self.previous_description = new_description
                return new_description
            else:
                return f"No description found for {enemy_key} on {floor_key}."

        except FileNotFoundError:
            return False

        

if __name__ == '__main__':

    enemy = Enemy.test_generation()