import json
import random as rand

LOOT = 'data\\loot.json'

class Merchant():
    def __init__(self, inventory=None, gold_amount=100):
        
        self.inventory = inventory if inventory is not None else []
        self.gold_amount = gold_amount
        
    def generate_inventory(self, dungeon, filename=LOOT, max_items=3, max_gear=4):
        """
        Generates a random inventory for the merchant based on the loot table.
        
        Parameters:
            filename (str): Path to the loot table file.
            max_items (int): Maximum number of consumable items.
            max_gear (int): Maximum number of gear items.
        """
        try:
            with open(filename, 'r') as file:
                loot_data = json.load(file)

            # Determine the loot level based on the dungeon floor
            level_key = f'level_{dungeon.floor_level}'
            
            # Only generate health potions for items
            health_potions = [
                item for item in loot_data['items'][level_key] if item['name'] == 'health potion'
            ]
            if health_potions:
                health_potion = health_potions[0]  # Assume there's only one health potion definition
                health_potion['quantity'] = rand.randint(1, max_items)  # Random quantity between 1 and max_items
                items = [health_potion]
            else:
                items = []

            gear = rand.sample(loot_data['gear'][level_key], min(max_gear, len(loot_data['gear'][level_key])))

            self.inventory = items + gear

        except FileNotFoundError:
            print('Loot data file not found.')

    def sell_item_to_player(self, item_name, player):
        """
        Sells an item to the player if it exists in merchant inventory.
        
        Parameters:
            item_name (str): Name of the item to sell.
            player (Player): The player object buying the item.
            
        Returns:
            bool: True if the transaction was successful, False otherwise.
        """
        for item in self.inventory:
            if item['name'] == item_name:
                item_value = item.get('value', 0)
                if player.inventory['gold'] >= item_value:
                    player.inventory['gold'] -= item_value
                    player.add_item_to_inventory(item_name, 1)
                    self.gold_amount += item_value

                    # Decrease quantity or remove item if quantity reaches 0
                    if 'quantity' in item:
                        item['quantity'] -= 1
                        if item['quantity'] <= 0:
                            self.inventory.remove(item)
                    else:
                        self.inventory.remove(item)
                    return True
                else:
                    print('Player does not have enought gold.')
                    return False
        print("Item not found in merchant's inventory.")
        return False

    def buy_item_from_player(self, item_name, player):
        """
        Buys an item from the player if the merchant has enough gold.
        
        Parameters:
            item_name (str): Name of the item to sell.
            player (Player): The player object buying the item.
            
        Returns:
            bool: True if the transaction was successful, False otherwise.
        """
        for item in player.inventory['equipment']:
            if item['name'] == item_name:
                item_value = item.get('value', 0)
                if self.gold_amount >= item_value:
                    self.gold_amount -= item_value
                    player.inventory['gold'] += item_value
                    player.inventory['equipment'].remove(item)

                    for inv_item in self.inventory:
                        if inv_item['name'] == item_name and 'quantity' in inv_item:
                            inv_item['quantity'] += 1
                            break
                    else:
                        self.inventory.append(item)
                    return True
                else:
                    print("Merchant doesn't have enough gold.")
                    return False
        print("Item not found in player's inventory.")
        return False
    


if __name__ == '__main__':
        
    merchant = Merchant()
    merchant.generate_inventory()

    print(merchant.inventory)