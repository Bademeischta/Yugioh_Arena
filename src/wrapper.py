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
                self.lib = ctypes.WinDLL(lib_path)
                print(f"Successfully loaded library via WinDLL: {lib_path}")
            elif system == "Linux":
                self.lib = ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
            else:
                self.lib = ctypes.CDLL(lib_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load ocgcore library: {e}")

    def _find_func(self, name):
        """Search for mangled names on 32-bit Windows."""
        try:
            return getattr(self.lib, name)
        except AttributeError:
            pass
        if platform.system() == "Windows":
            for i in range(0, 65, 4):
                mangled = f"_{name}@{i}"
                try:
                    return getattr(self.lib, mangled)
                except AttributeError:
                    continue
        return None

    def _safe_bind(self, name, argtypes=None, restype=None):
        func = self._find_func(name)
        if func:
            if argtypes is not None: func.argtypes = argtypes
            if restype is not None: func.restype = restype
            setattr(self, f"_{name}", func)
            return True
        return False

    def _setup_bindings(self):
        # New OCG API Mapping
        self._safe_bind("OCG_CreateDuel", restype=ctypes.c_void_p)
        self._safe_bind("OCG_DestroyDuel", argtypes=[ctypes.c_void_p])
        self._safe_bind("OCG_StartDuel", argtypes=[ctypes.c_void_p, ctypes.c_int32])
        self._safe_bind("OCG_DuelProcess", argtypes=[ctypes.c_void_p], restype=ctypes.c_int32)
        self._safe_bind("OCG_DuelGetMessage", argtypes=[ctypes.c_void_p, ctypes.POINTER(ctypes.c_byte)], restype=ctypes.c_int32)
        self._safe_bind("OCG_DuelNewCard", argtypes=[ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8])
        self._safe_bind("OCG_DuelSetResponse", argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int32])

    # Exposed methods mapped to the new API
    def create_duel(self, seed):
        if hasattr(self, "_OCG_CreateDuel"): return self._OCG_CreateDuel(seed)
        return None

    def start_duel(self, pduel, options=0):
        if hasattr(self, "_OCG_StartDuel"): self._OCG_StartDuel(pduel, options)

    def end_duel(self, pduel):
        if hasattr(self, "_OCG_DestroyDuel"): self._OCG_DestroyDuel(pduel)

    def process(self, pduel):
        if hasattr(self, "_OCG_DuelProcess"): return self._OCG_DuelProcess(pduel)
        return 0

    def get_message(self, pduel, buffer):
        if hasattr(self, "_OCG_DuelGetMessage"): return self._OCG_DuelGetMessage(pduel, buffer)
        return 0

    def new_card(self, pduel, code, owner, playerid, location, sequence, position):
        if hasattr(self, "_OCG_DuelNewCard"):
            self._OCG_DuelNewCard(pduel, code, owner, playerid, location, sequence, position)

    def set_responsei(self, pduel, value):
        if hasattr(self, "_OCG_DuelSetResponse"):
            # Pack integer into bytes for the uniform response function
            v = ctypes.c_int32(value)
            self._OCG_DuelSetResponse(pduel, ctypes.byref(v), ctypes.sizeof(v))

    def set_responseb(self, pduel, buffer):
        if hasattr(self, "_OCG_DuelSetResponse"):
            # Assume buffer is already a ctypes array or buffer
            self._OCG_DuelSetResponse(pduel, buffer, len(buffer))

    # Compatibility Stubs (Now internal to engine)
    def set_card_reader(self, callback): pass
    def set_script_reader(self, callback): pass
    def set_log_handler(self, callback): pass
    def set_player_info(self, pduel, playerid, lp, startcount, drawcount): pass

    def _get_default_lib_path(self):
        system = platform.system()
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'engine')
        if system == "Windows": return os.path.join(base_path, "ocgcore.dll")
        elif system == "Linux": return os.path.join(base_path, "libocgcore.so")
        elif system == "Darwin": return os.path.join(base_path, "libocgcore.dylib")
        else: raise OSError(f"Unsupported operating system: {system}")
