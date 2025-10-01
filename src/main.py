from __future__ import annotations
import asyncio, uvicorn, os
from .config import cfg
from .api_server import app
from .bot import BotApp

async def run_api():
    config = uvicorn.Config(app, host=cfg.api_host, port=cfg.api_port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def run_bot():
    bot = BotApp()
    await bot.run_polling()

async def main():
    await asyncio.gather(run_api(), run_bot())

if __name__ == "__main__":
    asyncio.run(main())
