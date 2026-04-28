import ctypes
import os
import platform
import sys

class CardData(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_uint32),
        ("alias", ctypes.c_uint32),
        ("setcode", ctypes.c_uint64),
        ("type", ctypes.c_uint32),
        ("level", ctypes.c_uint32),
        ("attribute", ctypes.c_uint32),
        ("race", ctypes.c_uint32),
        ("attack", ctypes.c_int32),
        ("defense", ctypes.c_int32),
        ("lscale", ctypes.c_uint32),
        ("rscale", ctypes.c_uint32),
        ("link_marker", ctypes.c_uint32),
    ]

class OcgCoreWrapper:
    def __init__(self, lib_path=None):
        if lib_path is None:
            lib_path = self._get_default_lib_path()

        if not os.path.exists(lib_path):
            raise FileNotFoundError(f"ocgcore library not found at: {lib_path}")

        try:
            # Use RTLD_GLOBAL on Linux to ensure symbols are available for Lua scripts if needed
            if platform.system() == "Linux":
                self.lib = ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
            else:
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
        self.lib.set_card_reader.argtypes = [ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(CardData))]
        self.lib.set_card_reader.restype = None

        self.lib.set_script_reader.argtypes = [ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int))]
        self.lib.set_script_reader.restype = None

        self.lib.set_log_handler.argtypes = [ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int)]
        self.lib.set_log_handler.restype = None

        self.lib.create_duel.argtypes = [ctypes.c_uint32]
        self.lib.create_duel.restype = ctypes.c_void_p

        self.lib.start_duel.argtypes = [ctypes.c_void_p, ctypes.c_int32]
        self.lib.start_duel.restype = None

        self.lib.end_duel.argtypes = [ctypes.c_void_p]
        self.lib.end_duel.restype = None

        self.lib.set_player_info.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32]
        self.lib.set_player_info.restype = None

        self.lib.new_card.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8]
        self.lib.new_card.restype = None

        self.lib.process.argtypes = [ctypes.c_void_p]
        self.lib.process.restype = ctypes.c_int32

        self.lib.get_message.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_byte)]
        self.lib.get_message.restype = ctypes.c_int32

        self.lib.set_responsei.argtypes = [ctypes.c_void_p, ctypes.c_int32]
        self.lib.set_responsei.restype = None

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
        self._card_reader_cb = callback
        self.lib.set_card_reader(callback)

    def set_script_reader(self, callback):
        self._script_reader_cb = callback
        self.lib.set_script_reader(callback)

    def set_log_handler(self, callback):
        self._log_handler_cb = callback
        self.lib.set_log_handler(callback)
