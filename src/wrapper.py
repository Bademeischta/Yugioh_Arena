import ctypes
import os
import platform
import sys

class OcgCoreWrapper:
    def __init__(self, lib_path=None):
        if lib_path is None:
            lib_path = self._get_default_lib_path()

        if not os.path.exists(lib_path):
            raise FileNotFoundError(f"ocgcore library not found at: {lib_path}")

        try:
            self.lib = ctypes.cdll.LoadLibrary(lib_path)
            self._setup_bindings()
        except Exception as e:
            raise RuntimeError(f"Failed to load ocgcore library: {e}")

    def _get_default_lib_path(self):
        system = platform.system()
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'engine')

        if system == "Windows":
            return os.path.join(base_path, "ocgcore.dll")
        elif system == "Linux":
            return os.path.join(base_path, "libocgcore.so")
        elif system == "Darwin": # macOS
            return os.path.join(base_path, "libocgcore.dylib")
        else:
            raise OSError(f"Unsupported operating system: {system}")

    def _setup_bindings(self):
        # We define common ocgcore functions.
        # Note: Actual signatures might vary slightly depending on the specific version of ocgcore.
        # These are based on common implementations like those used in EDOPro.

        # void set_card_reader(card_reader_t reader)
        self.lib.set_card_reader.argtypes = [ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_byte))]
        self.lib.set_card_reader.restype = None

        # void set_script_reader(script_reader_t reader)
        self.lib.set_script_reader.argtypes = [ctypes.CFUNCTYPE(ctypes.POINTER(ctypes.c_byte), ctypes.POINTER(ctypes.c_char), ctypes.POINTER(ctypes.c_int))]
        self.lib.set_script_reader.restype = None

        # void set_log_handler(log_handler_t handler)
        self.lib.set_log_handler.argtypes = [ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_char), ctypes.c_int)]
        self.lib.set_log_handler.restype = None

        # intptr_t create_duel(uint32_t seed)
        self.lib.create_duel.argtypes = [ctypes.c_uint32]
        self.lib.create_duel.restype = ctypes.c_void_p

        # void start_duel(intptr_t pduel, int32_t options)
        self.lib.start_duel.argtypes = [ctypes.c_void_p, ctypes.c_int32]
        self.lib.start_duel.restype = None

        # void end_duel(intptr_t pduel)
        self.lib.end_duel.argtypes = [ctypes.c_void_p]
        self.lib.end_duel.restype = None

        # void set_player_info(intptr_t pduel, int32_t playerid, int32_t lp, int32_t startcount, int32_t drawcount)
        self.lib.set_player_info.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32]
        self.lib.set_player_info.restype = None

        # void new_card(intptr_t pduel, uint32_t code, uint8_t owner, uint8_t playerid, uint8_t location, uint8_t sequence, uint8_t position)
        self.lib.new_card.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
        self.lib.new_card.restype = None

        # int32_t process(intptr_t pduel)
        self.lib.process.argtypes = [ctypes.c_void_p]
        self.lib.process.restype = ctypes.c_int32

        # int32_t get_message(intptr_t pduel, byte* buf)
        self.lib.get_message.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_byte)]
        self.lib.get_message.restype = ctypes.c_int32

        # void set_responsei(intptr_t pduel, int32_t value)
        self.lib.set_responsei.argtypes = [ctypes.c_void_p, ctypes.c_int32]
        self.lib.set_responsei.restype = None

        # void set_responseb(intptr_t pduel, byte* buf)
        self.lib.set_responseb.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_byte)]
        self.lib.set_responseb.restype = None

    def create_duel(self, seed):
        return self.lib.create_duel(seed)

    def start_duel(self, pduel, options=0):
        self.lib.start_duel(pduel, options)

    def end_duel(self, pduel):
        self.lib.end_duel(pduel)

    def set_player_info(self, pduel, playerid, lp, startcount, drawcount):
        self.lib.set_player_info(pduel, playerid, lp, startcount, drawcount)

    def new_card(self, pduel, code, owner, playerid, location, sequence, position):
        self.lib.new_card(pduel, code, owner, playerid, location, sequence, position)

    def process(self, pduel):
        return self.lib.process(pduel)

    def get_message(self, pduel, buffer):
        return self.lib.get_message(pduel, buffer)

    def set_responsei(self, pduel, value):
        self.lib.set_responsei(pduel, value)

    def set_responseb(self, pduel, buffer):
        self.lib.set_responseb(pduel, buffer)

    def set_card_reader(self, callback):
        self._card_reader_cb = callback # keep reference
        self.lib.set_card_reader(callback)

    def set_script_reader(self, callback):
        self._script_reader_cb = callback # keep reference
        self.lib.set_script_reader(callback)

    def set_log_handler(self, callback):
        self._log_handler_cb = callback # keep reference
        self.lib.set_log_handler(callback)
