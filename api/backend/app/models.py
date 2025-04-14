from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    # Relationships
    player_save = relationship("PlayerSave", back_populates='user', uselist=False)
    
class PlayerSave(Base):
    __tablename__ = "player_saves"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    player_class = Column(String, nullable=False)
    level = Column(Integer, default=0)
    experience = Column(Integer, default=0)
    health = Column(Integer, default=20)
    max_health = Column(Integer, default=20)
    defense = Column(Integer, default=3)
    inventory = Column(Text, nullable=False)        # JSON string for inventory
    skills = Column(Text, nullable=False)           # JSON string for skills    
    dungeon_floor = Column(Integer, default=1)
    player_location = Column(Text, nullable=True)   # JSON string for location

    # Relationships
    user = relationship("User", back_populates="player_save")
    dungoen = relationship("Dungeon", back_populates="player_save")

class Dungeon(Base):
    __tablename__ = "dungeons"

    id = Column(Integer, primary_key=True, index=True)
    player_save_id = Column(Integer, ForeignKey("player_saves.id"), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    num_rooms = Column(Integer, nullable=False)
    room_positions = Column(Text, nullable=False)  # JSON string for room positions
    connections = Column(Text, nullable=False)  # JSON string for connections
    start_location = Column(Text, nullable=False)  # JSON string for start location
    exit_location = Column(Text, nullable=False)  # JSON string for exit location
    merchant_location = Column(Text, nullable=True)  # JSON string for merchant location
    floor_level = Column(Integer, nullable=False)

    # Relationships
    player_save = relationship("PlayerSave", back_populates="dungeon")