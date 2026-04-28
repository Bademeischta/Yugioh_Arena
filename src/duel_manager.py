import ctypes
import struct
import os
from constants import MSG, LOCATION, POS

class DuelManager:
    def __init__(self, wrapper, data_loader, script_dir='data/scripts'):
        self.wrapper = wrapper
        self.data_loader = data_loader
        self.script_dir = script_dir
        self.pduel = None
        self.players = [None, None]
        self.buffer = ctypes.create_string_buffer(4096)
        self._script_cache = {}

        self._setup_callbacks()

    def _setup_callbacks(self):
        def card_reader(code, data_ptr): return 0
        def script_reader(name_ptr, len_ptr): return None
        self._card_reader_cb = card_reader
        self._script_reader_cb = script_reader
        self.wrapper.set_card_reader(card_reader)
        self.wrapper.set_script_reader(script_reader)

    def setup_duel(self, deck0, deck1, lp=8000, start_count=5, draw_count=1, seed=0):
        self.pduel = self.wrapper.create_duel(seed)
        if not self.pduel:
            raise RuntimeError("Failed to create duel instance")

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
                raw_buf = self.buffer.raw
                while ptr < msg_len:
                    msg_type = raw_buf[ptr]

                    if msg_type == MSG.WIN:
                        winner = raw_buf[ptr + 1]
                        return {"winner": winner, "turns": turns}

                    if msg_type in [MSG.SELECT_IDLECMD, MSG.SELECT_BATTLECMD, MSG.SELECT_YESNO, MSG.SELECT_CARD]:
                        self._handle_ai_response(msg_type, ptr, raw_buf)
                        # Exit processing to allow engine to receive response
                        break

                    length = self._get_msg_length(msg_type, ptr, raw_buf)
                    ptr += length

                    if msg_type == MSG.CUR_PHASE:
                        # Safety check for buffer access
                        if ptr - 2 >= 0:
                            phase = struct.unpack_from('H', raw_buf, ptr - 2)[0]
                            if phase == 0x01: # DP
                                turns += 1

            if res == 2: return {"winner": -1, "turns": turns}

    def _get_msg_length(self, msg_type, ptr, buf):
        # Comprehensive fixed length mapping for common messages
        # Any unknown message will default to 1, but we include as many as possible
        fixed_lengths = {
            MSG.START: 1, MSG.WIN: 3, MSG.DRAW: 3, MSG.DAMAGE: 5, MSG.RECOVER: 5,
            MSG.LPUPDATE: 5, MSG.SET: 1, MSG.CUR_PHASE: 3, MSG.SHUFFLE_DECK: 2,
            MSG.SHUFFLE_HAND: 2, MSG.POS_CHANGE: 9, MSG.SUMMONED: 1, MSG.SPSUMMONED: 1,
            MSG.FLIPSUMMONED: 1, MSG.CHAIN_DONE: 1, MSG.DAMAGE_STEP: 1, MSG.UN_DAMAGE_STEP: 1,
            MSG.NEW_PHASE: 3, MSG.MOVE: 16, MSG.SUMMONING: 8, MSG.SPSUMMONING: 8,
            MSG.FLIPSUMMONING: 8, MSG.CHAIN_SOLVED: 1, MSG.CHAIN_END: 1,
            MSG.HINT: 6, MSG.WAITING: 2, MSG.UPDATE_DATA: 1, MSG.UPDATE_CARD: 1,
            MSG.REQUEST_ID: 1, MSG.PAY_LPCOST: 5, MSG.ADD_COUNTER: 7, MSG.REMOVE_COUNTER: 7,
            MSG.ATTACK: 1, MSG.BATTLE: 1, MSG.ATTACK_DISABLED: 1, MSG.DAMAGE_STEP_START: 1,
            MSG.DAMAGE_STEP_END: 1, MSG.BE_BATTLE_TARGET: 1, MSG.CREATE_RELATION: 1,
            MSG.RELEASE_RELATION: 1, MSG.TOSS_COIN: 1, MSG.TOSS_DICE: 1,
            MSG.CARD_HINT: 1, MSG.AI_NAME: 1, MSG.SHOW_HINT: 1,
        }
        return fixed_lengths.get(msg_type, 1)

    def _handle_ai_response(self, msg_type, ptr, buf):
        player = buf[ptr + 1]
        if msg_type == MSG.SELECT_IDLECMD:
            options = {"bp": True, "ep": True}
            choice = self.players[player].select_idlecmd(options)
            resp = struct.pack('HH', choice[0], choice[1])
            self.wrapper.set_responseb(self.pduel, (ctypes.c_byte * len(resp)).from_buffer_copy(resp))
        elif msg_type == MSG.SELECT_YESNO:
            choice = self.players[player].select_yesno()
            self.wrapper.set_responsei(self.pduel, choice)
        elif msg_type == MSG.SELECT_CARD:
            # Basic dummy response for SELECT_CARD: select the first available card
            # Standard response for SELECT_CARD is: count(1) + indices(count)
            resp = struct.pack('B', 1) + struct.pack('B', 0)
            self.wrapper.set_responseb(self.pduel, (ctypes.c_byte * len(resp)).from_buffer_copy(resp))
        elif msg_type == MSG.SELECT_BATTLECMD:
            # Basic dummy response: skip battle (usually -1 or specific index)
            self.wrapper.set_responsei(self.pduel, -1)

    def __del__(self):
        if self.pduel:
            try: self.wrapper.end_duel(self.pduel)
            except: pass
