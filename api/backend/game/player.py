from backend.app.db import supabase
import json
import os

BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CLASS_SKILLS = os.path.join(BASE_DIRECTORY, '..', 'data', 'class_skills.json')

class Player():
    def __init__(self, name: str, player_class: str, level=0, experience=0, health=20, max_health=20,
                 defense=3, inventory=None, skills=None, dungeon_floor=1, player_location=None,
                 save_slot = None):

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
        self.save_slot = save_slot

    @classmethod
    def load_or_create_player(cls, user_id: int, save_slot):
        """Load player data from the database or create a new player."""
        response = supabase.table('player_saves').select('*').eq('user_id', user_id).eq('save_slot', save_slot).execute()
        if response.data:
            player_save = response.data[0]
            return cls(
                name=player_save['name'],
                player_class=player_save['player_class'],
                level=player_save['level'],
                experience=player_save['experience'],
                health=player_save['health'],
                max_health=player_save['max_health'],
                defense=player_save['defense'],
                inventory=json.loads(player_save['inventory']),
                skills=json.loads(player_save['skills']),
                dungeon_floor=player_save['dungeon_floor'],
                player_location=json.loads(player_save['player_location']),
                save_slot=player_save['save_slot']
            )
        return None

    def save_player_data(self, user_id: int):
        """Save player data to the database."""
        response = supabase.table('player_saves').select('*').eq('user_id', user_id).eq('save_slot', self.save_slot).execute()
        if not response.data:
            # Create a new PlayerSave entry
            supabase.table('player_saves').insert({
                'user_id': user_id,
                'name': self.name,
                'player_class': self.player_class,
                'level': self.level,
                'experience': self.experience,
                'health': self.health,
                'max_health': self.max_health,
                'defense': self.defense,
                'inventory': json.dumps(self.inventory),
                'skills': json.dumps(self.skills),
                'dungeon_floor': self.dungeon_floor,
                'player_location': json.dumps(self.player_location),
                'save_slot': self.save_slot
            }).execute()
        else:
            # Update existing PlayerSave entry
            supabase.table('player_saves').update({
                'name': self.name,
                'player_class': self.player_class,
                'level': self.level,
                'experience': self.experience,
                'health': self.health,
                'max_health': self.max_health,
                'defense': self.defense,
                'inventory': json.dumps(self.inventory),
                'skills': json.dumps(self.skills),
                'dungeon_floor': self.dungeon_floor,
                'player_location': json.dumps(self.player_location),
                'save_slot': self.save_slot
            }).eq('user_id', user_id).eq('save_slot', self.save_slot).execute()

    def load_skills(self, player_class: str):
        """Returns skills based off of player class."""
        try:
            with open(CLASS_SKILLS, 'r') as file:
                skill_data = json.load(file)
                return skill_data.get(player_class, [])
        except FileNotFoundError:
            print('Class skills file not found.')
            return []
    
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
        
    def remove_item_from_inventory(self, item: str, amount: int = 1):
        """Removes a given amount of an item from the inventory."""
        if item in self.inventory and isinstance(self.inventory[item], int):
            if self.inventory[item] >= amount:
                self.inventory[item] -= amount
                return True
            else:
                return False
        elif item in self.inventory['equipment']:
            self.inventory['equipment'].remove(item)
            return True
        return False
    
    def has_item(self, item: str, amount: int = 1):
        """Check if the player has at least a certain amount of an item."""
        if item in self.inventory:
            return self.inventory[item] >= amount
        elif item in self.inventory['equipment']:
            return True
        return False

    def get_inventory_summary(self):
        """Returns a dict summarizing all inventory items."""
        summary = {k: v for k, v in self.inventory.items() if k != 'equipment'}
        summary['equipment'] = [item for item in self.inventory['equipment']]
        return summary

    def attack_enemy(self, enemy, skill_name):
        """
        Attacks the enemy using a specified skill.
        
        Parameters:
            enemy (Enemy): The enemy instance to attack.
            skill_name (str): The name of the skill to use.

        Returns:
            str: A summary of the attack and its result        
        """
        if skill_name:
            chosen_skill = next((skill for skill in self.skills if skill['name'].lower() == skill_name.lower()), None)
            if not chosen_skill:
                return False
        else:
            return False
        
        damage = chosen_skill['damage']
        damage_dealt = enemy.take_damage(damage)

        if enemy.health == 0:
            return f"{self.name} used {chosen_skill['name']} and defeated {enemy.name}!"
        else:
            return f"{self.name} used {chosen_skill['name']} and dealt {damage_dealt} damage to {enemy.name} (HP: {enemy.health}/{enemy.max_health})"

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