import sqlite3
import os

class DataLoader:
    def __init__(self, cdb_path='data/cards.cdb', strings_path='data/strings.conf'):
        self.cdb_path = cdb_path
        self.strings_path = strings_path
        self._conn = None
        self.system_strings = {}

    def _get_conn(self):
        if self._conn is None:
            if os.path.exists(self.cdb_path):
                self._conn = sqlite3.connect(self.cdb_path)
            else:
                return None
        return self._conn

    def get_card_data(self, card_id):
        """Fetches card data and text from the SQLite database."""
        conn = self._get_conn()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            # Join datas and texts tables
            cursor.execute("""
                SELECT d.*, t.name, t.desc
                FROM datas d
                JOIN texts t ON d.id = t.id
                WHERE d.id=?
            """, (card_id,))
            data = cursor.fetchone()
            return data
        except Exception as e:
            print(f"Error reading card database: {e}")
            return None

    def load_system_strings(self):
        """Parses strings.conf for system messages."""
        if not os.path.exists(self.strings_path):
            return {}

        strings = {}
        with open(self.strings_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('!system'):
                    parts = line.split(' ', 2)
                    if len(parts) >= 3:
                        try:
                            str_id = int(parts[1])
                            str_val = parts[2]
                            strings[str_id] = str_val
                        except ValueError:
                            continue
        self.system_strings = strings
        return strings

    @staticmethod
    def parse_ydk(filepath):
        """Parses a .ydk file and returns a dictionary with main, extra, and side deck lists."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"YDK file not found: {filepath}")

        deck = {'main': [], 'extra': [], 'side': []}
        current_section = None

        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    if line == '#main':
                        current_section = 'main'
                    elif line == '#extra':
                        current_section = 'extra'
                    elif line == '!side':
                        current_section = 'side'
                    continue

                if line.isdigit() and current_section:
                    deck[current_section].append(int(line))

        return deck

    @staticmethod
    def load_all_decks(decks_dir='decks'):
        """Loads all .ydk files from a directory."""
        decks = {}
        if not os.path.exists(decks_dir):
            return decks

        for filename in os.listdir(decks_dir):
            if filename.endswith('.ydk'):
                filepath = os.path.join(decks_dir, filename)
                decks[filename] = DataLoader.parse_ydk(filepath)

        return decks

    def __del__(self):
        if self._conn:
            self._conn.close()
