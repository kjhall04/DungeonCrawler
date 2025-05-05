from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from backend.app.db import supabase
from backend.game.player import Player
from backend.game.dungeon import Dungeon
from backend.game.enemy import Enemy
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
    user_id = session.get('user_id')
    if not user_id or save_slot is None:
        return redirect(url_for('auth.login_route'))

    player = Player.load_or_create_player(user_id, save_slot)
    dungeon = Dungeon.load_from_db(user_id=user_id, save_slot=save_slot)
    if not player or not dungeon:
        return redirect(url_for('auth.select_save'))

    # --- Enemy state management on load ---
    enemy = None
    enemy_description = None
    room_enemy_name = dungeon.room_enemies.get(str(player.player_location))
    if room_enemy_name:
        enemy = Enemy.create_enemy(room_enemy_name, dungeon)
        enemy_description = dungeon.room_enemy_descriptions.get(str(player.player_location))
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

    # --- Actions ---
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
                'label': "Descend to Next Floor",
                'value': "descend_next_floor",
                'enabled': True,
                'is_descend': True
            })
        return actions

    def get_skill_actions():
        return [
            {'label': f"{skill['name'].capitalize()} (Damage: {skill['damage']})", 'value': f"skill_{skill['name']}"}
            for skill in player.skills
        ] + [{'label': "Heal", 'value': "heal"}]

    if enemy:
        narrative = enemy_description or f"A {enemy.name} appears!"
        actions = get_skill_actions()
    else:
        narrative = dungeon.get_room_description(player)
        actions = get_movement_actions()

    return render_template(
        'game.html',
        narrative=narrative,
        interaction=None,
        actions=actions,
        health=player.health,
        max_health=player.max_health,
        inventory=player.get_inventory(),
        saved=False,
        enemy=enemy,
        enemy_description=enemy_description,
        player_defense=player.defense
    )