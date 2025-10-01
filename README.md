# MD2ImageBot

一个把 **Markdown** 自动转换为 **图片** 的 Telegram 机器人，支持：

- 发送/回复 Markdown 文本，机器人返回渲染后的 PNG 图片
- 管理员控制：是否公开使用、黑名单/白名单、查看运行状态与统计
- 预留 **HTTP API** 与 **插件机制**，便于未来拓展（如：加入群组/频道后自动转换帖子）
- 一键脚本 `setup.sh`：下载依赖、安装浏览器、生成 `.env`、引导填写信息

> 渲染实现：Markdown → HTML（本地 CSS）→ 无头 Chromium 截图（Playwright）→ PNG。**不会加载外部资源**，安全可靠。

## 快速开始

1. 向 **BotFather** 创建机器人，拿到 `BOT_TOKEN`。
2. 克隆本仓库并执行：

```bash
./setup.sh
# 按提示填写 .env 配置
# 完成后执行：
source .venv/bin/activate && python -m src.main
```

> 首次运行会自动安装 Playwright 的 Chromium。

## 使用方法

- 私聊或在群组里发送 Markdown 文本（或回复某条 Markdown 文本），机器人将返回渲染后的图片。
- 管理命令（仅管理员可用）：
  - `/public_on` / `/public_off`：打开/关闭公开使用
  - `/status`：查看运行状态与统计
  - `/wl_add 111 222`、`/wl_remove 111 222`：增删白名单
  - `/bl_add 111 222`、`/bl_remove 111 222`：增删黑名单
  - `/wl_list`、`/bl_list`：查看名单

> 如果关闭公开使用，仅**管理员与白名单**可用。黑名单**始终**无权使用。

## 群组/频道自动转换（插件）

项目内置插件 **`channel_autoconvert`**，当机器人加入频道（并具备读取消息权限）后，可自动将新发的 Markdown 帖子转换为图片并在频道中回帖。可在 `state.json` 的 `enabled_plugins` 中开关。

> 若要让机器人在群组/频道里读取消息，请在 [@BotFather](https://t.me/BotFather) 设置 **Disable Privacy Mode**（关闭隐私模式），并给予相应权限。

## HTTP API

本项目自带 FastAPI 服务（默认 `http://0.0.0.0:8000`），并通过 `X-API-Key` 鉴权。详见 **[API.md](API.md)**。

## 配置

所有配置从 `.env` 读取：

- `BOT_TOKEN`：Telegram 机器人 Token
- `ADMIN_IDS`：管理员用户 ID，逗号分隔
- `PUBLIC_ENABLED`：是否公开使用（`true`/`false`）
- `API_HOST` / `API_PORT`：API 监听地址与端口
- `API_TOKEN`：API 密钥（通过 `X-API-Key` 传入）
- `RENDER_WIDTH`：渲染宽度（像素）

## 运行状态与数据持久化

- 持久化文件：`storage/state.json`（自动创建）
- 记录内容：开关配置、黑/白名单、统计计数（总请求、成功/失败、用户维度）、启用的插件等
- 运行状态包含：启动时间、累计统计等

## 常见问题

- **渲染失败**：首次运行必须安装浏览器：`python -m playwright install --with-deps chromium`
- **无法在群/频道读消息**：关闭隐私模式，并确保将机器人设为管理员或赋予读取权限。
- **安全性**：渲染时**不加载**任何外部 JS/图片，使用本地 CSS，并添加严格 CSP。

## 许可

MIT
