# One More Descent

A web-based dungeon crawler RPG built with Flask, Supabase, and modern HTML/CSS. Players create a character, explore procedurally generated dungeons, battle enemies, collect loot, and descend deeper into the darkness.   
  
Play at onemoredescent.vercel.app     
  
Note: This is still a work-in-progress application and is still missing a few features.

---

## Features

- **Character Creation:** Choose your name and class (Mage, Warrior, Rogue), each with unique skills.
- **Procedural Dungeon Generation:** Every floor is a new challenge with randomized layouts, rooms, and connections.
- **Turn-Based Combat:** Encounter a variety of enemies, each with their own skills and loot drops.
- **Inventory & Equipment:** Collect items, potions, and gear. Manage your inventory and equip powerful items.
- **Merchant Encounters:** Find merchants in the dungeon to buy and sell items.
- **Auto-Save System:** Game state is automatically saved after every action—no manual saving required.
- **Multiple Save Slots:** Up to three save slots per user.
- **Pause & Inventory Menus:** In-game menus for pausing, returning to the main menu, or viewing your inventory.
- **Responsive UI:** Clean, modern interface with custom CSS and Google Fonts.

---

## Tech Stack

- **Backend:** Python, Flask, Supabase (PostgreSQL)
- **Frontend:** HTML5, Jinja2 templates, CSS3 (Bebas Neue font, Boxicons)
- **Other:** NetworkX & Matplotlib for dungeon visualization (debugging), dotenv for config

---

## Project Structure

```
DungeonCrawler/
│
├── api/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── routes.py         # Main Flask routes (game logic, auth, menus)
│   │   │   ├── game_api.py       # API endpoints (load/save, player stats)
│   │   │   ├── db.py             # Supabase DB connection
│   │   │   └── auth.py           # Account creation & login logic
│   │   │   └── game_action.py    # Reused logic used in the game action route
│   │   ├── game/
│   │   │   ├── player.py         # Player class & logic
│   │   │   ├── dungeon.py        # Dungeon generation & logic
│   │   │   ├── enemy.py          # Enemy class & logic
│   │   │   └── merchant.py       # Merchant class & logic
│   │   └── data/                 # Game data (skills, loot, enemies, descriptions)
│   ├── index.py                  # Flask app entrypoint
│   └── requirements.txt          # Python dependencies
│
├── frontend/
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── game.html
│   │   ├── login.html
│   │   ├── create_account.html
│   │   ├── create_character.html
│   │   ├── select_save.html
│   │   └── title_animation.html
│   └── static/                   # CSS and images
│       ├── game.css
│       ├── select_save.css
│       ├── account_pages.css
│       ├── create_character.css
│       ├── title_animation.css
│       └── images/
│           └── treasure_chest.svg
│
├── vercel.json                   # Vercel deployment config
└── README.md                     # (This file)
```

---

## Setup & Running Locally

1. **Clone the repository:**
    ```sh
    git clone https://github.com/yourusername/one-more-descent.git
    cd one-more-descent
    ```

2. **Install Python dependencies:**
    ```sh
    cd api
    pip install -r requirements.txt
    ```

3. **Configure environment variables:**
    - Create a `.env` file in `api/` with your Supabase credentials:
      ```
      SUPABASE_URL=your_supabase_url
      SUPABASE_KEY=your_supabase_key
      FLASK_SECRET_KEY=your_flask_secret
      ```

4. **Run the Flask app:**
    ```sh
    python index.py
    ```
    The app will be available at `http://localhost:5000`.

---

## Deployment

- **Vercel:** The project includes a `vercel.json` for deploying the Python API on Vercel.
- **Static files** are served from the `frontend/static` directory.

---

## License

MIT License

---

## Credits

- Dungeon and enemy data inspired by classic roguelikes.
- UI uses [Bebas Neue](https://fonts.google.com/specimen/Bebas+Neue) and [Boxicons](https://boxicons.com/).
- Built with [Flask](https://flask.palletsprojects.com/), [Supabase](https://supabase.com/), and [NetworkX](https://networkx.org/).

---
