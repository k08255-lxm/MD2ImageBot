from __future__ import annotations
from typing import Iterable

def parse_ints(parts: Iterable[str]) -> list[int]:
    out = []
    for p in parts:
        try:
            out.append(int(p))
        except ValueError:
            pass
    return out
