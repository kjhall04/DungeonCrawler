import json
import random as rand

ENEMIES = 'data\\enemies.json'
LOOT = 'data\\loot.json'

class Enemy():
    def __init__(self, name, health, max_health, defense, skills, loot=None):
        
        self.name = name
        self.health = health
        self.max_health = max_health
        self.defense = defense
        self.skills = skills
        self.loot = loot if loot is not None else self.load_loot()

    @classmethod
    def create_enemy(cls, enemy_name, filename=ENEMIES):
        """Loads enemy data to create an enemy."""
        try:
            with open(filename, 'r') as file:
                enemy_data = json.load(file)
            
            if enemy_name in enemy_data:
                data = enemy_data[enemy_name]
                return cls(
                    enemy_name,
                    data['health'],
                    data['health'],
                    data['defense'],
                    data['skills']
                )
            else:
                print(f"Enemy '{enemy_name}' not found in data.")
                return None
        except FileNotFoundError:
            print('Enemy data file not found.')
            return None

    def load_loot(self, filename=LOOT, default_min=0, default_max=3, gear_chance=0.25, max_gear=2, gold_range=(0, 10)):
        """
        Loads loot data and assigns random loot to the enemy.
        
        Parameters:
            default_min (int): Min number of default drop item types.
            default_max (int): Max number of default drop item types.
            gear_chance (float): Chance (0.0 - 1.0) of dropping gear.
            max_gear (int): Max number of gear items that can drop.
            gold_range (tuple): Min and max amount of gold that can drop.
            
        Returns:
            list: A list of dropped items.
        """
        try:
            with open(filename, 'r') as file:
                loot_data = json.load(file)

            loot_drops = {}

            # Random number of different default items
            num_items = rand.randint(default_min, default_max)
            selected_items = rand.sample(loot_data['items'], min(num_items, len(loot_data['items'])))

            for item in selected_items:
                if item == 'gold':
                    loot_drops[item] = rand.randint(*gold_range)  # Random gold amount.
                else:
                    loot_drops[item] = rand.randint(1, 3)  # Random amount for other items

            if rand.random() < gear_chance:
                num_gear = rand.randint(1, max_gear)
                gear_drops = rand.sample(loot_data["gear"], min(num_gear, len(loot_data['gear'])))
                
                for gear in gear_drops:
                    loot_drops[gear['name']] = gear
            
            return loot_drops

        except FileNotFoundError:
            print('Loot data file not found.')
            return None

    def take_damage(self, damage: int):
        """Reduces health based on incoming damage and defense."""
        damage_taken = max(damage - self.defense, 0)
        self.health -= damage_taken
        if self.health < 0:
            self.health = 0
            return True
        return damage_taken



if __name__ == '__main__':

    enemy = Enemy.create_enemy('skeleton')
    if enemy:
        print(vars(enemy))