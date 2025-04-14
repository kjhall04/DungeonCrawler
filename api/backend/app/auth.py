from sqlalchemy.orm import Session
from backend.app.db import SessionLocal
from backend.app.models import User
from werkzeug.security import generate_password_hash, check_password_hash
import re

def get_db():
    """Provide a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def validate_password(password: str) -> bool:
    """Validate password strength."""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):  # At least one uppercase letter
        return False
    if not re.search(r'[a-z]', password):  # At least one lowercase letter
        return False
    if not re.search(r'[0-9]', password):  # At least one digit
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):  # At least one special character
        return False
    return True

def validate_email(email: str) -> bool:
    """Validate email format."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def create_account(db: Session, username: str, email: str, password: str, confirm_password: str):
    """
    Creates a new user account.

    Args:
        db (Session): The database to use.
        username (str): The username for the new account.
        email (str): The email for the new account.
        password (str): The password for the new account.
        confirm_password (str): The password confirmation.

    Returns:
        dict: A success message or an error message
    """
    if db.query(User).filter(User.username == username).first():
        return {'error': 'Username already exists'}
    
    if not validate_email(email):
        return {'error': 'Invalid email format'}
    
    if db.query(User).filter(User.email == email).first():
        return {'error': 'Email already in use'}
    
    if not validate_password(password):
        return {'error': 'Password must be at least 8 characters long and include uppercase, lowercase, a number, and a special character.'}
   
    if password != confirm_password:
        return {'error': 'Passwords do not match'}
    
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, email=email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {'success': 'Account created successfully'}

def login(db: Session, username: str, password: str):
    """
    Log in a user.

    Args:
        db (Session): The database to use.
        username (str): The username.
        password (str): The password.

    Returns:
        dict: A success message or an error message
    """
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not check_password_hash(user.password, password):
        return {'error': 'Invalid username or password'}
    
    return {'success': 'Login successful', 'user_id': user.id}