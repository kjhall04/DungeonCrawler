def player_creation():
    """
    Handles the player creation process during a new game save.
    
    Returns:
        tuple: A tuple containing:
            - List of strings to display (story and prompts).
            - Player's chosen name (str).
            - Player's chosen class (str).
    """
    # Story introduction
    story = [
        'Welcome, adventurer, to One More Descent!',
        'Before you embark on your journey, you must tell us who you are...',
        'Choose wisely, your decisions here will shape your destiny...'
    ]

    for line in story:
        print(line)

    # Prompt for player name
    name_prompt = 'What shall we call you, brave adventurer?'
    player_name = input(name_prompt + " ")

    # Prompt for player class
    class_prompt = (
        'Choose your class:\n'
        '1. Mage - Masters of elemental magic.\n'
        '2. Warrior - Strong and resilient fighters.\n'
        '3. Rogue - Agile and cunning assassins.\n'
        'Enter the number corresponding to your class: '
    )
    class_choices = {'1': 'mage', '2': 'warrior', '3': 'rogue'}
    player_class = None

    while player_class is None:
        class_choice = input(class_prompt)
        if class_choice in class_choices:
            player_class = class_choices[class_choice]
        else:
            print('That is not a valid choice. Please select 1, 2, or 3.')

    # Confirmation message
    confirmation = [
        f'Welcome, {player_name} the {player_class.capitalize()}!',
        'Your journey begins now. Prepare yourself, for the dungeon depths await.'
    ]

    # Combine all story elements
    display_text = story + [name_prompt] + [class_prompt] + confirmation
    print(display_text)

    return display_text, player_name, player_class


if __name__ == "__main__":
    display_text, player_name, player_class = player_creation()

    # Display the story and prompts
    for line in display_text:
        print(line)

    # Use the player's name and class for further game logic
    print(f"\nPlayer Name: {player_name}")
    print(f"Player Class: {player_class}")