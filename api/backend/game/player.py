from backend.app.db import supabase
from backend.game.data_utils import load_json_file
import json
import os

BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CLASS_SKILLS = os.path.join(BASE_DIRECTORY, '..', 'data', 'class_skills.json')
LOOT = os.path.join(BASE_DIRECTORY, '..', 'data', 'loot.json')

class Player():
    def __init__(self, name: str, player_class: str, level=1, experience=0, health=20, max_health=20,
                 defense=3, inventory=None, skills=None, dungeon_floor=1, player_location=None,
                 save_slot = None):

        self.name = name
        self.player_class = player_class
        self.level = level
        self.experience = experience
        self.health = health
        self.max_health = max_health
        self.base_defense = defense
        self.inventory = self.normalize_inventory(inventory)
        self.skills = skills if skills is not None else self.load_skills(player_class)
        self.dungeon_floor = dungeon_floor
        self.player_location = player_location
        self.save_slot = save_slot
        self.defense = self.base_defense
        self.refresh_combat_stats()

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
                player_location=str(player_save['player_location']).strip('"'),
                save_slot=player_save['save_slot']
            )
        return None

    @staticmethod
    def normalize_inventory(inventory):
        """Normalize inventory keys so saves and loot drops share one shape."""
        if inventory is None:
            return {
                'gold': 5,
                'health potion': 3,
                'equipment': [],
                'equipped': {'weapon': None, 'armor': None},
            }

        normalized = dict(inventory)
        legacy_potions = normalized.pop('health_potions', 0)
        normalized['gold'] = int(normalized.get('gold', 0))
        normalized['health potion'] = int(normalized.get('health potion', 0)) + int(legacy_potions)

        equipment = normalized.get('equipment', [])
        normalized['equipment'] = [
            item['name'] if isinstance(item, dict) and 'name' in item else item
            for item in equipment
        ]

        equipped = normalized.get('equipped') or {}
        if isinstance(equipped, list):
            equipped = {'weapon': equipped[0] if equipped else None, 'armor': equipped[1] if len(equipped) > 1 else None}

        normalized['equipped'] = {
            'weapon': equipped.get('weapon'),
            'armor': equipped.get('armor'),
        }

        for slot, item_name in list(normalized['equipped'].items()):
            if item_name not in normalized['equipment']:
                normalized['equipped'][slot] = None

        return normalized

    @staticmethod
    def load_loot_data(filename=LOOT):
        return load_json_file(filename)

    @classmethod
    def get_item_data(cls, item_name, filename=LOOT):
        loot_data = cls.load_loot_data(filename)
        for category in ('gear', 'items'):
            for item_list in loot_data[category].values():
                for item in item_list:
                    if item['name'] == item_name:
                        return dict(item)
        return None

    @classmethod
    def classify_equipment(cls, item_name, filename=LOOT):
        item_data = cls.get_item_data(item_name, filename)
        if not item_data:
            return None
        attack = item_data.get('attack', 0)
        defense = item_data.get('defense', 0)
        return 'weapon' if attack >= defense else 'armor'

    def get_equipment_bonuses(self):
        bonuses = {'attack': 0, 'defense': 0}
        for item_name in self.inventory.get('equipped', {}).values():
            if not item_name:
                continue
            item_data = self.get_item_data(item_name)
            if not item_data:
                continue
            bonuses['attack'] += int(item_data.get('attack', 0))
            bonuses['defense'] += int(item_data.get('defense', 0))
        return bonuses

    def refresh_combat_stats(self):
        bonuses = self.get_equipment_bonuses()
        self.defense = self.base_defense + bonuses['defense']
        return bonuses

    def get_attack_bonus(self):
        return self.get_equipment_bonuses()['attack']

    def get_equipment_details(self):
        details = []
        equipped = self.inventory.get('equipped', {})
        for item_name in self.inventory.get('equipment', []):
            item_data = self.get_item_data(item_name) or {'name': item_name}
            slot = self.classify_equipment(item_name) or 'gear'
            details.append({
                'name': item_name,
                'attack': int(item_data.get('attack', 0)),
                'defense': int(item_data.get('defense', 0)),
                'value': int(item_data.get('value', 0)),
                'slot': slot,
                'equipped': equipped.get(slot) == item_name,
            })
        return details

    def get_equipped_loadout(self):
        loadout = {}
        for slot in ('weapon', 'armor'):
            item_name = self.inventory.get('equipped', {}).get(slot)
            item_data = self.get_item_data(item_name) if item_name else None
            loadout[slot] = {
                'name': item_name,
                'attack': int(item_data.get('attack', 0)) if item_data else 0,
                'defense': int(item_data.get('defense', 0)) if item_data else 0,
            }
        return loadout

    def get_inventory_items(self):
        items = []
        for item_name, quantity in self.inventory.items():
            if item_name in ('equipment', 'equipped', 'gold') or not isinstance(quantity, int) or quantity <= 0:
                continue

            item_data = self.get_item_data(item_name) or {'value': 0}
            items.append({
                'name': item_name,
                'quantity': quantity,
                'value': int(item_data.get('value', 0)),
                'usable': item_name == 'health potion',
                'sellable': item_name != 'gold',
            })
        return items

    def toggle_equipment(self, item_name):
        if item_name not in self.inventory['equipment']:
            return {
                'success': False,
                'message': "You don't own that equipment.",
            }

        slot = self.classify_equipment(item_name)
        if slot is None:
            return {
                'success': False,
                'message': 'That item cannot be equipped.',
            }

        equipped_item = self.inventory['equipped'].get(slot)
        if equipped_item == item_name:
            self.inventory['equipped'][slot] = None
            self.refresh_combat_stats()
            return {
                'success': True,
                'message': f'You unequipped {item_name}.',
            }

        self.inventory['equipped'][slot] = item_name
        self.refresh_combat_stats()
        if equipped_item:
            return {
                'success': True,
                'message': f'You equipped {item_name} and stowed {equipped_item}.',
            }
        return {
            'success': True,
            'message': f'You equipped {item_name}.',
        }

    def save_player_data(self, user_id: int, save_slot: int):
        """Save player data to the database."""
        target_save_slot = self.save_slot if self.save_slot is not None else save_slot
        self.save_slot = target_save_slot

        response = supabase.table('player_saves').select('*').eq('user_id', user_id).eq('save_slot', target_save_slot).execute()
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
                'defense': self.base_defense,
                'inventory': json.dumps(self.inventory),
                'skills': json.dumps(self.skills),
                'dungeon_floor': self.dungeon_floor,
                'player_location': str(self.player_location),
                'save_slot': target_save_slot
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
                'defense': self.base_defense,
                'inventory': json.dumps(self.inventory),
                'skills': json.dumps(self.skills),
                'dungeon_floor': self.dungeon_floor,
                'player_location': str(self.player_location),
                'save_slot': target_save_slot
            }).eq('user_id', user_id).eq('save_slot', target_save_slot).execute()

    def load_skills(self, player_class: str):
        """Returns skills based off of player class."""
        try:
            skill_data = load_json_file(CLASS_SKILLS)
            return skill_data.get(player_class, [])
        except FileNotFoundError:
            print('Class skills file not found.')
            return []
    
    def add_item_to_inventory(self, item, amount: int = 1):
        """Adds new items to the player inventory"""
        if amount is None:
            amount = 1

        if isinstance(item, dict):
            item_name = item.get('name')
            if (
                not item_name
                or len(self.inventory['equipment']) >= 5
                or item_name in self.inventory['equipment']
            ):
                return False
            self.inventory['equipment'].append(item_name)
            return True

        if item in self.inventory and isinstance(self.inventory[item], int):
            self.inventory[item] += amount
            return True

        if item == 'equipment':
            return False

        self.inventory[item] = max(amount, 0)
        return True
        
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
            for slot, equipped_item in list(self.inventory['equipped'].items()):
                if equipped_item == item:
                    self.inventory['equipped'][slot] = None
            self.refresh_combat_stats()
            return True
        return False
    
    def has_item(self, item: str, amount: int = 1):
        """Check if the player has at least a certain amount of an item."""
        if item in self.inventory:
            return self.inventory[item] >= amount
        elif item in self.inventory['equipment']:
            return True
        return False

    def get_inventory(self):
        """Returns a dict summarizing all inventory items."""
        summary = {k: v for k, v in self.inventory.items() if k not in ('equipment', 'equipped')}
        summary['equipment'] = [item for item in self.inventory['equipment']]
        summary['equipped'] = dict(self.inventory['equipped'])
        return summary

    def collect_loot(self, loot):
        """Add enemy loot to the inventory and return a readable summary."""
        if not loot:
            return ""

        collected = []
        for item_name, value in loot.items():
            if isinstance(value, dict):
                if self.add_item_to_inventory(value):
                    collected.append(value['name'])
                continue

            if self.add_item_to_inventory(item_name, value):
                suffix = f" x{value}" if value > 1 else ""
                collected.append(f"{item_name}{suffix}")

        return ", ".join(collected)

    def gain_experience(self, amount: int):
        """Award experience and apply simple level-up progression."""
        leveled_up = False
        self.experience += amount

        while self.experience >= self.level * 10:
            self.experience -= self.level * 10
            self.level += 1
            self.max_health += 5
            self.health = self.max_health
            self.base_defense += 1
            leveled_up = True

        self.refresh_combat_stats()

        return {
            'awarded': amount,
            'leveled_up': leveled_up,
        }

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
        
        damage = chosen_skill['damage'] + self.get_attack_bonus()
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
        if self.inventory.get('health potion', 0) > 0:
            self.health = min(self.health + 5, self.max_health)
            self.inventory['health potion'] -= 1
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
            self.player_location = str(valid_directions[direction])
            return True
        else:
            return False
