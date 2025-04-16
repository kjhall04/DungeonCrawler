from backend.app.db import supabase
from werkzeug.security import generate_password_hash, check_password_hash
import re

def validate_password(password: str) -> bool:
    """Validate password strength."""
    if len(password) < 8:
        return False
    return True

def validate_email(email: str) -> bool:
    """Validate email format."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def create_account(username: str, email: str, password: str, confirm_password: str):
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
    # Check if username already 
    response = supabase.table('users').select('*').eq('username', username).execute()
    if response.data:
        return {'error': 'Username already exists'}
    
    # Validate email
    if not validate_email(email):
        return {'error': 'Invalid email format'}
    
    # Check if email already exists
    response = supabase.table('users').select('*').eq('email', email).execute()
    if response.data:
        return {'error': 'Email already in use'}
    
    # Validate password
    if not validate_password(password):
        return {'error': 'Password must be at least 8 characters long'}
   
    if password != confirm_password:
        return {'error': 'Passwords do not match'}
    
    # Hash the password and insert the new user
    hashed_password = generate_password_hash(password)
    response = supabase.table('users').insert({
        'username': username,
        'email': email,
        'password' : hashed_password
    }).execute()

    if response.error:
        return {'error': 'Failed to create account'}
    
    return {'success': 'Account created successfully'}

def login(username: str, password: str):
    """
    Log in a user.

    Args:
        username (str): The username.
        password (str): The password.

    Returns:
        dict: A success message or an error message
    """
    response = supabase.table('users').select('*').eq('username', username).execute()
    if not response.data:
        return {'error': 'Invalid username or password'}
    
    user = response.data[0]
    if not check_password_hash(user['password'], password):
        return {'error': 'Invalid username or password'}
    
    return {'success': 'Login successful', 'user_id': user['id']}