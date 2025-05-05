from flask import render_template, redirect, url_for, session, request
from backend.app.db import supabase
from backend.game.player import Player
from backend.game.dungeon import Dungeon
from backend.game.enemy import Enemy

def get_movement_actions(player, dungeon):
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

def get_skill_actions(player):
    return [
        {'label': f"{skill['name'].capitalize()} (Damage: {skill['damage']})", 'value': f"skill_{skill['name']}"}
        for skill in player.skills
    ] + [{'label': "Heal", 'value': "heal"}]

def render_game(player, dungeon, narrative, actions, saved, enemy=None, enemy_description=None, interaction=None, enemy_defeated_transition=False):
    return render_template(
        'game.html',
        narrative=narrative,
        interaction=interaction,
        actions=actions,
        health=player.health,
        max_health=player.max_health,
        inventory=player.get_inventory(),
        saved=saved,
        enemy=enemy,
        enemy_description=enemy_description,
        player_defense=player.defense,
        enemy_defeated_transition=enemy_defeated_transition
    )

def handle_combat_action(player, dungeon, enemy, enemy_description, action, user_id, save_slot, saved):
    interaction = player.attack_enemy(enemy, action[len('skill_'):])
    if enemy.health <= 0:
        narrative = f" {enemy.name} is defeated!"
        enemy = None
        dungeon.room_enemies[str(player.player_location)] = None
        player.save_player_data(user_id, save_slot)
        response = supabase.table('player_saves').select('id').eq('user_id', user_id).eq('save_slot', save_slot).execute()
        if response.data:
            player_save_id = response.data[0]['id']
            dungeon.save_to_db(player_save_id, user_id=user_id, save_slot=save_slot)
        session['just_defeated_enemy'] = True
        return render_game(
            player, dungeon,
            narrative=narrative,
            actions=[],
            saved=saved,
            enemy=None,
            enemy_description=enemy_description,
            interaction=interaction,
            enemy_defeated_transition=True
        )
    else:
        # Enemy attacks back
        enemy_attack = enemy.attack_player(player)
        interaction += f"\n{enemy.name} uses {enemy_attack['skill_used']} and deals {enemy_attack['damage_dealt']} damage! (Your HP: {player.health})"
        dungeon.room_enemies[str(player.player_location)] = {
            "name": enemy.name,
            "health": enemy.health,
            "max_health": enemy.max_health,
            "defense": enemy.defense,
            "skills": enemy.skills
        }
        player.save_player_data(user_id, save_slot)
        response = supabase.table('player_saves').select('id').eq('user_id', user_id).eq('save_slot', save_slot).execute()
        if response.data:
            player_save_id = response.data[0]['id']
            dungeon.save_to_db(player_save_id, user_id=user_id, save_slot=save_slot)
        return None, interaction

def handle_heal_action(player, enemy):
    if player.heal():
        interaction = "You used a health potion and restored some health."
    else:
        interaction = "You don't have any health potions left."
    if enemy:
        enemy_attack = enemy.attack_player(player)
        interaction += f" {enemy.name} uses {enemy_attack['skill_used']} and deals {enemy_attack['damage_dealt']} damage! (Your HP: {player.health})"
    return interaction

def handle_move_action(player, dungeon, direction, user_id, save_slot, saved):
    valid_directions = dungeon.get_valid_directions(player.player_location)
    if direction in valid_directions:
        if player.move(direction, dungeon):
            player.save_player_data(user_id, save_slot)
            response = supabase.table('player_saves').select('id').eq('user_id', user_id).eq('save_slot', save_slot).execute()
            if not response.data:
                return redirect(url_for('auth.select_save'))
            player_save_id = response.data[0]['id']
            dungeon.save_to_db(player_save_id=player_save_id, user_id=user_id, save_slot=save_slot)
            room_enemy_data = dungeon.room_enemies.get(str(player.player_location))
            enemy = None
            enemy_description = None
            if room_enemy_data:
                enemy = Enemy(
                    name=room_enemy_data['name'],
                    health=room_enemy_data['health'],
                    max_health=room_enemy_data['max_health'],
                    defense=room_enemy_data['defense'],
                    skills=room_enemy_data['skills'],
                    dungeon=dungeon
                )
                enemy_description = dungeon.room_enemy_descriptions.get(str(player.player_location))
                narrative = enemy_description or f"A {enemy.name} appears!"
                actions = get_skill_actions(player)
            else:
                narrative = dungeon.get_room_description(player)
                actions = get_movement_actions(player, dungeon)
            return render_game(
                player, dungeon,
                narrative=narrative,
                actions=actions,
                saved=saved,
                enemy=enemy,
                enemy_description=enemy_description
            )
    return None

def handle_descend_action(player, user_id, save_slot, saved):
    player.dungeon_floor += 1
    dungeon = Dungeon(width=10, height=10, num_rooms=5, floor_level=player.dungeon_floor)
    dungeon.generate()
    player.player_location = dungeon.start_location[0]
    player.save_player_data(user_id, save_slot)
    response = supabase.table('player_saves').select('id').eq('user_id', user_id).eq('save_slot', save_slot).execute()
    if not response.data:
        return redirect(url_for('auth.select_save'))
    player_save_id = response.data[0]['id']
    dungeon.save_to_db(player_save_id, user_id=user_id, save_slot=save_slot)
    actions = get_movement_actions(player, dungeon)
    return render_game(
        player, dungeon,
        narrative=dungeon.room_descriptions.get(str(dungeon.start_location[0]), "You descend to the next floor."),
        actions=actions,
        saved=saved,
        enemy=None,
        enemy_description=None
    )