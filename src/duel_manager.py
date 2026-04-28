import ctypes
import struct
import os
from constants import MSG, LOCATION, POS
from wrapper import CardData

class DuelManager:
    def __init__(self, wrapper, data_loader, script_dir='data/scripts'):
        self.wrapper = wrapper
        self.data_loader = data_loader
        self.script_dir = script_dir
        self.pduel = None
        self.players = [None, None]
        self.buffer = (ctypes.c_byte * 4096)()
        self._script_cache = {}
        self._keep_alive_buffers = []

        self._setup_callbacks()

    def _setup_callbacks(self):
        @ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(CardData))
        def card_reader(code, data_ptr):
            raw_data = self.data_loader.get_card_data(code)
            if raw_data:
                # raw_data format from DataLoader.get_card_data:
                # d.* (id, ot, alias, setcode, type, level, race, attribute, atk, def, category), t.name, t.desc
                data_ptr.contents.code = raw_data[0]
                data_ptr.contents.alias = raw_data[2]
                data_ptr.contents.setcode = raw_data[3]
                data_ptr.contents.type = raw_data[4]
                level = raw_data[5]
                data_ptr.contents.level = level & 0xff
                data_ptr.contents.lscale = (level >> 24) & 0xff
                data_ptr.contents.rscale = (level >> 16) & 0xff
                data_ptr.contents.race = raw_data[6]
                data_ptr.contents.attribute = raw_data[7]
                data_ptr.contents.attack = raw_data[8]
                data_ptr.contents.defense = raw_data[9]
                return code
            return 0

        @ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int))
        def script_reader(name_ptr, len_ptr):
            name = ctypes.string_at(name_ptr).decode('utf-8')
            if name in self._script_cache:
                content, buf = self._script_cache[name]
                len_ptr.contents.value = len(content)
                return ctypes.addressof(buf)

            path = os.path.join(self.script_dir, name)
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    content = f.read()
                    buf = ctypes.create_string_buffer(content)
                    self._script_cache[name] = (content, buf)
                    len_ptr.contents.value = len(content)
                    return ctypes.addressof(buf)
            return None

        self._card_reader_cb = card_reader
        self._script_reader_cb = script_reader
        self.wrapper.set_card_reader(card_reader)
        self.wrapper.set_script_reader(script_reader)

    def setup_duel(self, deck0, deck1, lp=8000, start_count=5, draw_count=1, seed=0):
        self.pduel = self.wrapper.create_duel(seed)
        for p_idx, deck in enumerate([deck0, deck1]):
            self.wrapper.set_player_info(self.pduel, p_idx, lp, start_count, draw_count)
            for code in deck['main']:
                self.wrapper.new_card(self.pduel, code, p_idx, p_idx, LOCATION.DECK, 0, POS.FACEDOWN_ATTACK)
            for code in deck.get('extra', []):
                self.wrapper.new_card(self.pduel, code, p_idx, p_idx, LOCATION.EXTRA, 0, POS.FACEDOWN_ATTACK)
        self.wrapper.start_duel(self.pduel, 0)

    def run(self, ai0, ai1):
        self.players = [ai0, ai1]
        turns = 0
        while True:
            res = self.wrapper.process(self.pduel)
            msg_len = self.wrapper.get_message(self.pduel, self.buffer)
            if msg_len > 0:
                ptr = 0
                while ptr < msg_len:
                    msg_type = self.buffer[ptr]

                    if msg_type == MSG.WIN:
                        winner = self.buffer[ptr + 1]
                        return {"winner": winner, "turns": turns}

                    if msg_type in [MSG.SELECT_IDLECMD, MSG.SELECT_BATTLECMD, MSG.SELECT_YESNO, MSG.SELECT_CARD]:
                        # AI needs to respond
                        self._handle_ai_response(msg_type, ptr)
                        # We must exit the message processing loop to let the engine react to the response
                        break

                    # Advance pointer for informative messages
                    length = self._get_msg_length(msg_type, ptr)
                    ptr += length

                    if msg_type == MSG.CUR_PHASE:
                        phase = struct.unpack_from('H', self.buffer, ptr - 2)[0]
                        if phase == 0x01: # DP
                            turns += 1

            if res == 2: return {"winner": -1, "turns": turns}

    def _get_msg_length(self, msg_type, ptr):
        # Dictionary of fixed lengths for common messages
        fixed_lengths = {
            MSG.START: 1, MSG.WIN: 3, MSG.DRAW: 3, MSG.DAMAGE: 5, MSG.RECOVER: 5,
            MSG.LPUPDATE: 5, MSG.SET: 1, MSG.CUR_PHASE: 3, MSG.SHUFFLE_DECK: 2,
            MSG.SHUFFLE_HAND: 2, MSG.POS_CHANGE: 9, MSG.SUMMONED: 1, MSG.SPSUMMONED: 1,
            MSG.FLIPSUMMONED: 1, MSG.CHAIN_DONE: 1, MSG.DAMAGE_STEP: 1, MSG.UN_DAMAGE_STEP: 1,
            MSG.NEW_PHASE: 3, MSG.MOVE: 16, MSG.SUMMONING: 8, MSG.SPSUMMONING: 8,
            MSG.FLIPSUMMONING: 8, MSG.CHAIN_SOLVED: 1, MSG.CHAIN_END: 1,
        }
        return fixed_lengths.get(msg_type, 1)

    def _handle_ai_response(self, msg_type, ptr):
        player = self.buffer[ptr + 1]
        if msg_type == MSG.SELECT_IDLECMD:
            options = self._parse_idle_options(ptr)
            choice = self.players[player].select_idlecmd(options)
            resp = struct.pack('HH', choice[0], choice[1])
            self.wrapper.set_responseb(self.pduel, (ctypes.c_byte * len(resp)).from_buffer_copy(resp))
        elif msg_type == MSG.SELECT_YESNO:
            choice = self.players[player].select_yesno()
            self.wrapper.set_responsei(self.pduel, choice)
        # More cases can be added here

    def _parse_idle_options(self, ptr):
        # Placeholder for full parsing logic
        return {"summon": [], "bp": True, "ep": True}

    def __del__(self):
        if self.pduel:
            try: self.wrapper.end_duel(self.pduel)
            except: pass
