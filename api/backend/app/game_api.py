from flask import Blueprint, request, jsonify, session
from backend.app.db import supabase
from backend.game.player import Player
from backend.game.dungeon import Dungeon
import json

game_api = Blueprint('game_api', __name__)

def move_player():
    username = session.get('username')
    if not username:
        return jsonify({'error': 'User not logged in'}), 401

    data = request.json
    direction = data.get('direction')

    # Load player and dungeon
    player = Player.load_or_create_player(username)
    response = supabase.table('player_saves').select('id').eq('username', username).execute()
    if not response.data:
        return jsonify({'error': 'Player save not found'}), 404
    player_save_id = response.data[0]['id']
    dungeon = Dungeon.load_from_db(player_save_id)

    if not dungeon:
        return jsonify({'error': 'Dungeon not found'}), 404

    # Attempt to move the player
    if player.move(direction, dungeon):
        # Save updated player and dungeon data
        player.save_player_data(username)
        dungeon.save_to_db(player_save_id)
        return jsonify({
            'success': True,
            'room_description': dungeon.get_room_description(player.player_location),
            'story_log': f"You moved {direction}."
        })
    else:
        return jsonify({'success': False, 'error': 'Invalid move'}), 400

@game_api.route('/api/dungeon', methods=['POST'])
def generate_dungeon():
    username = session.get('username')
    if not username:
        return jsonify({'error': 'User not logged in'}), 401

    # Fetch the player's save data
    response = supabase.table('player_saves').select('id').eq('username', username).execute()
    if not response.data:
        return jsonify({'error': 'Player save not found'}), 404
    player_save_id = response.data[0]['id']

    data = request.json
    width = data.get('width', 10)
    height = data.get('height', 10)
    num_rooms = data.get('num_rooms', 15)
    floor_level = data.get('floor_level', 1)

    # Generate a new dungeon
    dungeon = Dungeon(width, height, num_rooms, floor_level)
    dungeon.generate()

    # Save the dungeon to the database
    dungeon.save_to_db(player_save_id)

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
    username = session.get('username')
    if not username:
        return jsonify({'error': 'User not logged in'}), 401

    # Fetch the player's save data
    response = supabase.table('player_saves').select('*').eq('username', username).execute()
    if not response.data:
        return jsonify({'error': 'Player save not found'}), 404
    player_save = response.data[0]

    # Return player stats
    return jsonify({
        'name': player_save['name'],
        'player_class': player_save['player_class'],
        'level': player_save['level'],
        'experience': player_save['experience'],
        'health': player_save['health'],
        'max_health': player_save['max_health'],
        'defense': player_save['defense'],
        'inventory': json.loads(player_save['inventory']),
        'skills': json.loads(player_save['skills']),
        'dungeon_floor': player_save['dungeon_floor'],
        'player_location': json.loads(player_save['player_location'])
    })