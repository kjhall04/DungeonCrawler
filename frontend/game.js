document.addEventListener('DOMContentLoaded', () => {
    const playerStats = {
        name: '',
        class: '',
        health: 0,
        gold: 0,
        location: null
    };

    const updatePlayerStats = (data) => {
        playerStats.name = data.name;
        playerStats.class = data.class;
        playerStats.health = data.health;
        playerStats.gold = data.inventory.gold;
        playerStats.location = data.player_location;

        document.getElementById('player-name').textContent = `Name: ${playerStats.name}`;
        document.getElementById('player-class').textContent = `Class: ${playerStats.class}`;
        document.getElementById('player-health').textContent = `Health: ${playerStats.health}`;
        document.getElementById('player-gold').textContent = `Gold: ${playerStats.gold}`;
        document.getElementById('current-room').textContent = `Current Room: ${playerStats.location}`;
    };

    const movePlayer = async (direction) => {
        const response = await fetch('/api/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                direction,
                player_location: playerStats.location
            })
        });

        const result = await response.json();
        if (response.ok) {
            playerStats.location = result.new_location;
            document.getElementById('current-room').textContent = `Current Room: ${playerStats.location}`;
        } else {
            alert(result.error);
        }
    };

    document.getElementById('move-north').addEventListener('click', () => movePlayer('north'));
    document.getElementById('move-south').addEventListener('click', () => movePlayer('south'));
    document.getElementById('move-east').addEventListener('click', () => movePlayer('east'));
    document.getElementById('move-west').addEventListener('click', () => movePlayer('west'));

    // Fetch initial player stats
    fetch('/api/player')
        .then(response => response.json())
        .then(data => updatePlayerStats(data))
        .catch(error => console.error('Error fetching player stats:', error));
});