from sqlalchemy.orm import Session
from backend.app.models import PlayerSave, User
import json
import os

BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
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
    def load_or_create_player(cls, db: Session, username: str):
        """Load player data from the database or create a new player."""
        player_save = db.query(PlayerSave).filter(PlayerSave.user.has(username=username)).first()
        if player_save:
            return cls(
                name=player_save.name,
                player_class=player_save.player_class,
                level=player_save.level,
                experience=player_save.experience,
                health=player_save.health,
                max_health=player_save.max_health,
                defense=player_save.defense,
                inventory=json.loads(player_save.inventory),
                skills=json.loads(player_save.skills),
                dungeon_floor=player_save.dungeon_floor,
                player_location=json.loads(player_save.player_location)
            )
        else:
            # Create a new player
            name = input('Enter character name: ')
            player_class = input("Choose class (mage, warrior, rogue): ")
            new_player = cls(name, player_class.lower())
            new_player.save_player_data(db, username)
            return new_player

    def save_player_data(self, db: Session, username: str):
        """Save player data to the database."""
        player_save = db.query(PlayerSave).filter(PlayerSave.user.has(username=username)).first()
        if not player_save:
            # Create a new PlayerSave entry
            player_save = PlayerSave(
                user=db.query(User).filter(User.username == username).first(),
                name=self.name,
                player_class=self.player_class,
                level=self.level,
                experience=self.experience,
                health=self.health,
                max_health=self.max_health,
                defense=self.defense,
                inventory=json.dumps(self.inventory),
                skills=json.dumps(self.skills),
                dungeon_floor=self.dungeon_floor,
                player_location=json.dumps(self.player_location)
            )
            db.add(player_save)
        else:
            # Update existing PlayerSave entry
            player_save.name = self.name
            player_save.player_class = self.player_class
            player_save.level = self.level
            player_save.experience = self.experience
            player_save.health = self.health
            player_save.max_health = self.max_health
            player_save.defense = self.defense
            player_save.inventory = json.dumps(self.inventory)
            player_save.skills = json.dumps(self.skills)
            player_save.dungeon_floor = self.dungeon_floor
            player_save.player_location = json.dumps(self.player_location)
        db.commit()

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
        


if __name__ == '__main__':
    
    player = Player.load_or_create_player()
    player.save_player_data()  