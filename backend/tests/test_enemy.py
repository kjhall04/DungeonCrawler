import unittest
from backend.game.enemy import Enemy

class TestEnemy(unittest.TestCase):
    def setUp(self):
        """Set up a test enemy for each test."""
        class MockDungeon:
            def __init__(self, floor_level):
                self.floor_level = floor_level

        self.dungeon = MockDungeon(floor_level=1)
        self.enemy = Enemy(name="goblin", health=10, max_health=10, defense=2, skills=[], dungeon=self.dungeon)

    def test_initialization(self):
        """Test enemy initialization."""
        self.assertEqual(self.enemy.name, "goblin")
        self.assertEqual(self.enemy.health, 10)
        self.assertEqual(self.enemy.defense, 2)

    def test_take_damage(self):
        """Test the enemy taking damage."""
        damage_taken = self.enemy.take_damage(5)
        self.assertEqual(damage_taken, 3)  # 5 - defense (2)
        self.assertEqual(self.enemy.health, 7)

    def test_load_loot(self):
        """Test loading loot for the enemy."""
        loot = self.enemy.load_loot(self.dungeon)
        self.assertIsInstance(loot, dict)

if __name__ == "__main__":
    unittest.main()