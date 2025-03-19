import tomllib
import platformdirs


class Config:

    def __init__(self, path=None):
        self._data = {}
        self._path = path

        self.load_file(path or self._get_config_file_path())

    @staticmethod
    def _get_config_file_path():
        cfgfile = platformdirs.user_config_path("plankacli") / "config"
        return cfgfile if cfgfile.exists() else None

    def load_file(self, path):
        if path:
            with open(path, "rb") as f:
                self._data = tomllib.load(f)

    def get(self, key, default=None):
        rv = self._data
        try:
            keys = key.split(".")
            for k in keys[:-1]:
                rv = rv[k]

            return rv.get(keys[-1], default)

        except KeyError as err:
            raise KeyError(key)

    def set(self, key, value):
        self._data[key] = value
