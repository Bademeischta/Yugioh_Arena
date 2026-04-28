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

        self.lib = None
        self._load_library(lib_path)
        self._setup_bindings()

    def _load_library(self, lib_path):
        system = platform.system()
        try:
            if system == "Windows":
                # User specified that it's highly likely stdcall for this 32-bit DLL
                self.lib = ctypes.WinDLL(lib_path)
                print(f"Successfully loaded library via WinDLL (stdcall): {lib_path}")
            elif system == "Linux":
                self.lib = ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
            else:
                self.lib = ctypes.CDLL(lib_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load ocgcore library: {e}")

    def _find_func(self, name):
        """Intelligently search for mangled names on 32-bit Windows."""
        # Try exact name
        try:
            return getattr(self.lib, name)
        except AttributeError:
            pass

        # Try mangled name pattern: _name@X
        if platform.system() == "Windows":
            for i in range(0, 65, 4):
                mangled = f"_{name}@{i}"
                try:
                    return getattr(self.lib, mangled)
                except AttributeError:
                    continue
        return None

    def _safe_bind(self, name, argtypes, restype):
        """Helper to safely bind a C function with mangling resolution."""
        func = self._find_func(name)
        if func:
            try:
                func.argtypes = argtypes
                func.restype = restype
                setattr(self, f"_{name}", func)
                return True
            except Exception as e:
                print(f"Warning: Failed to set signatures for function '{name}': {e}")
        else:
            print(f"Warning: function '{name}' (or mangled variants) not found in library.")
        return False

    def _setup_bindings(self):
        self._safe_bind("set_card_reader", [ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(CardData))], None)
        self._safe_bind("set_script_reader", [ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int))], None)
        self._safe_bind("set_log_handler", [ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int)], None)
        self._safe_bind("create_duel", [ctypes.c_uint32], ctypes.c_void_p)
        self._safe_bind("start_duel", [ctypes.c_void_p, ctypes.c_int32], None)
        self._safe_bind("end_duel", [ctypes.c_void_p], None)
        self._safe_bind("set_player_info", [ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32], None)
        self._safe_bind("new_card", [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8], None)
        self._safe_bind("process", [ctypes.c_void_p], ctypes.c_int32)
        self._safe_bind("get_message", [ctypes.c_void_p, ctypes.POINTER(ctypes.c_byte)], ctypes.c_int32)
        self._safe_bind("set_responsei", [ctypes.c_void_p, ctypes.c_int32], None)
        self._safe_bind("set_responseb", [ctypes.c_void_p, ctypes.POINTER(ctypes.c_byte)], None)

    # Exposed methods
    def create_duel(self, seed):
        if hasattr(self, "_create_duel"): return self._create_duel(seed)
        return None
    def start_duel(self, pduel, options=0):
        if hasattr(self, "_start_duel"): self._start_duel(pduel, options)
    def end_duel(self, pduel):
        if hasattr(self, "_end_duel"): self._end_duel(pduel)
    def set_player_info(self, pduel, playerid, lp, startcount, drawcount):
        if hasattr(self, "_set_player_info"): self._set_player_info(pduel, playerid, lp, startcount, drawcount)
    def new_card(self, pduel, code, owner, playerid, location, sequence, position):
        if hasattr(self, "_new_card"): self._new_card(pduel, code, owner, playerid, location, sequence, position)
    def process(self, pduel):
        if hasattr(self, "_process"): return self._process(pduel)
        return 0
    def get_message(self, pduel, buffer):
        if hasattr(self, "_get_message"): return self._get_message(pduel, buffer)
        return 0
    def set_responsei(self, pduel, value):
        if hasattr(self, "_set_responsei"): self._set_responsei(pduel, value)
    def set_responseb(self, pduel, buffer):
        if hasattr(self, "_set_responseb"): self._set_responseb(pduel, buffer)
    def set_card_reader(self, callback):
        self._card_reader_cb = callback
        if hasattr(self, "_set_card_reader"): self._set_card_reader(callback)
    def set_script_reader(self, callback):
        self._script_reader_cb = callback
        if hasattr(self, "_set_script_reader"): self._set_script_reader(callback)
    def set_log_handler(self, callback):
        self._log_handler_cb = callback
        if hasattr(self, "_set_log_handler"): self._set_log_handler(callback)

    def _get_default_lib_path(self):
        system = platform.system()
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'engine')
        if system == "Windows": return os.path.join(base_path, "ocgcore.dll")
        elif system == "Linux": return os.path.join(base_path, "libocgcore.so")
        elif system == "Darwin": return os.path.join(base_path, "libocgcore.dylib")
        else: raise OSError(f"Unsupported operating system: {system}")
