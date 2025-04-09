import unittest
from backend.game.player import Player

class TestPlayer(unittest.TestCase):
    def setUp(self):
        """Set up a test player for each test."""
        self.player = Player(name="TestPlayer", player_class="warrior")

    def test_initialization(self):
        """Test player initialization."""
        self.assertEqual(self.player.name, "TestPlayer")
        self.assertEqual(self.player.player_class, "warrior")
        self.assertEqual(self.player.health, 20)
        self.assertEqual(self.player.inventory['gold'], 5)

    def test_take_damage(self):
        """Test the player taking damage."""
        damage_taken = self.player.take_damage(10)
        self.assertEqual(damage_taken, 7)  # 10 - defense (3)
        self.assertEqual(self.player.health, 13)

    def test_heal(self):
        """Test the player healing."""
        self.player.health = 10
        healed = self.player.heal()
        self.assertTrue(healed)
        self.assertEqual(self.player.health, 15)
        self.assertEqual(self.player.inventory['health_potions'], 2)

    def test_add_item_to_inventory(self):
        """Test adding items to the player's inventory."""
        added = self.player.add_item_to_inventory("iron sword", 1)
        self.assertTrue(added)
        self.assertIn("iron sword", self.player.inventory['equipment'])

    def test_move(self):
        """Test player movement."""
        class MockDungeon:
            def get_valid_directions(self, room_id):
                return {"north": 1, "south": 2}

        dungeon = MockDungeon()
        self.player.player_location = 0
        moved = self.player.move("north", dungeon)
        self.assertTrue(moved)
        self.assertEqual(self.player.player_location, 1)

if __name__ == "__main__":
    unittest.main()