from cryptography.fernet import Fernet
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
USER_DATA_FILE = os.path.join(BASE_DIRECTORY, '..', 'data', 'users.json')

ENCRYPTION_KEY = os.getenv('EMAIL_ENCRYPTION_KEY')
fernet = Fernet(ENCRYPTION_KEY)

def encrypt_email(email):
    """Encrypt the email address."""
    return fernet.encrypt(email.encode()).decode()

def decrypt_email(encrypted_email):
    """Decrypt the email address."""
    return fernet.decrypt(encrypted_email.encode()).decode()

def load_users():
    """Load user data from the JSON file."""
    if not os.path.exists(USER_DATA_FILE):
        return {}
    try:
        with open(USER_DATA_FILE, 'r') as file:
            return json.load(file)
    except json.JSONDecodeError:
        return {}
    
def save_users(users):
    """Save user data to the JSON file."""
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(users, file, indent=4)

def create_account(username, email, password, confirm_password):
    """
    Creates a new user account.

    Args:
        username (str): The username for the new account.
        email (str): The email for the new account.
        password (str): The password for the new account.
        confirm_password (str): The password confirmation.

    Returns:
        dict: A success message or an error message
    """
    users = load_users()

    if username in users:
        return {'error': 'Username already exists'}
    
    encrypted_email = encrypt_email(email)
    if any(user.get('email') == encrypted_email for user in users.values()):
        return {'error': 'Email already in user'}
    
    if password != confirm_password:
        return {'error': 'Passwords do not match'}
    
    hashed_password = generate_password_hash(password)
    users[username] = {'eamil': encrypted_email, 'password': hashed_password}
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
    
    return {'success': 'Login successful'}