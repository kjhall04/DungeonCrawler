import json
import random as rand
import re
import os
import networkx as nx
import matplotlib.pyplot as plt

DUNGEON_SAVE = 'data\\dungeon_floor_save.json'

BRANCH_CHANCE = 0.4  # Chance to branch out from the current path
ADD_CONNECTION_CHANCE = 0.3  # Chance to add extra connections between rooms
MERCHANT_CHANCE = 0.6  # Chance to add a merchant in the dungeon

class DungeonGenerator():
    def __init__(self, width, height, num_rooms):
        self.width = width
        self.height = height
        self.num_rooms = num_rooms
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.rooms = {}
        self.room_positions = {}
        self.start_location = []
        self.exit_location = []
        self.merchant_location = []

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

    def save_to_json(self, filename=DUNGEON_SAVE):
        """Saves the dungeon layout to a json file."""
        cleaned_connections = {str(room_id): connections for room_id, connections in sorted(self.rooms.items()) if connections}

        data = {
            "grid_size": {"width": self.width, "height": self.height},
            "num_rooms": self.num_rooms,
            "room_positions": {str(room_id): list(position) for room_id, position in self.room_positions.items()},
            "connections": cleaned_connections,
            "start": self.start_location,
            "exit": self.exit_location,
            "merchant": self.merchant_location
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
    
    def delete_current_dungeon(self, filename=DUNGEON_SAVE):
        """Deletes the current dungeon file to generate a new one."""
        try:
            os.remove(filename)
            print(f"File '{filename}' deleted successfully.")
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
        except PermissionError:
            print(f"Error: Permission denied to delete '{filename}'.")
        except Exception as e:
            print(f"An error occurred: {e}")

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
    
    dungeon = DungeonGenerator(width, height, rooms)
    dungeon.delete_current_dungeon()
    dungeon.generate()
    dungeon.save_to_json()
    dungeon.plot_graph()