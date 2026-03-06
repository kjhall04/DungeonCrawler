from backend.app.db import SUPABASE_ANON_KEY, SUPABASE_KEY_ROLE, SUPABASE_SECRET_KEY, supabase
from werkzeug.security import generate_password_hash, check_password_hash
import re


def _describe_supabase_error(exc: Exception, default_message: str) -> str:
    error_text = str(exc).lower()

    if 'users' in error_text and ('does not exist' in error_text or 'relation' in error_text):
        return "Supabase table 'users' is missing in the database."

    if (
        'permission' in error_text
        or 'row-level security' in error_text
        or 'not allowed' in error_text
        or 'forbidden' in error_text
        or 'unauthorized' in error_text
    ):
        if SUPABASE_KEY_ROLE == 'anon':
            if SUPABASE_SECRET_KEY and not SUPABASE_ANON_KEY:
                return (
                    "Supabase rejected the request because SUPABASE_SECRET_KEY is set to an anon/publishable key. "
                    "Replace it with the real secret key from Supabase."
                )
            return "Supabase rejected the request because the server is using a publishable/anon key. Set SUPABASE_SECRET_KEY in Vercel."
        return "Supabase rejected the request. Check the server-side key and database permissions."

    if SUPABASE_KEY_ROLE == 'anon':
        if SUPABASE_SECRET_KEY and not SUPABASE_ANON_KEY:
            return (
                "Supabase rejected the request because SUPABASE_SECRET_KEY is set to an anon/publishable key. "
                "Replace it with the real secret key from Supabase."
            )
        return "Supabase rejected the request because the server is using a publishable/anon key. Set SUPABASE_SECRET_KEY in Vercel."

    return default_message

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
    try:
        # Check if username already 
        response = supabase.table('users').select('*').eq('username', username).execute()
        if response.data:
            return {'error': 'Username already exists', 'username': username, 'email': email}
        
        # Validate email
        if not validate_email(email):
            return {'error': 'Invalid email format', 'username': username, 'email': email}
        
        # Check if email already exists
        response = supabase.table('users').select('*').eq('email', email).execute()
        if response.data:
            return {'error': 'Email already in use', 'username': username, 'email': email}
        
        # Validate password
        if not validate_password(password):
            return {'error': 'Password must be at least 8 characters long', 'username': username, 'email': email}
       
        if password != confirm_password:
            return {'error': 'Passwords do not match', 'username': username, 'email': email}
        
        # Hash the password and insert the new user
        hashed_password = generate_password_hash(password)
        response = supabase.table('users').insert({
            'username': username,
            'email': email,
            'password' : hashed_password
        }).execute()

        if not response.data:
            return {'error': 'Failed to create account', 'username': username, 'email': email}
        
        return {'success': 'Account created successfully'}
    except Exception as exc:
        message = _describe_supabase_error(
            exc,
            "Account creation failed because the Supabase connection or schema is not ready.",
        )
        return {'error': message, 'username': username, 'email': email}

def login(username: str, password: str):
    """
    Log in a user.

    Args:
        username (str): The username.
        password (str): The password.

    Returns:
        dict: A success message or an error message
    """
    try:
        response = supabase.table('users').select('*').eq('username', username).execute()
        if not response.data:
            return {'error': 'Invalid username or password'}
        
        user = response.data[0]
        if not check_password_hash(user['password'], password):
            return {'error': 'Invalid username or password'}
        
        return {'success': 'Login successful', 'user_id': user['id']}
    except Exception as exc:
        return {
            'error': _describe_supabase_error(
                exc,
                'Login failed because the Supabase connection or schema is not ready',
            )
        }
