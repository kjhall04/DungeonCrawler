from flask import Blueprint, request, jsonify
from backend.game.player import Player
from backend.game.dungeon import DungeonGenerator

game_api = Blueprint('game_api', __name__)

@game_api.route('/api/move', methods=['POST'])
def move_player():
    data = request.json
    direction = data.get('direction')
    player_location = data.get('player_location')
    dungeon_data = data.get('dungeon')

    # Validate input
    if not direction or player_location is None or not dungeon_data:
        return jsonify({'error': 'Invalid input'}), 400

    # Load dungeon and player
    dungeon = DungeonGenerator(**dungeon_data)
    player = Player(**data.get('player'))

    # Attempt to move the player
    if player.move(direction, dungeon):
        return jsonify({'success': True, 'new_location': player.player_location})
    else:
        return jsonify({'success': False, 'error': 'Invalid move'}), 400
    
@game_api.route('/api/dungeon', methods=['POST'])
def generate_dungeon():
    data = request.json
    width = data.get('width', 10)
    height = data.get('height', 10)
    num_rooms = data.get('num_rooms', 15)
    floor_level = data.get('floor_level', 1)

    dungoen = DungeonGenerator(width, height, num_rooms, floor_level)
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
    player = Player.load_or_create_player()
    return jsonify(player.player_stats_to_dict())