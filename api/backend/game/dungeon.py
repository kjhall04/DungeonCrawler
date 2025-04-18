from backend.app.db import supabase
import json
import random as rand
import networkx as nx 
import matplotlib.pyplot as plt

BRANCH_CHANCE = 0.4  # Chance to branch out from the current path
ADD_CONNECTION_CHANCE = 0.3  # Chance to add extra connections between rooms
MERCHANT_CHANCE = 0.7  # Chance to add a merchant in the dungeon

class Dungeon():
    def __init__(self, width, height, num_rooms, floor_level):
        self.width = width
        self.height = height
        self.num_rooms = num_rooms
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.rooms = {}
        self.room_positions = {}
        self.start_location = []
        self.exit_location = []
        self.merchant_location = []
        self.floor_level = floor_level

    @classmethod
    def load_from_db(cls, player_save_id: int):
        """Load dungeon data from the database."""
        response = supabase.table('dungeons').select('*').eq('player_save_id', player_save_id).execute()
        if not response.data:
            return None
        dungeon_data = response.data[0]
        dungeon = cls(
            width=dungeon_data['width'],
            height=dungeon_data['height'],
            num_rooms=dungeon_data['num_rooms'],
            floor_level=dungeon_data['floor_level']
        )
        dungeon.room_positions = json.loads(dungeon_data['room_positions'])
        dungeon.rooms = json.loads(dungeon_data['connections'])
        dungeon.start_location = json.loads(dungeon_data['start_location'])
        dungeon.exit_location = json.loads(dungeon_data['exit_location'])
        dungeon.merchant_location = json.loads(dungeon_data['merchant_location']) if dungeon_data['merchant_location'] else None
        return dungeon

    def save_to_db(self, player_save_id: int):
        """Save dungeon data to the database."""
        response = supabase.table('dungeons').select('*').eq('player_save_id', player_save_id).execute()
        if not response.data:
            # Create a new Dungeon entry
            supabase.table('dungeons').insert({
                'player_save_id': player_save_id,
                'width': self.width,
                'height': self.height,
                'num_rooms': self.num_rooms,
                'room_positions': json.dumps(self.room_positions),
                'connections': json.dumps(self.rooms),
                'start_location': json.dumps(self.start_location),
                'exit_location': json.dumps(self.exit_location),
                'merchant_location': json.dumps(self.merchant_location) if self.merchant_location else None,
                'floor_level': self.floor_level
            }).execute()
        else:
            # Update existing Dungeon entry
            supabase.table('dungeons').update({
                'width': self.width,
                'height': self.height,
                'num_rooms': self.num_rooms,
                'room_positions': json.dumps(self.room_positions),
                'connections': json.dumps(self.rooms),
                'start_location': json.dumps(self.start_location),
                'exit_location': json.dumps(self.exit_location),
                'merchant_location': json.dumps(self.merchant_location) if self.merchant_location else None,
                'floor_level': self.floor_level
            }).eq('player_save_id', player_save_id).execute()

    def generate(self):
        # Designed with help of Chatgpt
        """Generate a dungeon with a mix of linear paths and branching connections."""
        start_x, start_y = rand.randint(0, self.width - 1), rand.randint(0, self.height - 1)
        self.grid[start_y][start_x] = 0
        self.room_positions[0] = (start_x, start_y)
        self.rooms[0] = []

        stack = [(start_x, start_y, 0)]  # (x, y, room_id)
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
                    self.room_positions[room_id] = (nx, ny)
                    self.rooms[room_id] = []
                    self.rooms[current_id].append(room_id)
                    self.rooms[room_id].append(current_id)
                    stack.append((nx, ny, room_id))
                    room_id += 1
                    created_new_room = True

                    # **New Feature: Chance to branch or loop**
                    # 40% chance to branch: higher value = more branching 
                    if rand.random() < BRANCH_CHANCE and len(stack) > 3:  
                        stack.pop(rand.randint(0, len(stack) - 3))

                    break  # Move to the next room

            if not created_new_room:
                stack.pop()  # Backtrack if no new room was created

        self._connect_extra_paths()

        self.add_start()
        self.add_exit()
        self.add_merchant()

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
        start_id = rand.choice([0, max(self.room_positions.keys())])
        self.start_location = (start_id, self.room_positions[start_id])

    def add_exit(self):
        """Randomly select a room to be the exit location."""
        if self.start_location[0] == max(self.rooms):
            exit_id = min(self.rooms)  # Choose the smallest room ID if the start is the largest
        else:
            exit_id = max(self.rooms)  # Choose the largest room ID otherwise
        self.exit_location = (exit_id, self.room_positions[exit_id])

    def add_merchant(self):
        """Randomly select a room to be the merchant location."""
        if rand.random() < MERCHANT_CHANCE:
            merchant_candidates = [room for room in self.room_positions.keys() if room not in (self.start_location[0], self.exit_location[0])]
            merchant_id = rand.choice(merchant_candidates)
            self.merchant_location = (merchant_id, self.room_positions[merchant_id])

    def get_valid_directions(self, room_id):
        """Returns the valid directions (north, south, east, west) the player can move in a given room."""
        directions = {}
        x, y = self.room_positions[room_id]

        # Check each direction
        for dx, dy, direction in [(0, -1, 'north'), (0, 1, 'south'), (1, 0, 'east'), (-1, 0, 'west')]:
            nx, ny = x + dx, y + dy
            neighbor_id = next((id for id, pos in self.room_positions.items() if pos == (nx, ny)), None)
            if neighbor_id:
                directions[direction] = neighbor_id

        return directions
    
    def get_room_description():
        pass

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



if __name__ == '__main__':

    width, height = 10, 10
    rooms = rand.randint(14, 20)
    username = 'hallkj04'
    
    dungeon = Dungeon(width, height, rooms, 1)
    dungeon.generate()
    dungeon.plot_graph()