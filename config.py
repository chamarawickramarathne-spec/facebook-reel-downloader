import json
import os
import threading

MAX_CONFIG_BYTES = 64 * 1024
CONFIG_NAME = "config.json"

DEFAULTS = {
    "auto_check_updates": True,
}


def _config_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "FacebookReelDownloader")


class Settings:
    def __init__(self):
        self._lock = threading.Lock()
        self._path = os.path.join(_config_dir(), CONFIG_NAME)
        self._data = dict(DEFAULTS)
        self._load()

    def _load(self):
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                raw = f.read(MAX_CONFIG_BYTES + 1)
            if len(raw) > MAX_CONFIG_BYTES:
                return
            data = json.loads(raw)
            if not isinstance(data, dict):
                return
            for key, value in data.items():
                if key in DEFAULTS and isinstance(value, type(DEFAULTS[key])):
                    self._data[key] = value
        except (OSError, ValueError, TypeError):
            pass

    def get(self, key):
        with self._lock:
            return self._data.get(key, DEFAULTS.get(key))

    def set(self, key, value):
        if key not in DEFAULTS:
            return
        if not isinstance(value, type(DEFAULTS[key])):
            return
        with self._lock:
            self._data[key] = value
        self._save()

    def _save(self):
        try:
            d = _config_dir()
            os.makedirs(d, exist_ok=True)
            tmp = self._path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            os.replace(tmp, self._path)
        except OSError:
            pass