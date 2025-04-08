import os
import json
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
USER_DATA_FILE = os.path.join(BASE_DIRECTORY, '..', 'data', 'users.json')

def load_users():
    """Load user data from the JSON file."""
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, 'r') as file:
        return json.load(file)
    
def save_users(users):
    """Save user data to the JSON file."""
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(users, file, indent=4)

def create_account(username, password):
    """
    Creates a new user account.

    Args:
        username (str): The username for the new account.
        password (str): The password for the new account.

    Returns:
        dict: A success message or an error message
    """
    users = load_users()

    if username in users:
        return {'error': 'Username already exists'}
    
    hashed_password = generate_password_hash(password)
    users[username] = {'password': hashed_password}
    save_users(users)

    return {'success': 'Account created successfully'}

def login(username, password):
    """
    Log in a user.

    Args:
        username (str): The username.
        password (str): The password.

    Returns:
        dict: A success message or an error message
    """
    users = load_users()

    if username not in users:
        return {'error': 'Invalid username or password'}
    
    if not check_password_hash(users[username]['password'], password):
        return {'error': 'Invalid username or password'}
    
    return {'success': 'Invalid username or password'}