import sys
import os
from wrapper import OcgCoreWrapper
from data_loader import DataLoader

def main():
    print("YGO Arena - Phase 1 Verification (Updated)")
    print("-" * 40)

    # 1. Test Project Structure
    print("Checking directories...")
    for d in ['engine', 'data', 'decks', 'src']:
        if os.path.exists(d):
            print(f" [OK] {d}/")
        else:
            print(f" [MISSING] {d}/")

    # 2. Test Data Loader
    print("\nTesting DataLoader...")

    # Create dummy files for testing
    dummy_ydk = "decks/test_deck.ydk"
    with open(dummy_ydk, "w") as f:
        f.write("#main\n46986414\n46986414\n46986414\n#extra\n!side\n")

    dummy_strings = "data/strings.conf"
    with open(dummy_strings, "w", encoding='utf-8') as f:
        f.write("!system 100 First Player\n!system 101 Second Player\n")

    loader = DataLoader(strings_path=dummy_strings)

    # Test YDK Parser
    try:
        deck = loader.parse_ydk(dummy_ydk)
        print(f" [OK] YDK Parser: Parsed {len(deck['main'])} cards from {dummy_ydk}.")
    except Exception as e:
        print(f" [FAIL] YDK Parser: {e}")

    # Test Strings Parser
    try:
        strings = loader.load_system_strings()
        if strings.get(100) == "First Player":
            print(f" [OK] Strings Parser: Correctly loaded system strings.")
        else:
            print(f" [FAIL] Strings Parser: Could not find expected string ID 100.")
    except Exception as e:
        print(f" [FAIL] Strings Parser: {e}")

    # Test DB Connection (Graceful failure expected without real CDB)
    print("\nTesting CDB Access (Expected to fail gracefully without real data/cards.cdb)...")
    data = loader.get_card_data(46986414)
    if data:
        print(f" [OK] CDB Access: Found card data.")
    else:
        print(f" [INFO] CDB Access: Card not found or DB missing (Expected).")

    # 3. Test OcgCoreWrapper
    print("\nTesting OcgCoreWrapper...")
    try:
        wrapper = OcgCoreWrapper()
        print(" [OK] OcgCoreWrapper initialized (Library found!)")
    except FileNotFoundError as e:
        print(f" [INFO] OcgCoreWrapper: Library file not found (Expected if not yet provided).")
    except Exception as e:
        print(f" [FAIL] OcgCoreWrapper: {e}")

if __name__ == "__main__":
    main()
