from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from backend.app.db import supabase
from backend.game.player import Player
from backend.game.dungeon import Dungeon
import json

game_api = Blueprint('game_api', __name__)

@game_api.route('/api/dungeon', methods=['POST'])
def generate_dungeon():
    user_id = session.get('user_id')
    save_slot = session.get('save_slot')
    if not user_id or save_slot is None:
        return redirect(url_for('auth.login_route'))

    # Fetch the player's save data
    response = supabase.table('player_saves').select('id').eq('user_id', user_id).eq('save_slot', save_slot).execute()
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
    user_id = session.get('user_id')
    save_slot = session.get('save_slot')
    if not user_id or save_slot is None:
        return redirect(url_for('auth.login_route'))

    # Fetch the player's save data
    response = supabase.table('player_saves').select('*').eq('user_id', user_id).eq('save_slot', save_slot).execute()
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
        'player_location': str(player_save['player_location']).strip('"'),
        'save_slot': player_save['save_slot']
    })

@game_api.route('/load_save/<int:save_slot>', methods=['GET'])
def load_save(save_slot):
    """Load the game for the selected save slot."""
    user_id = session.get('user_id')
    if not user_id or save_slot is None:
        return redirect(url_for('auth.login_route'))
    
    # Load the player and dungeon
    player = Player.load_or_create_player(user_id, save_slot)
    if not player:
        return redirect(url_for('auth.select_save'))

    dungeon = Dungeon.load_from_db(user_id=user_id, save_slot=save_slot)
    if not dungeon:
        return redirect(url_for('auth.select_save'))

    # --- Helper: get movement actions ---
    def get_movement_actions():
        all_directions = ['north', 'south', 'east', 'west']
        valid_directions = dungeon.get_valid_directions(player.player_location)
        actions = [
            {
                'label': f"Move {direction.capitalize()}",
                'value': f"move_{direction}" if direction in valid_directions else None,
                'enabled': direction in valid_directions
            }
            for direction in all_directions
        ]
        # Add descend button if at exit
        if str(player.player_location) == str(dungeon.exit_location[0]):
            actions.append({
                'label': "Descend to the Next Floor",
                'value': "descend_next_floor",
                'enabled': True,
                'is_descend': True
            })
        return actions

    return render_template(
        'game.html',
        narrative=dungeon.get_room_description(player),
        interaction=None,
        actions=get_movement_actions(),
        health=player.health,
        max_health=player.max_health,
        inventory=player.get_inventory(),
        saved=False,
        enemy=None,
        player_defense=player.defense
    )