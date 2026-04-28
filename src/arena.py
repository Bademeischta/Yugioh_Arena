from duel_manager import DuelManager
from ai_agent import DummyAI

class ArenaController:
    def __init__(self, wrapper, data_loader):
        self.wrapper = wrapper
        self.data_loader = data_loader
        self.results = []

    def run_simulation(self, deck0, deck1, num_duels=10):
        print(f"Starting simulation: {num_duels} duels...")
        self.results = []

        for i in range(num_duels):
            dm = DuelManager(self.wrapper, self.data_loader)
            ai0 = DummyAI(0)
            ai1 = DummyAI(1)

            try:
                # In a real environment, this might fail if the library is missing
                # We wrap it to allow the script to run for demonstration
                dm.setup_duel(deck0, deck1, seed=i)
                result = dm.run(ai0, ai1)
                self.results.append(result)
                print(f" Duel {i+1}/{num_duels} finished. Winner: Player {result['winner']}")
            except Exception as e:
                print(f" Duel {i+1} failed: {e}")
                # For demonstration purposes, we might want to fake a result if lib is missing
                # but better to report the error.

        self.display_statistics()

    def display_statistics(self):
        if not self.results:
            print("No results to display.")
            return

        total = len(self.results)
        wins0 = sum(1 for r in self.results if r['winner'] == 0)
        wins1 = sum(1 for r in self.results if r['winner'] == 1)
        draws = sum(1 for r in self.results if r['winner'] == -1 or r['winner'] == 2)

        avg_turns = sum(r['turns'] for r in self.results) / total

        print("\n" + "="*30)
        print(" SIMULATION STATISTICS")
        print("="*30)
        print(f"Total Duels:  {total}")
        print(f"Player 0 Wins: {wins0} ({wins0/total*100:.1f}%)")
        print(f"Player 1 Wins: {wins1} ({wins1/total*100:.1f}%)")
        print(f"Draws/Error:   {draws} ({draws/total*100:.1f}%)")
        print(f"Average Turns: {avg_turns:.1f}")
        print("="*30)
