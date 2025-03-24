import json

FILENAME = 'data\\player_save.json'

class Player():
    def __init__(self, name: str, player_class: str):

        self.name = name
        self.player_class = player_class
        self.level = 1
        self.health = 100
        self.max_health = 100
        self.defense = 3
        self.inventory = []
        self.skills = self.load_skills(player_class)

    def load_skills(self, player_class):
        """Returns skills based off of player class."""
        class_skills = {
            'mage': ['fireball', 'lightning', 'staff hit'],
            'warrior': ['punch', 'stab', 'headbut'],
            'rogue': ['slash', 'throw poison', 'pick pocket'],
            'necromancer': ['life steal', 'necrotic orb', 'bone jab']
        }

        return class_skills.get(player_class, [])
    
    def data_to_dict(self):
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

    def save_player_data(self, filename=FILENAME):
        """Saves player data into a json file."""
        with open(filename, 'w') as file:
            json.dump(self.data_to_dict(), file, indent=4)

    @classmethod
    def load_from_file(cls, filename=FILENAME):
        """Loads player data from a json file."""
        try:
            with open(filename, 'r') as file:
                player_data = json.load(file)
                player = cls(player_data['name'], player_data['player_class'])
                player.level = player_data['level']
                player.health = player_data['health']
                player.max_health = player_data['max_health']
                player.defense = player_data['defense']
                player.inventory = player_data['inventory']
                return player
            
        except FileNotFoundError:
            print(f'Error: {filename} not found.')
            return None
        
if __name__ == '__main__':
    
    player = Player('Aariq', 'mage')

    player.save_player_data()