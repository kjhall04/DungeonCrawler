import json

LOOT = 'data\\loot.json'

class Merchant():
    def __init__(self, inventory, gold_amount):
        
        self.inventory = inventory
        self.gold_amount = gold_amount
        
    def generate_inventory(self):
        pass

    def sell_item(self):
        pass

    def buy_item(self):
        pass