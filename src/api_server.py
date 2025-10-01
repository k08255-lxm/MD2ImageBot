from __future__ import annotations
import io, json, time
from typing import Annotated

from fastapi import FastAPI, Body, Header, HTTPException, Response
from pydantic import BaseModel

from .config import cfg
from .storage import Storage
from .renderer import Renderer

app = FastAPI(title="MD2ImageBot API", version="1.0.0")

storage = Storage()
renderer = Renderer(width=cfg.render_width)
START_TIME = int(time.time())

def require_api_key(x_api_key: str | None):
    if not x_api_key or x_api_key != cfg.api_token:
        raise HTTPException(status_code=401, detail="invalid api key")

class RenderReq(BaseModel):
    markdown: str
    width: int | None = None

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/render")
async def render_endpoint(
    req: RenderReq,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None
):
    require_api_key(x_api_key)
    png = await renderer.render_markdown(req.markdown, width=req.width)
    storage.inc_stat("total_requests")
    storage.inc_stat("render_success")
    return Response(content=png, media_type="image/png")

@app.get("/stats")
def stats(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None
):
    require_api_key(x_api_key)
    now = int(time.time())
    st = storage.get()
    return {"uptime_seconds": now - START_TIME, "stats": st["stats"], "config": st["config"]}

class PublicReq(BaseModel):
    enabled: bool

@app.post("/admin/config/public")
def admin_public(req: PublicReq, x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None):
    require_api_key(x_api_key)
    storage.set_public(bool(req.enabled))
    return {"public_enabled": storage.config().get("public_enabled", True)}

class ListReq(BaseModel):
    add: list[int] | None = None
    remove: list[int] | None = None

@app.post("/admin/whitelist")
def admin_whitelist(req: ListReq, x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None):
    require_api_key(x_api_key)
    storage.modify_list("whitelist", add=req.add, remove=req.remove)
    return {"whitelist": storage.config().get("whitelist", [])}

@app.post("/admin/blacklist")
def admin_blacklist(req: ListReq, x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None):
    require_api_key(x_api_key)
    storage.modify_list("blacklist", add=req.add, remove=req.remove)
    return {"blacklist": storage.config().get("blacklist", [])}
