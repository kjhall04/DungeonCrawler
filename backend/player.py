import json

PLAYER_SAVE = 'data\\player_save.json'
CLASS_SKILLS = 'data\\class_skills.json'

class Player():
    def __init__(self, name: str, player_class: str, level=1, health=20, max_health=20,
                 defense=3, inventory=None, skills=None):

        self.name = name
        self.player_class = player_class
        self.level = level
        self.health = health
        self.max_health = max_health
        self.defense = defense
        self.inventory = inventory if inventory is not None else {'gold': 5, 'health_potions': 3, 'equipment': []}
        self.skills = skills if skills is not None else self.load_skills(player_class)

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
                    player_data['health'],
                    player_data['max_health'],
                    player_data['defense'],
                    player_data['inventory'],
                    player_data['skills']
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
    
    def add_item_to_inventory(self, item: str, amount: int):
        """ Adds new items to the player inventory"""
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

    def player_stats_to_dict(self):
        """Turns player data into a dictionary for saving."""
        return {
            "name": self.name,
            "player_class": self.player_class,
            "level": self.level,
            "health": self.health,
            "max_health": self.max_health,
            "defense": self.defense,
            "inventory": self.inventory,
            "skills": self.skills
        }

    def save_player_data(self, filename=PLAYER_SAVE):
        """Saves player data into a json file."""
        with open(filename, 'w') as file:
            json.dump(self.player_stats_to_dict(), file, indent=4)
        


if __name__ == '__main__':
    
    player = Player.load_or_create_player()
    player.save_player_data()