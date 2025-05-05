from backend.app.db import supabase
import os
import json
import random as rand
import networkx as nx 
import matplotlib.pyplot as plt

BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DESCRIPTIONS = os.path.join(BASE_DIRECTORY, '..', 'data', 'descriptions.json')
ENEMIES = os.path.join(BASE_DIRECTORY, '..', 'data', 'enemies.json')

BRANCH_CHANCE = 0.4  # Chance to branch out from the current path
ADD_CONNECTION_CHANCE = 0.3  # Chance to add extra connections between rooms
MERCHANT_CHANCE = 0.85  # Chance to add a merchant in the dungeon
ENEMY_CHANCE = 0.65  # Chance to add an enemy in a room

class Dungeon():
    def __init__(self, width, height, num_rooms, floor_level):
        self.width = width
        self.height = height
        self.num_rooms = num_rooms
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.rooms = {}
        self.room_positions = {}
        self.room_descriptions = {}
        self.room_enemies = {}
        self.room_enemy_descriptions = {}
        self.start_location = []
        self.exit_location = []
        self.merchant_location = []
        self.floor_level = floor_level
        self.previous_description = None

    @classmethod
    def load_from_db(cls, user_id: int, save_slot: int):
        """Load dungeon data from the database."""
        response = supabase.table('dungeons').select('*').eq('user_id', user_id).eq('save_slot', save_slot).execute()
        if not response.data:
            return None
        dungeon_data = response.data[0]
        dungeon = cls(
            width=dungeon_data['width'],
            height=dungeon_data['height'],
            num_rooms=dungeon_data['num_rooms'],
            floor_level=dungeon_data['floor_level']
        )
        dungeon.room_positions = {str(k): tuple(v) for k, v in json.loads(dungeon_data['room_positions']).items()}
        dungeon.rooms = {str(k): [str(i) for i in v] for k, v in json.loads(dungeon_data['connections']).items()}
        dungeon.start_location = json.loads(dungeon_data['start_location'])
        dungeon.exit_location = json.loads(dungeon_data['exit_location'])
        dungeon.merchant_location = json.loads(dungeon_data['merchant_location']) if dungeon_data['merchant_location'] else None
        dungeon.room_descriptions = json.loads(dungeon_data['room_descriptions'])
        dungeon.room_enemies = json.loads(dungeon_data['room_enemies'])
        dungeon.room_enemy_descriptions = json.loads(dungeon_data['room_enemy_descriptions'])

        dungeon.position_to_id = {tuple(pos): room_id for room_id, pos in dungeon.room_positions.items()}
        
        return dungeon

    def save_to_db(self, player_save_id: int, user_id: int, save_slot: int):
        """Save dungeon data to the database."""
        response = supabase.table('dungeons').select('*').eq('user_id', user_id).eq('save_slot', save_slot).execute()
        if not response.data:
            # Create a new Dungeon entry
            supabase.table('dungeons').insert({
                'player_save_id': player_save_id,
                'user_id': user_id,
                'width': self.width,
                'height': self.height,
                'num_rooms': self.num_rooms,
                'room_positions': json.dumps({str(k): v for k, v in self.room_positions.items()}),
                'connections': json.dumps({str(k): [str(i) for i in v] for k, v in self.rooms.items()}),
                'start_location': json.dumps(self.start_location),
                'exit_location': json.dumps(self.exit_location),
                'merchant_location': json.dumps(self.merchant_location) if self.merchant_location else None,
                'floor_level': self.floor_level,
                'save_slot': save_slot,
                'room_descriptions': json.dumps(self.room_descriptions),
                'room_enemies': json.dumps(self.room_enemies),
                'room_enemy_descriptions': json.dumps(self.room_enemy_descriptions)
            }).execute()
        else:
            # Update existing Dungeon entry
            supabase.table('dungeons').update({
                'width': self.width,
                'height': self.height,
                'num_rooms': self.num_rooms,
                'room_positions': json.dumps({str(k): v for k, v in self.room_positions.items()}),
                'connections': json.dumps({str(k): [str(i) for i in v] for k, v in self.rooms.items()}),
                'start_location': json.dumps(self.start_location),
                'exit_location': json.dumps(self.exit_location),
                'merchant_location': json.dumps(self.merchant_location) if self.merchant_location else None,
                'floor_level': self.floor_level,
                'room_descriptions': json.dumps(self.room_descriptions),
                'room_enemies': json.dumps(self.room_enemies),
                'room_enemy_descriptions': json.dumps(self.room_enemy_descriptions)
            }).eq('user_id', user_id).eq('save_slot', save_slot).execute()

    def generate(self):
        """Generate a dungeon with a mix of linear paths and branching connections."""
        self.position_to_id = {}  # Initialize the position-to-ID mapping

        start_x, start_y = rand.randint(0, self.width - 1), rand.randint(0, self.height - 1)
        self.grid[start_y][start_x] = 0
        self.room_positions["0"] = (start_x, start_y)
        self.position_to_id[(start_x, start_y)] = "0"  # Map position to string room ID
        self.rooms["0"] = []

        stack = [(start_x, start_y, "0")]  # (x, y, room_id as str)
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Up, Right, Down, Left
        room_id = 1

        while stack and len(self.room_positions) < self.num_rooms:
            x, y, current_id = stack[-1]
            rand.shuffle(directions)  # Shuffle directions for variety
            created_new_room = False

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < self.width and 0 <= ny < self.height
                    and self.grid[ny][nx] is None
                    and len(self.room_positions) < self.num_rooms
                ):
                    # Create a new room
                    self.grid[ny][nx] = room_id
                    str_room_id = str(room_id)
                    self.room_positions[str_room_id] = (nx, ny)
                    self.position_to_id[(nx, ny)] = str_room_id  # Map position to string room ID
                    self.rooms[str_room_id] = []
                    self.rooms[current_id].append(str_room_id)
                    self.rooms[str_room_id].append(current_id)
                    stack.append((nx, ny, str_room_id))
                    room_id += 1
                    created_new_room = True

                    break  # Move to the next room

            if not created_new_room:
                stack.pop()  # Backtrack if no new room was created

        self.get_room_description(player=None, type_key="descriptions")
        self._connect_extra_paths()
        self.add_start()
        self.add_exit()
        self.add_entrance_exit_descriptions()
        self.add_merchant()
        self.place_enemies()
        self.room_enemy_descriptions = {}
        for room_id, enemy_data in self.room_enemies.items():
            if enemy_data:
                self.room_enemy_descriptions[room_id] = self._generate_enemy_description(enemy_data['name'])

    def _connect_extra_paths(self):
        """Add extra connections between nearby rooms for more interconnectivity."""
        for room_id, (x, y) in self.room_positions.items():
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                neighbor_id = next((id for id, pos in self.room_positions.items() if pos == (nx, ny)), None)

                if neighbor_id and neighbor_id != room_id and neighbor_id not in self.rooms[room_id]:
                    # Chance to add an extra connection
                    # 30% chance to add extra connection: higher value = more branching
                    if rand.random() < ADD_CONNECTION_CHANCE:
                        self.rooms[room_id].append(neighbor_id)
                        self.rooms[neighbor_id].append(room_id)

    def add_start(self):
        """Randomly select a room to be the start location."""
        start_id = rand.choice(["0", str(max(int(k) for k in self.room_positions.keys()))])
        self.start_location = (start_id, self.room_positions[start_id])

    def add_exit(self):
        """Randomly select a room to be the exit location."""
        if self.start_location[0] == str(max(int(k) for k in self.rooms.keys())):
            exit_id = str(min(int(k) for k in self.rooms.keys()))
        else:
            exit_id = str(max(int(k) for k in self.rooms.keys()))
        self.exit_location = (exit_id, self.room_positions[exit_id])

    def add_merchant(self):
        """Randomly select a room to be the merchant location."""
        if rand.random() < MERCHANT_CHANCE:
            merchant_candidates = [k for k in self.room_positions.keys() if k not in (self.start_location[0], self.exit_location[0])]
            merchant_id = rand.choice(merchant_candidates)
            self.merchant_location = (merchant_id, self.room_positions[merchant_id])

    def place_enemies(self):
        """Place enemies in rooms (except start/exit) during dungeon generation."""
        self.room_enemies = {}
        floor_key = f"floor_{self.floor_level}"
        try:
            with open(ENEMIES, 'r') as file:
                enemies_data = json.load(file)[floor_key]
            for room_id in self.room_positions:
                if room_id not in (self.start_location[0], self.exit_location[0]):
                    if rand.random() < ENEMY_CHANCE:
                        enemy_name = rand.choice(list(enemies_data.keys()))
                        data = enemies_data[enemy_name]
                        self.room_enemies[room_id] = {
                            "name": enemy_name,
                            "health": data["health"],
                            "max_health": data["health"],
                            "defense": data["defense"],
                            "skills": data["skills"]
                        }
                    else:
                        self.room_enemies[room_id] = None
                else:
                    self.room_enemies[room_id] = None
        except Exception as e:
            print(f"Error placing enemies: {e}")
            for room_id in self.room_positions:
                self.room_enemies[room_id] = None


    def get_valid_directions(self, room_id):
        """Returns the valid directions (north, south, east, west) the player can move in a given room."""
        room_id = str(room_id).strip('"')
        if room_id not in self.room_positions:
            print(f"Invalid room_id: {room_id}")
            return {}

        directions = {}
        x, y = self.room_positions[room_id]

        # Check each direction
        for dx, dy, direction in [(0, -1, 'north'), (0, 1, 'south'), (1, 0, 'east'), (-1, 0, 'west')]:
            neighbor_pos = (x + dx, y + dy)
            neighbor_id = self.position_to_id.get(neighbor_pos)
            if neighbor_id is not None:
                directions[direction] = str(neighbor_id)

        return directions
    
    def get_room_description(self, player=None, type_key="descriptions", filename=DESCRIPTIONS):
        """Retrieve or generate a room description."""
        # Use room_id from player or fallback to None
        room_id = str(player.player_location) if player else None

        # If room_id is None, skip player logic and handle generation
        if room_id is None:
            for room_id in self.room_positions.keys():
                if room_id not in self.room_descriptions:
                    self.room_descriptions[room_id] = self._generate_room_description(room_id, type_key, filename)
            return None  # No specific description to return during generation

        # If room_id already has a description, return it
        if room_id in self.room_descriptions:
            return self.room_descriptions[room_id]

        # Generate a new description if one doesn't exist
        self.room_descriptions[room_id] = self._generate_room_description(room_id, type_key, filename)
        return self.room_descriptions[room_id]

    def _generate_room_description(self, room_id, type_key, filename):
        """Helper method to generate a room description."""
        try:
            with open(filename, 'r') as file:
                description_data = json.load(file)

            floor_key = f"floor_{self.floor_level}"
            if floor_key in description_data and type_key in description_data[floor_key]:
                descriptions = description_data[floor_key][type_key]

                # Ensure description is not the same as the previous one
                new_description = self.previous_description
                attempts = 0
                while new_description == self.previous_description and attempts < 20:
                    version = str(rand.randint(1, len(descriptions)))
                    new_description = descriptions[version]
                    attempts += 1

                self.previous_description = new_description
                return new_description
            else:
                return f"No description found for {type_key} on {floor_key}"
        except FileNotFoundError:
            return "Description file not found."
        
    def _generate_enemy_description(self, enemy_name, filename=DESCRIPTIONS):
        """Generate a random description for a given enemy on this floor."""
        try:
            with open(filename, 'r') as file:
                description_data = json.load(file)

            floor_key = f"floor_{self.floor_level}"
            if floor_key in description_data and "enemies" in description_data[floor_key]:
                enemy_descriptions = description_data[floor_key]["enemies"].get(enemy_name)
                if enemy_descriptions:
                    return rand.choice(list(enemy_descriptions.values()))
        except Exception as e:
            print(f"Error generating enemy description: {e}")
        return f"A {enemy_name} appears!"
                    
    def add_entrance_exit_descriptions(self, filename=DESCRIPTIONS):
        """Add entrance and exit descriptions to the dungeon."""
        try:
            with open(filename, 'r') as file:
                description_data = json.load(file)

            floor_key = f"floor_{self.floor_level}"
            if floor_key in description_data:
                if "entrances" in description_data[floor_key]:
                    entrance_descriptions = description_data[floor_key]["entrances"]
                    self.room_descriptions[str(self.start_location[0])] = rand.choice(list(entrance_descriptions.values()))
            
                if "exits" in description_data[floor_key]:
                    exit_descriptions = description_data[floor_key]["exits"]
                    self.room_descriptions[str(self.exit_location[0])] = rand.choice(list(exit_descriptions.values()))
        
        except FileNotFoundError:
            print("Description file not found.")

    def plot_graph(self):
        """Plots the dungeon layout as a graph using NetworkX, highlighting start, exit, and merchant rooms. For debugging purposes."""
        graph = nx.Graph()

        for room, connections in self.rooms.items():
            for connection in connections:
                graph.add_edge(room, connection)

        pos = {room: (self.room_positions[room][0], -self.room_positions[room][1]) for room in self.rooms}

        # Define colors and sizes
        node_colors = []
        node_sizes = []

        for room in self.rooms:
            if self.room_positions[room] == self.start_location[1]:
                node_colors.append('green')   # Start room
                node_sizes.append(700)
            elif self.room_positions[room] == self.exit_location[1]:
                node_colors.append('red')     # Exit room
                node_sizes.append(700)
            elif self.room_positions[room] == self.merchant_location[1] if self.merchant_location else None:
                node_colors.append('orange')  # Merchant room
                node_sizes.append(700)
            else:
                node_colors.append('skyblue') # Regular rooms
                node_sizes.append(500)

        # Draw the graph
        plt.figure(figsize=(8, 6))
        nx.draw(graph, pos, with_labels=True, node_size=node_sizes, node_color=node_colors, 
                font_size=10, font_weight='bold', edge_color='gray')

        # Add legend
        plt.scatter([], [], c='green', s=100, label="Start Room")
        plt.scatter([], [], c='red', s=100, label="Exit Room")
        plt.scatter([], [], c='orange', s=100, label="Merchant Room")
        plt.scatter([], [], c='skyblue', s=100, label="Regular Rooms")
        plt.legend(loc="upper right")

        plt.title("Dungeon Layout")
        plt.show()