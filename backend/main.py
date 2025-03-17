from player import Player
from enemy import Enemy


if __name__ == '__main__':

    player = Player()
    enemy = Enemy()

    print(f'Hello {player.name}\nHealth: {player.health}\nDefense: {player.defense}\nAttack: {player.attack}\n')
    print(f'The enemy is a {enemy.name}\nHealth: {enemy.health},\nDefense: {enemy.defense},\nAttack: {enemy.attack}\n')