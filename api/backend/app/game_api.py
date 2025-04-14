from flask import Blueprint, request, jsonify, session
from sqlalchemy.orm import Session
from backend.app.db import SessionLocal
from backend.app.models import PlayerSave, Dungeon
from backend.game.player import Player
from backend.game.dungeon import Dungeon
import json

game_api = Blueprint('game_api', __name__)

def get_db():
    """Provide a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@game_api.route('/api/move', methods=['POST'])
def move_player():
    db = next(get_db())
    username = session.get('username')
    if not username:
        return jsonify({'error': 'User not logged in'}), 401

    data = request.json
    direction = data.get('direction')

    # Load player and dungeon
    player = Player.load_or_create_player(db, username)
    dungeon = Dungeon.load_from_db(db, player_save_id=player.id)

    if not dungeon:
        return jsonify({'error': 'Dungeon not found'}), 404

    # Attempt to move the player
    if player.move(direction, dungeon):
        # Save updated player and dungeon data
        player.save_player_data(db, username)
        dungeon.save_to_db(db, player_save_id=player.id)
        return jsonify({
            'success': True,
            'room_description': dungeon.get_room_description(player.player_location),
            'story_log': f"You moved {direction}."
        })
    else:
        return jsonify({'success': False, 'error': 'Invalid move'}), 400

@game_api.route('/api/dungeon', methods=['POST'])
def generate_dungeon():
    db = next(get_db())
    username = session.get('username')
    if not username:
        return jsonify({'error': 'User not logged in'}), 401

    # Fetch the player's save data
    player_save = db.query(PlayerSave).filter(PlayerSave.user.has(username=username)).first()
    if not player_save:
        return jsonify({'error': 'Player save not found'}), 404

    data = request.json
    width = data.get('width', 10)
    height = data.get('height', 10)
    num_rooms = data.get('num_rooms', 15)
    floor_level = data.get('floor_level', 1)

    # Generate a new dungeon
    dungeon = Dungeon(width, height, num_rooms, floor_level)
    dungeon.generate()

    # Save the dungeon to the database
    dungeon_data = Dungeon(
        player_save_id=player_save.id,
        width=dungeon.width,
        height=dungeon.height,
        num_rooms=dungeon.num_rooms,
        room_positions=json.dumps(dungeon.room_positions),
        connections=json.dumps(dungeon.rooms),
        start_location=json.dumps(dungeon.start_location),
        exit_location=json.dumps(dungeon.exit_location),
        merchant_location=json.dumps(dungeon.merchant_location) if dungeon.merchant_location else None,
        floor_level=floor_level
    )
    db.add(dungeon_data)
    db.commit()

    return jsonify({
        'grid_size': {'width': dungeon.width, 'height': dungeon.height},
        'num_rooms': dungeon.num_rooms,
        'room_positions': dungeon.room_positions,
        'connections': dungeon.rooms,
        'start': dungeon.start_location,
        'exit': dungeon.exit_location,
        'merchant': dungeon.merchant_location
    })

@game_api.route('/api/player', methods=['GET'])
def get_player_stats():
    db = next(get_db())
    username = session.get('username')
    if not username:
        return jsonify({'error': 'User not logged in'}), 401

    # Fetch the player's save data
    player_save = db.query(PlayerSave).filter(PlayerSave.user.has(username=username)).first()
    if not player_save:
        return jsonify({'error': 'Player save not found'}), 404

    # Return player stats
    return jsonify({
        'name': player_save.name,
        'player_class': player_save.player_class,
        'level': player_save.level,
        'experience': player_save.experience,
        'health': player_save.health,
        'max_health': player_save.max_health,
        'defense': player_save.defense,
        'inventory': json.loads(player_save.inventory),
        'skills': json.loads(player_save.skills),
        'dungeon_floor': player_save.dungeon_floor,
        'player_location': json.loads(player_save.player_location)
    })