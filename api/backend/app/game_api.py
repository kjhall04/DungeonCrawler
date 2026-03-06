import json

from flask import Blueprint, jsonify, redirect, request, session, url_for

from backend.app.db import supabase
from backend.app.game_action import build_enemy_for_room, build_merchant_for_room, persist_game_state, render_current_room, set_room_state
from backend.game.player import Player
from backend.game.dungeon import Dungeon

game_api = Blueprint('game_api', __name__)


def _parse_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

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

    data = request.get_json(silent=True) or {}
    width = max(3, _parse_int(data.get('width', 10), 10))
    height = max(3, _parse_int(data.get('height', 10), 10))
    num_rooms = max(2, _parse_int(data.get('num_rooms', 15), 15))
    floor_level = max(1, _parse_int(data.get('floor_level', 1), 1))

    # Generate a new dungeon
    dungeon = Dungeon(width, height, num_rooms, floor_level)
    dungeon.generate()

    # Save the dungeon to the database
    dungeon.save_to_db(player_save_id, user_id=user_id, save_slot=save_slot)

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
        'inventory': Player.normalize_inventory(json.loads(player_save['inventory'])),
        'skills': json.loads(player_save['skills']),
        'dungeon_floor': player_save['dungeon_floor'],
        'player_location': str(player_save['player_location']).strip('"'),
        'save_slot': player_save['save_slot']
    })

@game_api.route('/load_save/<int:save_slot>', methods=['GET'])
def load_save(save_slot):
    user_id = session.get('user_id')
    if not user_id or save_slot is None:
        return redirect(url_for('auth.login_route'))

    player = Player.load_or_create_player(user_id, save_slot)
    dungeon = Dungeon.load_from_db(user_id=user_id, save_slot=save_slot)
    if not player or not dungeon:
        return redirect(url_for('auth.select_save'))

    enemy, enemy_description = build_enemy_for_room(dungeon, player.player_location)
    merchant, _ = build_merchant_for_room(dungeon, player.player_location)
    if enemy:
        room_state = dungeon.room_enemies.get(str(player.player_location), {})
        enemy_state = room_state.get('enemy') if isinstance(room_state, dict) and 'enemy' in room_state else room_state
        if enemy_state.get('loot') is None:
            enemy_state['loot'] = enemy.loot
            merchant_state = room_state.get('merchant') if isinstance(room_state, dict) else None
            set_room_state(dungeon, player.player_location, enemy=enemy_state, merchant=merchant_state)
            persist_game_state(player, dungeon, user_id, save_slot)
        session['enemy'] = {
            'name': enemy.name,
            'health': enemy.health,
            'max_health': enemy.max_health,
            'defense': enemy.defense,
            'skills': enemy.skills,
            'description': enemy_description
        }
    else:
        session.pop('enemy', None)
    if not persist_game_state(player, dungeon, user_id, save_slot):
        return redirect(url_for('auth.select_save'))
    return render_current_room(
        player,
        dungeon,
        saved=False,
        enemy=enemy,
        enemy_description=enemy_description,
        merchant=merchant,
    )
