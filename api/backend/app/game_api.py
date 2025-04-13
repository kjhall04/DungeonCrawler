from flask import Blueprint, request, jsonify, session
from backend.game.player import Player
from backend.game.dungeon import Dungeon

game_api = Blueprint('game_api', __name__)

@game_api.route('/api/move', methods=['POST'])
def move_player():
    username = session.get('username')
    if not username:
        return jsonify({'error': 'User not logged in'}), 401
    
    data = request.json
    direction = data.get('direction')

    player = Player.load_or_create_player(username)
    dungeon = Dungeon.load_from_json(username)

    if player.move(direction, dungeon):
        dungeon.save_to_json(username)
        player.save_player_data(username)
        return jsonify({
            'succes': True,
            'room_description': dungeon.get_room_description(player.player_location),
            'story_log': f"You moved {direction}."
        })
    else: 
        return jsonify({'succes': False, 'error': 'Invalid move'}), 400
    
@game_api.route('/api/dungeon', methods=['POST'])
def generate_dungeon():
    username = session.get('username')
    if not username:
        return jsonify({'error': 'User not logged in'}), 401

    data = request.json
    width = data.get('width', 10)
    height = data.get('height', 10)
    num_rooms = data.get('num_rooms', 15)
    floor_level = data.get('floor_level', 1)

    dungoen = Dungeon(width, height, num_rooms, floor_level)
    dungoen.generate()
    dungoen.save_to_json()

    return jsonify({
        'grid_size': {'width': dungoen.width, 'height': dungoen.height},
        'num_rooms': dungoen.num_rooms,
        'room_positions': dungoen.room_positions,
        'connections': dungoen.rooms,
        'start': dungoen.start_location,
        'exit': dungoen.exit_location,
        'merchant': dungoen.merchant_location
    })

@game_api.route('/api/player', methods=['GET'])
def get_player_stats():
    username = session.get('username')
    if not username:
        return jsonify({'error': 'User not logged in'}), 401
    player = Player.load_or_create_player(username)
    return jsonify(player.player_stats_to_dict())