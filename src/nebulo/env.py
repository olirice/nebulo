import os
from pathlib import Path

from appdirs import user_data_dir


class EnvManager:
    """Stashes environment variables in a file and
    retrieves them in (a different process) with get_environ

    with failover to os.environ
    """

    app_env_dir = Path(user_data_dir("NEBULO"))
    app_env = app_env_dir / ".env"

    def __init__(self, **env_vars):
        # Delete if exists
        try:
            os.remove(self.app_env)
        except OSError:
            pass

        self.app_env_dir.mkdir(parents=True, exist_ok=True)
        self.app_env.touch()
        self.vars = env_vars

    def __enter__(self):
        with self.app_env.open("w") as env_file:
            for key, val in self.vars.items():
                if val is not None:
                    env_file.write(f"{key}={val}\n")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        try:
            os.remove(self.app_env)
        except OSError:
            pass

    @classmethod
    def get_environ(cls):
        try:
            with cls.app_env.open("r") as f:
                for row in f:
                    key, value = row.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        except FileNotFoundError:
            pass
        return os.environ
