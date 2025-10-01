from __future__ import annotations
import asyncio, io, time
from typing import Optional

from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from .config import cfg
from .storage import Storage
from .renderer import Renderer
from .utils import parse_ints

# Globals
START_TIME = int(time.time())

class BotApp:
    def __init__(self):
        self.storage = Storage()
        self.renderer = Renderer(width=cfg.render_width)
        self.app = Application.builder().token(cfg.bot_token).build()
        self._register_handlers()
        self._load_plugins()

    # ---------- Permissions ----------
    def _is_admin(self, uid: int) -> bool:
        return uid in cfg.admin_ids

    def _is_authorized(self, uid: int) -> bool:
        state = self.storage.get()
        conf = state["config"]
        wl: list[int] = conf["whitelist"]
        bl: list[int] = conf["blacklist"]
        if uid in bl:
            return False
        if self._is_admin(uid):
            return True
        if conf.get("public_enabled", True):
            return True
        return uid in wl

    # ---------- Handlers ----------
    def _register_handlers(self):
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))

        # Admin commands
        self.app.add_handler(CommandHandler("public_on", self.cmd_public_on))
        self.app.add_handler(CommandHandler("public_off", self.cmd_public_off))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("wl_add", self.cmd_wl_add))
        self.app.add_handler(CommandHandler("wl_remove", self.cmd_wl_remove))
        self.app.add_handler(CommandHandler("bl_add", self.cmd_bl_add))
        self.app.add_handler(CommandHandler("bl_remove", self.cmd_bl_remove))
        self.app.add_handler(CommandHandler("wl_list", self.cmd_wl_list))
        self.app.add_handler(CommandHandler("bl_list", self.cmd_bl_list))

        # Content render
        self.app.add_handler(CommandHandler("render", self.cmd_render))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.on_text))

        # Channel posts (basic support even without plugin)
        self.app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, self.on_channel_post))

    def _load_plugins(self):
        from importlib import import_module
        enabled = self.storage.config().get("enabled_plugins", [])
        for name in enabled:
            try:
                mod = import_module(f".plugins.{name}", __package__)
                if hasattr(mod, "register"):
                    mod.register(self.app, self.renderer, self.storage, self)
            except Exception as e:
                print(f"[plugin:{name}] load error: {e}")

    # ---------- Commands ----------
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.effective_message.reply_text(
            "你好！我是 MD2ImageBot。\n"
            "直接发送 Markdown，我会转成图片发回给你。\n"
            "管理员可用 /status /public_on /public_off 等命令。"
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.effective_message.reply_text(
            "使用：直接发送 Markdown 文本，或用 /render 命令（可回复某条消息）。\n"
            "管理员命令：/status /public_on /public_off /wl_add /wl_remove /bl_add /bl_remove /wl_list /bl_list"
        )

    async def cmd_public_on(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not self._is_admin(uid):
            return
        self.storage.set_public(True)
        await update.effective_message.reply_text("已开启公开使用。")

    async def cmd_public_off(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not self._is_admin(uid):
            return
        self.storage.set_public(False)
        await update.effective_message.reply_text("已关闭公开使用（仅管理员与白名单可用）。")

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not self._is_admin(uid):
            return
        st = self.storage.get()
        uptime = int(time.time()) - START_TIME
        stats = st["stats"]
        conf = st["config"]
        msg = (
            f"🟢 运行中\n"
            f"Uptime: {uptime}s\n"
            f"公开使用: {conf.get('public_enabled', True)}\n"
            f"白名单: {len(conf.get('whitelist', []))} 人\n"
            f"黑名单: {len(conf.get('blacklist', []))} 人\n"
            f"总请求: {stats.get('total_requests',0)}\n"
            f"成功: {stats.get('render_success',0)} / 失败: {stats.get('render_failed',0)}\n"
        )
        await update.effective_message.reply_text(msg)

    async def cmd_wl_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_admin(update.effective_user.id):
            return
        ids = parse_ints(context.args)
        self.storage.modify_list("whitelist", add=ids)
        await update.effective_message.reply_text(f"已加入白名单: {ids}")

    async def cmd_wl_remove(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_admin(update.effective_user.id):
            return
        ids = parse_ints(context.args)
        self.storage.modify_list("whitelist", remove=ids)
        await update.effective_message.reply_text(f"已移出白名单: {ids}")

    async def cmd_bl_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_admin(update.effective_user.id):
            return
        ids = parse_ints(context.args)
        self.storage.modify_list("blacklist", add=ids)
        await update.effective_message.reply_text(f"已加入黑名单: {ids}")

    async def cmd_bl_remove(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_admin(update.effective_user.id):
            return
        ids = parse_ints(context.args)
        self.storage.modify_list("blacklist", remove=ids)
        await update.effective_message.reply_text(f"已移出黑名单: {ids}")

    async def cmd_wl_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_admin(update.effective_user.id):
            return
        wl, _ = self.storage.lists()
        await update.effective_message.reply_text(f"白名单: {wl}")

    async def cmd_bl_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_admin(update.effective_user.id):
            return
        _, bl = self.storage.lists()
        await update.effective_message.reply_text(f"黑名单: {bl}")

    async def cmd_render(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update.effective_user.id):
            await update.effective_message.reply_text("当前不可使用（未开放或不在白名单）。")
            return
        msg = update.effective_message
        text = " ".join(context.args) if context.args else (msg.reply_to_message.text if msg.reply_to_message else None)
        if not text:
            await msg.reply_text("请发送 /render <markdown> 或回复一条包含 Markdown 的消息。")
            return
        await self._render_and_reply(update, text)

    async def on_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_authorized(update.effective_user.id):
            return
        text = update.effective_message.text or ""
        if not text.strip():
            return
        await self._render_and_reply(update, text)

    async def on_channel_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Fallback: if plugin not loaded, still try to render
        post = update.channel_post
        if not post or not (post.text or post.caption):
            return
        text = post.text or post.caption or ""
        if not text.strip():
            return
        try:
            png = await self.renderer.render_markdown(text)
            bio = io.BytesIO(png); bio.name = "render.png"
            await post.reply_document(document=InputFile(bio), caption="已自动转换为图片")
            self.storage.inc_stat("total_requests")
            self.storage.inc_stat("render_success")
        except Exception as e:
            self.storage.inc_stat("total_requests")
            self.storage.inc_stat("render_failed")
            print(f"channel_post render error: {e}")

    async def _render_and_reply(self, update: Update, text: str):
        msg = update.effective_message
        uid = update.effective_user.id
        self.storage.inc_stat("total_requests")
        self.storage.inc_user(uid, "requests")
        try:
            png = await self.renderer.render_markdown(text)
            bio = io.BytesIO(png); bio.name = "render.png"
            await msg.reply_document(document=InputFile(bio), caption="✅ 已转换为图片")
            self.storage.inc_stat("render_success")
            self.storage.inc_user(uid, "render_success")
        except Exception as e:
            self.storage.inc_stat("render_failed")
            await msg.reply_text(f"❌ 渲染失败：{e}")

    async def run_polling(self):
        await self.app.initialize()
        print("Bot started. Polling updates...")
        await self.app.start()
        await self.app.updater.start_polling()
        await self.app.updater.wait()
        await self.app.stop()

async def main():
    app = BotApp()
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
