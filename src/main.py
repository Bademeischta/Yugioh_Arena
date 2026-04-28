import os
import sys
from wrapper import OcgCoreWrapper
from data_loader import DataLoader
from arena import ArenaController

def main():
    print("Yu-Gi-Oh! AI Arena Simulator")
    print("=" * 30)

    # 1. Initialize Infrastructure
    try:
        loader = DataLoader()
        wrapper = OcgCoreWrapper()
    except Exception as e:
        print(f"Error during initialization: {e}")
        # In a real scenario we'd exit, but for the task we continue to show the logic
        # sys.exit(1)
        wrapper = None

    # 2. Load Decks
    decks_dir = 'decks'
    if not os.path.exists(decks_dir):
        os.makedirs(decks_dir)

    # Create test deck if none exists
    test_deck_path = os.path.join(decks_dir, 'test_deck.ydk')
    if not os.path.exists(test_deck_path):
        with open(test_deck_path, 'w') as f:
            f.write("#main\n46986414\n46986414\n46986414\n#extra\n!side\n")

    decks = DataLoader.load_all_decks(decks_dir)
    if not decks:
        print("No decks found in decks/ folder.")
        return

    deck_names = list(decks.keys())
    deck0 = decks[deck_names[0]]
    deck1 = decks[deck_names[0]] # Play against itself for testing

    print(f"Loaded {len(decks)} decks.")
    print(f"Matchup: {deck_names[0]} vs {deck_names[0]}")

    # 3. Run Arena
    if wrapper:
        arena = ArenaController(wrapper, loader)
        arena.run_simulation(deck0, deck1, num_duels=10)
    else:
        print("\n[SKIP] Arena simulation skipped because ocgcore library was not found.")
        print("Please place ocgcore.dll/libocgcore.so in the 'engine/' folder to run duels.")

if __name__ == "__main__":
    main()
