import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def _bool(v: str | None, default: bool) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1","true","yes","on"}

def _int_list(v: str | None) -> list[int]:
    if not v:
        return []
    out = []
    for p in v.split(","):
        p = p.strip()
        if p:
            try:
                out.append(int(p))
            except ValueError:
                pass
    return out

@dataclass
class Config:
    bot_token: str = os.getenv("BOT_TOKEN","")
    admin_ids: list[int] = None  # type: ignore
    public_enabled: bool = _bool(os.getenv("PUBLIC_ENABLED"), True)
    api_host: str = os.getenv("API_HOST","0.0.0.0")
    api_port: int = int(os.getenv("API_PORT","8000"))
    api_token: str = os.getenv("API_TOKEN","")
    render_width: int = int(os.getenv("RENDER_WIDTH","1024"))

    def __post_init__(self):
        if self.admin_ids is None:
            self.admin_ids = _int_list(os.getenv("ADMIN_IDS"))

cfg = Config()
