from flask import redirect, render_template, session, url_for

from backend.app.db import supabase
from backend.game.enemy import Enemy
from backend.game.merchant import Merchant

ENEMY_FIELDS = {'name', 'health', 'max_health', 'defense', 'skills'}


def get_player_save_id(user_id, save_slot):
    response = supabase.table('player_saves').select('id').eq('user_id', user_id).eq('save_slot', save_slot).execute()
    if not response.data:
        return None
    return response.data[0]['id']


def persist_game_state(player, dungeon, user_id, save_slot):
    player.save_player_data(user_id, save_slot)
    player_save_id = get_player_save_id(user_id, save_slot)
    if player_save_id is None:
        return False
    dungeon.save_to_db(player_save_id=player_save_id, user_id=user_id, save_slot=save_slot)
    return True


def _normalize_room_state(room_state):
    if not room_state or not isinstance(room_state, dict):
        return {'enemy': None, 'merchant': None}

    if 'enemy' in room_state or 'merchant' in room_state:
        return {
            'enemy': room_state.get('enemy'),
            'merchant': room_state.get('merchant'),
        }

    if ENEMY_FIELDS.issubset(room_state.keys()):
        return {'enemy': room_state, 'merchant': None}

    return {'enemy': None, 'merchant': None}


def set_room_state(dungeon, room_id, enemy=None, merchant=None):
    room_state = {}
    if enemy:
        room_state['enemy'] = enemy
    if merchant:
        room_state['merchant'] = merchant
    dungeon.room_enemies[str(room_id)] = room_state


def build_enemy_for_room(dungeon, room_id):
    room_state = _normalize_room_state(dungeon.room_enemies.get(str(room_id)))
    room_enemy_data = room_state['enemy']
    if not room_enemy_data:
        return None, None

    enemy = Enemy(
        name=room_enemy_data['name'],
        health=room_enemy_data['health'],
        max_health=room_enemy_data['max_health'],
        defense=room_enemy_data['defense'],
        skills=room_enemy_data['skills'],
        dungeon=dungeon,
        loot=room_enemy_data.get('loot')
    )
    enemy_description = dungeon.room_enemy_descriptions.get(str(room_id))
    return enemy, enemy_description


def build_merchant_for_room(dungeon, room_id):
    room_id = str(room_id)
    room_state = _normalize_room_state(dungeon.room_enemies.get(room_id))
    merchant_data = room_state['merchant']

    if not merchant_data and dungeon.merchant_location and str(dungeon.merchant_location[0]) == room_id:
        merchant = Merchant(dungeon)
        merchant.generate_inventory(dungeon)
        description = merchant.load_description()
        merchant.description = description
        merchant_data = merchant.to_state()
        set_room_state(dungeon, room_id, enemy=room_state['enemy'], merchant=merchant_data)
        if description:
            dungeon.room_descriptions[room_id] = description

    if not merchant_data:
        return None, None

    description = merchant_data.get('description') or dungeon.room_descriptions.get(room_id)
    merchant = Merchant(
        dungeon,
        inventory=merchant_data.get('inventory', []),
        gold_amount=merchant_data.get('gold_amount'),
        description=description,
    )
    return merchant, description


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
    if str(player.player_location) == str(dungeon.exit_location[0]):
        actions.append({
            'label': "Descend to the Next Floor",
            'value': "descend_next_floor",
            'enabled': True,
            'is_descend': True
        })
    return actions


def get_skill_actions(player):
    attack_bonus = player.get_attack_bonus()
    return [
        {
            'label': f"{skill['name'].capitalize()} (Damage: {skill['damage'] + attack_bonus})",
            'value': f"skill_{skill['name']}"
        }
        for skill in player.skills
    ] + [{'label': "Heal", 'value': "heal"}]


def render_game(player, dungeon, narrative, actions, saved, enemy=None, enemy_description=None, interaction=None, enemy_defeated_transition=False, merchant=None):
    return render_template(
        'game.html',
        narrative=narrative,
        interaction=interaction,
        actions=actions,
        health=player.health,
        max_health=player.max_health,
        inventory=player.get_inventory(),
        inventory_items=player.get_inventory_items(),
        equipment_items=player.get_equipment_details(),
        equipped_loadout=player.get_equipped_loadout(),
        saved=saved,
        enemy=enemy,
        enemy_description=enemy_description,
        merchant=merchant,
        player_defense=player.defense,
        player_attack_bonus=player.get_attack_bonus(),
        player_gold=player.inventory.get('gold', 0),
        player_level=player.level,
        player_experience=player.experience,
        next_level_experience=player.level * 10,
        dungeon_floor=player.dungeon_floor,
        enemy_defeated_transition=enemy_defeated_transition
    )


