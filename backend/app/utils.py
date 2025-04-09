import os
import json

def ensure_directory_exists(filepath):
    """Ensure the directory for the given filepath exists."""
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_json(filepath):
    """Load JSON data from a file."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as file:
        return json.load(file)
    
def save_json(filepath, data):
    """Save JSON data to a file."""
    ensure_directory_exists(filepath)
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)