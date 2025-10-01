from __future__ import annotations
import io
from telegram import InputFile, Update
from telegram.ext import ContextTypes, MessageHandler, filters

def register(app, renderer, storage, botapp):
    async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
        post = update.channel_post
        if not post:
            return
        text = post.text or post.caption or ""
        if not text.strip():
            return
        try:
            png = await renderer.render_markdown(text)
            bio = io.BytesIO(png); bio.name = "render.png"
            await post.reply_document(document=InputFile(bio), caption="📸 自动转换")
            storage.inc_stat("total_requests")
            storage.inc_stat("render_success")
        except Exception as e:
            storage.inc_stat("total_requests")
            storage.inc_stat("render_failed")
            print(f"[channel_autoconvert] error: {e}")

    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, handle_channel_post), group=1)
