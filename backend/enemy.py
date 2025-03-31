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

    def load_loot(self, filename=LOOT):
        pass

    def take_damage(self):
        pass



if __name__ == '__main__':

    enemy = Enemy.create_enemy('skeleton')
    if enemy:
        print(vars(enemy))