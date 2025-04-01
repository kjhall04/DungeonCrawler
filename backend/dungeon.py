import json
import random as rand
import re
import networkx as nx
import matplotlib.pyplot as plt

DUNGEON_SAVE = 'data\\dungeon_floor_save.json'

BRANCH_CHANCE = 0.4  # Chance to branch out from the current path
ADD_CONNECTION_CHANCE = 0.3  # Chance to add extra connections between rooms

class DungeonGenerator():
    def __init__(self, width, height, num_rooms):
        self.width = width
        self.height = height
        self.num_rooms = num_rooms
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.rooms = {}
        self.room_positions = {}

    def generate(self):
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


    def add_start():
        pass

    def add_exit():
        pass

    def add_merchant():
        pass

    def save_to_json(self, filename=DUNGEON_SAVE):
        """Saves the dungeon layout to a json file."""
        cleaned_connections = {str(room_id): connections for room_id, connections in sorted(self.rooms.items()) if connections}

        data = {
            "grid_size": {"width": self.width, "height": self.height},
            "num_rooms": self.num_rooms,
            "room_positions": {str(room_id): list(position) for room_id, position in self.room_positions.items()},
            "connections": cleaned_connections
        }

        json_str = json.dumps(data, indent=4, sort_keys=False)

        # Extra formatting to remove unnecessary newlines and spaces
        json_str = re.sub(r'\[\n\s+(\d+)\n\s+\]', r'[\1]', json_str)  # For 1-item lists
        json_str = re.sub(r'\[\n\s+(\d+),\n\s+(\d+)\n\s+\]', r'[\1, \2]', json_str)  # For 2-item lists
        json_str = re.sub(r'\[\n\s+(\d+),\n\s+(\d+),\n\s+(\d+)\n\s+\]', r'[\1, \2, \3]', json_str)  # For 3-item lists
        json_str = re.sub(r'\[\n\s+(\d+),\n\s+(\d+),\n\s+(\d+),\n\s+(\d+)\n\s+\]', r'[\1, \2, \3, \4]', json_str)  # For 4-item lists

        with open(filename, 'w') as file:
            file.write(json_str)
        return None

    def plot_graph(self):
        """Plots the dungeon layout as a graph using NetworkX. For debugging purposes."""
        graph = nx.Graph()
        for room, connections in self.rooms.items():
            for connection in connections:
                graph.add_edge(room, connection)

        pos = {room: (self.room_positions[room][0], -self.room_positions[room][1]) for room in self.rooms}
        nx.draw(graph, pos, with_labels=True, node_size=500, node_color='skyblue', font_size=10, font_weight='bold', edge_color='gray')

        plt.title("Dungeon Layout")
        plt.show()



if __name__ == '__main__':

    width, height = 10, 10
    rooms = rand.randint(12, 15)
    
    dungeon = DungeonGenerator(width, height, rooms)
    dungeon.generate()
    dungeon.plot_graph()
    dungeon.save_to_json()