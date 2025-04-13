document.getElementById('move-button').addEventListener('click', async () => {
    const response = await fetch('/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction: 'north'})
    });

    const data = await response.json();
    if (data.success) {
        document.getElementById('room-contents').innerText = data.roon_description;
        document.getElementById('story-text').innerText = data.story_log;
    } else {
        alert(data.error);
    }
});

document.getElementById('inventory-button').addEventListener('click', () => {
    document.getElementById('inventory-modal').style.display = 'block';
});

document.getElementById('close-inventory').addEventListener('click', () => {
    document.getElementById('inventory-modal').style.display = 'none';
});