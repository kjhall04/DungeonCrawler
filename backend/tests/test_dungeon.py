import unittest
from backend.game.dungeon import DungeonGenerator, DUNGEON_SAVE

class TestDungeonGenerator(unittest.TestCase):
    def setUp(self):
        """Set up a test dungeon for each test."""
        self.dungeon = DungeonGenerator(width=5, height=5, num_rooms=10, floor_level=1)
        self.dungeon.generate()

    def test_dungeon_generation(self):
        """Test that the dungeon generates the correct number of rooms."""
        self.assertEqual(len(self.dungeon.room_positions), 10)
        self.assertIn(self.dungeon.start_location[0], self.dungeon.rooms)
        self.assertIn(self.dungeon.exit_location[0], self.dungeon.rooms)

    def test_valid_directions(self):
        """Test that valid directions are returned for a room."""
        room_id = list(self.dungeon.room_positions.keys())[0]
        directions = self.dungeon.get_valid_directions(room_id)
        self.assertIsInstance(directions, dict)
        self.assertTrue(all(direction in ["north", "south", "east", "west"] for direction in directions))

    def test_save_to_json(self):
        """Test saving the dungeon to a JSON file."""
        self.dungeon.save_to_json()
        with open(DUNGEON_SAVE, "r") as file:
            data = file.read()
        self.assertIn("grid_size", data)
        self.assertIn("connections", data)

if __name__ == "__main__":
    unittest.main()