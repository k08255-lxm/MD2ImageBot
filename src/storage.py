from __future__ import annotations
import json, os, time, threading
from pathlib import Path
from typing import Any

DEFAULT_STATE = {
    "created_at": int(time.time()),
    "stats": {
        "total_requests": 0,
        "render_success": 0,
        "render_failed": 0,
        "per_user": {}  # user_id -> {"requests": n, "render_success": m}
    },
    "config": {
        "public_enabled": True,
        "whitelist": [],
        "blacklist": [],
        "enabled_plugins": ["channel_autoconvert"]
    }
}

class Storage:
    def __init__(self, path: str | None = None):
        self.path = Path(path or "storage/state.json")
        self._lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write(DEFAULT_STATE)

    def _read(self) -> dict:
        if not self.path.exists():
            return DEFAULT_STATE.copy()
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict) -> None:
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(self.path)

    def get(self) -> dict:
        with self._lock:
            return self._read()

    def update(self, fn) -> dict:
        with self._lock:
            data = self._read()
            fn(data)
            self._write(data)
            return data

    # High-level helpers
    def inc_stat(self, key: str, by: int = 1):
        def _fn(d):
            d["stats"][key] = d["stats"].get(key, 0) + by
        self.update(_fn)

    def inc_user(self, user_id: int, key: str, by: int = 1):
        def _fn(d):
            per = d["stats"]["per_user"]
            user = per.get(str(user_id), {"requests":0, "render_success":0})
            user[key] = user.get(key, 0) + by
            per[str(user_id)] = user
        self.update(_fn)

    def lists(self) -> tuple[list[int], list[int]]:
        d = self.get()
        return d["config"]["whitelist"], d["config"]["blacklist"]

    def set_public(self, enabled: bool):
        self.update(lambda d: d["config"].__setitem__("public_enabled", enabled))

    def modify_list(self, list_name: str, add: list[int] | None = None, remove: list[int] | None = None):
        add = add or []
        remove = remove or []
        def _fn(d):
            cur: list[int] = d["config"][list_name]
            cur = list(sorted(set([*cur, *add]) - set(remove)))
            d["config"][list_name] = cur
        self.update(_fn)

    def config(self) -> dict:
        return self.get()["config"]
