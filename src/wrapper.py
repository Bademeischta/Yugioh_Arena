import ctypes
from ctypes import c_void_p, c_int, c_uint32, c_byte, POINTER, byref, sizeof
import os
import platform

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
        # Strict Signature Definitions for modern OCG API
        self._safe_bind("OCG_CreateDuel", argtypes=[c_uint32], restype=c_void_p)
        self._safe_bind("OCG_DestroyDuel", argtypes=[c_void_p], restype=None)
        self._safe_bind("OCG_StartDuel", argtypes=[c_void_p, c_int], restype=None)
        self._safe_bind("OCG_DuelProcess", argtypes=[c_void_p], restype=c_int)
        self._safe_bind("OCG_DuelGetMessage", argtypes=[c_void_p, c_void_p], restype=c_int)
        self._safe_bind("OCG_DuelNewCard", argtypes=[c_void_p, c_uint32, c_byte, c_byte, c_byte, c_byte, c_byte], restype=None)
        self._safe_bind("OCG_DuelSetResponse", argtypes=[c_void_p, c_void_p, c_int], restype=None)

    # Exposed methods mapped to the new API
    def create_duel(self, seed):
        if hasattr(self, "_OCG_CreateDuel"):
            return self._OCG_CreateDuel(c_uint32(seed))
        return None

    def start_duel(self, pduel, options=0):
        if hasattr(self, "_OCG_StartDuel"):
            self._OCG_StartDuel(pduel, c_int(options))

    def end_duel(self, pduel):
        if hasattr(self, "_OCG_DestroyDuel"):
            self._OCG_DestroyDuel(pduel)

    def process(self, pduel):
        if hasattr(self, "_OCG_DuelProcess"):
            return self._OCG_DuelProcess(pduel)
        return 0

    def get_message(self, pduel, buffer):
        if hasattr(self, "_OCG_DuelGetMessage"):
            return self._OCG_DuelGetMessage(pduel, buffer)
        return 0

    def new_card(self, pduel, code, owner, playerid, location, sequence, position):
        if hasattr(self, "_OCG_DuelNewCard"):
            self._OCG_DuelNewCard(pduel, c_uint32(code), c_byte(owner), c_byte(playerid),
                                 c_byte(location), c_byte(sequence), c_byte(position))

    def set_responsei(self, pduel, value):
        if hasattr(self, "_OCG_DuelSetResponse"):
            v = c_int(value)
            self._OCG_DuelSetResponse(pduel, byref(v), sizeof(v))

    def set_responseb(self, pduel, buffer):
        if hasattr(self, "_OCG_DuelSetResponse"):
            self._OCG_DuelSetResponse(pduel, buffer, len(buffer))

    # Compatibility Stubs
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