def render_current_room(player, dungeon, saved, interaction=None, narrative_override=None, enemy=None, enemy_description=None, merchant=None):
    if enemy is None and enemy_description is None:
        enemy, enemy_description = build_enemy_for_room(dungeon, player.player_location)

    if merchant is None:
        merchant, _ = build_merchant_for_room(dungeon, player.player_location)

    if narrative_override is not None:
        narrative = narrative_override
    elif enemy:
        narrative = enemy_description or f"A {enemy.name} appears!"
    elif merchant and merchant.description:
        narrative = merchant.description
    else:
        narrative = dungeon.get_room_description(player)

    actions = get_skill_actions(player) if enemy else get_movement_actions(player, dungeon)
    return render_game(
        player,
        dungeon,
        narrative=narrative,
        actions=actions,
        saved=saved,
        enemy=enemy,
        enemy_description=enemy_description,
        interaction=interaction,
        merchant=merchant,
    )


def handle_player_defeat(player, dungeon, user_id, save_slot, saved, interaction):
    lost_gold = 0
    current_gold = player.inventory.get('gold', 0)
    if current_gold > 0:
        lost_gold = max(1, current_gold // 4)
        player.inventory['gold'] = max(0, current_gold - lost_gold)

    player.health = player.max_health
    player.player_location = dungeon.start_location[0]

    defeat_lines = [interaction, 'You collapse and awaken back at the floor entrance.']
    if lost_gold:
        defeat_lines.append(f'You dropped {lost_gold} gold in the dark.')

    if not persist_game_state(player, dungeon, user_id, save_slot):
        return redirect(url_for('auth.select_save'))

    return render_current_room(
        player,
        dungeon,
        saved=saved,
        interaction="\n".join(line for line in defeat_lines if line),
    )


def handle_combat_action(player, dungeon, enemy, enemy_description, action, user_id, save_slot, saved):
    interaction = player.attack_enemy(enemy, action[len('skill_'):])
    if not interaction:
        return render_game(
            player, dungeon,
            narrative=enemy_description or f"A {enemy.name} appears!",
            actions=get_skill_actions(player),
            saved=saved,
            enemy=enemy,
            enemy_description=enemy_description,
            interaction="That skill is not available.",
        )

    room_state = _normalize_room_state(dungeon.room_enemies.get(str(player.player_location)))

    if enemy.health <= 0:
        loot_summary = player.collect_loot(enemy.loot)
        experience = player.gain_experience(dungeon.floor_level * 4 + enemy.defense + len(enemy.skills))
        narrative = f"{enemy.name} is defeated!"
        set_room_state(dungeon, player.player_location, merchant=room_state['merchant'])
        if not persist_game_state(player, dungeon, user_id, save_slot):
            return redirect(url_for('auth.select_save'))

        reward_lines = [f"Gained {experience['awarded']} experience."]
        if loot_summary:
            reward_lines.insert(0, f"Loot found: {loot_summary}.")
        if experience['leveled_up']:
            reward_lines.append(f"Level up! You are now level {player.level}.")

        interaction = "\n".join([line for line in [interaction, *reward_lines] if line])
        session['just_defeated_enemy'] = True
        return render_game(
            player, dungeon,
            narrative=narrative,
            actions=[],
            saved=saved,
            enemy=None,
            enemy_description=enemy_description,
            interaction=interaction,
            enemy_defeated_transition=True,
            merchant=None,
        )

    enemy_attack = enemy.attack_player(player)
    interaction += f"\n{enemy.name} uses {enemy_attack['skill_used']} and deals {enemy_attack['damage_dealt']} damage! (Your HP: {player.health})"
    set_room_state(dungeon, player.player_location, enemy={
        "name": enemy.name,
        "health": enemy.health,
        "max_health": enemy.max_health,
        "defense": enemy.defense,
        "skills": enemy.skills,
        "loot": enemy.loot,
    }, merchant=room_state['merchant'])

    if player.health <= 0:
        return handle_player_defeat(player, dungeon, user_id, save_slot, saved, interaction)

    if not persist_game_state(player, dungeon, user_id, save_slot):
        return redirect(url_for('auth.select_save'))
    return None, interaction


def handle_heal_action(player, dungeon, enemy, user_id, save_slot, saved):
    if player.heal():
        interaction = "You used a health potion and restored some health."
    else:
        interaction = "You don't have any health potions left."

    room_state = _normalize_room_state(dungeon.room_enemies.get(str(player.player_location)))
    if enemy:
        enemy_attack = enemy.attack_player(player)
        interaction += f" {enemy.name} uses {enemy_attack['skill_used']} and deals {enemy_attack['damage_dealt']} damage! (Your HP: {player.health})"
        set_room_state(dungeon, player.player_location, enemy={
            "name": enemy.name,
            "health": enemy.health,
            "max_health": enemy.max_health,
            "defense": enemy.defense,
            "skills": enemy.skills,
            "loot": enemy.loot,
        }, merchant=room_state['merchant'])

        if player.health <= 0:
            return handle_player_defeat(player, dungeon, user_id, save_slot, saved, interaction)

    if not persist_game_state(player, dungeon, user_id, save_slot):
        return redirect(url_for('auth.select_save'))

    return interaction


def handle_inventory_action(player, dungeon, enemy, action, user_id, save_slot, saved):
    _, item_name = action.split('::', 1)

    if action.startswith('use_item::'):
        if item_name != 'health potion':
            interaction = f"{item_name.title()} can't be used right now."
            return render_current_room(player, dungeon, saved=saved, interaction=interaction, enemy=enemy)

        result = handle_heal_action(player, dungeon, enemy, user_id, save_slot, saved)
        if hasattr(result, 'status_code'):
            return result
        return render_current_room(player, dungeon, saved=saved, interaction=result)

    if enemy:
        return render_current_room(
            player,
            dungeon,
            saved=saved,
            interaction="You can't change equipment in the middle of a fight.",
            enemy=enemy,
        )

    equipment_result = player.toggle_equipment(item_name)
    if not persist_game_state(player, dungeon, user_id, save_slot):
        return redirect(url_for('auth.select_save'))
    return render_current_room(player, dungeon, saved=saved, interaction=equipment_result['message'])


def handle_merchant_action(player, dungeon, merchant, action, user_id, save_slot, saved):
    _, item_name = action.split('::', 1)
    if action.startswith('merchant_buy::'):
        result = merchant.sell_item_to_player(item_name, player)
    else:
        result = merchant.buy_item_from_player(item_name, player)

    room_state = _normalize_room_state(dungeon.room_enemies.get(str(player.player_location)))
    set_room_state(dungeon, player.player_location, enemy=room_state['enemy'], merchant=merchant.to_state())

    if not persist_game_state(player, dungeon, user_id, save_slot):
        return redirect(url_for('auth.select_save'))

    return render_current_room(player, dungeon, saved=saved, interaction=result['message'], merchant=merchant)


def handle_move_action(player, dungeon, direction, user_id, save_slot, saved):
    valid_directions = dungeon.get_valid_directions(player.player_location)
    if direction in valid_directions and player.move(direction, dungeon):
        enemy, enemy_description = build_enemy_for_room(dungeon, player.player_location)
        merchant, merchant_description = build_merchant_for_room(dungeon, player.player_location)
        if not persist_game_state(player, dungeon, user_id, save_slot):
            return redirect(url_for('auth.select_save'))

        if enemy:
            narrative = enemy_description or f"A {enemy.name} appears!"
            actions = get_skill_actions(player)
        elif merchant and merchant_description:
            narrative = merchant_description
            actions = get_movement_actions(player, dungeon)
        else:
            narrative = dungeon.get_room_description(player)
            actions = get_movement_actions(player, dungeon)

        return render_game(
            player, dungeon,
            narrative=narrative,
            actions=actions,
            saved=saved,
            enemy=enemy,
            enemy_description=enemy_description,
            merchant=merchant,
        )
    return None


def handle_descend_action(player, user_id, save_slot, saved):
    from backend.game.dungeon import Dungeon

    player.dungeon_floor += 1
    dungeon = Dungeon(width=10, height=10, num_rooms=5, floor_level=player.dungeon_floor)
    dungeon.generate()
    player.player_location = dungeon.start_location[0]
    if not persist_game_state(player, dungeon, user_id, save_slot):
        return redirect(url_for('auth.select_save'))
    return render_current_room(player, dungeon, saved=saved)
