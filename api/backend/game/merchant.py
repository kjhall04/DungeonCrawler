import os
import random as rand

from backend.game.data_utils import load_json_file, resolve_progression_key

BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
LOOT = os.path.join(BASE_DIRECTORY, '..', 'data', 'loot.json')
DESCRIPTIONS = os.path.join(BASE_DIRECTORY, '..', 'data', 'descriptions.json')


def _load_loot_data(filename=LOOT):
    return load_json_file(filename)


class Merchant():
    def __init__(self, dungeon, inventory=None, gold_amount=None, description=None):
        self.inventory = inventory if inventory is not None else []
        self.gold_amount = gold_amount if gold_amount is not None else 30 * dungeon.floor_level
        self.description = description
        self.previous_description = None

    @staticmethod
    def _find_item_data(item_name, loot_data):
        for item_list in loot_data['items'].values():
            for item in item_list:
                if item['name'] == item_name:
                    return dict(item)

        for gear_list in loot_data['gear'].values():
            for gear in gear_list:
                if gear['name'] == item_name:
                    return dict(gear)

        return None

    @staticmethod
    def _merge_item(inventory, item_data):
        for existing_item in inventory:
            if existing_item['name'] != item_data['name']:
                continue

            if 'quantity' in existing_item or 'quantity' in item_data:
                existing_item['quantity'] = existing_item.get('quantity', 1) + item_data.get('quantity', 1)
                return

        inventory.append(dict(item_data))

    def generate_inventory(self, dungeon, filename=LOOT, max_items=3, max_gear=4):
        """
        Generates a random inventory for the merchant based on the loot table.
        
        Parameters:
            filename (str): Path to the loot table file.
            max_items (int): Maximum number of consumable items.
            max_gear (int): Maximum number of gear items.
        """
        try:
            loot_data = _load_loot_data(filename)

            # Determine the loot level based on the dungeon floor
            level_key = resolve_progression_key(loot_data['items'], 'level_', dungeon.floor_level)
            
            # Only generate health potions for items
            health_potions = [
                item for item in loot_data['items'][level_key] if item['name'] == 'health potion'
            ]
            if health_potions:
                health_potion = dict(health_potions[0])  # Copy so the source loot table is not mutated
                health_potion['quantity'] = rand.randint(1, max_items)  # Random quantity between 1 and max_items
                items = [health_potion]
            else:
                items = []

            gear = [
                dict(item)
                for item in rand.sample(loot_data['gear'][level_key], min(max_gear, len(loot_data['gear'][level_key])))
            ]

            self.inventory = items + gear

        except FileNotFoundError:
            print('Loot data file not found.')

    def load_description(self, filename=DESCRIPTIONS):
        """Loads and returns a non-repeating string of the merchant appearing."""
        try:
            description_data = load_json_file(filename)

            descriptions = description_data['merchant']

            new_description = self.previous_description
            attempts = 0
            while new_description == self.previous_description and attempts < 10:
                version = str(rand.randint(1, len(descriptions)))
                new_description = descriptions[version]
                attempts += 1

            self.previous_description = new_description
            self.description = new_description
            return new_description
        except FileNotFoundError:
            return False

    def to_state(self):
        return {
            'inventory': [dict(item) for item in self.inventory],
            'gold_amount': self.gold_amount,
            'description': self.description,
        }

    def sell_item_to_player(self, item_name, player):
        """
        Sells an item to the player if it exists in merchant inventory.
        
        Parameters:
            item_name (str): Name of the item to sell.
            player (Player): The player object buying the item.
            
        Returns:
            dict: Transaction result.
        """
        for item in self.inventory:
            if item['name'] == item_name:
                item_value = item.get('value', 0)
                if player.inventory['gold'] >= item_value:
                    item_to_add = dict(item) if any(key in item for key in ('attack', 'defense')) else item_name
                    if not player.add_item_to_inventory(item_to_add, 1):
                        return {
                            'success': False,
                            'message': 'You cannot carry that item right now.',
                        }

                    player.inventory['gold'] -= item_value
                    self.gold_amount += item_value

                    # Decrease quantity or remove item if quantity reaches 0
                    if 'quantity' in item:
                        item['quantity'] -= 1
                        if item['quantity'] <= 0:
                            self.inventory.remove(item)
                    else:
                        self.inventory.remove(item)
                    return {
                        'success': True,
                        'message': f"You bought {item_name} for {item_value} gold.",
                    }

                return {
                    'success': False,
                    'message': 'You do not have enough gold.',
                }

        return {
            'success': False,
            'message': "That item is no longer available.",
        }

    def buy_item_from_player(self, item_name, player):
        """
        Buys an item from the player if the merchant has enough gold.
        
        Parameters:
            item_name (str): Name of the item to sell.
            player (Player): The player object buying the item.
            
        Returns:
            dict: Transaction result.
        """
        loot_data = _load_loot_data()
        if item_name == 'gold':
            return {
                'success': False,
                'message': "The merchant refuses to buy gold.",
            }

        item_data = self._find_item_data(item_name, loot_data)
        if item_data is None:
            return {
                'success': False,
                'message': "The merchant has no interest in that item.",
            }

        item_value = item_data.get('value', 0)
        if self.gold_amount < item_value:
            return {
                'success': False,
                'message': "The merchant can't afford that right now.",
            }

        if item_name in player.inventory['equipment']:
            if not player.remove_item_from_inventory(item_name):
                return {
                    'success': False,
                    'message': "You don't have that equipment anymore.",
                }
            self._merge_item(self.inventory, item_data)
        else:
            if not player.remove_item_from_inventory(item_name):
                return {
                    'success': False,
                    'message': "You don't have that item anymore.",
                }
            self._merge_item(self.inventory, {
                'name': item_name,
                'value': item_value,
                'quantity': 1,
            })

        self.gold_amount -= item_value
        player.inventory['gold'] += item_value
        return {
            'success': True,
            'message': f"You sold {item_name} for {item_value} gold.",
        }
