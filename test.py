import json
import os
import random as rand

BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DESCRIPTIONS = os.path.join(BASE_DIRECTORY, 'api', 'backend', 'data', 'descriptions.json')

with open(DESCRIPTIONS, 'r') as file:
    data = json.load(file)

def get_unique_message(data, floor, enemy, previous_string):
    enemy_data = data[f'floor_{floor}']['enemies'][enemy]
    new_string = previous_string
    while new_string == previous_string:
        version = str(rand.randint(1, len(enemy_data)))
        new_string = enemy_data[version]
    return new_string
