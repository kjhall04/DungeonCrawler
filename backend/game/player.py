import json
import os

BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PLAYER_SAVE = os.path.join(BASE_DIRECTORY, '..', 'save_data', 'player_save.json')
CLASS_SKILLS = os.path.join(BASE_DIRECTORY, '..', 'data', 'class_skills.json')

class Player():
    def __init__(self, name: str, player_class: str, level=0, experience=0, health=20, max_health=20,
                 defense=3, inventory=None, skills=None, dungeon_floor=1, player_location=None):

        self.name = name
        self.player_class = player_class
        self.level = level
        self.experience = experience
        self.health = health
        self.max_health = max_health
        self.defense = defense
        self.inventory = inventory if inventory is not None else {'gold': 5, 'health_potions': 3, 'equipment': []}
        self.skills = skills if skills is not None else self.load_skills(player_class)
        self.dungeon_floor = dungeon_floor
        self.player_location = player_location

    @classmethod
    def load_or_create_player(cls, filename=PLAYER_SAVE):
        """Loads player data if it exists, otherwise creates a new character."""
        try:
            with open(filename, 'r') as file:
                player_data = json.load(file)
                return cls(
                    player_data['name'],
                    player_data['player_class'],
                    player_data['level'],
                    player_data['experience'],
                    player_data['health'],
                    player_data['max_health'],
                    player_data['defense'],
                    player_data['inventory'],
                    player_data['skills'],
                    player_data['dungeon_floor'],
                    player_data['player_location']
                )
        except FileNotFoundError:
            print('No save file found. Creating a new character.')
            name = input('Enter character name: ')
            player_class = input("Choose class (mage, warrior, rogue): ")
            return cls(name, player_class.lower())

    def load_skills(self, player_class, filename=CLASS_SKILLS):
        """Returns skills based off of player class."""
        try:
            with open(filename, 'r') as file:
                skill_data = json.load(file)
                return skill_data.get(player_class, [])
        except FileNotFoundError:
            print('Class skills file not found.')
    
    def add_item_to_inventory(self, item: str, amount: int):
        """Adds new items to the player inventory"""
        if amount is None:
            amount = 1

        if item in self.inventory:
            self.inventory[item] += amount
            return True
        elif len(self.inventory['equipment']) < 5:
            self.inventory['equipment'].append(item)
            return True
        else:
            return False
        
    def move(self):
        """Takes player input to move around the dungeon."""
        pass

    def attack_enemy(self):
        """Reduce enemy health based on outgoing damage."""
        pass

    def take_damage(self, damage: int):
        """Reduces health based on incoming damage and defense."""
        damage_taken = max(damage - self.defense, 0)
        self.health -= damage_taken
        if self.health < 0:
            self.health = 0
        return damage_taken
    
    def heal(self):
        """Heal the player if they have health potions."""
        if self.inventory['health_potions'] > 0:
            self.health = min(self.health + 5, self.max_health)
            self.inventory['health_potions'] -= 1
            return True
        return False
    
    def move(self, direction, dungeon):
        """
        Moves the player in the specified direction if it's valid.

        Parameters:
            direction (str): The direction to move in ('north', 'south', 'east', 'west').
            dungeon (DungeonGenerator): The current dungeon instance.

        Returns:
            bool: True if the move was successful, False otherwise.
        """
        current_room = self.player_location
        valid_directions = dungeon.get_valid_directions(current_room)

        if direction in valid_directions:
            self.player_location = valid_directions[direction]
            return True
        else:
            return False
        
    def player_stats_to_dict(self):
        """Turns player data into a dictionary for saving."""
        return {
            "name": self.name,
            "player_class": self.player_class,
            "level": self.level,
            "experience": self.experience,
            "health": self.health,
            "max_health": self.max_health,
            "defense": self.defense,
            "inventory": self.inventory,
            "skills": self.skills,
            "dungeon_floor": self.dungeon_floor,
            "dungeon_coordinates": self.dungeon_coordinates
        }

    def save_player_data(self, filename=PLAYER_SAVE):
        """Saves player data into a json file."""
        with open(filename, 'w') as file:
            json.dump(self.player_stats_to_dict(), file, indent=4)
        


if __name__ == '__main__':
    
    player = Player.load_or_create_player()
    player.save_player_data()