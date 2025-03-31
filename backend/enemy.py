import json

ENEMIES = 'data\\enemy_table.json'
LOOT = 'data\\loot.json'

class Enemy():
    def __init__(self, name, health, max_health, defense, skills, loot):
        
        self.name = name
        self.health = health
        self.max_health = max_health
        self.defense = defense
        self.skills = skills
        self.loot = loot

    @classmethod
    def create_enemy(cls, filename=ENEMIES):
        try:
            with open(filename, 'r') as file:
                pass
        except FileNotFoundError:
            pass

    def load_skills (self):
        pass

    def take_damage(self):
        pass

