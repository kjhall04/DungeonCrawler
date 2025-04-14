from backend.app.db import Base, engine
from backend.app.models import User, PlayerSave, Dungeon

# Create all tables
Base.metadata.create_all(bind=engine)