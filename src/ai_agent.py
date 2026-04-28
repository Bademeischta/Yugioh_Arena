import random

class DummyAI:
    def __init__(self, player_id):
        self.player_id = player_id

    def select_idlecmd(self, options):
        # type 7, index 0 is typically End Phase
        if options.get('bp'):
            return (6, 0) # Enter Battle Phase
        return (7, 0) # End Phase

    def select_yesno(self):
        return random.choice([0, 1])

    def select_option(self, options):
        return random.randint(0, len(options) - 1)

    def select_card(self, cards, min_count, max_count):
        return cards[:min_count]
