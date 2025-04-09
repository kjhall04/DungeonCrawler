import unittest
from backend.app.__init__ import create_app

class TestRoutes(unittest.TestCase):
    def setUp(self):
        """Set up the Flask test client."""
        app = create_app()
        app.testing = True
        self.client = app.test_client()

    def test_login_route(self):
        """Test the login route."""
        response = self.client.post("/login", json={"username": "test_user", "password": "test_password"})
        self.assertEqual(response.status_code, 200)  # Assuming no user exists yet

    def test_create_account_route(self):
        """Test the create account route."""
        response = self.client.post("/create_account", json={"username": "test_user", "password": "test_password"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Account created successfully", response.get_data(as_text=True))

    def test_move_player_route(self):
        """Test the player movement route."""
        response = self.client.post("/api/move", json={"direction": "north", "player_location": 0})
        self.assertEqual(response.status_code, 400)  # Assuming no valid dungeon/player data

if __name__ == "__main__":
    unittest.main()