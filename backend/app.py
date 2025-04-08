from flask import Flask, request, jsonify, render_template
# from backend.player import Player
# from backend.dungeon import DungeonGenerator
# from backend.story_elements import player_creation
# from backend.enemy import Enemy

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend')

@app.route('/')
def indes():
    """Serve the main html page."""
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)